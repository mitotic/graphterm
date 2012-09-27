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
import shlex
import ssl
import stat
import subprocess
import sys
import threading
import time
import traceback
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
import packetserver

from bin import gtermapi

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

APPS_URL = "/static"

App_dir = os.path.join(os.getenv("HOME"), ".graphterm")
File_dir = os.path.dirname(__file__)
if File_dir == ".":
    File_dir = os.getcwd()    # Need this for daemonizing to work?
    
Doc_rootdir = os.path.join(File_dir, "www")
Default_auth_file = os.path.join(App_dir, "graphterm_auth")
Gterm_secret_file = os.path.join(App_dir, "graphterm_secret")

Gterm_secret = "1%018d" % random.randrange(0, 10**18)   # 1 prefix to keep leading zeros when stringified

Check_state_cookie = False             # Controls checking of state cookie for file access

Cache_files = False                     # Controls caching of files (blobs are always cached)

MAX_COOKIE_STATES = 100
MAX_WEBCASTS = 500

MAX_CACHE_TIME = 86400

COOKIE_NAME = "GRAPHTERM_AUTH"
COOKIE_TIMEOUT = 10800

REQUEST_TIMEOUT = 15

HEX_DIGITS = 16

PROTOCOL = "http"

SUPER_USERS = set(["root"])
LOCAL_HOST = "local"

RSS_FEED_URL = "http://info.mindmeldr.com/code/graphterm/graphterm-announce/posts.xml"

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
        cmd_args = shlex.split(cmd % params)
        std_out, std_err = gtermapi.command_output(cmd_args, cwd=cwd, timeout=15)
        if std_err:
            logging.warning("gtermserver: SSL keygen %s %s", std_out, std_err)
    fingerprint = std_out
    if new:
        for cmd in client_cert_gen_cmds:
            cmd_args = shlex.split(cmd % params)
            std_out, std_err = gtermapi.command_output(cmd_args, cwd=cwd, timeout=15)
            if std_err:
                logging.warning("gtermserver: SSL client keygen %s %s", std_out, std_err)
    return fingerprint

