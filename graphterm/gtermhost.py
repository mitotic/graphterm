#!/usr/bin/env python

"""gtermhost: GraphTerm host connector
"""

import base64
import cgi
import calendar
import collections
import datetime
import email.utils
import functools
import hashlib
import logging
import mimetypes
import otrace
import os
import re
import signal
import stat
import sys
import threading
import time
import urllib

import random
try:
    random = random.SystemRandom()
except NotImplementedError:
    import random

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

try:
    from tornado.tcpserver import TCPServer   # Tornado 3.0+
except ImportError:
    from tornado.netutil import TCPServer     # Tornado 3.0-

from bin import gterm

import about
import lineterm
import packetserver

RETRY_SEC = 15

AJAX_EDITORS = set(["ace", "ckeditor", "textarea"])

OSHELL_NAME = "osh"

HTML_ESCAPES = ["\x1b[?1155;", "h",
                "\x1b[?1155l"]

USER_RE    = re.compile(r"^[a-z][a-z0-9\-]*$")                # Allowed user names
HOST_RE    = re.compile(r"^[a-z][a-z0-9\-\*\?\[\]]*$")        # Allowed host names
SESSION_RE = re.compile(r"^[a-zA-Z\*\?\[\]][\w\*\?\[\]]*$")   # Allowed session names

Host_secret = None
IO_loop = None
IO_loop_control = False
Widget_server = None

def get_normalized_host(host):
    """Return identifier version of hostname"""
    return re.sub(r"\W", "_", host.upper())

def datetime2str(datetime_obj):
    """Return datetime object as string, formatted for last-modified"""
    tm = calendar.timegm(datetime_obj.utctimetuple())
    return email.utils.formatdate(tm, localtime=False, usegmt=True)

def str2datetime(datetime_str):
    """Return datetime object from string, formatted for last-modified"""
    date_tuple = email.utils.parsedate(datetime_str)
    return datetime.datetime.fromtimestamp(time.mktime(date_tuple))
    
def dict2kwargs(dct, unicode2str=False):
    """Converts unicode keys in a dict to ascii, to allow it to be used for keyword args.
    If unicode2str, all unicode values to converted to str as well.
    (This is needed when the dict is created from JSON)
    """
    return dict([(str(k), str(v) if unicode2str and isinstance(v, unicode) else v) for k, v in dct.iteritems()])

class HtmlWrapper(object):
    """ Wrapper for HTML output
    """
    def __init__(self, lterm_cookie):
        self.lterm_cookie = lterm_cookie

    def wrap(self, html, msg_type=""):
        return HTML_ESCAPES[0] + self.lterm_cookie + HTML_ESCAPES[1]  + html + HTML_ESCAPES[-1]

class BlobCache(object):
    def __init__(self, max_bytes=10000000, max_time=5400):
        self.max_bytes = max_bytes
        self.max_time = max_time
        self.cache = OrderedDict()
        self.cache_size = 0

    def get_blob(self, blob_id):
        """Return (mod_time, headers, content)"""
        return self.cache.get(blob_id) or (None, None, None)

    def add_blob(self, blob_id, headers, content):
        """Add blob, refreshing cache, if need be"""
        if blob_id in self.cache:
            self.delete_blob(blob_id)

        self.cache_size += len(content)
        cur_time = time.time()
        for bid in self.cache.keys():
            btime, bheaders, bcontent = self.cache[bid]
            if (cur_time - btime) > self.max_time or self.cache_size > self.max_bytes:
                self.cache.pop(bid)
                self.cache_size -= len(bcontent)
        self.cache[blob_id] = (cur_time, headers, content)

    def delete_blob(self, blob_id):
        if blob_id in self.cache:
            btime, bheaders, bcontent = self.cache.pop(blob_id)
            self.cache_size -= len(bcontent)

