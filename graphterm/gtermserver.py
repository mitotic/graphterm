#!/usr/bin/env python

"""gtermserver: WebSocket server for GraphTerm
"""

import base64
import cgi
import collections
import datetime
import email.utils
import functools
import hashlib
import hmac
import logging
import os
import Queue
import re
import ssl
import stat
import subprocess
import sys
import threading
import time
import urllib
import urlparse
import uuid

import random
try:
    random = random.SystemRandom()
except NotImplementedError:
    import random

try:
    import ujson as json
except ImportError:
    import json

try:
    import otrace
except ImportError:
    otrace = None

import about
import gtermhost
import lineterm
import optconfig
import packetserver

from bin import gterm

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

APPS_URL = "/"+gterm.STATIC_PATH

File_dir = os.path.dirname(__file__)
if File_dir == ".":
    File_dir = os.getcwd()    # Need this for daemonizing to work?
    
Doc_rootdir = os.path.join(File_dir, "www")
Auto_add_file = os.path.join(gterm.App_dir, "AUTO_ADD_USERS")

Log_filename = os.path.join(gterm.App_dir, "graphterm.log")
Log_file = None

Check_state_cookie = False             # Controls checking of state cookie for file access

Cache_files = False                     # Controls caching of files (blobs are always cached)

MAX_COOKIE_STATES = 100
MAX_WEBCASTS = 500
MAX_RECURSION = 10

MAX_CACHE_TIME = 86400

COOKIE_NAME = "GRAPHTERM_AUTH"
COOKIE_TIMEOUT = 10800

REQUEST_TIMEOUT = 15

AUTH_DIGITS = 12    # Form authentication code hex-digits
                    # Note: Less than half of the 32 hex-digit state id should be used for form authentication

PROTOCOL = "http"

LOCAL_HOST = "local"

HOME_MNT = "/home"

RSS_FEED_URL = "http://code.mindmeldr.com/graphterm/graphterm-announce/posts.xml"

def cgi_escape(s):
    return cgi.escape(s) if s else ""

Episode4 = """


        Episode IV
        A NEW HOPE

It is a period of civil war. Rebel
spaceships, striking from a
hidden base, have won their
first victory against the evil
Galactic Empire.

During the battle, Rebel spies
managed to steal secret plans to
the Empire's ultimate weapon,
the DEATH STAR, an armored
space station with enough
power to destroy an entire
planet.

Pursued by the Empire's sinister
agents, Princess Leia races
home aboard her starship,
custodian of the stolen plans
that can save her people and
restore freedom to the galaxy....

"""
                                
class BlockingCall(object):
    """ Class to execute a blocking function in a separate thread and callback with return value.
    """
    def __init__(self, callback, timeout, io_loop=None):
        """ Setup callback and timeout for blocking call
        """
        self.callback = callback
        self.timeout = timeout
        self.io_loop = io_loop or IO_loop
        
    def call(self, func, *args, **kwargs):
        """ Execute non-blocking call
        """
        def execute_in_thread():
            try:
                self.handle_callback(func(*args, **kwargs))
            except Exception, excp:
                self.handle_callback(excp)

        if self.timeout:
            IO_loop.add_timeout(time.time()+self.timeout, functools.partial(self.handle_callback, Exception("Timed out")))
        thrd = threading.Thread(target=execute_in_thread)
        thrd.start()

    def handle_callback(self, ret_value):
        if not self.callback:
            return
        callback = self.callback
        self.callback = None
        self.io_loop.add_callback(functools.partial(callback, ret_value))

server_cert_gen_cmds = [
    'openssl genrsa -out %(hostname)s.key %(keysize)d',
    'openssl req -new -key %(hostname)s.key -out %(hostname)s.csr -batch -subj "/O=GraphTerm/CN=%(hostname)s"',
    'openssl x509 -req -days %(expdays)d -in %(hostname)s.csr -signkey %(hostname)s.key -out %(hostname)s.crt',
    'openssl x509 -noout -fingerprint -in %(hostname)s.crt',
    ]

client_cert_gen_cmds = [
    'openssl genrsa -out %(clientprefix)s.key %(keysize)d',
    'openssl req -new -key %(clientprefix)s.key -out %(clientprefix)s.csr -batch -subj "/O=GraphTerm/CN=%(clientname)s"',
    'openssl x509 -req -days %(expdays)d -in %(clientprefix)s.csr -CA %(hostname)s.crt -CAkey %(hostname)s.key -set_serial 01 -out %(clientprefix)s.crt',
    "openssl pkcs12 -export -in %(clientprefix)s.crt -inkey %(clientprefix)s.key -out %(clientprefix)s.p12 -passout pass:%(clientpassword)s"
    ]

def ssl_cert_gen(hostname="localhost", clientname="gterm-local", cwd=None, new=False):
    """Return fingerprint of self-signed server certficate, creating a new one, if need be"""
    params = {"hostname": hostname, "keysize": 1024, "expdays": 1024,
              "clientname": clientname, "clientprefix":"%s-%s" % (hostname, clientname),
              "clientpassword": "password",}
    cmd_list = server_cert_gen_cmds if new else server_cert_gen_cmds[-1:]
    for cmd in cmd_list:
        cmd_args = lineterm.shlex_split_str(cmd % params)
        std_out, std_err = gterm.command_output(cmd_args, cwd=cwd, timeout=15)
        if std_err:
            logging.warning("gtermserver: SSL keygen %s %s", std_out, std_err)
    fingerprint = std_out
    if new:
        for cmd in client_cert_gen_cmds:
            cmd_args = lineterm.shlex_split_str(cmd % params)
            std_out, std_err = gterm.command_output(cmd_args, cwd=cwd, timeout=15)
            if std_err:
                logging.warning("gtermserver: SSL client keygen %s %s", std_out, std_err)
    return fingerprint

def get_user(ws):
    return ws.authorized.get("user", "") if ws and ws.authorized else ""

