#!/usr/bin/env python

"""gtermhost: GraphTerm host connector
"""

import base64
import cgi
import calendar
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

import tornado.netutil
import lineterm
import packetserver

RETRY_SEC = 15

OSHELL_NAME = "osh"

##SHELL_CMD = "bash -l"
SHELL_CMD = "/bin/bash -l"

# Short prompt (long prompt with directory metadata fills most of row)
##PROMPT_PREFIX = '<gtprompt/>'    # Unique prompt prefix
PROMPT_PREFIX = ''              # No unique prefix necessary for bash (using PROMPT_COMMAND)
PROMPT_SUFFIX = '$'
SHELL_PROMPT = [PROMPT_PREFIX, '\W', PROMPT_SUFFIX]

HTML_ESCAPES = ["\x1b[?1155;", "h",
                "\x1b[?1155l"]

DEFAULT_HTTP_PORT = 8900
DEFAULT_HOST_PORT = DEFAULT_HTTP_PORT - 1

HOST_RE = re.compile(r"^[\w\-\.]+$")             # Allowed host names
SESSION_RE = re.compile(r"^[a-z]\w*$")           # Allowed session names

def get_normalized_host(host):
    """Return identifier version of hostname"""
    return re.sub(r"\W", "_", host.upper())

class HtmlWrapper(object):
    """ Wrapper for HTML output
    """
    def __init__(self, lterm_cookie):
        self.lterm_cookie = lterm_cookie

    def wrap(self, html, msg_type=""):
        return HTML_ESCAPES[0] + self.lterm_cookie + HTML_ESCAPES[1]  + html + HTML_ESCAPES[-1]

class TerminalClient(packetserver.RPCLink, packetserver.PacketClient):
    _all_connections = {}
    all_cookies = {}
    def __init__(self, host, port, command=SHELL_CMD, host_secret="", oshell=False, io_loop=None, ssl_options={},
                 term_type="", widget_port=0, lterm_logfile=""):
        super(TerminalClient, self).__init__(host, port, io_loop=io_loop,
                                             ssl_options=ssl_options, max_packet_buf=3,
                                             reconnect_sec=RETRY_SEC, server_type="frame")
        self.term_type = term_type
        self.host_secret = host_secret
        self.widget_port = widget_port
        self.lterm_logfile = lterm_logfile
        self.command = command
        self.oshell = oshell
        self.terms = {}
        self.lineterm = None
        self.osh_cookie = lineterm.make_lterm_cookie()

    def shutdown(self):
        print >> sys.stderr, "Shutting down client connection %s -> %s:%s" % (self.connection_id, self.host, self.port)
        if self.lineterm:
            self.lineterm.shutdown()
        self.lineterm = None
        super(TerminalClient, self).shutdown()

    def handle_connect(self):
        if self.oshell:
            self.add_oshell()
        normalized_host = get_normalized_host(self.connection_id)
        self.remote_response("", [["term_params", {"host_secret": self.host_secret,
                                                  "normalized_host": normalized_host}]])
        if self.widget_port:
            Widget_server = WidgetServer()
            Widget_server.listen(self.widget_port, address="localhost")
            print >> sys.stderr, "GraphTerm widgets listening on %s:%s" % ("localhost", self.widget_port)
        
    def add_oshell(self):
        self.add_term(OSHELL_NAME, self.osh_cookie)
        
    def add_term(self, term_name, lterm_cookie):
        if term_name not in self.terms:
            self.send_request_threadsafe("terminal_update", term_name, True)
        self.terms[term_name] = lterm_cookie
        self.all_cookies[lterm_cookie] = (self, term_name)

    def remove_term(self, term_name):
        try:
            lterm_cookie = self.terms.get(term_name)
            if lterm_cookie:
                del self.terms[term_name]
                del self.all_cookies[lterm_cookie]
        except Exception:
            pass
        self.send_request_threadsafe("terminal_update", term_name, False)

        if not self.lineterm:
            return
        if not term_name:
            self.lineterm.kill_all()
        else:
            self.lineterm.kill_term(term_name)

    def xterm(self, term_name="", height=25, width=80, command=SHELL_CMD):
        if not self.lineterm:
            self.lineterm = lineterm.Multiplex(self.screen_callback, command=command,
                                               shared_secret=self.host_secret, host=self.connection_id,
                                               prompt=SHELL_PROMPT, term_type=self.term_type,
                                               widget_port=self.widget_port, logfile=self.lterm_logfile)
        term_name, lterm_cookie = self.lineterm.terminal(term_name, height=height, width=width)
        self.add_term(term_name, lterm_cookie)
        return term_name

    def screen_callback(self, term_name, command, arg):
        # Invoked in lineterm thread; schedule callback in ioloop
        self.send_request_threadsafe("response", term_name, [["terminal", command, arg]])

    def remote_response(self, term_name, message_list):
        self.send_request_threadsafe("response", term_name, message_list)

    def remote_request(self, term_name, req_list):
        """
        Setup commands:
          reconnect

        Input commands:
          incomplete_input <line>
          input <line>
          click_paste <text> <file_uri> {command:, clear_last:, normalize:, enter:}
          get_finder <kind> <directory>
          save_file <filepath> <filedata>

        Output commands:
          completed_input <line>
          prompt <str>
          stdin <str>
          stdout <str>
          stderr <str>
        """
        try:
            lterm_cookie = self.terms.get(term_name)
            resp_list = []
            for cmd in req_list:
                action = cmd.pop(0)

                if action == "reconnect":
                    if self.lineterm:
                        self.lineterm.reconnect(term_name)

                elif action == "set_size":
                    if term_name != OSHELL_NAME:
                        self.xterm(term_name, cmd[0][0], cmd[0][1])

                elif action == "kill_term":
                    self.remove_term(term_name)

                elif action == "keypress":
                    if self.lineterm:
                        self.lineterm.term_write(term_name, cmd[0].encode("ascii", "ignore"))

                elif action == "save_file":
                    if self.lineterm:
                        self.lineterm.save_file(term_name, cmd[0], cmd[1])

                elif action == "click_paste":
                    # click_paste: text, file_uri, {command:, clear_last:, normalize:, enter:}
                    if self.lineterm:
                        self.lineterm.click_paste(term_name, cmd[0], cmd[1], cmd[2])

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
                    here_doc = cmd[1]
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
                    last_modified = None
                    etag = None
                    content_type = None
                    content_length = None
                    content = ""
                    abspath = file_path
                    if os.path.sep != "/":
                        abspath = abspath.replace("/", os.path.sep)

                    if os.path.isfile(abspath) and os.access(abspath, os.R_OK):
                        stat_result = os.stat(abspath)
                        mod_datetime = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

                        if if_mod_since:
                            date_tuple = email.utils.parsedate(if_mod_since)
                            copy_datetime = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
                        else:
                            copy_datetime = None

                        if copy_datetime and copy_datetime >= mod_datetime:
                            status = (304, "Not Modified")
                        else:
                            # Read file contents
                            try:
                                tm = calendar.timegm(mod_datetime.utctimetuple())
                                last_modified = email.utils.formatdate(tm, localtime=False, usegmt=True)

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
                                        content = data
                                    status = (200, "OK")
                            except Exception:
                                pass

                    resp_list.append(["file_response", request_id,
                                      dict(status=status, last_modified=last_modified,
                                           etag=etag,
                                           content_type=content_type, content_length=content_length,
                                           content=base64.b64encode(content))])

                elif action == "errmsg":
                    logging.warning("remote_request: ERROR %s", cmd[0])
                else:
                    raise Exception("Invalid action: "+action)
            self.remote_response(term_name, resp_list);
        except Exception, excp:
            import traceback
            errmsg = "%s\n%s" % (excp, traceback.format_exc())
            print >> sys.stderr, "TerminalClient.remote_request: "+errmsg
            self.remote_response(term_name, [["errmsg", errmsg]])
            ##self.shutdown()


