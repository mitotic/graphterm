#!/usr/bin/env python

""" Lineterm: Line-oriented pseudo-tty wrapper for GraphTerm
  https://github.com/mitotic/graphterm

Derived from the public-domain Ajaxterm code, v0.11 (2008-11-13).
  https://github.com/antonylesuisse/qweb
  http://antony.lesuisse.org/software/ajaxterm/
The contents of this file remain in the public-domain.
"""

from __future__ import with_statement

import array, cgi, copy, fcntl, glob, logging, mimetypes, optparse, os, pty
import re, signal, select, socket, sys, threading, time, termios, tty, struct, pwd

try:
    import ujson as json
except ImportError:
    import json

import random
try:
    random = random.SystemRandom()
except NotImplementedError:
    import random

import base64
import hashlib
import hmac
import Queue
import shlex
import subprocess
import traceback

MAX_SCROLL_LINES = 500

MAX_PAGELET_BYTES = 1000000  # Max size for pagelet buffer

IDLE_TIMEOUT = 300      # Idle timeout in seconds
UPDATE_INTERVAL = 0.05  # Fullscreen update time interval
TERM_TYPE = "xterm"     # "screen" may be a better default terminal, but arrow keys do not always work

NO_COPY_ENV = set(["GRAPHTERM_EXPORT", "TERM_PROGRAM","TERM_PROGRAM_VERSION", "TERM_SESSION_ID"])

ALTERNATE_SCREEN_CODES = (47, 1047, 1049) # http://rtfm.etla.org/xterm/ctlseq.html
GRAPHTERM_SCREEN_CODES = (1150, 1155)

FILE_EXTENSIONS = {"css": "css", "htm": "html", "html": "html", "js": "javascript", "py": "python",
                   "xml": "xml"}

FILE_COMMANDS = set(["cd", "cp", "mv", "rm", "gcp", "gimages", "gls", "gopen", "gvi"])
REMOTE_FILE_COMMANDS = set(["gbrowse", "gcp"])
COMMAND_DELIMITERS = "<>;"

# Scroll lines array components
JINDEX = 0
JOFFSET = 1
JDIR = 2
JMARKUP = 3
JLINE = 4

Log_ignored = False
MAX_LOG_CHARS = 8

BINDIR = "bin"
File_dir = os.path.dirname(__file__)
Exec_path = os.path.join(File_dir, BINDIR)
Gls_path = os.path.join(Exec_path, "gls")
Exec_errmsg = False

ENCODING = "utf-8"  # "utf-8" or "ascii"

# Bash PROMPT CMD variable (and export version)
BASH_PROMPT_CMD = 'export PS1=$GRAPHTERM_PROMPT; echo -n "\033[?%s;${GRAPHTERM_COOKIE}h$PWD\033[?%s;l"'
EXPT_PROMPT_CMD = 'export PS1=$GRAPHTERM_PROMPT; echo -n `printf \"\\033\"`\"[?%s;${GRAPHTERM_COOKIE}h$PWD\"`printf \"\\033\"`\"[?%s;l\"'

STYLE4 = 4
UNI24 = 24
UNIMASK = 0xffffff
ASCIIMASK = 0x7f

def make_lterm_cookie():
        return "%016d" % random.randrange(10**15, 10**16)

# Meta info indices
JCURDIR = 0
JCONTINUATION = 1

def create_array(fill_value, count):
        """Return array of 32-bit values"""
        return array.array('L', [fill_value]*count)

def dump(data, trim=False, encoded=False):
        """Return unicode string from array of long data, trimming NULs, and encoded to str, if need be"""
        if ENCODING == "ascii":
                ucodes = [(x & ASCIIMASK) for x in data]
        else:
                ucodes = [(x & UNIMASK) for x in data]

        # Replace non-NUL, non-newline control character by space
        ucodes = [(32 if (x < 32 and x and x != 10) else x) for x in ucodes]

        return uclean( u"".join(map(unichr, ucodes)), trim=trim, encoded=encoded)

def uclean(ustr, trim=False, encoded=False):
        """Return cleaned up unicode string, trimmed and encoded to str, if need be"""
        if trim:
                # Trim trailing NULs
                ustr = ustr.rstrip(u"\x00")
        # Replace NULs with spaces and DELs with "?"
        ustr = ustr.replace(u"\x00", u" ").replace(u"\x7f", u"?")

        return ustr.encode(ENCODING, "replace") if encoded else ustr

def prompt_offset(line, prompt, meta=None):
        """Return offset at end of prompt (not including trailing space), or zero"""
        offset = 0
        if (meta and not meta[JCONTINUATION]) or (prompt and prompt[0] and line.startswith(prompt[0])):
                end_offset = line.find(prompt[2])
                if end_offset >= 0:
                        offset = end_offset + len(prompt[2])
        return offset