class GTSocket(tornado.websocket.WebSocketHandler):
    _all_websockets = {}
    _all_paths = collections.defaultdict(set)
    _all_users = collections.defaultdict(set)
    _control_set = collections.defaultdict(set)
    _control_params = collections.defaultdict(dict)
    _watch_dict = collections.defaultdict(dict)
    _counter = [0]
    _webcast_paths = OrderedDict()
    _cookie_states = OrderedDict()
    _auth_users = OrderedDict()
    WEBCAST_AUTH, NULL_AUTH, NAME_AUTH, LOCAL_AUTH, MULTI_AUTH = range(5)
    # Note: WEBCAST_AUTH is used only for sockets, not for the server
    _auth_code = uuid.uuid4().hex[:gterm.HEX_DIGITS]
    _auth_type = LOCAL_AUTH
    _wildcards = {}
    _super_users = set()
    _connect_cookies = OrderedDict()

    @classmethod
    def set_super_users(cls, users=[]):
        cls._super_users = set(users)

    @classmethod
    def is_super_user(cls, user):
        return user and user in cls._super_users

    @classmethod
    def set_auth_code(cls, value, local=False):
        cls._auth_code = value
        if not value:
            cls._auth_type = cls.NULL_AUTH
        elif value == "name":
            cls._auth_type = cls.NAME_AUTH
        else:
            cls._auth_type = cls.LOCAL_AUTH if local else cls.MULTI_AUTH

    @classmethod
    def get_auth_code(cls):
        return cls._auth_code

    @classmethod
    def get_auth_type(cls):
        return cls._auth_type

    @classmethod
    def get_connect_cookie(cls):
        while len(cls._connect_cookies) > 100:
            cls._connect_cookies.popitem(last=False)
        new_cookie = uuid.uuid4().hex[:12]
        cls._connect_cookies[new_cookie] = 1
        return new_cookie

    @classmethod
    def check_connect_cookie(cls, value):
        return cls._connect_cookies.pop(value, None)            

    @classmethod
    def get_terminal_params(cls, path):
        return cls._control_params.get(path)
    
    @classmethod
    def get_path_set(cls, path):
        return cls._all_paths.get(path, set())
    
    def __init__(self, *args, **kwargs):
        self.request = args[1]
        try:
            self.client_cert = self.request.get_ssl_certificate()
        except Exception:
            self.client_cert = ""

        self.common_name = ""
        if self.client_cert:
            try:
                subject = dict([x[0] for x in self.client_cert["subject"]])
                self.common_name = subject.get("commonName")
            except Exception, excp:
                logging.warning("gtermserver: client_cert ERROR %s", excp)
        if self.client_cert or self.client_cert:
            logging.warning("gtermserver: client_cert=%s, name=%s", self.client_cert, self.client_cert)
        rpath, sep, self.request_query = self.request.uri.partition("?")
        self.req_path = "/".join(rpath.split("/")[2:])  # Strip out /_websocket from path
        if self.req_path.endswith("/"):
            self.req_path = self.req_path[:-1]

        super(GTSocket, self).__init__(*args, **kwargs)

        self.authorized = None
        self.remote_path = None
        self.wildcard = None
        self.websocket_id = None
        self.oshell = None
        self.last_output = None

    def allow_draft76(self):
        return True

    @classmethod
    def get_state(cls, state_id):
        if state_id not in cls._cookie_states:
            return None
        state_value = cls._cookie_states[state_id]
        ##if cls._auth_type >= cls.LOCAL_AUTH and (time.time() - state_value["time"]) > COOKIE_TIMEOUT:
        ##    del cls._cookie_states[state_id]
        ##    return None
        return state_value

    @classmethod
    def drop_state(cls, state_id):
        cls._cookie_states.pop(state_id, None)

    @classmethod
    def add_state(cls, user, auth_type):
        state_id = "" if auth_type == cls.WEBCAST_AUTH else uuid.uuid4().hex
        authorized = {"user": user, "auth_type": auth_type, "state_id": state_id,
                      "time": time.time()}
        if not state_id:
            return authorized
        if len(cls._cookie_states) >= MAX_COOKIE_STATES:
            cls._cookie_states.pop(last=False)
        cls._cookie_states[state_id] = authorized
        return authorized

    def open(self):
        need_code = self._auth_type >= self.LOCAL_AUTH
        need_user = self._auth_type == self.NAME_AUTH or self._auth_type >= self.MULTI_AUTH

        user = ""
        try:
            auth_message = "Please authenticate"
            if COOKIE_NAME in self.request.cookies:
                state_value = self.get_state(self.request.cookies[COOKIE_NAME].value)
                if state_value:
                    if state_value["auth_type"] == self._auth_type:
                        self.authorized = state_value
                        user = self.authorized["user"]
                    else:
                        # Note: webcast auth will always be dropped
                        self.drop_state(self.request.cookies[COOKIE_NAME].value)
                        auth_message = "Authentication expired"

            query_data = {}
            if self.request_query:
                try:
                    query_data = urlparse.parse_qs(self.request_query)
                except Exception:
                    pass

            cauth = query_data.get("cauth", [""])[0]
            if not self.check_connect_cookie(cauth):
                cauth = None

            if not Server_settings["allow_embed"] and "embedded" in query_data:
                self.write_json([["body", "Terminal cannot be embedded in web page on different host"]])
                self.close()
                return

            new_auto_user = False
            if not self.authorized:
                if self._auth_type == self.NULL_AUTH:
                    # No authorization code needed
                    self.authorized = self.add_state("", self.NULL_AUTH)
                else:
                    user = query_data.get("user", [""])[0].lower()
                    code = query_data.get("code", [""])[0]

                    if user and (user == LOCAL_HOST or not gtermhost.USER_RE.match(user)):
                        # Username "local" is not allowed to prevent localhost access
                        self.write_json([["abort", "Invalid username '%s'; must start with letter and include only letters/digits/hyphen" % user]])
                        self.close()
                        return

                    if not user:
                        if not code and self.req_path in self._webcast_paths:
                            pass
                        elif self._auth_type == self.LOCAL_AUTH:
                            if code == gterm.compute_hmac(self._auth_code, cauth):
                                self.authorized = self.add_state(user, self._auth_type)
                            else:
                                auth_message = "Enter authentication code (found in %s), or use 'gterm' command" % gterm.get_auth_filename(server=Server_settings["host"])
                        else:
                            auth_message = "Please specify username (letters/digits/hyphens, starting with letter)."
                            if Server_settings["auto_users"] and os.path.exists(Auto_add_file):
                                auth_message += " If new user, leave code blank."
                    elif self._auth_type == self.NAME_AUTH:
                        # Name-only authentication
                        if user not in self._all_users:
                            # New named user
                            self.authorized = self.add_state(user, self.NAME_AUTH)
                        else:
                            auth_message = "User name %s already in use" % user
                    else:
                        validated = False
                        if code == gterm.compute_hmac(self._auth_code, cauth):
                            # Validation using master secret
                            validated = True
                        elif self._auth_users:
                            if user in self._auth_users:
                                validated = (code == gterm.compute_hmac(self._auth_users[user], cauth))
                        else:
                            if not self.is_super_user(user) and Server_settings["auto_users"] and os.path.exists(Auto_add_file) and not os.path.exists(HOME_MNT+"/"+user):
                                # New auto user; no code validation required
                                validated = True
                                new_auto_user = True
                                if not os.path.exists(gterm.SETUP_USER_CMD):
                                    self.write_json([["abort", "Unable to create new user"]])
                                    self.close()
                                    return
                                cmd_args = ["sudo", gterm.SETUP_USER_CMD, user, Server_settings["host"]]
                                std_out, std_err = gterm.command_output(cmd_args, timeout=15)
                                if std_err:
                                    logging.warning("gtermserver: ERROR in %s %s %s", gterm.SETUP_USER_CMD, std_out, std_err)
                                    self.write_json([["abort", "Error in creating new user "+user]])
                                    self.close()
                                    return
                                if Log_file:
                                    Log_file.write("Created new user: %s\n" % user)
                                    Log_file.flush()
                            else:
                                # Non-auto user, super user, or existing auto user; need to validate with user auth code
                                key_version = "1" if self._auth_type >= self.MULTI_AUTH else None
                                validated = (code == gterm.compute_hmac(gterm.user_hmac(self._auth_code, user, key_version=key_version), cauth))

                        if validated:
                            # User auth code matched
                            self.authorized = self.add_state(user, self.MULTI_AUTH)
                        else:
                            auth_message = "Authentication failed; check user/code"

            if not self.authorized:
                if self.req_path in self._webcast_paths:
                    self.authorized = self.add_state(user, self.WEBCAST_AUTH)
                else:
                    self.write_json([["authenticate", need_user, need_code, self.get_connect_cookie(), auth_message]])
                    self.close()
                    return

            qauth = query_data.get("qauth", [""])[0]
            if not Server_settings["no_formcheck"] and not cauth and (not qauth or qauth != self.authorized["state_id"][:AUTH_DIGITS]):
                # Invalid query auth; clear any form data (always cleared for webcasts and when user is first authorized)
                query_data = {}

            if not Server_settings["no_formcheck"] and not query_data and self.req_path not in self._webcast_paths:
                # Confirm path, if no form data and not webcasting
                if self.req_path:
                    self.write_json([["confirm_path", self.authorized["state_id"], "/"+self.req_path]])
                    self.close()
                    return
                else:
                    path_comps = []
            else:
                path_comps = self.req_path.split("/")

            is_local = (self.authorized["auth_type"] == self.LOCAL_AUTH and self._auth_type == self.LOCAL_AUTH)
            is_super_user = self.is_super_user(user) or is_local

            if len(path_comps) < 1 or not path_comps[0]:
                host_list = TerminalConnection.get_connection_ids()
                if self._auth_type >= self.MULTI_AUTH and not is_super_user:
                    if Server_settings["allow_share"]:
                        ##if LOCAL_HOST in host_list:
                        ##    host_list.remove(LOCAL_HOST)
                        pass
                    else:
                        if user in host_list:
                            host_list = [ user ]
                        else:
                            host_list = []
                host_list.sort()
                self.write_json([["host_list", self.authorized["state_id"], user, new_auto_user, host_list]])
                self.close()
                return

            host = path_comps[0].lower()
            if not host or not gtermhost.HOST_RE.match(host):
                self.write_json([["abort", "Invalid characters in host name"]])
                self.close()
                return

            if self._auth_type >= self.MULTI_AUTH and not is_super_user:
                ##if host == LOCAL_HOST:
                ##    self.write_json([["abort", "Local host access not allowed for user %s" % user]])
                ##    self.close()
                ##    return
                if not Server_settings["allow_share"] and host != user:
                    self.write_json([["abort", "Inaccesible host %s" % host]])
                    self.close()
                    return

            wildhost = is_wildcard(host)
            term_feedback = False
            conn = None
            
            option = path_comps[2] if len(path_comps) > 2 else ""
            if wildhost:
                allow_wild_host = (not self._super_users and self._auth_type <= self.LOCAL_AUTH) or is_super_user
                if not allow_wild_host:
                    self.write_json([["abort", "User not authorized for wildcard host"]])
                    self.close()
                    return
                if len(path_comps) < 2 or not path_comps[1] or path_comps[1].lower() == "new":
                    self.write_json([["abort", "Must specify terminal name for wildcard host"]])
                    self.close()
                    return
                term_name = path_comps[1].lower()
            else:
                conn = TerminalConnection.get_connection(host)
                if not conn:
                    self.write_json([["abort", "Invalid host"]])
                    self.close()
                    return

                if len(path_comps) < 2 or not path_comps[1]:
                    term_list = []
                    for term_name in conn.term_dict:
                        path = host + "/" + term_name
                        tparams = self._control_params.get(path)
                        if tparams and (not tparams["share_private"] or is_local or (user and user == tparams["owner"]) or (not user and tparams["state_id"] == self.authorized["state_id"])):
                            term_list.append(term_name)
                    term_list.sort()
                    allow_new = self._auth_type <= self.LOCAL_AUTH or (user and user == host) or (is_super_user and host == "local")
                    self.write_json([["term_list", self.authorized["state_id"], user, host, allow_new, term_list]])
                    self.close()
                    return

                term_name = path_comps[1].lower()
                if term_name == "new" or not qauth:
                    term_name = conn.remote_terminal_update(parent=option) if term_name == "new" else term_name
                    redir_url = "/"+host+"/"+term_name+"/"
                    if self.request_query and qauth:
                        redir_url += "?"+self.request_query
                    else:
                        redir_url += "?qauth="+self.authorized["state_id"][:AUTH_DIGITS]
                    self.write_json([["redirect", redir_url, self.authorized["state_id"]]])
                    self.close()
                    return
                
                if not gtermhost.SESSION_RE.match(term_name):
                    self.write_json([["abort", "Invalid characters in terminal name"]])
                    self.close()
                    return

                term_feedback = term_name in conn.allow_feedback

            path = host + "/" + term_name

            if self.authorized["state_id"] in self._watch_dict[path].values():
                if not option:
                    self.write_json([["abort", "Already connected to this terminal from different window"]])
                    self.close()
                    return
                if self._watch_dict[path].values().count(self.authorized["state_id"]) > MAX_RECURSION:
                    self.write_json([["body", "Max recursion level exceeded!"]])
                    self.close()
                    return

            if path not in self._control_params:
                # Initialize parameters for new terminal
                allow_host_access = (self.authorized["auth_type"] > self.WEBCAST_AUTH) and (self._auth_type <= self.LOCAL_AUTH or (host != LOCAL_HOST and host == user) or (host == LOCAL_HOST and is_super_user))
                if not allow_host_access:
                    self.write_json([["abort", "Unable to create terminal on host %s" % host]])
                    self.close()
                    return
                terminal_params = {"share_locked": self._auth_type > self.LOCAL_AUTH,
                                   "share_private": self._auth_type > self.LOCAL_AUTH,
                                   "share_tandem": False,
                                   "owner": user, "state_id": self.authorized["state_id"]}
                terminal_params.update(Term_settings)
                self._control_params[path] = terminal_params
                is_owner = True
            else:
                # Existing terminal
                terminal_params = self._control_params[path]
                is_owner = is_local or (user and user == terminal_params["owner"]) or (not user and self.authorized["state_id"] == terminal_params["state_id"])
                if terminal_params["share_private"] and not is_owner:
                    # No sharing
                    self.write_json([["abort", "Invalid terminal path: %s" % path]])
                    self.close()
                    return

            if option == "kill":
                if not wildhost and (is_super_user or is_owner):
                    kill_remote(path, user)
                else:
                    self.close()
                return

            self.oshell = (term_name == gtermhost.OSHELL_NAME)

            self._counter[0] += 1
            self.websocket_id = str(self._counter[0])

            if is_wildcard(path):
                allow_wild_card = (not self._super_users and self.authorized["auth_type"] > self.NULL_AUTH and self._auth_type <= self.LOCAL_AUTH) or is_super_user or (host != LOCAL_HOST and host == user)
                if not allow_wild_card:
                    self.write_json([["abort", "User not authorized for wildcard path"]])
                    self.close()
                    return
                self.wildcard = wildcard2re(path)
                self._wildcards[self.websocket_id] = self.wildcard
                # Wildcard terminals are always private
                terminal_params["share_private"] = True
                terminal_params["share_locked"] = True

            assert self.websocket_id not in self._watch_dict[path]

            controller = False
            if self.authorized["auth_type"] == self.WEBCAST_AUTH:
                controller = False
            elif self._auth_type >= self.MULTI_AUTH and not is_super_user and not is_owner:
                controller = False
            elif self.wildcard:
                controller = True
            elif option == "steal" and (is_owner or not terminal_params["share_locked"]):
                controller = True
                if terminal_params["share_tandem"]:
                    self._control_set[path].add(self.websocket_id)
                else:
                    self.broadcast(path, ["update_menu", "share_control", False], controller=True)
                    self._control_set[path] = set([self.websocket_id])
            elif not self._control_set.get(path) and option != "watch" and (is_owner or self._auth_type == self.LOCAL_AUTH):
                controller = True
                self._control_set[path] = set([self.websocket_id])

            self.remote_path = path
            self._all_websockets[self.websocket_id] = self
            self._all_paths[self.remote_path].add(self.websocket_id)
            if user:
                self._all_users[user].add(self.websocket_id)

            self._watch_dict[path][self.websocket_id] = self.authorized["state_id"]
            self.broadcast(path, ["join", get_user(self), True])

            display_splash = controller and self._counter[0] <= 2
            normalized_host, host_secret = "", ""
            if not self.wildcard:
                TerminalConnection.send_to_connection(host, "request", term_name, user, [["reconnect", self.websocket_id]])
                normalized_host = gtermhost.get_normalized_host(host)
                if self.authorized["auth_type"] > self.WEBCAST_AUTH:
                    host_secret = TerminalConnection.host_secrets.get(normalized_host)

            parent_term = conn.term_dict.get(term_name, "") if conn else ""
            state_values = terminal_params.copy()
            state_values.pop("state_id", None)
            state_values["share_webcast"] = bool(path in self._webcast_paths)
            state_values["allow_webcast"] = bool(self._auth_type <= self.LOCAL_AUTH or is_super_user or Server_settings["allow_share"])
            users = [get_user(self._all_websockets.get(ws_id)) for ws_id in self._watch_dict[self.remote_path]]
            self.write_json([["setup", {"user": user, "host": host, "term": term_name, "oshell": self.oshell,
                                        "host_secret": host_secret, "normalized_host": normalized_host,
                                        "about_version": about.version, "about_authors": about.authors,
                                        "about_url": about.url, "about_description": about.description,
                                        "state_values": state_values, "watchers": users,
                                        "controller": controller, "super_user": is_super_user, "parent_term": parent_term,
                                        "wildcard": bool(self.wildcard), "display_splash": display_splash,
                                        "apps_url": APPS_URL, "feedback": term_feedback, "update_opts": {},
                                        "state_id": self.authorized["state_id"]}]])
        except Exception, excp:
            import traceback
            errmsg = "%s\n%s" % (excp, traceback.format_exc())
            logging.warning("GTSocket.open: ERROR (%s:%s) %s", self.remote_path, get_user(self), errmsg)
            self.close()

    def broadcast(self, path, msg, controller=False, include_self=False):
        ws_ids = self._control_set[path] if controller else self._watch_dict[path]
        for ws_id in ws_ids:
            ws = self._all_websockets.get(ws_id)
            if ws and (ws_id != self.websocket_id or include_self):
                ws.write_json([msg])

    def on_close(self):
        if self.authorized:
            user = self.authorized["user"]
            if user:
                user_socket_ids = self._all_users.get(user)
                if user_socket_ids:
                    user_socket_ids.discard(self.websocket_id)

        if self.remote_path in self._control_set:
             self._control_set[self.remote_path].discard(self.websocket_id)

        if self.remote_path in self._watch_dict:
            if self.websocket_id in self._watch_dict[self.remote_path]:
                self._watch_dict[self.remote_path].pop(self.websocket_id, None)
                self.broadcast(self.remote_path, ["join", get_user(self), False])

        if self.wildcard:
            self._wildcards.pop(self.websocket_id, None)
        self._all_websockets.pop(self.websocket_id, None)
        if self.remote_path in self._all_paths:
            self._all_paths[self.remote_path].discard(self.websocket_id)

    def write_json(self, data):
        try:
            self.write_message(json.dumps(data))
        except Exception, excp:
            logging.error("write_json: ERROR %s", excp)
            try:
                # Close websocket on write error
                self.close()
            except Exception:
                pass

    def close_watchers(self, keep_controllers=False, close_self=False):
        if self.remote_path not in self._watch_dict:
            return
        controllers = self._control_set.get(self.remote_path, set())
        for ws_id in self._watch_dict[self.remote_path]:
            if ws_id == self.websocket_id and not close_self:
                continue
            if keep_controllers and ws_id in controllers:
                continue
            ws = self._all_websockets.get(ws_id)
            if ws:
                ws.close()

    def on_message(self, message):
        ##logging.warning("GTSocket.on_message: %s", message)
        if not self.remote_path:
            return

        remote_host, term_name = self.remote_path.split("/")

        terminal_params = self._control_params[self.remote_path]

        from_user = self.authorized["user"] if self.authorized else ""

        is_local = (self.authorized["auth_type"] == self.LOCAL_AUTH and self._auth_type == self.LOCAL_AUTH)

        is_super_user = self.is_super_user(from_user) or is_local

        is_owner = is_local or (from_user and from_user == terminal_params["owner"]) or (not from_user and self.authorized["state_id"] == terminal_params["state_id"])

        controller = self.wildcard or (self.remote_path in self._control_set and self.websocket_id in self._control_set[self.remote_path])

        conn = None
        allow_feedback_only = False
        if not self.wildcard:
            conn = TerminalConnection.get_connection(remote_host)
            if not conn:
                self.write_json([["errmsg", "ERROR: Remote host %s not connected" % remote_host]])
                return

            if not controller and term_name in conn.allow_feedback:
                allow_feedback_only = True

        allow_control_request = not terminal_params["share_locked"] and not terminal_params["share_private"] and not self._webcast_paths.get(self.remote_path)
        if is_owner or controller or allow_feedback_only or allow_control_request:
            try:
                msg_list = json.loads(message if isinstance(message,str) else message.encode("UTF-8", "replace"))
                if allow_feedback_only:
                    msg_list = [msg for msg in msg_list if msg[0] == "feedback"]
                elif not controller:
                    msg_list = [msg for msg in msg_list if msg[0] == "update_params" and msg[1] == "share_control"]
            except Exception, excp:
                logging.warning("GTSocket.on_message: ERROR %s", excp)
                self.write_json([["errmsg", str(excp)]])
                return
        else:
            self.write_json([["errmsg", "ERROR: Remote path %s not under control" % self.remote_path]])
            return

        kill_term = False
        req_list = []
        try:
            for msg in msg_list:
                if msg[0] == "osh_stdout":
                    TraceInterface.receive_output("stdout", msg[1], from_user or self.websocket_id, msg[2])

                elif msg[0] == "osh_stderr":
                    TraceInterface.receive_output("stderr", msg[1], from_user or self.websocket_id, msg[2])

                elif msg[0] == "server_log":
                    logging.warning("gtermserver_log: %s", msg[1])
                elif msg[0] == "reconnect_host":
                    if conn:
                        # Close host connection (should automatically reconnect)
                        conn.on_close()
                        return

                elif msg[0] == "check_updates":
                    # Check for announcements/updates
                    try:
                        import feedparser
                    except ImportError:
                        feedparser = None
                    if feedparser and not self.wildcard:
                        blocking_call = BlockingCall(self.updates_callback, 10)
                        blocking_call.call(feedparser.parse, RSS_FEED_URL)
        
                elif msg[0] == "kill_term":
                    kill_term = True

                elif msg[0] == "update_params":
                    # params key value
                    key, value = msg[1], msg[2]
                    if self.wildcard:
                        raise Exception("Cannot change setting for wildcard terminal: %s" % key)
                    elif key == "share_control":
                        if not value:
                            # Give up control
                            self._control_set[self.remote_path].discard(self.websocket_id)
                        elif is_super_user or is_owner or (not terminal_params["share_locked"] and
                                                           (self._auth_type <= self.LOCAL_AUTH or
                                                            (Server_settings["allow_share"] and
                                                             not self.is_super_user(terminal_params["owner"])))):
                            # Gain control
                            if terminal_params["share_tandem"]:
                                # Shared control
                                self._control_set[self.remote_path].add(self.websocket_id)
                            else:
                                # Sole control
                                self.broadcast(self.remote_path, ["update_menu", key, False], controller=True)
                                self._control_set[self.remote_path] = set([self.websocket_id])
                        else:
                            raise Exception("Failed to acquire control of terminal")
                    elif key == "share_tandem":
                        terminal_params["share_tandem"] = value
                        if not value:
                            # No tandem access; restrict control access to self
                            self.broadcast(self.remote_path, ["update_menu", key, False], controller=True)
                            self._control_set[self.remote_path] = set([self.websocket_id])
                        self.broadcast(self.remote_path, ["update_menu", key, value])
                    elif key == "share_webcast":
                        if not terminal_params["share_private"]:
                            if self.remote_path in self._webcast_paths:
                                del self._webcast_paths[self.remote_path]
                            if len(self._webcast_paths) > MAX_WEBCASTS:
                                self._webcast_paths.pop(last=False)
                            if value:
                                # Initiate webcast
                                if self._auth_type <= self.LOCAL_AUTH or (Server_settings["allow_share"] or
                                                                          is_super_user):
                                    self._webcast_paths[self.remote_path] = time.time()
                            else:
                                # Cancel webcast
                                self.close_watchers(keep_controllers=True)
                            self.broadcast(self.remote_path, ["update_menu", key, value])
                    elif key == "share_locked":
                        terminal_params["share_locked"] = value
                        self.broadcast(self.remote_path, ["update_menu", key, value])
                    elif key == "share_private":
                        terminal_params["share_private"] = value
                        if not value:
                            # Share access to terminal
                            self.broadcast(self.remote_path, ["update_menu", key, value])
                        else:
                            # Revert to private mode; close all watchers, excluding self
                            self.close_watchers()
                    else:
                        raise Exception("Invalid setting: %s" % key)
                            
                elif msg[0] == "send_msg":
                    # Send message to other watchers for this session
                    if self.wildcard:
                        continue
                    to_user = msg[1]
                    for ws_id in self._watch_dict.get(self.remote_path, {}):
                        if ws_id == self.websocket_id:
                            continue
                        # Broadcast to all watchers (excluding originator)
                        ws = self._all_websockets.get(ws_id)
                        if not ws:
                            continue
                        ws_user = ws.authorized["user"] if ws.authorized else ""
                        if (not to_user and controller) or to_user == "*" or to_user == ws_user:
                            try:
                                # Change command and add from_user
                                ws.write_message(json.dumps([["receive_msg", from_user] + msg[1:]]))
                            except Exception, excp:
                                logging.error("send_msg: ERROR %s", excp)
                                try:
                                    # Close websocket on write error
                                    ws.close()
                                except Exception:
                                    pass

                elif not kill_term:
                    req_list.append(msg)

            if self.wildcard:
                self.last_output = None
                matchpaths = TerminalConnection.get_matching_paths(self.wildcard, from_user, self.authorized["state_id"], self.authorized["auth_type"])
            else:
                matchpaths = [self.remote_path]

            for matchpath in matchpaths:
                matchhost, matchterm = matchpath.split("/")
                if req_list:
                    TerminalConnection.send_to_connection(matchhost, "request", matchterm, from_user, req_list)
                if kill_term:
                    kill_remote(matchpath, from_user)

        except Exception, excp:
            logging.warning("GTSocket.on_message: ERROR %s", excp)
            self.write_json([["errmsg", str(excp)]])
            return

    def updates_callback(self, feed_data):
        if isinstance(feed_data, Exception):
            self.write_json([["errmsg", "ERROR in checking for updates: %s" % excp]])
        else:
            # Need to filter feed to send only "unread" postings or applicable alerts
            feed_list = [{"title": entry.title, "summary":entry.summary} for entry in feed_data.entries]
            self.write_json([["updates_response", feed_list]])
            logging.warning(feed_data["feed"]["title"])