class TerminalClient(packetserver.RPCLink, packetserver.PacketClient):
    _all_connections = {}
    all_cookies = {}
    def __init__(self, host, port, host_secret="", io_loop=None, ssl_options={},
                 key_secret=None, key_version=None, key_id=None, lterm_logfile=""):
        super(TerminalClient, self).__init__(host, port, io_loop=io_loop,
                                             ssl_options=ssl_options, max_packet_buf=3,
                                             reconnect_sec=RETRY_SEC, server_type="frame",
                                             key_secret=key_secret, key_version=key_version, key_id=key_id)
        self.host_secret = host_secret

        self.lterm_logfile = lterm_logfile

        self.terms = {}
        self.lineterm = None
        self.blob_server = ""
        self.osh_cookie = lineterm.make_lterm_cookie()
        self.blob_cache = BlobCache()
        self.host_settings = {}
        self.widget_port = 0
        self.log_filename = ""

    def handle_shutdown(self):
        logging.warning("Shutting down client connection %s -> %s:%s", self.connection_id, self.host, self.port)
        if self.lineterm:
            self.lineterm.shutdown()
        self.lineterm = None

    def connection_validated(self):
        normalized_host = get_normalized_host(self.connection_id)
        host_params = {"host_secret": self.host_secret, "host_email": gterm.read_email()}
        self.remote_response("", "", [["term_params", {"version": about.version,
                                                       "min_version": about.min_version,
                                                       "normalized_host": normalized_host, 
                                                       "host_params": host_params,
                                                       "term_prefs": gterm.read_prefs(),
                                                       "term_names": self.terms.keys()}]])
        
    def add_oshell(self):
        self.add_term(OSHELL_NAME, self.osh_cookie)
        
    def add_term(self, term_name, lterm_cookie):
        if term_name not in self.terms:
            self.send_request_threadsafe("terminal_update", term_name, True)
        self.terms[term_name] = (lterm_cookie, {})
        self.all_cookies[lterm_cookie] = (self, term_name)

    def remove_term(self, term_name):
        try:
            lterm_cookie, blobs = self.terms.get(term_name, [None, None])
            if lterm_cookie:
                del self.terms[term_name]
                del self.all_cookies[lterm_cookie]
                for blob_id in blobs:
                    self.blob_cache.delete_blob(blob_id)
        except Exception:
            pass
        self.send_request_threadsafe("terminal_update", term_name, False)

        if not self.lineterm:
            return
        if not term_name:
            self.lineterm.kill_all()
        else:
            self.lineterm.kill_term(term_name)

    def xterm(self, term_name="", height=25, width=80, winheight=0, winwidth=0, parent="", command=""):
        if not self.lineterm:
            version_str = gterm.API_VERSION
            if gterm.API_MIN_VERSION and version_str != gterm.API_MIN_VERSION and not version_str.startswith(gterm.API_MIN_VERSION+"."):
                version_str += "/" + gterm.API_MIN_VERSION
            self.lineterm = lineterm.Multiplex(self.screen_callback, command=(command or self.host_settings["command"]),
                                               shared_secret=self.host_secret, host=self.connection_id,
                                               server_url=self.host_settings["server_url"],
                                               term_type=self.host_settings["term_type"],
                                               api_version=version_str, widget_port=self.widget_port,
                                               prompt_list=self.host_settings["prompt_list"], blob_server=self.blob_server,
                                               term_params=self.host_settings["lterm_params"], logfile=self.lterm_logfile)
        term_name, lterm_cookie, alert_msg = self.lineterm.terminal(term_name, height=height, width=width,
                                                                    winheight=winheight, winwidth=winwidth,
                                                                    parent=parent)
        self.add_term(term_name, lterm_cookie)
        if alert_msg:
            self.screen_callback(term_name, "", "alert", [alert_msg])
        return term_name

    def paste_command(self, term_name, command_line):
        if not self.lineterm:
            return
        if command_line.endswith("\n"):
            # Send delayed newline to allow multiline command to be parsed
            command_line = command_line[:-1]
            IO_loop.add_timeout(time.time()+0.1, functools.partial(self.lineterm.term_write, term_name, "\n"))

        if command_line:
            try:
                self.lineterm.term_write(term_name, command_line)
            except Exception, excp:
                logging.warning("Error in paste_command: %s", excp)

    def screen_callback(self, term_name, response_id, command, arg):
        # Invoked in lineterm thread; schedule callback in ioloop
        lterm_cookie, blobs = self.terms.get(term_name, [None, None])
        if not lterm_cookie:
            logging.warning("Error in screen_callback: terminal %s not found for command %s", term_name, command)
            return
        if command == "create_blob":
            blob_id, headers, content = arg
            self.blob_cache.add_blob(blob_id, headers, content)
            blobs[blob_id] = 1
        elif command == "delete_blob":
            blob_id = arg[0]
            self.blob_cache.delete_blob(blob_id)
            blobs.pop(blob_id, None)
        else:
            self.send_request_threadsafe("response", term_name, response_id, [["terminal", command, arg]])

    def term_reconnect(self, host_settings):
        global Widget_server
        if self.host_settings and self.host_settings != host_settings:
            logging.error("ERROR: Host settings mismatch: %s vs. %s" % (self.host_settings, host_settings))

        self.host_settings = host_settings

        if self.connection_id != gterm.LOCAL_HOST and not self.log_filename and (self.host_settings["logging"] or Options.logging):
            self.log_filename = os.path.join(gterm.App_dir, "gtermhost.log")
            gterm.setup_logging(logging.WARNING, self.log_filename, logging.INFO)
            logging.warning("*************************Logging to file %s", self.log_filename)

        if self.host_settings["widget_port"] > 0:
            self.widget_port = widget_port
        elif self.host_settings["widget_port"] < 0:
            self.widget_port = gterm.DEFAULT_HTTP_PORT-2 if self.connection_id == gterm.LOCAL_HOST else gterm.WIDGET_BASE_PORT+os.getuid()
        else:
            self.widget_port = 0
        
        if self.host_settings["blob_host"] == "wildcard":
            self.blob_server = ("https" if self.host_settings["https"] else "http") + "://*." + self.host + ":" + str(self.port+1)
        elif self.host_settings["blob_host"]:
            self.blob_server = ("https" if self.host_settings["https"] else "http") + "://" + self.host_settings["blob_host"] + ":" + str(self.port+1)
        else:
            self.blob_server = ""

        if self.widget_port and not Widget_server:
            Widget_server = WidgetServer()
            Widget_server.listen(self.widget_port, address="localhost")
            logging.warning("GraphTerm widgets listening on %s:%s", "localhost", self.widget_port)

    def remote_response(self, term_name, websocket_id, message_list):
        self.send_request_threadsafe("response", term_name, websocket_id, message_list)

    def remote_request(self, term_name, from_user, req_list):
        """
        Setup commands:
          reconnect <response_id> <host_settings>
          set_email <email>

        Input commands:
          incomplete_input <line>
          input <line>
          click_paste <text> <file_url> {command:, clear_last:, normalize:, enter:}
          paste_command <text>
          get_finder <kind> <directory>
          save_data <save_params> <filedata>
          open_notebook <filepath> <prompts> <content>
          close_notebook <discard>
          save_notebook <filepath> <input_data> <params>
          add_cell <new_cell_type> <init_text> <before_cell_index>
          select_cell <cell_index> <move_up> <next_code>
          select_page <move_up> <endpoint> <slide>
          move_cell <move_up>
          delete_cell <move_up>
          merge_above
          erase_output <all_cells>
          update_type <cell_type>
          complete_cell <incomplete_line>
          update_cell <cellIndex> <execute> <save> <input_data>

        Output commands:
          completed_input <line>
          prompt <str>
          stdin <str>
          stdout <str>
          stderr <str>
        """
        try:
            lterm_cookie, blobs = self.terms.get(term_name, [None, None])
            resp_list = []
            for cmd in req_list:
                action = cmd.pop(0)
                if action == "shutdown":
                    if cmd:
                        logging.warning("SHUTDOWN %s", cmd[0])
                    self.shutdown()

                elif action == "reconnect":
                    self.term_reconnect(cmd[1])
                    if self.lineterm:
                        response_id = cmd[0]
                        self.lineterm.reconnect(term_name, response_id)
                        widget_pagelet = WidgetStream.get_widget_pagelet(lterm_cookie)
                        if widget_pagelet:
                            self.send_request_threadsafe("response", term_name, response_id, [["terminal", "graphterm_widget", widget_pagelet]])

                elif action == "set_email":
                    gterm.write_email(cmd[0])

                elif action == "set_size":
                    if term_name != OSHELL_NAME:
                        self.xterm(term_name, cmd[0][0], cmd[0][1], cmd[0][2], cmd[0][3], cmd[0][4])

                elif action == "kill_term":
                    self.remove_term(term_name)

                elif action == "clear_term":
                    if self.lineterm:
                        self.lineterm.clear(term_name)

                elif action == "export_environment":
                    if self.lineterm:
                        self.lineterm.export_environment(term_name, cmd[0])

                elif action == "keypress":
                    if self.lineterm:
                        self.lineterm.term_write(term_name, cmd[0].encode(self.host_settings["term_encoding"], "ignore"))

                elif action == "chat":
                    # ["" or host/session, "" or token, message]
                    msg = from_user + ": " + cmd[2]
                    chat_widget = WidgetStream.get_chat_widget(lterm_cookie)
                    if chat_widget:
                        chat_widget.send_packet(msg.encode(self.host_settings["term_encoding"], "ignore"))

                elif action == "save_data":
                    # save_data <save_params> <filedata>
                    if self.lineterm:
                        self.lineterm.save_data(term_name, cmd[0], cmd[1])

                elif action == "save_prefs":
                    # save_prefs <prefs_dict>
                    prefs_file, status = gterm.write_prefs(cmd[0])
                    self.send_request_threadsafe("response", term_name, "", [["terminal", "save_status", [prefs_file, "", status]] ])

                elif action == "click_paste":
                    # click_paste: text, file_url, {command:, clear_last:, normalize:, enter:}
                    if self.lineterm:
                        paste_text = self.lineterm.click_paste(term_name, cmd[0], cmd[1], cmd[2])
                        self.paste_command(term_name, paste_text)

                elif action == "open_notebook":
                    # open_notebook <filepath> <prompts> <content>
                    if self.lineterm:
                        self.lineterm.open_notebook(term_name, cmd[0], cmd[1], cmd[2])

                elif action == "close_notebook":
                    # close_notebook <discard>
                    if self.lineterm:
                        self.lineterm.close_notebook(term_name, cmd[0])

                elif action == "save_notebook":
                    # save_notebook <filepath> <input_data> <params>
                    if self.lineterm:
                        self.lineterm.save_notebook(term_name, cmd[0], cmd[1], cmd[2])

                elif action == "add_cell":
                    # add_cell <new_cell_type> <init_text> <before_cell_index>
                    if self.lineterm:
                        self.lineterm.add_cell(term_name, cmd[0], cmd[1], cmd[2])

                elif action == "select_cell":
                    # select_cell <cell_index> <move_up> <next_code>
                    if self.lineterm:
                        self.lineterm.select_cell(term_name, cmd[0], cmd[1], cmd[2])

                elif action == "select_page":
                    # select_page <move_up> <endpoint> <slide>
                    if self.lineterm:
                        self.lineterm.select_page(term_name, cmd[0], cmd[1], cmd[2])

                elif action == "move_cell":
                    # move_cell <move_up>
                    if self.lineterm:
                        self.lineterm.move_cell(term_name, cmd[0])

                elif action == "delete_cell":
                    # delete_cell <move_up>
                    if self.lineterm:
                        self.lineterm.delete_cell(term_name, cmd[0])

                elif action == "merge_above":
                    # merge_above
                    if self.lineterm:
                        self.lineterm.merge_above(term_name)

                elif action == "erase_output":
                    # erase_output <all_cells>
                    if self.lineterm:
                        self.lineterm.erase_output(term_name, cmd[0])

                elif action == "update_type":
                    # update_type <cell_type>
                    if self.lineterm:
                        self.lineterm.update_type(term_name, cmd[0])

                elif action == "complete_cell":
                    # complete_cell <incomplete_line>
                    if self.lineterm:
                        self.lineterm.complete_cell(term_name, cmd[0])

                elif action == "update_cell":
                    # update_cell <cellIndex> <execute> <save>, <input_data>
                    if self.lineterm:
                        self.lineterm.update_cell(term_name, cmd[0], cmd[1], cmd[2], cmd[3])

                elif action == "paste_command":
                    # paste_command: command_line
                    self.paste_command(term_name, cmd[0])

                elif action == "clear_last_entry":
                    if self.lineterm:
                        self.lineterm.clear_last_entry(term_name, long(cmd[0]))

                elif action == "get_finder":
                    if self.lineterm:
                        self.lineterm.get_finder(term_name, cmd[0], cmd[1])

                elif action == "incomplete_input":
                    cmd_incomplete = cmd[0].encode("ascii", "ignore")
                    dummy, sep, text = cmd_incomplete.rpartition(" ")
                    options = otrace.OShell.instance.completer(text, 0, line=cmd_incomplete, all=True)
                    if text:
                        options = [cmd_incomplete[:-len(text)]+option for option in options]
                    else:
                        options = [cmd_incomplete+option for option in options]
                    resp_list.append(["completed_input", options])   # Not escaped; handle as text

                elif action == "input":
                    cmd_input = cmd[0].encode("ascii", "ignore").lstrip()   # Unescaped text
                    here_doc = base64.b64decode(cmd[1]) if cmd[1] else cmd[1]
                    entry_list = []

                    if cmd_input == "cat episode4.txt":
                        # Easter egg
                        std_out, std_err = Episode4, ""
                    else:
                        std_out, std_err = otrace.OShell.instance.execute(cmd_input, here_doc=here_doc)
                    resp_list.append(["input", cmd[0]])   # Not escaped; handle as text

                    prompt, cur_dir_path = otrace.OShell.instance.get_prompt()
                    resp_list.append(["prompt", cgi.escape(prompt), "file://"+urllib.quote(cur_dir_path)])

                    auth_html = False
                    if lterm_cookie and std_out.startswith(HTML_ESCAPES[0]):
                        auth_prefix = HTML_ESCAPES[0]+lterm_cookie+HTML_ESCAPES[1]
                        auth_html = std_out.startswith(auth_prefix)
                        if auth_html:
                            offset = len(auth_prefix)
                        else:
                            # Unauthenticated html
                            offset = std_out.find(HTML_ESCAPES[1])+len(HTML_ESCAPES[1])

                        if std_out.endswith(HTML_ESCAPES[-1]):
                            html_output = std_out[offset:-len(HTML_ESCAPES[-1])]
                        elif std_out.endswith(HTML_ESCAPES[-1]+"\n"):
                            html_output = std_out[offset:-len(HTML_ESCAPES[-1])-1]
                        else:
                            html_output = std_out[offset:]

                        headers, content = lineterm.parse_headers(html_output)

                        if auth_html:
                            resp_list.append(["html_output", content])
                        else:
                            # Unauthenticated; extract plain text from html
                            try:
                                import lxml.html
                                std_out = lxml.html.fromstring(content).text_content()
                            except Exception:
                                std_out = content

                    if not auth_html:
                        entry_list.append('<pre class="output">')
                        if std_out and std_out != "_NoPrompt_":
                            entry_list.append('<span class="stdout">%s</span>' % cgi.escape(std_out))
                        if std_err:
                            entry_list.append('<span class="stderr">%s</span>' % cgi.escape(std_err))
                        entry_list.append('</pre>')
                        resp_list.append(["output", "\n".join(entry_list)])

                elif action == "file_request":
                    request_id, request_method, file_path, if_mod_since = cmd
                    status = (404, "Not Found")
                    etag = None
                    last_modified = None
                    content_type = None
                    content_length = None
                    content_b64 = ""
                    remote_modtime = None
                    if if_mod_since:
                        remote_modtime = str2datetime(if_mod_since)

                    if not file_path.startswith("/"):
                        # Blob request
                        btime, bheaders, bcontent = self.blob_cache.get_blob(file_path)
                        if bheaders:
                            mod_datetime = datetime.datetime.fromtimestamp(btime)
                            if remote_modtime and remote_modtime >= mod_datetime:
                                # Somewhat redundant check, since blobs are never modified!
                                status = (304, "Not Modified")
                            else:
                                last_modified = datetime2str(mod_datetime)
                                etag = file_path
                                content_type = bheaders.get("content_type") or "text/html"
                                content_length = bheaders["content_length"]
                                if request_method != "HEAD":
                                    content_b64 = bcontent # B64 encoded
                                status = (200, "OK")
                    else:
                        abspath = file_path
                        if os.path.sep != "/":
                            abspath = abspath.replace("/", os.path.sep)

                        if os.path.isfile(abspath) and os.access(abspath, os.R_OK):
                            mod_datetime = datetime.datetime.fromtimestamp(os.path.getmtime(abspath))

                            if remote_modtime and remote_modtime >= mod_datetime:
                                status = (304, "Not Modified")
                            else:
                                # Read file contents
                                try:
                                    last_modified = datetime2str(mod_datetime)

                                    mime_type, encoding = mimetypes.guess_type(abspath)
                                    if mime_type:
                                        content_type = mime_type

                                    with open(abspath, "rb") as file:
                                        data = file.read()
                                        hasher = hashlib.sha1()
                                        hasher.update(data)
                                        digest = hasher.hexdigest()
                                        etag = '"%s"' % digest
                                        if request_method == "HEAD":
                                            content_length = len(data)
                                        else:
                                            content_b64 = base64.b64encode(data)
                                        status = (200, "OK")
                                except Exception:
                                    pass

                    resp_list.append(["file_response", request_id,
                                      dict(status=status, last_modified=last_modified,
                                           etag=etag,
                                           content_type=content_type, content_length=content_length,
                                           content_b64=content_b64)])

                elif action == "errmsg":
                    logging.warning("remote_request: ERROR %s", cmd[0])
                else:
                    raise Exception("Invalid action: "+action)
            self.remote_response(term_name, "", resp_list);
        except Exception, excp:
            import traceback
            errmsg = "%s\n%s" % (excp, traceback.format_exc())
            logging.error("TerminalClient.remote_request: %s", errmsg)
            self.remote_response(term_name, "", [["errmsg", errmsg]])
            ##self.shutdown()