def command_output(command_args, **kwargs):
        """ Executes a command and returns the string tuple (stdout, stderr)
        keyword argument timeout can be specified to time out command (defaults to 15 sec)
        """
        timeout = kwargs.pop("timeout", 15)
        def command_output_aux():
            try:
                proc = subprocess.Popen(command_args, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                return proc.communicate()
            except Exception, excp:
                return "", str(excp)
        if not timeout:
            return command_output_aux()

        exec_queue = Queue.Queue()
        def execute_in_thread():
            exec_queue.put(command_output_aux())
        thrd = threading.Thread(target=execute_in_thread)
        thrd.start()
        try:
            return exec_queue.get(block=True, timeout=timeout)
        except Queue.Empty:
            return "", "Timed out after %s seconds" % timeout

def is_executable(filepath):
        return os.path.isfile(filepath) and os.access(filepath, os.X_OK)

def which(filepath, add_path=[]):
        filedir, filename = os.path.split(filepath)
        if filedir:
                if is_executable(filepath):
                        return filepath
        else:
                for path in os.environ["PATH"].split(os.pathsep) + add_path:
                        whichpath = os.path.join(path, filepath)
                        if is_executable(whichpath):
                                return whichpath
        return None

def getcwd(pid):
        """Return working directory of running process"""
        if sys.platform.startswith("linux"):
                command_args = ["pwdx", str(pid)]
        else:
                command_args = ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"]
        std_out, std_err = command_output(command_args, timeout=1)
        if std_err:
                logging.warning("getcwd: ERROR %s", std_err)
                return ""
        try:
                if sys.platform.startswith("linux"):
                        return std_out.split()[1]
                else:
                        return std_out.split("\n")[1][1:]
        except Exception, excp:
                logging.warning("getcwd: ERROR %s", excp)
                return ""

def parse_headers(text):
        """Parse gterm output and return (headers, content)"""
        headers = {"content_type": "text/html", "x_gterm_response": "",
                   "x_gterm_parameters": {}}
        content = text
        if text.startswith("<"):
                # Raw HTML
                return (headers, content)

        # "MIME headers"
        head_str, sep, tail_str = text.partition("\r\n\r\n")
        if not sep:
                head_str, sep, tail_str = text.partition("\n\n")
        if not sep:
                head_str, sep, tail_str = text.partition("\r\r")
        if sep:
                if head_str.startswith("{"):
                        # JSON headers
                        try:
                                headers = json.loads(head_str)
                                content = tail_str
                        except Exception, excp:
                                content = str(excp)
                                headers["json_error"] = "JSON parse error"
                                headers["content_type"] = "text/plain"
                else:
                        # Parse mime headers: "-" -> "_" (TO DO)
                        pass

        if "x_gterm_response" not in headers:
                headers["x_gterm_response"] = ""
        if "x_gterm_parameters" not in headers:
                headers["x_gterm_parameters"] = {}

        return (headers, content)
                                        

def shplit(line, delimiters=COMMAND_DELIMITERS, final_delim="&", index=None):
        """Split shell command line, returning all components as a list, including separators
        """
        if not line:
                return []
        comps = shlex.split(line)
        indices = []
        buf = line
        offset = 0
        for comp in comps:
                ncomp = len(buf) - len(buf.lstrip())
                if ncomp:
                        indices.append(offset+ncomp)
                        offset += ncomp
                        buf = buf[ncomp:]
                ncomp = len(comp)
                while True:
                        try:
                                temcomp = shlex.split(buf[:ncomp])[0]
                        except Exception:
                                temcomp = None
                        if temcomp == comp:
                                break
                        ncomp += 1
                        if ncomp > len(buf):
                                raise Exception("shplit ERROR ('%s','%s')" % (comp, buf))
                comp = buf[:ncomp]
                buf = buf[ncomp:]

                if delimiters:
                        tembuf = comp.replace(" ", ".").replace(delimiters[0], " ")
                        indices += shplit(tembuf, delimiters=delimiters[1:], index=offset)
                else:
                        indices.append(offset+ncomp)

                offset += ncomp

        if buf:
                indices.append(offset+len(buf))

        if index is None:
                jprev = 0
                retval = []
                for j in indices:
                        retval.append(line[jprev:j])
                        jprev = j
                if final_delim and retval and retval[-1].endswith(final_delim) and retval[-1] != final_delim:
                        retval[-1] = retval[-1][:-len(final_delim)]
                        retval.append(final_delim)
                                      
                return retval
        else:
                return [j+index for j in indices]

FILE_URI_PREFIX = "file://"
FILE_PREFIX = "/file/"

JSERVER = 0
JHOST = 1
JFILENAME = 2
JFILEPATH = 3
JQUERY = 4

HEX_DIGITS = 16

def create_file_uri(url_comps):
        return FILE_URI_PREFIX + url_comps[JHOST] + url_comps[JFILEPATH] + url_comps[JQUERY]

def split_file_url(url, check_host_secret=None):
        """Return [protocol://server[:port], hostname, filename, fullpath, query] for file://host/path
        or http://server:port/file/host/path, or /file/host/path URLs.
        If not file URL, returns []
        If check_host_secret is specified, and file hmac matches, then hostname is set to the null string.
        """
        if not url:
                return []
        server_port = ""
        if url.startswith(FILE_URI_PREFIX):
                host_path = url[len(FILE_URI_PREFIX):]
        elif url.startswith(FILE_PREFIX):
                host_path = url[len(FILE_PREFIX):]
        else:
                if url.startswith("http://"):
                        protocol = "http"
                elif url.startswith("https://"):
                        protocol = "https"
                else:
                        return []
                j = url.find("/", len(protocol)+3)
                if j < 0:
                        return []
                server_port = url[:j]
                url_path = url[j:]
                if not url_path.startswith(FILE_PREFIX):
                        return []
                host_path = url_path[len(FILE_PREFIX):]

        j = host_path.find("?")
        if j >= 0:
                query = host_path[j:]
                host_path = host_path[:j]
        else:
                query = ""
        comps = host_path.split("/")
        hostname = comps[0]
        filepath = "/"+"/".join(comps[1:])
        filename = comps[-1]
        if check_host_secret:
                filehmac = "?hmac="+hmac.new(str(check_host_secret), filepath, digestmod=hashlib.sha256).hexdigest()[:HEX_DIGITS]
                if query.lower() == filehmac.lower():
                        hostname = ""
        return [server_port, hostname, filename, filepath, query]
        
def relative_file_url(file_url, cwd):
        url_comps = split_file_url(file_url)
        if not url_comps:
            return file_url
        filepath = url_comps[JFILEPATH]
        if filepath == cwd:
                return "."
        else:
                relpath = os.path.relpath(filepath, cwd)
                if relpath.startswith("../../../"):
                        # Too many .. would be confusing
                        return filepath
                else:
                        return relpath

def prompt_markup(text, entry_index, current_dir):
        return '<span class="gterm-cmd-prompt gterm-link" id="prompt%s" data-gtermdir="%s">%s</span>' % (entry_index, current_dir, cgi.escape(text))

def plain_markup(text, command=False):
        cmd_class = " gterm-command" if command else ""
        return '<span class="gterm-cmd-text gterm-link%s">%s</span>' % (cmd_class, cgi.escape(text),)

def path_markup(text, current_dir, command=False):
        cmd_class = " gterm-command" if command else ""
        fullpath = os.path.normpath(os.path.join(current_dir, text))
        return '<a class="gterm-cmd-path gterm-link%s" href="file://%s" data-gtermmime="x-graphterm/%s" data-gtermcmd="%s">%s</a>' % (cmd_class, fullpath, "path", "xpaste", cgi.escape(text))

def command_markup(entry_index, current_dir, pre_offset, offset, line):
        marked_up = prompt_markup(line[pre_offset:offset], entry_index, current_dir)
        try:
                comps = shplit(line[offset:])
        except Exception:
                return marked_up + line[offset:]

        while comps and not comps[0].strip():
                marked_up += comps.pop(0)
        if not comps:
                return marked_up
        cmd = comps.pop(0)
        if current_dir and (cmd.startswith("./") or cmd.startswith("../")):
                marked_up += path_markup(cmd, current_dir, command=True)
        else:
                marked_up += plain_markup(cmd, command=True)
        file_command = cmd in FILE_COMMANDS
        for comp in comps:
                if not comp.strip():
                        # Space
                        marked_up += comp
                elif comp[0] in COMMAND_DELIMITERS:
                        marked_up += plain_markup(comp)
                        if comp[0] == ";":
                                file_command = False
                elif file_command and current_dir and comp[0] != "-":
                        marked_up += path_markup(comp, current_dir)
                else:
                        marked_up += plain_markup(comp)
        return marked_up
                        

class ScreenBuf(object):
        def __init__(self, prompt, fg_color=0, bg_color=7):
                self.prompt = prompt
                self.pre_offset = len(prompt[0]) if prompt else 0
                self.width = None
                self.height = None
                self.cursorx = None
                self.cursory = None
                self.main_screen = None
                self.alt_screen = None
                self.entry_index = 0
                self.current_scroll_count = 0

                self.clear_buf()
                self.cleared_current_dir = None
                self.cleared_last = False

                self.fg_color = fg_color
                self.bg_color = bg_color
                self.default_style = (bg_color << STYLE4) | fg_color
                self.inverse_style = (fg_color << STYLE4) | bg_color
                self.bold_style = 0x08

                self.default_nul = self.default_style << UNI24

        def clear_buf(self):
                self.last_scroll_count = self.current_scroll_count
                self.scroll_lines = []
                self.full_update = True

        def clear_last_entry(self, last_entry_index=None):
                if not self.scroll_lines or self.entry_index <= 0:
                        return
                n = len(self.scroll_lines)-1
                entry_index, offset, dir, markup, line = self.scroll_lines[n]
                if self.entry_index != entry_index:
                        return
                if last_entry_index and last_entry_index != entry_index:
                        return
                self.entry_index -= 1
                while n > 0 and self.scroll_lines[n-1][JINDEX] == entry_index:
                        n -= 1
                self.current_scroll_count -= len(self.scroll_lines) - n
                self.cleared_last = True
                if self.cleared_current_dir is None:
                        self.cleared_current_dir = self.scroll_lines[n][JDIR]
                self.scroll_lines[n:] = []
                if self.last_scroll_count > self.current_scroll_count:
                        self.last_scroll_count = self.current_scroll_count

        def scroll_buf_up(self, line, meta, offset=0):
                current_dir = ""
                current_markup = None
                if offset:
                        # Prompt line (i.e., command line)
                        self.entry_index += 1
                        current_dir = meta[JCURDIR] if meta else ""
                        current_markup = command_markup(self.entry_index, current_dir, self.pre_offset, offset, line)
                        if not self.cleared_last:
                                self.cleared_current_dir = None
                        self.cleared_last = False
                self.current_scroll_count += 1
                self.scroll_lines.append([self.entry_index, offset, current_dir, current_markup, line])
                if len(self.scroll_lines) > MAX_SCROLL_LINES:
                        entry_index, offset, dir, markup, line = self.scroll_lines.pop(0)
                        while self.scroll_lines and self.scroll_lines[0][JINDEX] == entry_index:
                                self.scroll_lines.pop(0)

        def update(self, active_rows, width, height, cursorx, cursory, main_screen,
                   alt_screen=None, prompt=[], reconnecting=False):
                """ Returns full_update, update_rows, update_scroll
                """
                full_update = self.full_update or reconnecting

                if not reconnecting and (width != self.width or height != self.height):
                        self.width = width
                        self.height = height
                        full_update = True

                if (alt_screen and not self.alt_screen) or (not alt_screen and self.alt_screen):
                        full_update = True

                if alt_screen:
                        screen = alt_screen
                        old_screen = self.alt_screen
                        row_count = height
                else:
                        screen = main_screen
                        old_screen = self.main_screen
                        row_count = active_rows

                cursor_moved = (cursorx != self.cursorx or cursory != self.cursory)
                update_rows = []

                for j in range(row_count):
                        new_row = screen.data[width*j:width*(j+1)]
                        if full_update or old_screen is None:
                                row_update = True
                        else:
                                row_update = (new_row != old_screen.data[width*j:width*(j+1)])
                        if row_update or (cursor_moved and (cursory == j or self.cursory == j)):
                                offset = prompt_offset(dump(new_row), prompt, screen.meta[j])
                                update_rows.append([j, offset, "", None, self.dumprichtext(new_row, trim=True)])

                if reconnecting:
                        update_scroll = self.scroll_lines[:]
                elif self.last_scroll_count < self.current_scroll_count:
                        update_scroll = self.scroll_lines[self.last_scroll_count-self.current_scroll_count:]
                else:
                        update_scroll = []

                if not reconnecting:
                    self.last_scroll_count = self.current_scroll_count
                    self.full_update = False
                    self.cursorx = cursorx
                    self.cursory = cursory
                    self.main_screen = main_screen.make_copy() if main_screen else None
                    self.alt_screen = alt_screen.make_copy() if alt_screen else None

                return full_update, update_rows, update_scroll

        def dumprichtext(self, data, trim=False):
                """Returns [(style_list, utf8str), ...] for line data"""
                if all((x >> UNI24) == self.default_style for x in data):
                        # All default style (optimize)
                        return [([], dump(data, trim=trim, encoded=True))]

                span_list = []
                style_list = []
                span_style, span_bg, span_fg = self.default_style, -1, -1
                span = u""
                for scode in data:
                        char_style = scode >> UNI24
                        ucode = scode & ASCIIMASK if ENCODING == "ascii" else scode & UNIMASK
                        if ucode < 32 and ucode and ucode != 10:
                                # Replace non-NUL, non-newline control character by space
                                ucode = 32
                        if span_style != char_style:
                                if span:
                                        span_list.append( (style_list, uclean(span, encoded=True)) )
                                        span = u""
                                span_style = char_style
                                style_list = []
                                if span_style & self.bold_style:
                                        style_list.append("bold")
                                if (span_style & 0x77) == self.inverse_style:
                                        style_list.append("inverse")
                        span += unichr(ucode)
                cspan = uclean(span, trim=trim, encoded=True)
                if cspan:
                        span_list.append( (style_list, cspan) )
                return span_list

        def __repr__(self):
                if not self.main_screen:
                        return ""
                d = dump(self.main_screen.data, trim=True)
                r = ""
                for i in range(self.height):
                        r += "|%s|\n"%d[self.width*i:self.width*(i+1)]
                return r

class Screen(object):
        def __init__(self, width, height, data=None, meta=None):
                self.width = width
                self.height = height
                self.data = data or create_array(0, width*height)
                self.meta = [None] * height

        def make_copy(self):
                return Screen(self.width, self.height, data=copy.copy(self.data), meta=copy.copy(self.meta))

class Terminal(object):
        def __init__(self, term_name, fd, pid, screen_callback, height=25, width=80, cookie=0,
                     shared_secret="", host="", prompt=[], logfile=""):
                self.term_name = term_name
                self.fd = fd
                self.pid = pid
                self.screen_callback = screen_callback
                self.width = width
                self.height = height
                self.cookie = cookie
                self.shared_secret = shared_secret
                self.host = host
                self.prompt = prompt
                self.logfile = logfile
                self.screen_buf = ScreenBuf(prompt)

                self.init()
                self.reset()
                self.output_time = time.time()
                self.buf = ""
                self.alt_mode = False
                self.screen = self.main_screen
                self.trim_first_prompt = bool(prompt)
                self.logchars = 0

        def init(self):
                self.esc_seq={
                        "\x00": None,
                        "\x05": self.esc_da,
                        "\x07": None,
                        "\x08": self.esc_0x08,
                        "\x09": self.esc_0x09,
                        "\x0a": self.esc_0x0a,
                        "\x0b": self.esc_0x0a,
                        "\x0c": self.esc_0x0a,
                        "\x0d": self.esc_0x0d,
                        "\x0e": None,
                        "\x0f": None,
                        "\x1b#8": None,
                        "\x1b=": None,
                        "\x1b>": None,
                        "\x1b(0": None,
                        "\x1b(A": None,
                        "\x1b(B": None,
                        "\x1b[c": self.esc_da,
                        "\x1b[0c": self.esc_da,
                        "\x1b[>c": self.esc_sda,
                        "\x1b[>0c": self.esc_sda,
                        "\x1b[5n": self.esc_sr,
                        "\x1b[6n": self.esc_cpr,
                        "\x1b[x": self.esc_tpr,
                        "\x1b]R": None,
                        "\x1b7": self.esc_save,
                        "\x1b8": self.esc_restore,
                        "\x1bD": self.esc_ind,
                        "\x1bE": self.esc_nel,
                        "\x1bH": None,
                        "\x1bM": self.esc_ri,
                        "\x1bN": None,
                        "\x1bO": None,
                        "\x1bZ": self.esc_da,
                        "\x1ba": None,
                        "\x1bc": self.reset,
                        "\x1bn": None,
                        "\x1bo": None,
                }

                for k,v in self.esc_seq.items():
                        if v==None:
                                self.esc_seq[k] = self.esc_ignore
                # regex
                d={
                        r'\[\??([0-9;]*)([@ABCDEFGHJKLMPXacdefghlmnqrstu`])' : self.csi_dispatch,
                        r'\]([^\x07]+)\x07' : self.esc_ignore,
                }

                self.esc_re=[]
                for k,v in d.items():
                        self.esc_re.append((re.compile('\x1b'+k), v))
                # define csi sequences
                self.csi_seq={
                        '@': (self.csi_at,[1]),
                        '`': (self.csi_G,[1]),
                        'J': (self.csi_J,[0]),
                        'K': (self.csi_K,[0]),
                }

                for i in [i[4] for i in dir(self) if i.startswith('csi_') and len(i)==5]:
                        if not self.csi_seq.has_key(i):
                                self.csi_seq[i] = (getattr(self,'csi_'+i),[1])

        def reset(self, s=""):
                self.update_time = 0
                self.needs_updating = True
                self.main_screen = Screen(self.width, self.height)
                self.alt_screen  = Screen(self.width, self.height)
                self.scroll_top = 0
                self.scroll_bot = self.height-1
                self.cursor_x_bak = self.cursor_x = 0
                self.cursor_y_bak = self.cursor_y = 0
                self.cursor_eol = 0
                self.current_nul = self.screen_buf.default_nul
                self.echobuf = ""
                self.echobuf_count = 0
                self.outbuf = ""
                self.last_html = ""
                self.active_rows = 0
                self.current_meta = None
                self.gterm_code = None
                self.gterm_buf = None
                self.gterm_buf_size = 0
                self.gterm_entry_index = None
                self.gterm_validated = False
                self.gterm_output_buf = []

        def resize(self, height, width):
                reset_flag = (self.width != width or self.height != height)
                if reset_flag:
                        self.scroll_screen()
                        min_width = min(self.width, width)
                        saved_line = None
                        if self.active_rows:
                                # Check first active line for prompt
                                line = dump(self.main_screen.data[:min_width])
                                if prompt_offset(line, self.prompt, self.main_screen.meta[0]):
                                        saved_line = [len(line.rstrip(u'\x00')), self.main_screen.meta[0], self.main_screen.data[:min_width]]
                        self.width = width
                        self.height = height
                        self.reset()

                        if saved_line:
                                # Restore saved line
                                self.active_rows = 1
                                self.cursor_x = saved_line[0]
                                self.main_screen.meta[0] = saved_line[1]
                                self.main_screen.data[:min_width] = saved_line[2]

                self.screen = self.alt_screen if self.alt_mode else self.main_screen
                self.needs_updating = True

        def clear(self):
                self.screen_buf.clear_buf()
                self.needs_updating = True

        def reconnect(self, response_id=""):
                self.update_callback(response_id=response_id)
                self.graphterm_output(response_id=response_id, from_buffer=True)

        def clear_last_entry(self, last_entry_index=None):
                self.screen_buf.clear_last_entry(last_entry_index=last_entry_index)

        def scroll_screen(self, scroll_rows=None):
                if scroll_rows == None:
                        scroll_rows = 0
                        for j in range(self.active_rows-1,-1,-1):
                                line = dump(self.main_screen.data[self.width*j:self.width*(j+1)])
                                if prompt_offset(line, self.prompt, self.main_screen.meta[j]):
                                        # Move rows before last prompt to buffer
                                        scroll_rows = j
                                        break
                if not scroll_rows:
                        return

                # Move scrolled active rows to buffer
                cursor_y = 0
                while cursor_y < scroll_rows:
                        row = self.main_screen.data[self.width*cursor_y:self.width*cursor_y+self.width]
                        meta = self.main_screen.meta[cursor_y]
                        offset = prompt_offset(dump(row), self.prompt, meta)
                        if meta:
                                # Concatenate rows for multiline command
                                while cursor_y < scroll_rows-1 and self.main_screen.meta[cursor_y+1] and self.main_screen.meta[cursor_y+1][JCONTINUATION]:
                                        cursor_y += 1
                                        row += self.main_screen.data[self.width*cursor_y:self.width*cursor_y+self.width]
                        self.screen_buf.scroll_buf_up(dump(row, trim=True, encoded=True), meta, offset=offset)
                        cursor_y += 1

                # Scroll and zero rest of screen
                if scroll_rows < self.active_rows:
                        self.poke(0, 0, self.peek(scroll_rows, 0, self.active_rows-1, self.width))
                self.active_rows = self.active_rows - scroll_rows
                if self.active_rows:
                        self.screen.meta[0:self.active_rows] = self.screen.meta[scroll_rows:scroll_rows+self.active_rows] 
                self.zero_lines(self.active_rows, self.height-1)
                self.cursor_y = max(0, self.cursor_y - scroll_rows)
                if not self.active_rows:
                        self.cursor_x = 0
                        self.cursor_eol = 0

        def update(self):
                self.update_time = time.time()
                self.needs_updating = False

                if not self.alt_mode:
                        self.scroll_screen()

                self.update_callback()

        def update_callback(self, response_id=""):
                alt_screen = self.alt_screen if self.alt_mode else None
                full_update, update_rows, update_scroll = self.screen_buf.update(self.active_rows, self.width, self.height,
                                                                                 self.cursor_x, self.cursor_y,
                                                                                 self.main_screen,
                                                                                 alt_screen=alt_screen,
                                                                                 prompt=self.prompt,
                                                                                 reconnecting=bool(response_id))
                pre_offset = len(self.prompt[0]) if self.prompt else 0
                self.screen_callback(self.term_name, response_id, "row_update",
                                     [self.alt_mode, full_update, self.active_rows,
                                      self.width, self.height,
                                      self.cursor_x, self.cursor_y, pre_offset,
                                      update_rows, update_scroll])
                if not response_id and (update_rows or update_scroll):
                    self.gterm_output_buf = []

        def zero(self, y1, x1, y2, x2, screen=None):
                if screen is None: screen = self.screen
                w = self.width*(y2-y1) + x2 - x1 + 1
                z = create_array(0, w)
                screen.data[self.width*y1+x1:self.width*y2+x2+1] = z

        def zero_lines(self, y1, y2):
                self.zero(y1, 0, y2, self.width-1)
                self.screen.meta[y1:y2+1] = [None]*(y2+1-y1)

        def zero_screen(self):
                self.zero_lines(0, self.height-1)

        def peek(self, y1, x1, y2, x2):
                return self.screen.data[self.width*y1+x1:self.width*y2+x2]

        def poke(self, y, x, s):
                pos = self.width*y + x
                self.screen.data[pos:pos+len(s)] = s
                if not self.alt_mode:
                        self.active_rows = max(y+1, self.active_rows)

        def scroll_up(self, y1, y2):
                self.poke(y1, 0, self.peek(y1+1, 0, y2, self.width))
                self.screen.meta[y1:y2] = self.screen.meta[y1+1:y2+1] 
                self.zero_lines(y2, y2)

        def scroll_down(self, y1, y2):
                self.poke(y1+1, 0, self.peek(y1, 0, y2-1, self.width))
                self.screen.meta[y1+1:y2+1] = self.screen.meta[y1:y2] 
                self.zero_lines(y1, y1)

        def scroll_right(self, y, x):
                self.poke(y, x+1, self.peek(y, x, y, self.width-1))
                self.zero(y, x, y, x)

        def cursor_down(self):
                if self.cursor_y >= self.scroll_top and self.cursor_y <= self.scroll_bot:
                        self.cursor_eol = 0
                        q, r = divmod(self.cursor_y+1, self.scroll_bot+1)
                        if q:
                                if not self.alt_mode:
                                        row = self.peek(self.scroll_top, 0, self.scroll_top, self.width)
                                        self.screen_buf.scroll_buf_up(dump(row, trim=True, encoded=True),
                                                                      self.screen.meta[self.scroll_top],
                                                        offset=prompt_offset(dump(row), self.prompt, self.screen.meta[self.scroll_top]))
                                self.scroll_up(self.scroll_top, self.scroll_bot)
                                self.cursor_y = self.scroll_bot
                        else:
                                self.cursor_y = r

                        if not self.alt_mode:
                                self.active_rows = max(self.cursor_y+1, self.active_rows)
                                if self.current_meta and not self.screen.meta[self.active_rows-1]:
                                        self.current_meta = (self.current_meta[JCURDIR], self.current_meta[JCONTINUATION]+1)
                                        self.screen.meta[self.active_rows-1] = self.current_meta

        def cursor_right(self):
                q, r = divmod(self.cursor_x+1, self.width)
                if q:
                        self.cursor_eol = 1
                else:
                        self.cursor_x = r

        def expect_prompt(self, current_directory):
                if not self.active_rows or self.cursor_y+1 == self.active_rows:
                        self.current_meta = (current_directory, 0)
                        self.screen.meta[self.cursor_y] = self.current_meta
        
        def enter(self):
                """Called when CR or LF is received from the user to indicate possible end of command"""
                self.current_meta = None   # Command entry is completed
                
        def echo(self, char):
                char_code = ord(char)
                if ENCODING == "utf-8" and (char_code & 0x80):
                        # Multi-byte UTF-8
                        if char_code & 0x40:
                                # New UTF-8 sequence
                                self.echobuf = char
                                if not (char_code & 0x20):
                                        self.echobuf_count = 2
                                elif not (char_code & 0x10):
                                        self.echobuf_count = 3
                                elif not (char_code & 0x08):
                                        self.echobuf_count = 4
                                else:
                                        # Invalid UTF encoding (> 4 bytes?)
                                        self.echobuf = ""
                                        self.echobuf_count = 0
                                return
                        # Continue UTF-8 sequence
                        if not self.echobuf:
                                # Ignore incomplete UTF-8 sequence
                                return
                        self.echobuf += char
                        if len(self.echobuf) < self.echobuf_count:
                                return
                        # Complete UTF-8 sequence
                        uchar = self.echobuf.decode("utf-8", "replace")
                        self.echobuf = ""
                        self.echobuf_count = 0
                else:
                        uchar = unichr(char_code)

                if self.logfile and self.logchars < MAX_LOG_CHARS:
                        with open(self.logfile, "a") as logf:
                                if not self.logchars:
                                        logf.write("TXT:")
                                logf.write(uchar.encode("utf-8", "replace"))
                                self.logchars += 1
                                if self.logchars == MAX_LOG_CHARS:
                                        logf.write("\n")
                if self.cursor_eol:
                        self.cursor_down()
                        self.cursor_x = 0
                self.screen.data[(self.cursor_y*self.width)+self.cursor_x] = self.current_nul | ord(uchar)
                self.cursor_right()
                if not self.alt_mode:
                        self.active_rows = max(self.cursor_y+1, self.active_rows)

        def esc_0x08(self, s):
                """Backspace"""
                self.cursor_x = max(0,self.cursor_x-1)

        def esc_0x09(self, s):
                """Tab"""
                x = self.cursor_x+8
                q, r = divmod(x, 8)
                self.cursor_x = (q*8)%self.width

        def esc_0x0a(self,s):
                """Newline"""
                self.cursor_down()

        def esc_0x0d(self,s):
                """Carriage Return"""
                self.cursor_eol = 0
                self.cursor_x = 0

        def esc_save(self, s):
                self.cursor_x_bak = self.cursor_x
                self.cursor_y_bak = self.cursor_y

        def esc_restore(self,s):
                self.cursor_x = self.cursor_x_bak
                self.cursor_y = self.cursor_y_bak
                self.cursor_eol = 0
                if not self.alt_mode:
                        self.active_rows = max(self.cursor_y+1, self.active_rows)

        def esc_da(self, s):
                """Send primary device attributes"""
                self.outbuf = "\x1b[?6c"

        def esc_sda(self, s):
                """Send secondary device attributes"""
                self.outbuf = "\x1b[>0;0;0c"

        def esc_tpr(self, s):
                """Send Terminal Parameter Report"""
                self.outbuf = "\x1b[0;0;0;0;0;0;0x"

        def esc_sr(self, s):
                """Send Status Report"""
                self.outbuf = "\x1b[0n"

        def esc_cpr(self, s):
                """Send Cursor Position Report"""
                self.outbuf = "\x1b[%d;%dR" % (self.cursor_y+1, self.cursor_x+1)

        def esc_nel(self, s):
                """Next Line (NEL)"""
                self.cursor_down()
                self.cursor_x = 0

        def esc_ind(self, s):
                """Index (IND)"""
                self.cursor_down()

        def esc_ri(self, s):
                """Reverse Index (RI)"""
                if self.cursor_y == self.scroll_top:
                        self.scroll_down(self.scroll_top, self.scroll_bot)
                else:
                        self.cursor_y = max(self.scroll_top, self.cursor_y-1)

                if not self.alt_mode:
                        self.active_rows = max(self.cursor_y+1, self.active_rows)

        def esc_ignore(self,*s):
                if Log_ignored or self.logfile:
                        print >> sys.stderr, "lineterm:ignore: %s"%repr(s)

        def csi_dispatch(self,seq,mo):
                # CSI sequences
                s = mo.group(1)
                c = mo.group(2)
                f = self.csi_seq.get(c, None)
                if f:
                        try:
                                l = [int(i) for i in s.split(';')]
                        except ValueError:
                                l = []
                        if len(l)==0:
                                l = f[1]
                        f[0](l)
                elif Log_ignored or self.logfile:
                        print >> sys.stderr, 'lineterm: csi ignore', s, c

        def csi_at(self, l):
                for i in range(l[0]):
                        self.scroll_right(self.cursor_y, self.cursor_x)

        def csi_A(self, l):
                """Cursor up (default 1)"""
                self.cursor_y = max(self.scroll_top, self.cursor_y-l[0])

        def csi_B(self, l):
                """Cursor down (default 1)"""
                self.cursor_y = min(self.scroll_bot, self.cursor_y+l[0])
                if not self.alt_mode:
                        self.active_rows = max(self.cursor_y+1, self.active_rows)

        def csi_C(self, l):
                """Cursor forward (default 1)"""
                self.cursor_x = min(self.width-1, self.cursor_x+l[0])
                self.cursor_eol = 0

        def csi_D(self, l):
                """Cursor backward (default 1)"""
                self.cursor_x = max(0, self.cursor_x-l[0])
                self.cursor_eol = 0

        def csi_E(self, l):
                """Cursor next line (default 1)"""
                self.csi_B(l)
                self.cursor_x = 0
                self.cursor_eol = 0

        def csi_F(self, l):
                """Cursor preceding line (default 1)"""
                self.csi_A(l)
                self.cursor_x = 0
                self.cursor_eol = 0

        def csi_G(self, l):
                """Cursor Character Absolute [column]"""
                self.cursor_x = min(self.width, l[0])-1

        def csi_H(self, l):
                """Cursor Position [row;column]"""
                if len(l) < 2: l=[1,1]
                self.cursor_x = min(self.width, l[1])-1
                self.cursor_y = min(self.height, l[0])-1
                self.cursor_eol = 0
                if not self.alt_mode:
                        self.active_rows = max(self.cursor_y+1, self.active_rows)

        def csi_J(self, l):
                """Erase in Display"""
                if l[0]==0:
                        # Erase below (default)
                        if not self.cursor_x:
                                self.zero_lines(self.cursor_y, self.height-1)
                        else:
                                self.zero(self.cursor_y, self.cursor_x, self.height-1, self.width-1)
                elif l[0]==1:
                        # Erase above
                        if self.cursor_x==self.width-1:
                                self.zero_lines(0, self.cursor_y)
                        else:
                                self.zero(0, 0, self.cursor_y, self.cursor_x)
                elif l[0]==2:
                        # Erase all
                        self.zero_screen()

        def csi_K(self, l):
                """Erase in Line"""
                if l[0]==0:
                        # Erase to right (default)
                        self.zero(self.cursor_y, self.cursor_x, self.cursor_y, self.width-1)
                elif l[0]==1:
                        # Erase to left
                        self.zero(self.cursor_y, 0, self.cursor_y, self.cursor_x)
                elif l[0]==2:
                        # Erase all
                        self.zero_lines(self.cursor_y, self.cursor_y)

        def csi_L(self, l):
                """Insert lines (default 1)"""
                for i in range(l[0]):
                        if self.cursor_y<self.scroll_bot:
                                self.scroll_down(self.cursor_y, self.scroll_bot)
        def csi_M(self, l):
                """Delete lines (default 1)"""
                if self.cursor_y>=self.scroll_top and self.cursor_y<=self.scroll_bot:
                        for i in range(l[0]):
                                self.scroll_up(self.cursor_y, self.scroll_bot)
        def csi_P(self, l):
                """Delete characters (default 1)"""
                w, cx, cy = self.width, self.cursor_x, self.cursor_y
                end = self.peek(cy, cx, cy, w)
                self.csi_K([0])
                self.poke(cy, cx, end[l[0]:])

        def csi_X(self, l):
                """Erase characters (default 1)"""
                self.zero(self.cursor_y, self.cursor_x, self.cursor_y, self.cursor_x+l[0])

        def csi_a(self, l):
                """Cursor forward (default 1)"""
                self.csi_C(l)

        def csi_c(self, l):
                """Send Device attributes"""
                #'\x1b[?0c' 0-8 cursor size
                pass

        def csi_d(self, l):
                """Vertical Position Absolute [row]"""
                self.cursor_y = min(self.height, l[0])-1
                if not self.alt_mode:
                        self.active_rows = max(self.cursor_y+1, self.active_rows)

        def csi_e(self, l):
                """Cursor down"""
                self.csi_B(l)

        def csi_f(self, l):
                """Horizontal and Vertical Position [row;column]"""
                self.csi_H(l)

        def csi_h(self, l):
                """Set private mode"""
                if l[0] in GRAPHTERM_SCREEN_CODES:
                        if not self.alt_mode:
                                self.gterm_code = l[0]
                                self.gterm_validated = (len(l) >= 2 and str(l[1]) == self.cookie)
                                self.gterm_buf = []
                                self.gterm_buf_size = 0
                                self.gterm_entry_index = self.screen_buf.entry_index+1
                                if self.gterm_code != GRAPHTERM_SCREEN_CODES[0]:
                                        self.scroll_screen(self.active_rows)
                                        if self.logfile:
                                                with open(self.logfile, "a") as logf:
                                                        logf.write("GTERMMODE\n")

                elif l[0] in ALTERNATE_SCREEN_CODES:
                        self.alt_mode = True
                        self.screen = self.alt_screen
                        self.current_nul = self.screen_buf.default_nul
                        self.zero_screen()
                        if self.logfile:
                                with open(self.logfile, "a") as logf:
                                        logf.write("ALTMODE\n")
                elif l[0] == 4:
                        pass
#                       print "insert on"

        def csi_l(self, l):
                """Reset private mode"""
                if l[0] in GRAPHTERM_SCREEN_CODES:
                        pass # No-op (mode already exited in escape)

                elif l[0] in ALTERNATE_SCREEN_CODES:
                        self.alt_mode = False
                        self.screen = self.main_screen
                        self.current_nul = self.screen_buf.default_nul
                        self.cursor_y = max(0, self.active_rows-1)
                        self.cursor_x = 0
                        if self.logfile:
                                with open(self.logfile, "a") as logf:
                                        logf.write("NORMODE\n")
                elif l[0] == 4:
                        pass
#                       print "insert off"

        def csi_m(self, l):
                """Select Graphic Rendition"""
                for i in l:
                        if i==0 or i==39 or i==49 or i==27:
                                # Normal
                                self.current_nul = self.screen_buf.default_nul
                        elif i==1:
                                # Bold
                                self.current_nul = self.current_nul | (self.screen_buf.bold_style << UNI24)
                        elif i==7:
                                # Inverse
                                self.current_nul = self.screen_buf.inverse_style << UNI24
                        elif i>=30 and i<=37:
                                # Foreground Black(30), Red, Green, Yellow, Blue, Magenta, Cyan, White
                                c = i-30
                                self.current_nul = (self.current_nul & 0xf8ffffff) | (c << UNI24)
                        elif i>=40 and i<=47:
                                # Background Black(40), Red, Green, Yellow, Blue, Magenta, Cyan, White
                                c = i-40
                                self.current_nul = (self.current_nul & 0x8fffffff) | (c << (UNI24+STYLE4))
#                       else:
#                               print >> sys.stderr, "lineterm: CSI style ignore",l,i
#               print >> sys.stderr, 'lineterm: style: %r %x'%(l, self.current_nul)

        def csi_r(self, l):
                """Set scrolling region [top;bottom]"""
                if len(l)<2: l = [1, self.height]
                self.scroll_top = min(self.height-1, l[0]-1)
                self.scroll_bot = min(self.height-1, l[1]-1)
                self.scroll_bot = max(self.scroll_top, self.scroll_bot)

        def csi_s(self, l):
                self.esc_save(0)

        def csi_u(self, l):
                self.esc_restore(0)

        def escape(self):
                e = self.buf
                if len(e)>32:
                        if Log_ignored or self.logfile:
                                print >> sys.stderr, "lineterm: escape error %r"%e
                        self.buf = ""
                elif e in self.esc_seq:
                        if self.logfile:
                                with open(self.logfile, "a") as logf:
                                        logf.write("SQ%02x%s\n" % (ord(e[0]), e[1:]))
                        self.esc_seq[e](e)
                        self.buf = ""
                        self.logchars = 0
                else:
                        for r,f in self.esc_re:
                                mo = r.match(e)
                                if mo:
                                        if self.logfile:
                                                with open(self.logfile, "a") as logf:
                                                        logf.write("RE%02x%s\n" % (ord(e[0]), e[1:]))
                                        f(e,mo)
                                        self.buf = ""
                                        self.logchars = 0
                                        break
#               if self.buf=='': print >> sys.stderr, "lineterm: ESC %r\n"%e

        def gterm_append(self, s):
                if '\x1b' in s:
                        prefix, sep, suffix = s.partition('\x1b')
                else:
                        prefix, sep, suffix = s, "", ""
                self.gterm_buf_size += len(prefix)
                if self.gterm_buf_size <= MAX_PAGELET_BYTES:
                    # Only append data if within buffer size limit
                    self.gterm_buf.append(prefix)
                if not sep:
                        return ""
                retval = sep + suffix
                # ESCAPE sequence encountered; terminate
                if self.gterm_buf_size > MAX_PAGELET_BYTES:
                        # Buffer overflow
                        content = "ERROR pagelet size (%d bytes) exceeds limit (%d bytes)" % (self.gterm_buf_size,  MAX_PAGELET_BYTES)
                        headers["x_gterm_response"] = "error_message"
                        headers["x_gterm_parameters"] = {}
                        headers["content_type"] = "text/plain"
                    
                elif self.gterm_code == GRAPHTERM_SCREEN_CODES[0]:
                        # Handle prompt command output
                        current_dir = "".join(self.gterm_buf)
                        if current_dir:
                                self.expect_prompt(current_dir)
                elif self.gterm_buf:
                        # graphterm output ("pagelet")
                        self.update()
                        gterm_output = "".join(self.gterm_buf).lstrip()
                        headers, content = parse_headers(gterm_output)
                        response_type = headers["x_gterm_response"]
                        response_params = headers["x_gterm_parameters"]
                        plain_text = False
                        if self.gterm_validated:
                                if response_type == "edit_file":
                                        filepath = response_params.get("filepath", "")
                                        try:
                                                if "filetype" not in response_params:
                                                        basename, extension = os.path.splitext(filepath)
                                                        if extension:
                                                                response_params["filetype"] = FILE_EXTENSIONS.get(extension[1:].lower(), "")
                                                        else:
                                                                response_params["filetype"] = ""
                                                filestats = os.stat(filepath)
                                                if filestats.st_size > MAX_PAGELET_BYTES:
                                                    raise Exception("File size (%d bytes) exceeds pagelet limit (%d bytes)" % (filestats.st_size,  MAX_PAGELET_BYTES))
                                                with open(filepath) as f:
                                                        content = f.read()
                                        except Exception, excp:
                                                content = "ERROR in opening file '%s': %s" % (filepath, excp)
                                                headers["x_gterm_response"] = "error_message"
                                                headers["x_gterm_parameters"] = {}
                                                headers["content_type"] = "text/plain"
                        elif response_type == "pagelet":
                                # Display non-validated pagelet as plain text
                                plain_text = True
                                headers["x_gterm_response"] = "pagelet"
                                headers["x_gterm_parameters"] = {}
                                try:
                                        import lxml.html
                                        content = lxml.html.fromstring(content).text_content()
                                        headers["content_type"] = "text/plain"
                                except Exception:
                                        content = cgi.escape(content)

                        if self.gterm_validated and response_type == "create_blob":
                                del headers["x_gterm_response"]
                                del headers["x_gterm_parameters"]
                                blob_id = response_params.get("blob_id")
                                if not blob_id:
                                    logging.warning("No blob_id for create_blob")
                                elif "content_length" not in headers:
                                    logging.warning("No content_length specified for create_blob")
                                else:
                                    # Note: blob content should be Base64 encoded
                                    self.screen_callback(self.term_name, "", "create_blob",
                                                         [blob_id, headers, content])
                        elif self.gterm_validated and response_type == "frame_msg":
                            self.screen_callback(self.term_name, "", "frame_msg",
                                 [response_params.get("user",""), response_params.get("frame",""), content])
                        elif self.gterm_validated or plain_text:
                                headers["content_length"] = len(content)
                                params = {"validated": self.gterm_validated, "headers": headers}
                                self.graphterm_output(params, content)
                self.gterm_code = None
                self.gterm_buf = None
                self.gterm_buf_size = 0
                self.gterm_validated = False
                self.gterm_entry_index = None
                return retval

        def graphterm_output(self, params={}, content="", response_id="", from_buffer=False):
                if not from_buffer:
                        self.gterm_output_buf = [params, base64.b64encode(content) if content else ""]
                elif not self.gterm_output_buf:
                        return
                self.screen_callback(self.term_name, response_id, "graphterm_output", self.gterm_output_buf)

        def save_file(self, filepath, filedata):
                status = ""
                try:
                        with open(filepath, "w") as f:
                                f.write(base64.b64decode(filedata))
                except Exception, excp:
                        status = str(excp)
                self.screen_callback(self.term_name, "", "save_status", [filepath, status])

        def get_finder(self, kind, directory=""):
                test_finder_head = """<table frame=none border=0>
<colgroup colspan=1 width=1*>
"""
                test_finder_row = """
  <tr class="gterm-rowimg">
    <td><a class="gterm-link gterm-imglink" href="file://%(fullpath)s" data-gtermmime="x-graphterm/%(filetype)s" data-gtermcmd="%(clickcmd)s"><img class="gterm-img" src="%(fileicon)s"></img></a>
  <tr class="gterm-rowtxt">
    <td><a class="gterm-link" href="file://%(fullpath)s" data-gtermmime="x-graphterm/%(filetype)s" data-gtermcmd="%(clickcmd)s">%(filename)s</a>
"""
                test_finder_tail = """
</table>
"""
                if not self.active_rows:
                        # Not at command line
                        return
                if not directory:
                        meta = self.screen.meta[self.active_rows-1]
                        directory = meta[JCURDIR] if meta else getcwd(self.pid)
                row_content = test_finder_row % {"fullpath": directory,
                                                 "filetype": "directory",
                                                 "clickcmd": "cd %(path); gls -f",
                                                 "fileicon": "/static/images/tango-folder.png",
                                                 "filename": "."}
                content = "\n".join([test_finder_head] + 40*[row_content] + [test_finder_tail])
                headers = {"content_type": "text/html",
                           "x_gterm_response": "display_finder",
                           "x_gterm_parameters": {"finder_type": kind, "current_directory": ""}}
                params = {"validated": self.gterm_validated, "headers": headers}
                self.graphterm_output(params, content)

        def click_paste(self, text, file_url="", options={}):
                """Return text or filename (and command) for pasting into command line.
                (Text may or may not be terminated by a newline, and maybe a null string.)
                Different behavior depending upon whether command line is empty or not.
                If not text, create text from filepath, normalizing if need be.
                options = {command: "", clear_last: 0/n, normalize: null/true/false, enter: false/true
                If clear_last and command line is empty, clear last entry (can also be numeric string).
                Normalize may be None (for default behavior), False or True.
                if enter, append newline to text, when applicable.
                """
                if not self.active_rows:
                        # Not at command line
                        return ""
                command = options.get("command", "")
                dest_url = options.get("dest_url", "")
                clear_last = options.get("clear_last", 0)
                normalize = options.get("normalize", None)
                enter = options.get("enter", False)

                line = dump(self.peek(self.active_rows-1, 0, self.active_rows-1, self.width), trim=True)
                meta = self.screen.meta[self.active_rows-1]
                cwd = meta[JCURDIR] if meta else getcwd(self.pid)
                offset = prompt_offset(line, self.prompt, (cwd, 0))

                try:
                        clear_last = int(clear_last) if clear_last else 0
                except Exception, excp:
                        logging.warning("click_paste: ERROR %s", excp)
                        clear_last = 0
                if clear_last and offset and offset == len(line.rstrip()):
                        # Empty command line; clear last entry
                        self.screen_buf.clear_last_entry(clear_last)

                space_prefix = ""
                command_prefix = ""
                expect_filename = False
                expect_url = (command in REMOTE_FILE_COMMANDS)
                file_url_comps = split_file_url(file_url, check_host_secret=self.shared_secret)
                if not text and file_url:
                        if file_url_comps:
                                text = create_file_uri(file_url_comps) if (expect_url and file_url_comps[JHOST]) else file_url_comps[JFILEPATH]
                        else:
                                text = file_url

                if dest_url:
                        dest_comps = split_file_url(dest_url, check_host_secret=self.shared_secret)
                        if expect_url and dest_comps and dest_comps[JHOST]:
                                dest_paste = create_file_uri(dest_comps)
                        else:
                                dest_paste = relative_file_url(dest_url, cwd)
                        if command == "gcp" and not file_url_comps[JHOST] and not dest_comps[JHOST]:
                                # Source and destination on this host; move instead of copying
                                command = "mv"
                else:
                        dest_paste = ""

                if offset:
                        # At command line
                        if normalize is None and cwd and (not self.screen_buf.cleared_last or self.screen_buf.cleared_current_dir is None or self.screen_buf.cleared_current_dir == cwd):
                                # Current directory known and no entries cleared
                                # or first cleared entry had same directory as current; normalize
                                normalize = True

                        if self.cursor_y == self.active_rows-1:
                                pre_line = line[:self.cursor_x]
                        else:
                                pre_line = line
                        pre_line = pre_line[offset:]
                        if pre_line and pre_line[0] == u" ":
                                # Strip space associated with prompt
                                pre_line = pre_line[1:]
                        if not pre_line.strip():
                                # Empty/blank command line
                                if command:
                                        # Command to precede filename
                                        command_prefix = command
                                        expect_filename = True
                                elif text:
                                        # Use text as command
                                        if not pre_line and not which(text, add_path=[Exec_path]):
                                                raise Exception("Command '%s' not found" % text)
                                        command_prefix = text.replace(" ", "\\ ")
                                        text = ""
                                if command_prefix and command_prefix[-1] != " ":
                                        command_prefix += " "
                        else:
                                # Non-empty command line; expect filename
                                expect_filename = True
                                if pre_line[-1] != u" ":
                                        space_prefix = " "

                if cwd and normalize and expect_filename and file_url:
                        # Check if file URI represents subdirectory of CWD
                        if expect_url and file_url_comps and file_url_comps[JHOST]:
                                text = create_file_uri(file_url_comps)
                        else:
                                normpath = relative_file_url(file_url, cwd)
                                if not normpath.startswith("/"):
                                        text = normpath

                if text or command_prefix:
                        text = text.replace(" ", "\\ ")
                        if expect_filename and command_prefix.find("%(path)") >= 0:
                                paste_text = command_prefix.replace("%(path)", text)
                        else:
                                paste_text = command_prefix+space_prefix+text+" "
                        if dest_paste:
                                if paste_text and paste_text[-1] != " ":
                                        paste_text += " "
                                paste_text += dest_paste
                        if enter and offset and not pre_line and command:
                                # Empty command line with pasted command
                                paste_text += "\n"

                        return paste_text

                return ""

        def write(self, s):
                self.output_time = time.time()
                if self.gterm_buf is not None:
                        s = self.gterm_append(s)
                if not s:
                        return
                assert self.gterm_buf is None
                self.needs_updating = True

                for k, i in enumerate(s):
                        if self.gterm_buf is not None:
                                self.write(s[k:])
                                return
                        if len(self.buf) or (i in self.esc_seq):
                                self.buf += i
                                self.escape()
                        elif i == '\x1b':
                                self.buf += i
                        else:
                                self.echo(i)

        def read(self):
                b = self.outbuf
                self.outbuf = ""
                return b

        def pty_write(self, data):
                if "\x0d" in data or "\x0a" in data:
                        # Data contains CR/LF
                        self.enter()
                os.write(self.fd, data)

                
class Multiplex(object):
        def __init__(self, screen_callback, command=None, shared_secret="",
                     host="", server_url="", prompt=[], term_type="linux", api_version="",
                     widget_port=0, logfile="", app_name="graphterm"):
                """ prompt = [prefix, format, suffix]
                """
                ##signal.signal(signal.SIGCHLD, signal.SIG_IGN)
                self.screen_callback = screen_callback
                self.command = command
                self.shared_secret = shared_secret
                self.host = host
                self.server_url = server_url
                self.prompt = prompt
                self.term_type = term_type
                self.api_version = api_version
                self.widget_port = widget_port
                self.logfile = logfile
                self.app_name = app_name
                self.proc = {}
                self.lock = threading.RLock()
                self.thread = threading.Thread(target=self.loop)
                self.alive = 1
                self.check_kill_idle = False
                self.name_count = 0
                self.thread.start()

        def terminal(self, term_name=None, command="", height=25, width=80):
                """Return (tty_name, cookie) for existing or newly created pty"""
                command = command or self.command
                with self.lock:
                        if term_name:
                                term = self.proc.get(term_name)
                                if term:
                                        self.set_size(term_name, height, width)
                                        return (term_name, term.cookie)

                        else:
                                # New default terminal name
                                while True:
                                        self.name_count += 1
                                        term_name = "tty%s" % self.name_count
                                        if term_name not in self.proc:
                                                break

                        # Create new terminal
                        cookie = make_lterm_cookie()

                        pid, fd = pty.fork()
                        if pid==0:
                                try:
                                        fdl = [int(i) for i in os.listdir('/proc/self/fd')]
                                except OSError:
                                        fdl = range(256)
                                for i in [i for i in fdl if i>2]:
                                        try:
                                                os.close(i)
                                        except OSError:
                                                pass
                                if command:
                                        comps = command.split()
                                        if comps and re.match(r'^[/\w]*/(ba|c|k|tc)?sh$', comps[0]):
                                                cmd = comps
                                        else:
                                                cmd = ['/bin/sh', '-c', command]
                                elif os.getuid()==0:
                                        cmd = ['/bin/login']
                                else:
                                        sys.stdout.write("Login: ")
                                        login = sys.stdin.readline().strip()
                                        if re.match('^[0-9A-Za-z-_. ]+$',login):
                                                cmd = ['ssh']
                                                cmd += ['-oPreferredAuthentications=keyboard-interactive,password']
                                                cmd += ['-oNoHostAuthenticationForLocalhost=yes']
                                                cmd += ['-oLogLevel=FATAL']
                                                cmd += ['-F/dev/null', '-l', login, 'localhost']
                                        else:
                                                os._exit(0)
                                env = {}
                                for var in os.environ.keys():
                                        if var not in NO_COPY_ENV:
                                                val = os.getenv(var)
                                                env[var] = val
                                                if var == "PATH":
                                                        # Prepend app bin directory to path
                                                        env[var] = Exec_path + ":" + env[var]
                                env["COLUMNS"] = str(width)
                                env["LINES"] = str(height)
                                env.update( dict(self.term_env(term_name, cookie)) )

                                # cd to HOME
                                os.chdir(os.path.expanduser("~"))
                                os.execvpe(cmd[0], cmd, env)
                        else:
                                global Exec_errmsg
                                fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
                                self.proc[term_name] = Terminal(term_name, fd, pid, self.screen_callback,
                                                                height=height, width=width,
                                                                cookie=cookie, host=self.host,
                                                                shared_secret=self.shared_secret,
                                                                prompt=self.prompt, logfile=self.logfile)
                                self.set_size(term_name, height, width)
                                if not is_executable(Gls_path) and not Exec_errmsg:
                                        Exec_errmsg = True
                                        self.screen_callback(term_name, "", "alert", ["File %s is not executable. Did you 'sudo gterm_setup' after 'sudo easy_install graphterm'?" % Gls_path])
                                return term_name, cookie

        def term_env(self, term_name, cookie, export=False):
                env = []
                env.append( ("TERM", self.term_type or TERM_TYPE) )
                env.append( ("GRAPHTERM_COOKIE", str(cookie)) )
                env.append( ("GRAPHTERM_SHARED_SECRET", self.shared_secret) )
                env.append( ("GRAPHTERM_PATH", "%s/%s" % (self.host, term_name)) )
                if self.server_url:
                        env.append( ("GRAPHTERM_URL", self.server_url) )

                if self.api_version:
                        env.append( ("GRAPHTERM_API", self.api_version) )

                if self.widget_port:
                        env.append( ("GRAPHTERM_SOCKET", "/dev/tcp/localhost/%d" % self.widget_port) )

                if self.prompt:
                        env.append( ("GRAPHTERM_PROMPT", "".join(self.prompt) + " ") )
                        ##env.append( ("PROMPT_COMMAND", "export PS1=$GRAPHTERM_PROMPT; unset PROMPT_COMMAND") )
                        cmd_fmt = EXPT_PROMPT_CMD if export else BASH_PROMPT_CMD

                        env.append( ("PROMPT_COMMAND", cmd_fmt % (GRAPHTERM_SCREEN_CODES[0], GRAPHTERM_SCREEN_CODES[0]) ) )

                env.append( ("GRAPHTERM_DIR", File_dir) )
                return env
                
        def export_environment(self, term_name):
                term = self.proc.get(term_name)
                if term:
                    term.pty_write('[ "$GRAPHTERM_COOKIE" ] || export GRAPHTERM_EXPORT="%s"\n' % (socket.getfqdn() or "unknown",))
                    for name, value in self.term_env(term_name, term.cookie, export=True):
                        try:
                            if name in ("GRAPHTERM_DIR",):
                                term.pty_write( ('[ "$%s" ] || ' % name) + ("export %s='%s'\n" % (name, value)) )
                            else:
                                term.pty_write( "export %s='%s'\n" % (name, value) )  # Keep inner single quotes to handle PROMPT_COMMAND
                        except Exception:
                            print >> sys.stderr, "lineterm: Error exporting environment to %s" % term_name
                            break
                    term.pty_write('[[ "$PATH" != */graphterm/* ]] && [ -d "$GRAPHTERM_DIR" ] && export PATH="$GRAPHTERM_DIR/%s:$PATH"\n' % BINDIR)

        def set_size(self, term_name, height, width):
                # python bug http://python.org/sf/1112949 on amd64
                term = self.proc.get(term_name)
                if term:
                        term.resize(height, width)
                        fcntl.ioctl(term.fd, struct.unpack('i',struct.pack('I',termios.TIOCSWINSZ))[0],
                                    struct.pack("HHHH",height,width,0,0))

        def term_names(self):
                with self.lock:
                        return self.proc.keys()

        def running(self):
                with self.lock:
                        return self.alive

        def shutdown(self):
                with self.lock:
                        if not self.alive:
                                return
                        self.alive = 0
                        self.kill_all()

        def kill_term(self, term_name):
                with self.lock:
                        term = self.proc.get(term_name)
                        if term:
                                # "Idle" terminal
                                term.output_time = 0
                        self.check_kill_idle = True

        def kill_all(self):
                with self.lock:
                        for term in self.proc.values():
                                # "Idle" terminal
                                term.output_time = 0
                        self.check_kill_idle = True

        def kill_idle(self):
                # Kill all "idle" terminals
                with self.lock:
                        cur_time = time.time()
                        for term_name in self.term_names():
                                term = self.proc.get(term_name)
                                if term:
                                        if (cur_time-term.output_time) > IDLE_TIMEOUT:
                                                try:
                                                        os.close(term.fd)
                                                        os.kill(term.pid, signal.SIGTERM)
                                                except (IOError, OSError):
                                                        pass
                                                try:
                                                        del self.proc[term_name]
                                                except Exception:
                                                        pass
                                                logging.warning("kill_idle: %s", term_name)

        def term_read(self, term_name):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return
                        try:
                                data = os.read(term.fd, 65536)
                                if not data:
                                        print >> sys.stderr, "lineterm: EOF in reading from %s; closing it" % term_name
                                        self.term_update(term_name)
                                        self.kill_term(term_name)
                                        return
                                if term.trim_first_prompt:
                                        term.trim_first_prompt = False
                                        # Fix for the very first prompt not being set
                                        if data.startswith("> "):
                                                data = data[2:]
                                        elif data.startswith("\r\x1b[K> "):
                                                data = data[6:]
                                                
                                term.write(data)
                                reply = term.read()
                                if reply:
                                        os.write(term.fd, reply)
                        except (KeyError, IOError, OSError):
                                print >> sys.stderr, "lineterm: Error in reading from %s; closing it" % term_name
                                self.kill_term(term_name)

        def term_write(self, term_name, data):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return
                        try:
                                term.pty_write(data)
                        except (IOError, OSError):
                                print >> sys.stderr, "lineterm: Error in writing to %s; closing it" % term_name
                                self.kill_term(term_name)

        def term_update(self, term_name):
                with self.lock:
                        term = self.proc.get(term_name)
                        if term:
                                term.update()

        def dump(self, term_name, data, trim=False, color=1):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return ""
                        try:
                                return dump(data, trim=trim, encoded=True)
                        except KeyError:
                                return "ERROR in dump"

        def save_file(self, term_name, filepath, filedata):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return
                        term.save_file(filepath, filedata)

        def get_finder(self, term_name, kind, directory=""):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return
                        term.get_finder(kind, directory=directory)

        def click_paste(self, term_name, text, file_url="", options={}):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return ""
                        return term.click_paste(text, file_url=file_url, options=options)

        def reconnect(self, term_name, response_id=""):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return
                        term.reconnect(response_id=response_id)

        def clear(self, term_name):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return
                        term.clear()

        def clear_last_entry(self, term_name, last_entry_index=None):
                with self.lock:
                        term = self.proc.get(term_name)
                        if not term:
                                return
                        term.clear_last_entry(last_entry_index=last_entry_index)

        def loop(self):
                while self.running():
                        try:
                                fd_dict = dict((term.fd, name) for name, term in self.proc.items())
                                if not fd_dict:
                                        time.sleep(0.02)
                                        continue
                                inputs, outputs, errors = select.select(fd_dict.keys(), [], [], 0.02)
                                for fd in inputs:
                                        try:
                                                self.term_read(fd_dict[fd])
                                        except Exception, excp:
                                                traceback.print_exc()
                                                term_name = fd_dict[fd]
                                                logging.warning("Multiplex.loop: INTERNAL READ ERROR (%s) %s", term_name, excp)
                                                self.kill_term(term_name)
                                cur_time = time.time()
                                for term_name in fd_dict.values():
                                        term = self.proc.get(term_name)
                                        if term:
                                                if (term.needs_updating or term.output_time > term.update_time) and cur_time-term.update_time > UPDATE_INTERVAL:
                                                        try:
                                                                self.term_update(term_name)
                                                        except Exception, excp:
                                                                traceback.print_exc()
                                                                logging.warning("Multiplex.loop: INTERNAL UPDATE ERROR (%s) %s", term_name, excp)
                                                                self.kill_term(term_name)
                                if self.check_kill_idle:
                                        self.check_kill_idle = False
                                        self.kill_idle()

                                if len(inputs):
                                        time.sleep(0.002)
                        except Exception, excp:
                                traceback.print_exc()
                                logging.warning("Multiplex.loop: ERROR %s", excp)
                                break
                self.kill_all()

if __name__ == "__main__":
        ## Code to test LineTerm on reguler terminal
        ## Re-size terminal to 80x25 before testing

        # Determine terminal width, height
        height, width = struct.unpack("hh", fcntl.ioctl(pty.STDOUT_FILENO, termios.TIOCGWINSZ, "1234"))
        if not width or not height:
                try:
                        height, width = [int(os.getenv(var)) for var in ("LINES", "COLUMNS")]
                except Exception:
                        height, width = 25, 80

        Prompt = "> "
        Log_file = "term.log"
        Log_file = ""
        def screen_callback(term_name, response_id, command, arg):
                if command == "row_update":
                        alt_mode, reset, active_rows, width, height, cursorx, cursory, pre_offset, update_rows, update_scroll = arg
                        for row_num, row_offset, row_dir, row_markup, row_span in update_rows:
                                row_str = "".join(x[1] for x in row_span)
                                sys.stdout.write("\x1b[%d;%dH%s" % (row_num+1, 0, row_str))
                                sys.stdout.write("\x1b[%d;%dH" % (row_num+1, len(row_str)+1))
                                sys.stdout.write("\x1b[K")
                        if not alt_mode and active_rows < height and cursory+1 < height:
                                # Erase below
                                sys.stdout.write("\x1b[%d;%dH" % (cursory+2, 0))
                                sys.stdout.write("\x1b[J")
                        sys.stdout.write("\x1b[%d;%dH" % (cursory+1, cursorx+1))
                        ##if Log_file:
                        ##      with open(Log_file, "a") as logf:
                        ##              logf.write("CALLBACK:(%d,%d) %d\n" % (cursorx, cursory, active_rows))
                        sys.stdout.flush()

        Line_term = Multiplex(screen_callback, "sh", cookie=1, logfile=Log_file)
        Term_name = Line_term.terminal(height=height, width=width)
        
        Term_attr = termios.tcgetattr(pty.STDIN_FILENO)
        try:
                tty.setraw(pty.STDIN_FILENO)
                expectEOF = False
                while True:
                        ##data = raw_input(Prompt)
                        ##Line_term.write(data+"\n")
                        data = os.read(pty.STDIN_FILENO, 1024)
                        if ord(data[0]) == 4:
                                if expectEOF: raise EOFError
                                expectEOF = True
                        else:
                                expectEOF = False
                        if not data:
                                raise EOFError
                        Line_term.term_write(Term_name, data)
        except EOFError:
                Line_term.shutdown()
        finally:
            # Restore terminal attributes
            termios.tcsetattr(pty.STDIN_FILENO, termios.TCSANOW, Term_attr)