# OTrace websocket interface
class TraceInterface(object):
    root_depth = 1   # Max. path components for web directory (below /osh/web)
    trace_hook = None

    @classmethod
    def set_web_hook(cls, hook):
        cls.trace_hook = hook

    @classmethod
    def get_root_tree(cls):
        """Returns directory dict tree (with depth=root_depth) that is updated automatically"""
        return GTSocket._all_users or GTSocket._all_websockets

    @classmethod
    def send_command(cls, path_comps, command):
        """ Send command to browser via websocket (invoked in the otrace thread)
        path_comps: path component array (first element identifies websocket)
        command: Javascript expression to be executed on the browser
        """
        # Must be thread-safe
        if GTSocket._all_users:
            websocket_ids = GTSocket._all_users.get(path_comps[0])
            if websocket_ids:
                websocket_id = list(websocket_ids)[0]
            else:
                websocket_id = None
        else:
            websocket_id = path_comps[0]
        websocket = GTSocket._all_websockets.get(websocket_id)
        if not websocket:
            cls.receive_output("stderr", False, "", "No such socket: %s" % path_comps[0])
            return

        # Schedules callback in event loop
        tornado.ioloop.IOLoop.instance().add_callback(functools.partial(websocket.write_message,
                                                                        json.dumps([["osh_stdin", command]])))

    @classmethod
    def receive_output(cls, channel, repeat, username, message):
        """Receive channel="stdout"/"stderr" output from browser via websocket and forward to oshell
        """
        path_comps = [username] if username else []
        cls.trace_hook(channel, repeat, path_comps, message)
            