class GTCallbackMixin(object):
    """ GT callback implementation
    """
    oshell_client = None
    def set_client(self, oshell_client):
        self.oshell_client = oshell_client
        
    def logmessage(self, log_level, msg, exc_info=None, logtype="", prompt="", plaintext=""):
        # If log_level is None, always display message
        if self.oshell_client and (log_level is None or log_level >= self.log_level):
            self.oshell_client.remote_response(OSHELL_NAME, "", [["log", "", [logtype, log_level, msg]]])

        if logtype or log_level is None:
            sys.stderr.write((plaintext or msg)+"\n"+prompt)
            if prompt:
                sys.stderr.flush()

    def editback(self, content, filepath="", filetype="", editor="", modify=False):
        if editor and editor not in AJAX_EDITORS:
            return otrace.TraceCallback.editback(self, content, filepath=filepath, filetype=filetype,
                                          editor=editor, modify=modify)
        params = {"editor": editor, "modify": modify, "command": "edit -f "+filepath if modify else "",
                  "filepath": filepath, "filetype": filetype}
        self.oshell_client.remote_response(OSHELL_NAME, "", [["edit", params, base64.b64encode(content) if content else ""]])
        return (None, None)

if otrace:
    class GTCallback(GTCallbackMixin, otrace.TraceCallback):
        pass