class GTCallbackMixin(object):
    """ GT callback implementation
    """
    oshell_client = None
    def set_client(self, oshell_client):
        self.oshell_client = oshell_client
        
    def logmessage(self, log_level, msg, exc_info=None, logtype="", plaintext=""):
        # If log_level is None, always display message
        if self.oshell_client and (log_level is None or log_level >= self.log_level):
            self.oshell_client.remote_response(OSHELL_NAME, [["log", logtype, log_level, msg]])

        if logtype or log_level is None:
            sys.stderr.write((plaintext or msg)+"\n")

    def editback(self, content, filepath="", filetype="", editor="", modify=False):
        if editor and editor != "web":
            return otrace.TraceCallback.editback(self, content, filepath=filepath, filetype=filetype,
                                          editor=editor, modify=modify)
        params = {"editor": editor, "modify": modify, "command": "edit -f "+filepath if modify else "",
                  "filepath": filepath, "filetype": filetype}
        self.oshell_client.remote_response(OSHELL_NAME, [["edit", params, content]])
        return (None, None)

if otrace:
    class GTCallback(GTCallbackMixin, otrace.TraceCallback):
        pass
else:
    class GTCallback(GTCallbackMixin):
        pass

class WidgetStream(object):
    _all_widgets = []

    startseq = "\x1b[?1155;"
    startdelim = "h"
    endseq = "\x1b[?1155l"

    def __init__(self, stream, address):
        self.stream = stream
        self.address = address
        self.cookie = None
        self._all_widgets.append(self)

    @classmethod
    def shutdown_all(cls):
        for widget in cls._all_widgets[:]:
            widget.shutdown()

    def shutdown(self):
        if not self.stream:
            return
        try:
            self.stream.close()
            self.stream = None
            self._all_widgets.remove(self)
        except Exception:
            pass

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
        self.cookie = data
        if self.stream:
            self.stream.read_until(self.endseq, self.receive_packet)

    def receive_packet(self, data):
        data = data[:-len(self.endseq)]

        term_info = TerminalClient.all_cookies.get(self.cookie)
        if not term_info:
            return self.shutdown()

        host_connection, term_name = term_info

        headers, content = lineterm.parse_headers(data)
        params = {"validated": True, "headers": headers}
        host_connection.send_request_threadsafe("response", term_name, [["terminal", "graphterm_widget", [params,
                                                 base64.b64encode(content) if content else ""]]])
        self.cookie = None
        self.next_packet()
        