def xterm(command="", name=None, host="localhost", port=gterm.DEFAULT_HTTP_PORT):
    """Create new terminal"""
    pass

def kill_remote(path, user):
    if path == "*":
        TerminalConnection.shutdown_all()
        return
    for ws_id in GTSocket.get_path_set(path):
        ws = GTSocket._all_websockets.get(ws_id)
        if ws:
            ws.write_json([["body", 'CLOSED<p><a href="/">Home</a>']])
            ws.close()
    host, term_name = path.split("/")
    if term_name == "*": term_name = ""
    try:
        TerminalConnection.send_to_connection(host, "request", term_name, user, [["kill_term"]])
    except Exception, excp:
        pass

def is_wildcard(path):
    return "?" in path or "*" in path or "[" in path

def wildcard2re(path):
    return re.compile("^"+path.replace("+", "\\+").replace(".", "\\.").replace("?", ".?").replace("*", ".*")+"$")

class TerminalConnection(packetserver.RPCLink, packetserver.PacketConnection):
    _all_connections = {}
    host_secrets = {}
    @classmethod
    def get_matching_paths(cls, regexp, user, state_id, auth_type):
        is_super_user = GTSocket.is_super_user(user) or (auth_type == GTSocket.LOCAL_AUTH and GTSocket.get_auth_type() == GTSocket.LOCAL_AUTH)
        matchpaths = []
        for host, conn in cls._all_connections.iteritems():
            for term_name in conn.term_dict:
                path = host + "/" + term_name
                if regexp.match(path):
                    match_params = GTSocket.get_terminal_params(path)
                    if match_params and (is_super_user or (user and user == match_params["owner"]) or
                                         (not user and state_id == match_params["state_id"])):
                        matchpaths.append(path)
        return matchpaths
        
    def __init__(self, stream, address, server_address, key_secret=None, key_version=None, key_id=None, ssl_options={}):
        super(TerminalConnection, self).__init__(stream, address, server_address, server_type="frame",
                                                 key_secret=key_secret, key_version=key_version, key_id=key_id,
                                                 ssl_options=ssl_options, max_packet_buf=2)
        self.term_dict = dict()
        self.term_count = 0
        self.allow_feedback = set()

    def shutdown(self):
        print >> sys.stderr, "Shutting down server connection %s <- %s" % (self.connection_id, self.source)
        super(TerminalConnection, self).shutdown()

    def on_close(self):
        print >> sys.stderr, "Closing server connection %s <- %s" % (self.connection_id, self.source)
        super(TerminalConnection, self).on_close()

    def handle_close(self):
        pass

    def remote_terminal_update(self, term_name=None, add_flag=True, parent=""):
        """If term_name is None, generate new terminal name and return it"""
        if not term_name:
            while True:
                self.term_count += 1
                term_name = "tty"+str(self.term_count)
                if term_name not in self.term_dict:
                    break

        if add_flag:
            self.term_dict[term_name] = parent
        else:
            self.term_dict.pop(term_name, None)
        return term_name

    def remote_response(self, term_name, websocket_id, msg_list):
        fwd_list = []
        path = self.connection_id + "/" + term_name
        control_params = GTSocket._control_params.get(path)
        for msg in msg_list:
            if msg[0] == "term_params":
                client_version = msg[1]["version"]
                min_client_version = msg[1]["min_version"]
                try:
                    min_client_comps = gterm.split_version(min_client_version)
                    if gterm.split_version(client_version) < gterm.split_version(about.min_version):
                        raise Exception("Obsolete client version %s (expected %s+)" % (client_version, about.min_version))

                    if gterm.split_version(about.version) < min_client_comps:
                        raise Exception("Obsolete server version %s (need %d.%d+)" % (about.version, min_client_comps[0], min_client_comps[1]))

                except Exception, excp:
                    errmsg = "gtermserver: Failed version compatibility check: %s" % excp
                    logging.error(errmsg)
                    self.send_request("request", "", "", [["shutdown", errmsg]])
                    raise Exception(errmsg)
                
                self.host_secrets[msg[1]["normalized_host"]] = msg[1]["host_secret"]
                self.term_dict = dict((key, "") for key in msg[1]["term_names"])
            elif msg[0] == "file_response":
                ProxyFileHandler.complete_request(msg[1], **gtermhost.dict2kwargs(msg[2]))
            elif  msg[0] == "terminal" and msg[1] == "remote_command":
                # Send input to matching paths, if created by same user or session
                include_self = msg[2][0]
                remote_path = msg[2][1]
                remote_command = msg[2][2]
                if is_wildcard(remote_path):
                    matchpaths = TerminalConnection.get_matching_paths(wildcard2re(remote_path), control_params["owner"], control_params["state_id"], control_params["auth_type"])
                else:
                    matchpaths = [remote_path]
                for matchpath in matchpaths:
                    if not include_self and matchpath == path:
                        continue
                    matchhost, matchterm = matchpath.split("/")
                    TerminalConnection.send_to_connection(matchhost, "request", matchterm, "", [["keypress", remote_command]])

            else:
                fwd_list.append(msg)
                if msg[0] == "terminal" and msg[1] == "graphterm_feedback":
                    if msg[2]:
                        self.allow_feedback.add(term_name)
                    else:
                        self.allow_feedback.discard(term_name)

        if websocket_id:
            ws_set = set([websocket_id])
        else:
            ws_set = set(GTSocket._watch_dict.get(path, {}).keys())

            for ws_id, regexp in GTSocket._wildcards.iteritems():
                if regexp.match(path):
                    ws_set.add(ws_id)
            
        for ws_id in ws_set:
            ws = GTSocket._all_websockets.get(ws_id)
            if ws:
                try:
                    if ws.wildcard:
                        prefix = '<pre class="output wildpath"><a href="/%s" target="%s">%s</a>' % (path, path, path)
                        multi_fwd_list = []
                        for fwd in fwd_list:
                            if fwd[0] in ("output", "html_output", "log"):
                                output = fwd[0] + ": " + " ".join(map(str,fwd[1:]))
                                if ws.last_output == output:
                                    multi_fwd_list.append(["output", prefix + ' ditto</pre>'])
                                else:
                                    ws.last_output = output
                                    multi_fwd_list.append([fwd[0], prefix+'</pre>\n'+fwd[1]]+fwd[2:])
                        
                        if multi_fwd_list:
                            ws.write_message(json.dumps(multi_fwd_list))
                    else:
                        ws.write_message(json.dumps(fwd_list))
                except Exception, excp:
                    logging.error("remote_response: ERROR %s", excp)
                    try:
                        # Close websocket on write error
                        ws.close()
                    except Exception:
                        pass