else:
    class GTCallback(GTCallbackMixin):
        pass

class WidgetStream(object):
    _all_widgets = []
    _term_pagelets = {}
    _chat_widgets = {}

    startseq = "\x1b[?1155;"
    startdelim = "h"
    endseq = "\x1b[?1155l"

    def __init__(self, stream, address):
        self.stream = stream
        self.address = address
        self.packet_cookie = ""
        self.chat_cookie = ""
        self.widget_token = ""
        self._all_widgets.append(self)
        self.stream.set_close_callback(self.on_close)

    @classmethod
    def get_chat_widget(cls, lterm_cookie):
        """Return chat WidgetStream instance"""
        return cls._chat_widgets.get(lterm_cookie)

    @classmethod
    def get_widget_pagelet(cls, lterm_cookie):
        """Return widget pagelet associated with terminal"""
        return cls._term_pagelets.get(lterm_cookie)

    @classmethod
    def shutdown_all(cls):
        for widget in cls._all_widgets[:]:
            widget.shutdown()

    def on_close(self):
        try:
            if self.chat_cookie:
                self.set_chat_status(False)
                self._chat_widgets.pop(self.chat_cookie, None)
                self.chat_cookie = ""
            self._all_widgets.remove(self)
            self.stream = None
        except Exception:
            pass
        
    def shutdown(self):
        if not self.stream:
            return
        try:
            self.stream.close()
        except Exception:
            pass
        self.on_close()

    def set_chat_status(self, status, widget_token=""):
        term_info = TerminalClient.all_cookies.get(self.chat_cookie)
        if not term_info:
            return
        self.widget_token = widget_token
        host_connection, term_name = term_info
        host_connection.send_request_threadsafe("response", term_name, "", [["terminal", "graphterm_chat", bool(status), widget_token]])

    def next_packet(self):
        if self.stream:
            self.stream.read_until(self.startseq, self.start_packet)

    def start_packet(self, data):
        if self.stream:
            self.stream.read_until(self.startdelim, self.check_cookie)

    def check_cookie(self, data):
        data = data[:-len(self.startdelim)].strip()
        if not data.isdigit() or data not in TerminalClient.all_cookies:
            return self.shutdown()
        self.packet_cookie = data
        if self.stream:
            self.stream.read_until(self.endseq, self.receive_packet)

    def receive_packet(self, data):
        data = data[:-len(self.endseq)]

        term_info = TerminalClient.all_cookies.get(self.packet_cookie)
        if not term_info:
            return self.shutdown()

        host_connection, term_name = term_info

        headers, content = lineterm.parse_headers(data)

        resp_type = headers["x_gterm_response"]

        if resp_type == "capture_chat":
            chat_cookie = headers["x_gterm_parameters"].get("cookie")
            widget_token = headers["x_gterm_parameters"].get("widget_token", "")
            if chat_cookie == self.packet_cookie:  # Redundant?
                prev_widget = self.get_chat_widget(chat_cookie)
                if prev_widget and prev_widget is not self:
                    # Only one active chat widget per terminal at a time
                    prev_widget.shutdown()
                self.chat_cookie = chat_cookie
                self._chat_widgets[chat_cookie] = self
                self.set_chat_status(True, widget_token)
            else:
                logging.warning("Invalid chat cookie %s", chat_cookie)

        elif resp_type == "create_blob":
            blob_id = headers["x_gterm_parameters"].get("blob_id")
            if not blob_id:
                logging.warning("No id for blob creation")
            elif "content_length" not in headers:
                logging.warning("No content_length specified for create_blob")
            else:
                host_connection.blob_cache.add_blob(blob_id, headers, content)

        else:
            params = {"validated": True, "headers": headers}
            args = [params, base64.b64encode(content) if content else ""]
            if resp_type == "pagelet":
                self._term_pagelets[self.packet_cookie] = args
            host_connection.send_request_threadsafe("response", term_name, "", [["terminal", "graphterm_widget", args]])
        self.packet_cookie = ""
        self.next_packet()

    def send_packet(self, data):
        if self.stream:
            self.stream.write(data)
        