class GTSocket(tornado.websocket.WebSocketHandler):
    _all_websockets = {}
    _all_users = collections.defaultdict(dict)
    _control_set = collections.defaultdict(set)
    _watch_set = collections.defaultdict(set)
    _counter = [0]
    _webcast_paths = OrderedDict()
    _cookie_states = OrderedDict()
    _auth_users = OrderedDict()
    _auth_code = uuid.uuid4().hex[:HEX_DIGITS]
    _wildcards = {}

    @classmethod
    def get_auth_code(cls):
        return cls._auth_code
    
    @classmethod
    def set_auth_code(cls, value):
        cls._auth_code = value
    
    @classmethod
    def get_auth_code(cls):
        return cls._auth_code
    
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
        logging.warning("gtermserver: client_cert=%s, name=%s", self.client_cert, self.common_name)
        rpath, sep, self.request_query = self.request.uri.partition("?")
        self.req_path = "/".join(rpath.split("/")[2:])  # Strip out /_websocket from path
        if self.req_path.endswith("/"):
            self.req_path = self.req_path[:-1]

        super(GTSocket, self).__init__(*args, **kwargs)

        self.authorized = None
        self.remote_path = None
        self.controller = False
        self.wildcard = None
        self.last_output = None

    def allow_draft76(self):
        return True

    @classmethod
    def get_state(cls, state_id):
        if state_id not in cls._cookie_states:
            return None
        state_value = cls._cookie_states[state_id]
        if (time.time() - state_value["time"]) <= COOKIE_TIMEOUT:
            return state_value
        del cls._cookie_states[state_id]
        return None

    def open(self):
        need_code = bool(self._auth_code)
        need_user = need_code      ##bool(self._auth_users)

        user = ""
        try:
            if not self._auth_code:
                self.authorized = {"user": "", "auth_type": "null_auth", "time": time.time(), "state_id": ""}

            elif COOKIE_NAME in self.request.cookies:
                state_value = self.get_state(self.request.cookies[COOKIE_NAME].value)
                if state_value:
                    self.authorized = state_value

            webcast_auth = False
            if not self.authorized:
                query_data = {}
                if self.request_query:
                    try:
                        query_data = urlparse.parse_qs(self.request_query)
                    except Exception:
                        pass

                user = query_data.get("user", [""])[0]
                code = query_data.get("code", [""])[0]

                expect_code = self._auth_code
                if self._auth_users:
                    if user in self._auth_users:
                        expect_code = self._auth_users[user]
                    else:
                        self.write_json([["authenticate", need_user, need_code, "Invalid user" if user else ""]])
                        self.close()
                        return

                if code == self._auth_code or code == expect_code:
                    state_id = uuid.uuid4().hex[:HEX_DIGITS]
                    self.authorized = {"user": user, "auth_type": "code_auth", "time": time.time(), "state_id": state_id}
                    if len(self._cookie_states) >= MAX_COOKIE_STATES:
                        self._cookie_states.pop(last=False)
                    self._cookie_states[state_id] = self.authorized

                elif self.req_path in self._webcast_paths:
                    self.authorized = {"user": user, "auth_type": "webcast_auth", "time": time.time(), "state_id": ""}
                    webcast_auth = True

            if not self.authorized:
                self.write_json([["authenticate", need_user, need_code, "Authentication failed; retry"]])
                self.close()
                return

            comps = self.req_path.split("/")
            if len(comps) < 1 or not comps[0]:
                host_list = TerminalConnection.get_connection_ids()
                if self._auth_users and self.authorized["user"] not in SUPER_USERS:
                    if LOCAL_HOST in host_list:
                        host_list.remove(LOCAL_HOST)
                host_list.sort()
                self.write_json([["host_list", self.authorized["state_id"], host_list]])
                self.close()
                return

            host = comps[0].lower()
            if not host or not gtermhost.HOST_RE.match(host):
                self.write_json([["abort", "Invalid characters in host name"]])
                self.close()
                return

            if host == LOCAL_HOST and self._auth_users and self.authorized["user"] not in SUPER_USERS: 
                self.write_json([["abort", "Local host access not allowed for user %s" % self.authorized["user"]]])
                self.close()
                return

            wildhost = "?" in host or "*" in host or "[" in host
            term_feedback = False
            
            if wildhost:
                if len(comps) < 2 or not comps[1] or comps[1].lower() == "new":
                    self.write_json([["abort", "Must specify terminal name for wildcard host"]])
                    self.close()
                    return
                term_name = comps[1].lower()
            else:
                conn = TerminalConnection.get_connection(host)
                if not conn:
                    self.write_json([["abort", "Invalid host"]])
                    self.close()
                    return

                if len(comps) < 2 or not comps[1]:
                    term_list = list(conn.term_set)
                    term_list.sort()
                    self.write_json([["term_list", self.authorized["state_id"], host, term_list]])
                    self.close()
                    return

                term_name = comps[1].lower()
                if term_name == "new":
                    term_name = conn.remote_terminal_update()
                    self.write_json([["redirect", "/"+host+"/"+term_name]])
                    self.close()

                if not gtermhost.SESSION_RE.match(term_name):
                    self.write_json([["abort", "Invalid characters in terminal name"]])
                    self.close()
                    return

                term_feedback = term_name in conn.allow_feedback

            path = host + "/" + term_name

            option = comps[2] if len(comps) > 2 else ""

            if option == "kill" and not webcast_auth and not wildhost:
                kill_remote(path)
                return

            self.oshell = (term_name == gtermhost.OSHELL_NAME)

            self._counter[0] += 1
            self.websocket_id = str(self._counter[0])

            if "?" in path or "*" in path or "[" in path:
                self.wildcard = re.compile("^"+path.replace("+", "\\+").replace(".", "\\.").replace("?", ".?").replace("*", ".*")+"$")
                self._wildcards[path] = (self.wildcard, self.websocket_id)

            self._watch_set[path].add(self.websocket_id)
            if webcast_auth:
                self.controller = False
            elif self.wildcard:
                self.controller = True
            elif option == "share":
                self.controller = True
                self._control_set[path].add(self.websocket_id)
            elif option == "steal":
                msg = ["update", "controller", False]
                for ws_id in self._control_set[path]:
                    ws = GTSocket._all_websockets.get(ws_id)
                    if ws and ws_id != self.websocket_id:
                        ws.write_json([msg])
                self.controller = True
                self._control_set[path] = set([self.websocket_id])
            elif option == "watch" or (path in self._control_set and self._control_set[path]):
                self.controller = False
            else:
                self.controller = True
                self._control_set[path] = set([self.websocket_id])

            self.remote_path = path
            self._all_websockets[self.websocket_id] = self
            if user:
                self._all_users[user][self.websocket_id] = self

            display_splash = self.controller and self._counter[0] <= 2
            normalized_host, host_secret = "", ""
            if not self.wildcard:
                TerminalConnection.send_to_connection(host, "request", term_name, [["reconnect", self.websocket_id]])
                normalized_host = gtermhost.get_normalized_host(host)
                if self.authorized["auth_type"] in ("null_auth", "code_auth"):
                    host_secret = TerminalConnection.host_secrets.get(normalized_host)
            self.write_json([["setup", {"host": host, "term": term_name, "oshell": self.oshell,
                                        "host_secret": host_secret, "normalized_host": normalized_host,
                                        "about_version": about.version, "about_authors": about.authors,
                                        "about_url": about.url, "about_description": about.description,
                                        "controller": self.controller,
                                        "wildcard": bool(self.wildcard), "display_splash": display_splash,
                                        "apps_url": APPS_URL, "feedback": term_feedback,
                                        "state_id": self.authorized["state_id"]}]])
        except Exception, excp:
            logging.warning("GTSocket.open: ERROR %s", excp)
            self.close()

    def on_close(self):
        if self.authorized:
            user = self.authorized["user"]
            if user:
                user_sockets = self._all_users.get(user)
                if user_sockets:
                    try:
                        del user_sockets[self.websocket_id]
                    except Exception:
                        pass

        if self.remote_path in self._control_set:
             self._control_set[self.remote_path].discard(self.websocket_id)
        if self.remote_path in self._watch_set:
             self._watch_set[self.remote_path].discard(self.websocket_id)

        if self.wildcard and self.remote_path:
            try:
                del self._wildcards[self.remote_path]
            except Exception:
                pass
        try:
            del self._all_websockets[self.websocket_id]
        except Exception:
            pass

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

    def on_message(self, message):
        ##logging.warning("GTSocket.on_message: %s", message)
        if not self.remote_path:
            return

        remote_host, term_name = self.remote_path.split("/")

        controller = self.wildcard or (self.remote_path in self._control_set and self.websocket_id in self._control_set[self.remote_path])

        from_user = self.authorized["user"] if self.authorized else ""
        conn = None
        allow_feedback_only = False
        if not self.wildcard:
            conn = TerminalConnection.get_connection(remote_host)
            if not conn:
                self.write_json([["errmsg", "ERROR: Remote host %s not connected" % remote_host]])
                return

            if not controller and term_name in conn.allow_feedback:
                allow_feedback_only = True

        if controller or allow_feedback_only:
            try:
                msg_list = json.loads(str(message))
                if allow_feedback_only:
                    msg_list = [msg for msg in msg_list if msg[0] == "feedback"]
            except Exception, excp:
                logging.warning("GTSocket.on_message: ERROR %s", excp)
                self.write_json([["errmsg", str(excp)]])
                return
        else:
            self.write_json([["errmsg", "ERROR: Remote path %s not under control" % self.remote_path]])
            return

        req_list = []
        try:
            for msg in msg_list:
                if msg[0] == "osh_stdout":
                    TraceInterface.receive_output("stdout", msg[1], from_user or self.websocket_id, msg[2])

                elif msg[0] == "osh_stderr":
                    TraceInterface.receive_output("stderr", msg[1], from_user or self.websocket_id, msg[2])

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
        
                elif msg[0] == "webcast":
                    if controller and not self.wildcard:
                        # Only controller can webcast
                        if self.remote_path in self._webcast_paths:
                            del self._webcast_paths[self.remote_path]
                        if len(self._webcast_paths) > MAX_WEBCASTS:
                            self._webcast_paths.pop(last=False)
                        if msg[1]:
                            self._webcast_paths[self.remote_path] = time.time()
                            
                elif msg[0] == "send_msg":
                    if self.wildcard:
                        continue
                    to_user = msg[1]
                    ws_list = GTSocket._watch_set.get(self.remote_path)
                    if not ws_list:
                        continue
                    for ws_id in ws_list:
                        if ws_id == self.websocket_id:
                            continue
                        # Broadcast to all watchers (excluding originator)
                        ws = GTSocket._all_websockets.get(ws_id)
                        if not ws:
                            continue
                        ws_user = ws.authorized["user"] if ws.authorized else ""
                        if (not to_user and controller) or to_user == "*" or to_user == ws_user:
                            try:
                                # Change command and add from_user
                                ws.write_message(json.dumps([["receive_msg", from_user] + msg[1:]]))
                            except Exception, excp:
                                logging.error("edit_broadcast: ERROR %s", excp)
                                try:
                                    # Close websocket on write error
                                    ws.close()
                                except Exception:
                                    pass

                else:
                    req_list.append(msg)

            matchpaths = TerminalConnection.get_matching_paths(self.wildcard) if self.wildcard else [self.remote_path]
            if self.wildcard:
                self.last_output = None
            for matchpath in matchpaths:
                matchhost, matchterm = matchpath.split("/")
                TerminalConnection.send_to_connection(matchhost, "request", matchterm, req_list)

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
            websocket_id = GTSocket._all_users.get(path_comps[0])
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
            