Proxy_cache = gtermhost.BlobCache()

class ProxyFileHandler(tornado.web.RequestHandler):
    """Serves file requests
    """
    _async_counter = long(0)
    _async_requests = OrderedDict()

    @classmethod
    def get_async_id(cls):
        cls._async_counter += 1
        return cls._async_counter

    @classmethod
    def complete_request(cls, async_id, **kwargs):
        request = cls._async_requests.get(async_id)
        if not request:
            return
        del cls._async_requests[async_id]
        request.complete_get(**kwargs)

    ##def write_error(self, status_code, **kwargs):
        ### No error message text
        ##self.finish()
        
    def head(self, path):
        self.get(path)

    @tornado.web.asynchronous
    def get(self, path):
        if Check_state_cookie and GTSocket.get_auth_code():
            state_cookie = self.get_cookie(COOKIE_NAME) or self.get_argument("state_cookie", "")
            if not GTSocket.get_state(state_cookie):
                raise tornado.web.HTTPError(403, "Invalid cookie to access %s", path)

        host, sep, self.file_path = path.partition("/")
        if not host or not self.file_path:
            raise tornado.web.HTTPError(403, "Null host/filename")

        if_mod_since_datetime = None
        if_mod_since = self.request.headers.get("If-Modified-Since")
        if if_mod_since:
            if_mod_since_datetime = gtermhost.str2datetime(if_mod_since)

        self.cached_copy = None
        last_modified = None
        last_modified_datetime = None
        btime, bheaders, bcontent = Proxy_cache.get_blob(self.request.path)
        if bheaders:
            # Path in cache
            last_modified = dict(bheaders).get("Last-Modified")
            if last_modified:
                last_modified_datetime = gtermhost.str2datetime(last_modified)

            if self.request.path.startswith(gterm.BLOB_PREFIX):
                if last_modified_datetime and \
                   if_mod_since_datetime and \
                   if_mod_since_datetime >= last_modified_datetime:
                      # Remote copy is up-to-date
                      self.set_status(304)  # Not modified status code
                      self.finish()
                      return
                # Return immutable cached blob
                self.finish_write(bheaders, bcontent)
                return

        if self.request.path.startswith(gterm.FILE_PREFIX):
            # Check if access to file is permitted
            self.file_path = "/" + self.file_path

            normalized_host = gtermhost.get_normalized_host(host)
            host_secret = TerminalConnection.host_secrets.get(normalized_host)

            if not host_secret:
                raise tornado.web.HTTPError(403, "Unauthorized access to %s", path)

            shared_secret = self.get_cookie("GRAPHTERM_HOST_"+normalized_host)

            if shared_secret:
                if host_secret != shared_secret:
                    raise tornado.web.HTTPError(403, "Unauthorized access to %s", path)
            else:
                shared_secret = self.get_argument("shared_secret", "")
                check_host = gtermhost.get_normalized_host(self.get_argument("host", ""))
                expect_secret = TerminalConnection.host_secrets.get(check_host)
                if not expect_secret or expect_secret != shared_secret:
                    raise tornado.web.HTTPError(403, "Unauthorized access to %s", path)

            fpath_hmac = gterm.file_hmac(self.file_path, host_secret)
            if fpath_hmac != self.get_argument("hmac", ""):
                raise tornado.web.HTTPError(403, "Unauthorized access to %s", path)

            if bheaders:
                # File copy is cached
                if last_modified_datetime and \
                    if_mod_since_datetime and \
                    if_mod_since_datetime < last_modified_datetime:
                        # Remote copy older than cached copy; change if_mod_since to cache copy time
                        self.cached_copy = (btime, bheaders, bcontent)
                        if_mod_since = last_modified

        self.async_id = self.get_async_id()
        self._async_requests[self.async_id] = self

        self.timeout_callback = IO_loop.add_timeout(time.time()+REQUEST_TIMEOUT, functools.partial(self.complete_request, self.async_id))

        TerminalConnection.send_to_connection(host, "request", "", "", [["file_request", self.async_id, self.request.method, self.file_path, if_mod_since]])

    def finish_write(self, headers, content, cache=False):
        for name, value in headers:
            self.set_header(name, value)

        if self.request.method != "HEAD":
            self.write(content)
        self.finish()

        if cache:
            # Cache blob
            Proxy_cache.add_blob(self.request.path, headers, content)

    def complete_get(self, status=(), last_modified=None, etag=None, content_type=None, content_length=None,
                     content_b64=""):
        # Callback for get
        if not status:
            # Timed out
            self.send_error(408)
            return

        IO_loop.remove_timeout(self.timeout_callback)

        if status[0] == 304:
            if self.cached_copy and self.request.method != "HEAD":
                # Not modified since cached copy was created; return cached copy
                self.finish_write(self.cached_copy[1], self.cached_copy[2])
                return
            self.set_status(304)
            self.finish()
            return

        if status[0] != 200:
            # "Error" status
            self.send_error(status[0])
            return

        headers = []
        content = ""

        if self.request.method != "HEAD":
            # For HEAD request, content-length shold already have been set
            if content_b64:
                try:
                    content = base64.b64decode(content_b64)
                except Exception:
                    logging.warning("gtermserver: Error in base64 decoding for %s", self.request.path)
                    content = "Error in b64 decoding"
                    content_type = "text/plain"
            headers.append(("Content-Length", len(content)))

        if content_type:
            headers.append(("Content-Type", content_type))

        if last_modified:
            headers.append(("Last-Modified", last_modified))

        if etag:
            headers.append(("Etag", etag))

        if self.request.path.startswith(gterm.BLOB_PREFIX):
            headers.append(("Expires", datetime.datetime.utcnow() +
                                      datetime.timedelta(seconds=MAX_CACHE_TIME)))
            headers.append(("Cache-Control", "private, max-age="+str(MAX_CACHE_TIME)))
        elif last_modified and content_type:
            headers.append(("Cache-Control", "private, max-age=0, must-revalidate"))

        cache = self.request.method != "HEAD" and (self.request.path.startswith(gterm.BLOB_PREFIX) or
                                                     (Cache_files and last_modified) )
        self.finish_write(headers, content, cache=cache)