class WidgetServer(TCPServer):
    def handle_stream(self, stream, address):
        widget_stream = WidgetStream(stream, address)
        widget_stream.next_packet()

def gterm_shutdown(trace_shell=None):
    if trace_shell:
        trace_shell.shutdown()

    def gterm_shutdown_aux():
        global IO_loop, IO_loop_control
        TerminalClient.shutdown_all()
        WidgetStream.shutdown_all()
        if IO_loop and IO_loop_control:
            IO_loop.stop()
            IO_loop = None

    if IO_loop:
        try:
            IO_loop.add_callback(gterm_shutdown_aux)
        except Exception:
            pass

Host_connections = {}
def gterm_connect(host_name, server_addr, server_port=gterm.DEFAULT_HOST_PORT, connect_kw={},
                  oshell_globals=None, oshell_thread=False, oshell_unsafe=False, oshell_workdir="",
                  oshell_init="", oshell_db_interface=None, oshell_web_interface=None,
                  oshell_hold_wrapper=None, oshell_no_input=True, gterm_callback=None, io_loop=None):
    """ Returns (host_connection, host_secret, trace_shell)
    If io_loop is provided, it is assumed that the caller controls io_loop. Otherwise, gterm_connect
    starts io_loop on a separate thread.
    If oshell_thread, then oshell loop is automatically started.
    """
    global IO_loop, IO_loop_control

    io_loop_thread = None
    if io_loop:
        IO_loop = io_loop
    else:
        IO_loop_control = True
        if not IO_loop:
            import tornado.ioloop
            IO_loop = tornado.ioloop.IOLoop.instance()
            io_loop_thread = threading.Thread(target=IO_loop.start)
        io_loop = IO_loop

    host_secret = "%016x" % random.randrange(0, 2**64)

    host_connection = TerminalClient.get_client(host_name,
                         connect=(server_addr, server_port, host_secret),
                          connect_kw=connect_kw)

    Host_connections[host_secret] = host_connection

    if io_loop_thread:
        io_loop_thread.start()

    if not oshell_globals:
        return (host_connection, host_secret, None)

    if not gterm_callback:
        gterm_callback = GTCallback()
    gterm_callback.set_client(host_connection)
    otrace.OTrace.setup(callback_handler=gterm_callback)
    otrace.OTrace.html_wrapper = HtmlWrapper(host_connection.osh_cookie)
    trace_shell = otrace.OShell(locals_dict=oshell_globals, globals_dict=oshell_globals,
                                new_thread=oshell_thread,
                                allow_unsafe=oshell_unsafe, work_dir=oshell_workdir,
                                add_env={gterm.GT_PREFIX+"COOKIE": host_connection.osh_cookie,
                                         gterm.GT_PREFIX+"SHARED_SECRET": host_secret},
                                init_file=oshell_init,
                                db_interface=oshell_db_interface,
                                web_interface=oshell_web_interface,
                                hold_wrapper=oshell_hold_wrapper,
                                no_input=oshell_no_input,
                                eventloop_callback=io_loop.add_callback)
    host_connection.add_oshell()

    return (host_connection, host_secret, trace_shell)