class WidgetServer(tornado.netutil.TCPServer):
    def handle_stream(self, stream, address):
        widget_stream = WidgetStream(stream, address)
        widget_stream.next_packet()

Host_secret = None
def gterm_shutdown(trace_shell=None):
    TerminalClient.shutdown_all()
    WidgetStream.shutdown_all()
    if trace_shell:
        trace_shell.close()

Host_connections = {}
def gterm_connect(host_name, server_addr, server_port=DEFAULT_HOST_PORT, shell_cmd=SHELL_CMD, connect_kw={},
                  oshell_globals=None, oshell_unsafe=False, oshell_workdir="", oshell_init=""):
    """ Returns (host_connection, host_secret, trace_shell)
    """
    host_secret = "%016x" % random.randrange(0, 2**64)

    host_connection = TerminalClient.get_client(host_name,
                         connect=(server_addr, server_port, shell_cmd, host_secret, bool(oshell_globals)),
                          connect_kw=connect_kw)

    Host_connections[host_secret] = host_connection

    if oshell_globals:
        gterm_callback = GTCallback()
        gterm_callback.set_client(host_connection)
        otrace.OTrace.setup(callback_handler=gterm_callback)
        otrace.OTrace.html_wrapper = HtmlWrapper(host_connection.osh_cookie)
        trace_shell = otrace.OShell(locals_dict=oshell_globals, globals_dict=oshell_globals,
                                    allow_unsafe=oshell_unsafe, work_dir=oshell_workdir,
                                    add_env={"GRAPHTERM_COOKIE": host_connection.osh_cookie,
                                             "GRAPHTERM_SHARED_SECRET": host_secret}, init_file=oshell_init)

    else:
        trace_shell = None

    return (host_connection, host_secret, trace_shell)

def run_host(options, args):
    global IO_loop, Gterm_host, Host_secret, Trace_shell, Xterm, Killterm
    import tornado.ioloop
    server_addr = args[0]
    host_name = args[1]
    protocol = "https" if options.https else "http"

    oshell_globals = globals() if options.oshell else None
    Gterm_host, Host_secret, Trace_shell = gterm_connect(host_name, server_addr,
                                                         server_port=options.server_port,
                                                         connect_kw={"widget_port":
                                                                     (DEFAULT_HTTP_PORT-2 if options.widgets else 0)},
                                                         oshell_globals=oshell_globals,
                                                         oshell_unsafe=True)
    Xterm = Gterm_host.xterm
    Killterm = Gterm_host.remove_term

    def host_shutdown():
        global Gterm_host
        gterm_shutdown(Trace_shell)
        Gterm_host = None
        IO_loop.stop()

    def sigterm(signal, frame):
        logging.warning("SIGTERM signal received")
        IO_loop.add_callback(host_shutdown)
    signal.signal(signal.SIGTERM, sigterm)

    IO_loop = tornado.ioloop.IOLoop.instance()
    try:
        ioloop_thread = threading.Thread(target=IO_loop.start)
        ioloop_thread.start()
        time.sleep(1)   # Time to start thread

        print >> sys.stderr, "\nType ^C to exit"
        if Trace_shell:
            Trace_shell.loop()
        else:
            while Gterm_host:
                time.sleep(1)
    except KeyboardInterrupt:
        print >> sys.stderr, "Interrupted"

    finally:
        try:
            pass
        except Exception:
            pass

    IO_loop.add_callback(host_shutdown)

def main():
    from optparse import OptionParser
    usage = "usage: gtermhost [-h ... options] <serveraddr> <hostname>"
    parser = OptionParser(usage=usage)

    parser.add_option("", "--server_port", dest="server_port", default=DEFAULT_HOST_PORT,
                      help="server port (default: %d)" % DEFAULT_HOST_PORT, type="int")

    parser.add_option("", "--oshell", dest="oshell", action="store_true",
                      help="Activate otrace/oshell")

    parser.add_option("", "--https", dest="https", action="store_true",
                      help="Use SSL (TLS) connections for security")

    parser.add_option("", "--widgets", dest="widgets", action="store_true",
                      help="Activate widgets on port %d" % (DEFAULT_HTTP_PORT-2))

    parser.add_option("", "--daemon", dest="daemon", default="",
                      help="daemon=start/stop/restart/status")

    (options, args) = parser.parse_args()
    if len(args) != 2 and options.daemon != "stop":
        print >> sys.stderr, usage
        sys.exit(1)

    if not HOST_RE.match(args[1]):
        print >> sys.stderr, "Invalid characters in host name"
        sys.exit(1)

    if not options.daemon:
        run_host(options, args)
    else:
        from daemon import ServerDaemon
        pidfile = "/tmp/gtermhost.pid"
        daemon = ServerDaemon(pidfile, functools.partial(run_host, options, args))
        daemon.daemon_run(options.daemon)

if __name__ == "__main__":
    main()