def xterm(command="", name=None, host="localhost", port=gtermhost.DEFAULT_HTTP_PORT):
    """Create new terminal"""
    pass

def kill_remote(path):
    if path == "*":
        TerminalClient.shutdown_all()
        return
    host, term_name = path.split("/")
    if term_name == "*": term_name = ""
    try:
        TerminalConnection.send_to_connection(host, "request", term_name, [["kill_term"]])
    except Exception, excp:
        pass

class TerminalConnection(packetserver.RPCLink, packetserver.PacketConnection):
    _all_connections = {}
    host_secrets = {}
    @classmethod
    def get_matching_paths(cls, regexp):
        matchpaths = []
        for host, conn in cls._all_connections.iteritems():
            for term_name in conn.term_set:
                path = host + "/" + term_name
                if regexp.match(path):
                    matchpaths.append(path)
        return matchpaths
        
    def __init__(self, stream, address, server_address, key_secret=None, key_version=None, ssl_options={}):
        super(TerminalConnection, self).__init__(stream, address, server_address, server_type="frame",
                                                 key_secret=key_secret, key_version=key_version,
                                                 ssl_options=ssl_options, max_packet_buf=2)
        self.term_set = set()
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

    def remote_terminal_update(self, term_name=None, add_flag=True):
        """If term_name is None, generate new terminal name and return it"""
        if not term_name:
            while True:
                self.term_count += 1
                term_name = "tty"+str(self.term_count)
                if term_name not in self.term_set:
                    break

        if add_flag:
            self.term_set.add(term_name)
        else:
            self.term_set.discard(term_name)
        return term_name

    def remote_response(self, term_name, websocket_id, msg_list):
        fwd_list = []
        for msg in msg_list:
            if msg[0] == "term_params":
                client_version = msg[1]["version"]
                min_client_version = msg[1]["min_version"]
                try:
                    min_client_comps = gtermapi.split_version(min_client_version)
                    if gtermapi.split_version(client_version) < gtermapi.split_version(about.min_version):
                        raise Exception("Obsolete client version %s (expected %s+)" % (client_version, about.min_version))

                    if gtermapi.split_version(about.version) < min_client_comps:
                        raise Exception("Obsolete server version %s (need %d.%d+)" % (about.version, min_client_comps[0], min_client_comps[1]))

                except Exception, excp:
                    errmsg = "gtermserver: Failed version compatibility check: %s" % excp
                    logging.error(errmsg)
                    self.send_request("request", "", [["shutdown", errmsg]])
                    raise Exception(errmsg)
                
                self.host_secrets[msg[1]["normalized_host"]] = msg[1]["host_secret"]
                self.term_set = set(msg[1]["term_names"])
            elif msg[0] == "file_response":
                ProxyFileHandler.complete_request(msg[1], **gtermhost.dict2kwargs(msg[2]))
            else:
                fwd_list.append(msg)
                if msg[0] == "terminal" and msg[1] == "graphterm_feedback":
                    if msg[2]:
                        self.allow_feedback.add(term_name)
                    else:
                        self.allow_feedback.discard(term_name)

        path = self.connection_id + "/" + term_name
        if websocket_id:
            ws_list = [websocket_id]
        else:
            ws_list = GTSocket._watch_set.get(path) or set()

            for regexp, ws_id in GTSocket._wildcards.itervalues():
                if regexp.match(path):
                    ws_list.add(ws_id)
            
        if not ws_list:
            return
        for ws_id in ws_list:
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

            if self.request.path.startswith("/blob/"):
                if last_modified_datetime and \
                   if_mod_since_datetime and \
                   if_mod_since_datetime >= last_modified_datetime:
                      # Remote copy is up-to-date
                      self.send_error(304)  # Not modified status code
                      return
                # Return immutable cached blob
                self.finish_write(bheaders, bcontent)
                return

        if self.request.path.startswith("/file/"):
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

            fpath_hmac = hmac.new(str(host_secret), self.file_path, digestmod=hashlib.sha256).hexdigest()[:HEX_DIGITS]
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

        TerminalConnection.send_to_connection(host, "request", "", [["file_request", self.async_id, self.request.method, self.file_path, if_mod_since]])

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

        if status[0] == 304 and self.cached_copy and self.request.method != "HEAD":
            # Not modified since cached copy was created; return cached copy
            self.finish_write(self.cached_copy[1], self.cached_copy[2])
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

        if self.request.path.startswith("/blob/"):
            headers.append(("Expires", datetime.datetime.utcnow() +
                                      datetime.timedelta(seconds=MAX_CACHE_TIME)))
            headers.append(("Cache-Control", "private, max-age="+str(MAX_CACHE_TIME)))
        elif last_modified and content_type:
            headers.append(("Cache-Control", "private, max-age=0, must-revalidate"))

        cache = self.request.method != "HEAD" and (self.request.path.startswith("/blob/") or
                                                     (Cache_files and last_modified) )
        self.finish_write(headers, content, cache=cache)