def run_host(options, args):
    global Gterm_host, Host_secret, Trace_shell, Xterm, Killterm
    host_name = args[0]

    oshell_globals = globals() if options.oshell else None

    auth_code = None
    ext_port = None
    if options.auth_file:
        if options.auth_file != "none":
            with open(options.auth_file) as f:
                comps = f.read().strip().split()
                auth_code = gterm.undashify(comps[0])
                ext_port = int(comps[1]) if len(comps) > 1 else None
    else:
        try:
            auth_code, ext_port = gterm.read_auth_code(user=host_name, server=options.external_host)
            print >> sys.stderr, "Using auth info from default file", gterm.get_auth_filename(user=host_name, server=options.external_host)
        except Exception, excp:
            raise
            auth_code = None

    key_version = "1" if auth_code else None
    server_port = options.server_port or gterm.DEFAULT_HOST_PORT
    internal_client_ssl = {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": options.internal_certfile} if options.internal_certfile else None
    Gterm_host, Host_secret, Trace_shell = gterm_connect(host_name, options.server_addr,
                                                         server_port=server_port,
                                                         connect_kw={"ssl_options": internal_client_ssl,
                                                                     "key_secret": auth_code or None,
                                                                     "key_version": key_version,
                                                                     "key_id": str(server_port),
                                                                     "lterm_logfile": options.lterm_logfile},
                                                         oshell_globals=oshell_globals,
                                                         oshell_unsafe=True,
                                                         oshell_no_input=(not options.oshell_input))
    Xterm = Gterm_host.xterm
    Killterm = Gterm_host.remove_term

    def host_shutdown():
        global Gterm_host
        gterm_shutdown(Trace_shell)
        Gterm_host = None

    def sigterm(signal, frame):
        logging.warning("SIGTERM signal received")
        IO_loop.add_callback(host_shutdown)
    signal.signal(signal.SIGTERM, sigterm)

    try:
        time.sleep(1)   # Wait for IO_loop thread to start

        print >> sys.stderr, "\nType ^C to exit"
        if Trace_shell and options.oshell_input:
            Trace_shell.loop()
        else:
            while Gterm_host:
                time.sleep(1)
    except KeyboardInterrupt:
        print >> sys.stderr, "Interrupted"

    finally:
        IO_loop.add_callback(host_shutdown)


def main():
    global Options
    from optparse import OptionParser
    usage = "usage: gtermhost [-h ... options] <hostname>"
    parser = OptionParser(usage=usage)

    parser.add_option("", "--server_addr", dest="server_addr", default="localhost",
                      help="Server hostname (or IP address) (default: localhost)")
    parser.add_option("", "--server_port", dest="server_port", default=0,
                      help="Server port (default: %d)" % gterm.DEFAULT_HOST_PORT, type="int")
    parser.add_option("", "--external_host", dest="external_host", default="",
                      help="external host name (or IP address), if different from server_addr")
    parser.add_option("", "--auth_file", dest="auth_file", default="",
                      help="Server auth file")

    parser.add_option("", "--oshell", dest="oshell", action="store_true",
                      help="Activate otrace/oshell")
    parser.add_option("", "--oshell_input", dest="oshell_input", action="store_true",
                      help="Allow stdin input otrace/oshell")
    parser.add_option("", "--internal_certfile", dest="internal_certfile", default="",
                      help="Internal SSL certfile")
    parser.add_option("", "--logging", dest="logging", action="store_true",
                      help="Log to ~/.graphterm/gtermhost.log")
    parser.add_option("", "--lterm_logfile", dest="lterm_logfile", default="",
                      help="Lineterm logfile")

    parser.add_option("", "--daemon", dest="daemon", default="",
                      help="daemon=start/stop/restart/status")

    (Options, args) = parser.parse_args()
    if len(args) != 1 and Options.daemon != "stop":
        print >> sys.stderr, usage
        sys.exit(1)

    if not args or not HOST_RE.match(args[0]):
        print >> sys.stderr, "Invalid/missing host name"
        sys.exit(1)

    gterm.setup_logging(logging.ERROR)

    if not Options.daemon:
        run_host(Options, args)
    else:
        from daemon import ServerDaemon
        host_name = args[0]
        pidfile = "/tmp/gtermhost."+host_name+".pid"
        daemon = ServerDaemon(pidfile, functools.partial(run_host, Options, args))
        daemon.daemon_run(Options.daemon)

if __name__ == "__main__":
    main()