def run_server(options, args):
    global IO_loop, Http_server, Local_client, Log_file, Host_secret, Server_settings, Term_settings, Trace_shell
    import signal

    class AuthHandler(tornado.web.RequestHandler):
        def get(self):
            self.set_header("Content-Type", "text/plain")
            user = self.get_argument("user", "")
            key_version = self.get_argument("key_version", "1")
            client_nonce = self.get_argument("nonce", "")
            if not client_nonce:
                raise tornado.web.HTTPError(401)
            server_nonce = GTSocket.get_connect_cookie()
            if GTSocket.get_auth_type() >= GTSocket.MULTI_AUTH:
                hmac_key = gterm.user_hmac(GTSocket.get_auth_code(), user, key_version=key_version)
            elif GTSocket.get_auth_type() == GTSocket.LOCAL_AUTH:
                hmac_key = GTSocket.get_auth_code()
            else:
                hmac_key = "none"
            try:
                client_token, server_token = gterm.auth_token(hmac_key, "graphterm", Server_settings["host"], Server_settings["port"], client_nonce, server_nonce)
            except Exception:
                raise tornado.web.HTTPError(401)

            # TODO NOTE: Save server_token to authenticate next connection

            self.set_header("Content-Type", "text/plain")
            self.write(server_nonce+":"+client_token)

    gterm.create_app_directory()

    http_port = options.port
    http_host = options.host
    internal_host = options.internal_host or "localhost"
    internal_port = options.internal_port or http_port-1

    Server_settings = {"host": http_host, "port": http_port,
                       "internal_host": internal_host, "internal_port": internal_port,
                       "allow_embed": options.allow_embed, "allow_share": options.allow_share,
                       "auto_users": options.auto_users, "no_formcheck": options.no_formcheck}
    try:
        Term_settings = json.loads(options.term_settings or "{}")
    except Exception, excp:
        logging.error("Error in parsing term_settings: %s", excp)
        Term_settings = {}

    auth_file = ""
    if options.auth_type == "local" or (options.auth_type == "multiuser" and not os.path.exists(gterm.get_auth_filename(server=http_host))):
        # Random auth code
        auth_code = GTSocket.get_auth_code()
        try:
            gterm.write_auth_code(auth_code, server=http_host, port=http_port)
        except Exception, excp:
            print >> sys.stderr, "Error in writing authentication file: %s" % excp
            sys.exit(1)
        auth_file = gterm.get_auth_filename(server=http_host)
    else:
        if options.auth_type == "none":
            # No auth code
            auth_code = ""
        elif options.auth_type == "name":
            # No auth code
            auth_code = "name"
        elif options.auth_type == "multiuser":
            try:
                auth_code, port = gterm.read_auth_code(server=http_host)
            except Exception, excp:
                print >> sys.stderr, "Error in reading authentication file: %s" % excp
                sys.exit(1)
            auth_file = gterm.get_auth_filename()
        else:
            print >> sys.stderr, "Invalid authentication type '%s'; must be one of local/none/name/multiuser" % options.auth_type
            sys.exit(1)

    GTSocket.set_auth_code(auth_code, local=options.auth_type=="local")

    if options.auth_type == "multiuser":
        if options.auto_users:
            if not os.path.exists(Auto_add_file):
                with open(Auto_add_file, "w") as f:
                    pass
        elif os.path.exists(Auto_add_file):
            os.remove(Auto_add_file)

    super_users = options.super_users.split(",") if options.super_users else []
    GTSocket.set_super_users(super_users)

    if options.auth_users:
        assert options.auth_type == "multiuser", "Must specify auth_type=multiuser "
        for user in options.auth_users.split(","):
            # Personalized user auth codes
            if user:
                GTSocket._auth_users[user] = gterm.user_hmac(auth_code, user, key_version="1")

    handlers = [(r"/_auth/.*", AuthHandler),
                (r"/_websocket/.*", GTSocket),
                (gterm.STATIC_PREFIX+r"(.*)", tornado.web.StaticFileHandler, {"path": Doc_rootdir}),
                (gterm.BLOB_PREFIX+r"(.*)", ProxyFileHandler, {}),
                (gterm.FILE_PREFIX+r"(.*)", ProxyFileHandler, {}),
                (r"/().*", tornado.web.StaticFileHandler, {"path": Doc_rootdir, "default_filename": "index.html"}),
                ]

    application = tornado.web.Application(handlers)

    ##logging.warning("DocRoot: "+Doc_rootdir);

    IO_loop = tornado.ioloop.IOLoop.instance()

    ssl_options = None
    if options.https or options.client_cert:
        cert_dir = gterm.App_dir
        server_name = "localhost"
        certfile = cert_dir+"/"+server_name+".crt"
        keyfile = cert_dir+"/"+server_name+".key"

        new = not (os.path.exists(certfile) and os.path.exists(keyfile))
        fingerprint = ssl_cert_gen(server_name, cwd=cert_dir, new=new)
        if not fingerprint:
            print >> sys.stderr, "gtermserver: Failed to generate server SSL certificate"
            sys.exit(1)
        print >> sys.stderr, fingerprint

        ssl_options = {"certfile": certfile, "keyfile": keyfile}
        if options.client_cert:
            if options.client_cert == ".":
                ssl_options["ca_certs"] = certfile
            elif not os.path.exists(options.client_cert):
                print >> sys.stderr, "Client cert file %s not found" % options.client_cert
                sys.exit(1)
            else:
                ssl_options["ca_certs"] = options.client_cert
            ssl_options["cert_reqs"] = ssl.CERT_REQUIRED

    internal_server_ssl = {"certfile": certfile, "keyfile": keyfile} if options.internal_https else None
    internal_client_ssl = {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": certfile} if options.internal_https else None
    if auth_code and auth_code != "name":
        key_secret = auth_code
        key_version = "1"
        local_key_secret = gterm.user_hmac(key_secret, LOCAL_HOST, key_version=key_version)
    else:
        key_secret = None
        key_version = None
        local_key_secret = key_secret
    TerminalConnection.start_tcp_server(internal_host, internal_port, io_loop=IO_loop,
                                        key_secret=key_secret, key_version=key_version,
                                        key_id=str(internal_port), ssl_options=internal_server_ssl)

    if options.internal_https or options.nolocal:
        # Internal https causes tornado to loop  (client fails to connect to server)
        # Connecting to internal https from another process seems to be OK.
        # Need to rewrite packetserver.PacketConnection to use tornado.netutil.TCPServer
        Local_client, Host_secret, Trace_shell = None, None, None
    else:
        oshell_globals = globals() if otrace and options.oshell else None
        prompt_list = options.prompts.split(",") if options.prompts else gterm.DEFAULT_PROMPTS
        term_params = {"lc_export": options.lc_export, "no_pyindent": options.no_pyindent}
        Local_client, Host_secret, Trace_shell = gtermhost.gterm_connect(LOCAL_HOST, internal_host,
                                                         server_port=internal_port,
                                                         connect_kw={"ssl_options": internal_client_ssl,
                                                                     "command": options.shell_command,
                                                                     "term_type": options.term_type,
                                                                     "term_encoding": options.term_encoding,
                                                                     "key_secret": local_key_secret,
                                                                     "key_version": key_version,
                                                                     "key_id": str(internal_port),
                                                                     "prompt_list": prompt_list,
                                                                     "term_params": term_params,
                                                                     "blob_host": options.blob_host,
                                                                     "lterm_logfile": options.lterm_logfile,
                                                                     "widget_port":
                                                                       (gterm.DEFAULT_HTTP_PORT-2 if options.widgets else 0)},
                                                         oshell_globals=oshell_globals,
                                                         oshell_init="gtermserver.trc",
                                                         oshell_unsafe=True,
                                                         oshell_thread=(not options.oshell_input),
                                                         oshell_no_input=(not options.oshell_input),
                                                         oshell_web_interface=TraceInterface,
                                                         io_loop=IO_loop)
        xterm = Local_client.xterm
        killterm = Local_client.remove_term

    Http_server = tornado.httpserver.HTTPServer(application, ssl_options=ssl_options)
    Http_server.listen(http_port, address=http_host)
    if auth_file:
        print >> sys.stderr, "\nAuthentication code in file " + auth_file
    else:
        print >> sys.stderr, "\n**WARNING** No authentication required"

    if options.daemon and options.auto_users:
        cmd_args = ["sudo", gterm.SETUP_USER_CMD, "--all", internal_host]
        std_out, std_err = gterm.command_output(cmd_args, timeout=15)
        if std_err:
            logging.warning("gtermserver: ERROR in starting up %s %s %s", gterm.SETUP_USER_CMD, std_out, std_err)

    if options.logging:
        Log_file = open(Log_filename, "a")
        print >> sys.stderr, "Logging to", Log_filename

    url = "%s://%s:%d/local/new" % ("https" if options.https else "http", http_host, http_port)
    if options.terminal:
        server_nonce = GTSocket.get_connect_cookie()
        query = "?cauth="+server_nonce
        if options.auth_type == "local":
            query += "&code="+gterm.compute_hmac(auth_code, server_nonce)
        elif options.auth_type == "multiuser" and super_users:
            query += "&user="+super_users[0]+"&code="+gterm.compute_hmac(gterm.user_hmac(auth_code, super_users[0], key_version=key_version), server_nonce)
        elif options.auth_type == "name" and super_users:
            query += "&user="+super_users[0]
        try:
            gterm.open_browser(url+"/"+query)
        except Exception, excp:
            print >> sys.stderr, "Error in creating terminal; please open URL %s in browser (%s)" % (url, excp)
            

    def test_fun():
        raise Exception("TEST EXCEPTION")

    def stop_server():
        global Http_server
        print >> sys.stderr, "\nStopping server"
        gtermhost.gterm_shutdown(Trace_shell)
        if Http_server:
            Http_server.stop()
            Http_server = None
        def stop_server_aux():
            IO_loop.stop()

        # Need to stop IO_loop only after all other scheduled shutdowns have completed
        IO_loop.add_callback(stop_server_aux)

    def sigterm(signal, frame):
        logging.warning("SIGTERM signal received")
        IO_loop.add_callback(stop_server)
    signal.signal(signal.SIGTERM, sigterm)

    try:
        ioloop_thread = threading.Thread(target=IO_loop.start)
        ioloop_thread.start()
        time.sleep(1)   # Time to start thread
        print >> sys.stderr, "Open URL %s in browser to connect" % url
        print >> sys.stderr, "GraphTerm server started (v%s)" % about.version
        print >> sys.stderr, "Type ^C to stop"
        if Trace_shell:
            Trace_shell.loop()
        if not Trace_shell or not options.oshell_input:
            while Http_server:
                time.sleep(1)
    except KeyboardInterrupt:
        print >> sys.stderr, "Interrupted"

    finally:
        if options.auth_type == "local":
            gterm.clear_auth_code(server=http_host)
        if Log_file:
            Log_file.close()
    IO_loop.add_callback(stop_server)

def main():
    from optparse import OptionParser

    config_file = os.path.join(gterm.App_dir, "gtermserver.cfg")
    if not os.path.isfile(config_file):
        config_file = None

    usage = "usage: gtermserver [-h ... options]"
    parser = optconfig.OptConfig(usage=usage, config_file=config_file)

    parser.add_option("auth_type", default="local",
                      help="Authentication type (local/none/name/multiuser)")

    parser.add_option("auth_users", default="",
                      help="Comma-separated list of authenticated user names")

    parser.add_option("host", default="localhost",
                      help="Hostname (or IP address) (default: localhost)")
    parser.add_option("port", default=gterm.DEFAULT_HTTP_PORT,
                      help="IP port (default: %d)" % gterm.DEFAULT_HTTP_PORT, opt_type="int")

    parser.add_option("terminal", default=False, opt_type="flag",
                      help="Open new terminal window")
    parser.add_option("internal_host", default="",
                      help="internal host name (or IP address) (default: localhost)")
    parser.add_option("internal_port", default=0,
                      help="internal port (default: PORT-1)", opt_type="int")
    parser.add_option("blob_host", default="",
                      help="blob server host name (or IP address) (default: same as server)")

    parser.add_option("nolocal", default=False, opt_type="flag",
                      help="Disable connection to localhost")

    parser.add_option("super_users", default="",
                      help="Super user list: root,admin,...")
    parser.add_option("shell_command", default="",
                      help="Shell command")
    parser.add_option("oshell", default=False, opt_type="flag",
                      help="Activate otrace/oshell")
    parser.add_option("oshell_input", default=False, opt_type="flag",
                      help="Allow stdin input otrace/oshell")
    parser.add_option("https", default=False, opt_type="flag",
                      help="Use SSL (TLS) connections for security")
    parser.add_option("internal_https", default=False, opt_type="flag",
                      help="Use https for internal connections")
    parser.add_option("prompts", default="",
                      help="Inner prompt formats delim1,delim2,fmt,remote_fmt (default:',$,\\W,\\h:\\W')")
    parser.add_option("lc_export", default=False, opt_type="flag",
                      help="Export environment as locale (ssh hack)")
    parser.add_option("no_pyindent", default=False, opt_type="flag",
                      help="Disable auto indentation mods for notebook cells in python interpreter")
    parser.add_option("allow_embed", default=False, opt_type="flag",
                      help="Allow iframe embedding of terminal on other domains (possibly insecure)")
    parser.add_option("allow_share", default=False, opt_type="flag",
                      help="Allow sharing of terminals between users")
    parser.add_option("auto_users", default=False, opt_type="flag",
                      help="Allow automatic user creation")
    parser.add_option("no_formcheck", default=False, opt_type="flag",
                      help="Disable form checking (INSECURE)")
    parser.add_option("client_cert", default="",
                      help="Path to client CA cert (or '.')")
    parser.add_option("term_type", default="",
                      help="Terminal type (linux/screen/xterm)")
    parser.add_option("term_encoding", default="utf-8",
                      help="Terminal character encoding (utf-8/latin-1/...)")
    parser.add_option("term_settings", default="{}",
                      help="Terminal settings (JSON)")
    parser.add_option("lterm_logfile", default="",
                      help="Lineterm logfile")
    parser.add_option("logging", default=False, opt_type="flag",
                      help="Log to ~/.graphterm/graphterm.log")
    parser.add_option("widgets", default=False, opt_type="flag",
                      help="Activate widgets on port %d" % (gterm.DEFAULT_HTTP_PORT-2))

    parser.add_option("daemon", default="",
                      help="daemon=start/stop/restart/status")

    args = parser.parse_args()
    options = parser.getallopts()

    if options.config:
        config_file = options.config

    if config_file:
        print >> sys.stderr, "***** Reading config info from %s:%s" % (config_file, options.select or "DEFAULT")

    if not options.daemon:
        run_server(options, args)
    else:
        import getpass
        from daemon import ServerDaemon
        pidfile = "/tmp/gtermserver.%s.pid" % getpass.getuser()
        daemon = ServerDaemon(pidfile, functools.partial(run_server, options, args))
        daemon.daemon_run(options.daemon)

if __name__ == "__main__":
    main()
