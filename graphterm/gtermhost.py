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

def get_lterm_host(host):
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
    def __init__(self, host, port, command=SHELL_CMD, lterm_cookie="", io_loop=None, ssl_options={},
                 term_type="", lterm_logfile=""):
        super(TerminalClient, self).__init__(host, port, io_loop=io_loop,
                                             ssl_options=ssl_options, max_packet_buf=3,
                                             reconnect_sec=RETRY_SEC, server_type="frame")
        self.term_type = term_type
        self.lterm_cookie = lterm_cookie
        self.lterm_logfile = lterm_logfile
        self.command = command
        self.terms = {}
        self.lineterm = None

    def shutdown(self):
        print >> sys.stderr, "Shutting down client connection %s -> %s:%s" % (self.connection_id, self.host, self.port)
        if self.lineterm:
            self.lineterm.shutdown()
        self.lineterm = None
        super(TerminalClient, self).shutdown()

    def handle_connect(self):
        lterm_host = get_lterm_host(self.connection_id)
        self.remote_response("", [["term_params", {"lterm_cookie": self.lterm_cookie,
                                                  "lterm_host": lterm_host}]])
        
    def add_oshell(self):
        self.add_term(OSHELL_NAME, 0, 0)
        
    def add_term(self, term_name, height, width):
        if term_name not in self.terms:
            self.send_request_threadsafe("terminal_update", term_name, True)
        self.terms[term_name] = (height, width)

    def remove_term(self, term_name):
        try:
            del self.terms[term_name]
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
                                               cookie=self.lterm_cookie, host=self.connection_id,
                                               prompt=SHELL_PROMPT, term_type=self.term_type,
                                               logfile=self.lterm_logfile)
        term_name = self.lineterm.terminal(term_name, height=height, width=width)
        self.add_term(term_name, height, width)
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
          open_terminal <name> <command>
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
            resp_list = []
            for cmd in req_list:
                action = cmd.pop(0)

                if action == "reconnect":
                    if self.lineterm:
                        self.lineterm.reconnect(term_name)

                elif action == "open_terminal":
                    if self.lineterm:
                        name = self.lineterm.terminal(cmd[0][0], command=cmd[0][1])
                        self.remote_response(term_name, [["open", name, ""]])

                elif action == "set_size":
                    if term_name != OSHELL_NAME:
                        self.xterm(term_name, cmd[0][0], cmd[0][1])

                elif action == "kill_term":
                    self.remove_term(term_name)

                elif action == "keypress":
                    if self.lineterm:
                        self.lineterm.term_write(term_name, str(cmd[0]))

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
                    cmd_incomplete = str(cmd[0])
                    dummy, sep, text = cmd_incomplete.rpartition(" ")
                    options = otrace.OShell.instance.completer(text, 0, line=cmd_incomplete, all=True)
                    if text:
                        options = [cmd_incomplete[:-len(text)]+option for option in options]
                    else:
                        options = [cmd_incomplete+option for option in options]
                    resp_list.append(["completed_input", options])   # Not escaped; handle as text

                elif action == "input":
                    cmd_input = str(cmd[0]).lstrip()   # Unescaped text
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
                    if self.lterm_cookie and std_out.startswith(HTML_ESCAPES[0]):
                        auth_prefix = HTML_ESCAPES[0]+self.lterm_cookie+HTML_ESCAPES[1]
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
                    modified = None
                    etag = None
                    content_type = None
                    content_length = None
                    content = None
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

Lterm_cookie = None
def gterm_shutdown(trace_shell=None):
    TerminalClient.shutdown_all()
    if trace_shell:
        trace_shell.close()

def gterm_connect(host_name, server_addr, server_port=8899, shell_cmd=SHELL_CMD, connect_kw={},
                  oshell_globals=None, oshell_unsafe=False, oshell_workdir="", oshell_init=""):
    """ Returns (host_connection, lterm_cookie, trace_shell)
    """
    lterm_cookie = "1%015d" % random.randrange(0, 10**15)   # 1 prefix to keep leading zeros when stringified

    host_connection = TerminalClient.get_client(host_name,
                         connect=(server_addr, server_port, shell_cmd, lterm_cookie),
                          connect_kw=connect_kw)

    if oshell_globals:
        host_connection.add_oshell()
        gterm_callback = GTCallback()
        gterm_callback.set_client(host_connection)
        otrace.OTrace.setup(callback_handler=gterm_callback)
        otrace.OTrace.html_wrapper = HtmlWrapper(lterm_cookie)
        trace_shell = otrace.OShell(locals_dict=oshell_globals, globals_dict=oshell_globals,
                                    allow_unsafe=oshell_unsafe, work_dir=oshell_workdir,
                                    add_env={"GRAPHTERM_COOKIE": lterm_cookie}, init_file=oshell_init)
    else:
        trace_shell = None

    return (host_connection, lterm_cookie, trace_shell)

def run_host(options, args):
    global IO_loop, Gterm_host, Lterm_cookie, Trace_shell, Xterm, Killterm
    import tornado.ioloop
    server_addr = args[0]
    host_name = args[1]
    protocol = "https" if options.https else "http"

    oshell_globals = globals() if options.oshell else None
    Gterm_host, Lterm_cookie, Trace_shell = gterm_connect(host_name, server_addr,
                                                          server_port=options.server_port,
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

    parser.add_option("", "--server_port", dest="server_port", default=8899,
                      help="server port (default: 8899)", type="int")

    parser.add_option("", "--oshell", dest="oshell", action="store_true",
                      help="Activate otrace/oshell")

    parser.add_option("", "--https", dest="https", action="store_true",
                      help="Use SSL (TLS) connections for security")


    parser.add_option("", "--daemon", dest="daemon", default="",
                      help="daemon=start/stop/restart/status")

    (options, args) = parser.parse_args()
    if len(args) != 2 and options.daemon != "stop":
        print >> sys.stderr, usage
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