def run_server(options, args):
    global IO_loop, Http_server, Local_client, Host_secret, Trace_shell
    import signal

    def auth_token(secret, connection_id, client_nonce, server_nonce):
        """Return (client_token, server_token)"""
        SIGN_SEP = "|"
        prefix = SIGN_SEP.join([connection_id, client_nonce, server_nonce]) + SIGN_SEP
        return [hmac.new(str(secret), prefix+conn_type, digestmod=hashlib.sha256).hexdigest()[:24] for conn_type in ("client", "server")]

    class AuthHandler(tornado.web.RequestHandler):
        def get(self):
            self.set_header("Content-Type", "text/plain")
            client_nonce = self.get_argument("nonce", "")
            if not client_nonce:
                raise tornado.web.HTTPError(401)
            server_nonce = "1%018d" % random.randrange(0, 10**18)   # 1 prefix to keep leading zeros when stringified
            try:
                client_token, server_token = auth_token(Gterm_secret, "graphterm", client_nonce, server_nonce)
            except Exception:
                raise tornado.web.HTTPError(401)

            # TODO NOTE: Save server_token to authenticate next connection

            self.set_header("Content-Type", "text/plain")
            self.write(server_nonce+":"+client_token)

    try:
        # Create App directory
        os.mkdir(App_dir, 0700)
    except OSError:
        if os.stat(App_dir).st_mode != 0700:
            # Protect App directory
            os.chmod(App_dir, 0700)

    auth_file = ""
    random_auth = False
    if not options.auth_code:
        # Default (random) auth code
        random_auth = True
        auth_code = GTSocket.get_auth_code()
    elif options.auth_code == "none":
        # No auth code
        auth_code = ""
        GTSocket.set_auth_code(auth_code)
    else:
        # Specified auth code
        auth_code = options.auth_code
        GTSocket.set_auth_code(auth_code)

    http_port = options.port
    http_host = options.host
    internal_host = options.internal_host or http_host
    internal_port = options.internal_port or http_port-1

    handlers = []
    if options.server_auth:
        handlers += [(r"/_auth/.*", AuthHandler)]
        with open(Gterm_secret_file, "w") as f:
            f.write("%d %d %s\n" % (http_port, os.getpid(), Gterm_secret))
        os.chmod(Gterm_secret_file, stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)

    if options.auth_users:
        for user in options.auth_users.split(","):
            if user:
                if random_auth:
                    # Personalized user auth codes
                    GTSocket._auth_users[user] = hmac.new(str(random_auth), user, digestmod=hashlib.sha256).hexdigest()[:HEX_DIGITS]
                else:
                    # Same auth code for all users
                    GTSocket._auth_users[user] = GTSocket.get_auth_code()

    if auth_code:
        if os.getenv("HOME", ""):
            auth_file = Default_auth_file
            try:
                with open(auth_file, "w") as f:
                    f.write("%s://%s:%d/?code=%s\n" % (PROTOCOL, http_host, http_port, auth_code));
                    if GTSocket._auth_users:
                        for user, key in GTSocket._auth_users.items():
                            f.write("%s %s://%s:%d/?user=%s&code=%s\n" % (user, PROTOCOL, http_host, http_port, user, key));
                    os.chmod(auth_file, stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)
            except Exception:
                logging.warning("Failed to create auth file: %s", auth_file)
                auth_file = ""

    handlers += [(r"/_websocket/.*", GTSocket),
                 (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": Doc_rootdir}),
                 (r"/blob/(.*)", ProxyFileHandler, {}),
                 (r"/file/(.*)", ProxyFileHandler, {}),
                 (r"/().*", tornado.web.StaticFileHandler, {"path": Doc_rootdir, "default_filename": "index.html"}),
                 ]

    application = tornado.web.Application(handlers)

    ##logging.warning("DocRoot: "+Doc_rootdir);

    IO_loop = tornado.ioloop.IOLoop.instance()

    ssl_options = None
    if options.https or options.client_cert:
        cert_dir = App_dir
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
    TerminalConnection.start_tcp_server(internal_host, internal_port, io_loop=IO_loop,
                                        key_secret=(options.server_secret or None), ssl_options=internal_server_ssl)

    if options.internal_https or options.nolocal:
        # Internal https causes tornado to loop  (client fails to connect to server)
        # Connecting to internal https from another process seems to be OK.
        # Need to rewrite packetserver.PacketConnection to use tornado.netutil.TCPServer
        Local_client, Host_secret, Trace_shell = None, None, None
    else:
        oshell_globals = globals() if otrace and options.oshell else None
        Local_client, Host_secret, Trace_shell = gtermhost.gterm_connect(LOCAL_HOST, internal_host,
                                                         server_port=internal_port,
                                                         connect_kw={"ssl_options": internal_client_ssl,
                                                                     "command": options.shell_command,
                                                                     "term_type": options.term_type,
                                                                     "term_encoding": options.term_encoding,
                                                                     "key_secret": options.server_secret or None,
                                                                     "lterm_logfile": options.lterm_logfile,
                                                                     "widget_port":
                                                                       (gtermhost.DEFAULT_HTTP_PORT-2 if options.widgets else 0)},
                                                         oshell_globals=oshell_globals,
                                                         oshell_unsafe=True,
                                                         oshell_thread=(not options.oshell_input),
                                                         oshell_no_input=(not options.oshell_input),
                                                         oshell_web_interface=TraceInterface,
                                                         io_loop=IO_loop)
        xterm = Local_client.xterm
        killterm = Local_client.remove_term

    Http_server = tornado.httpserver.HTTPServer(application, ssl_options=ssl_options)
    Http_server.listen(http_port, address=http_host)
    logging.warning("Auth code = %s %s" % (GTSocket.get_auth_code(), auth_file))

    if options.terminal:
        url = "%s://%s:%d/local/new" % ("https" if options.https else "http", http_host, http_port)
        gtermapi.open_browser(url)

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
        print >> sys.stderr, "GraphTerm server (v%s) listening on %s:%s" % (about.version, http_host, http_port)

        print >> sys.stderr, "\nType ^C to stop server"
        if Trace_shell:
            Trace_shell.loop()
        if not Trace_shell or not options.oshell_input:
            while Http_server:
                time.sleep(1)
    except KeyboardInterrupt:
        print >> sys.stderr, "Interrupted"

    finally:
        try:
            if options.server_auth:
                os.remove(Gterm_secret_file)
        except Exception:
            pass
    IO_loop.add_callback(stop_server)

def main():
    from optparse import OptionParser

    usage = "usage: gtermserver [-h ... options]"
    parser = OptionParser(usage=usage)

    parser.add_option("", "--auth_code", dest="auth_code", default="",
                      help="Authentication code (default: random value; specify 'none' for no auth)")

    parser.add_option("", "--auth_users", dest="auth_users", default="",
                      help="Comma-separated list of authenticated user names")

    parser.add_option("", "--host", dest="host", default="localhost",
                      help="Hostname (or IP address) (default: localhost)")
    parser.add_option("", "--port", dest="port", default=gtermhost.DEFAULT_HTTP_PORT,
                      help="IP port (default: %d)" % gtermhost.DEFAULT_HTTP_PORT, type="int")
    parser.add_option("", "--server_secret", dest="server_secret", default="",
                      help="Server secret (for host authentication)")

    parser.add_option("", "--terminal", dest="terminal", action="store_true",
                      help="Open new terminal window")
    parser.add_option("", "--internal_host", dest="internal_host", default="",
                      help="internal host name (or IP address) (default: external host name)")
    parser.add_option("", "--internal_port", dest="internal_port", default=0,
                      help="internal port (default: PORT-1)", type="int")

    parser.add_option("", "--nolocal", dest="nolocal", action="store_true",
                      help="Disable connection to localhost")

    parser.add_option("", "--shell_command", dest="shell_command", default="",
                      help="Shell command")
    parser.add_option("", "--oshell", dest="oshell", action="store_true",
                      help="Activate otrace/oshell")
    parser.add_option("", "--oshell_input", dest="oshell_input", action="store_true",
                      help="Allow stdin input otrace/oshell")
    parser.add_option("", "--https", dest="https", action="store_true",
                      help="Use SSL (TLS) connections for security")
    parser.add_option("", "--internal_https", dest="internal_https", action="store_true",
                      help="Use https for internal connections")
    parser.add_option("", "--server_auth", dest="server_auth", action="store_true",
                      help="Enable server authentication by gterm clients")
    parser.add_option("", "--client_cert", dest="client_cert", default="",
                      help="Path to client CA cert (or '.')")
    parser.add_option("", "--term_type", dest="term_type", default="",
                      help="Terminal type (linux/screen/xterm)")
    parser.add_option("", "--term_encoding", dest="term_encoding", default="utf-8",
                      help="Terminal character encoding (utf-8/latin-1/...)")
    parser.add_option("", "--lterm_logfile", dest="lterm_logfile", default="",
                      help="Lineterm logfile")
    parser.add_option("", "--widgets", dest="widgets", action="store_true",
                      help="Activate widgets on port %d" % (gtermhost.DEFAULT_HTTP_PORT-2))


    parser.add_option("", "--daemon", dest="daemon", default="",
                      help="daemon=start/stop/restart/status")

    (options, args) = parser.parse_args()

    if not options.daemon:
        run_server(options, args)
    else:
        from daemon import ServerDaemon
        pidfile = "/tmp/gtermserver.pid"
        daemon = ServerDaemon(pidfile, functools.partial(run_server, options, args))
        daemon.daemon_run(options.daemon)

if __name__ == "__main__":
    main()
