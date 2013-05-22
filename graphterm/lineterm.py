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
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

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
import errno
import hashlib
import hmac
import pipes
import Queue
import shlex
import subprocess
import traceback
import urllib
import uuid

from bin import gtermapi

MAX_SCROLL_LINES = 500

CHUNK_BYTES = 4096            # Chunk size for receiving data in stdin

MAX_PAGELET_BYTES = 1000000  # Max size for pagelet buffer

IDLE_TIMEOUT = 300      # Idle timeout in seconds
UPDATE_INTERVAL = 0.05  # Fullscreen update time interval
TERM_TYPE = "xterm"     # "screen" may be a better default terminal, but arrow keys do not always work

NO_COPY_ENV = set(["GRAPHTERM_EXPORT", "TERM_PROGRAM","TERM_PROGRAM_VERSION", "TERM_SESSION_ID"])
LC_EXPORT_ENV = ["GRAPHTERM_API", "GRAPHTERM_COOKIE", "GRAPHTERM_DIMENSIONS", "GRAPHTERM_PATH", "GRAPHTERM_SHARED_SECRET"]

ALTERNATE_SCREEN_CODES = (47, 1047, 1049) # http://rtfm.etla.org/xterm/ctlseq.html
GRAPHTERM_SCREEN_CODES = (1150, 1155)     # (prompt_escape, pagelet_escape)

FILE_EXTENSIONS = {"css": "css", "htm": "html", "html": "html", "js": "javascript", "py": "python",
                   "xml": "xml"}

FILE_COMMANDS = set(["cd", "cp", "mv", "rm", "gcp", "gimages", "gls", "gopen", "gvi"])
REMOTE_FILE_COMMANDS = set(["gbrowse", "gcp"])
COMMAND_DELIMITERS = "<>;"

MD_IMAGE_RE = re.compile(r"^\s*!\[([^\]]*)\]\s*\[([^\]]+)\]")
MD_REF_RE = re.compile(r"^\s*\[([^\]]+)\]:\s*data:")

MARKUP_TYPES = set(["markdown"])

BLOCKIMGFORMAT = '<!--gterm pagelet blob=%s--><div class="gterm-blockhtml"><img class="gterm-blockimg" src="%slocal/%s" alt="%s"></div>'

IPYNB_JSON_HEADER = """{
 "metadata": {
  "name": "%(name)s"
 },
 "nbformat": %(version_major)s,
 "nbformat_minor": %(version_minor)s,
 "worksheets": [
  {
   "cells": [
"""

IPYNB_JSON_FOOTER = """   ],
   "metadata": {}
  }
 ]
}
"""

IPYNB_JSON_MARKDOWN = """    {
     "cell_type": "markdown",
     "metadata": {},
     "source": %(source)s
    }"""

IPYNB_JSON_CODE0 = """    {
     "cell_type": "code",
     "collapsed": false,
     "input": %(input)s,
     "language": "%(lang)s",
     "metadata": {},
     "outputs": [
"""
     
IPYNB_JSON_CODE1 = """     ],
     "prompt_number": %(in_prompt)s
    }
"""
     
IPYNB_JSON_STDOUT   = """      {
       "output_type": "stream",
       "stream": "stdout",
       "text": %(text)s
      }"""

IPYNB_JSON_PYOUT    = """      {
       "output_type": "pyout",
       "prompt_number": %(out_prompt)s,
       "text": %(text)s
      }"""

IPYNB_JSON_DATA     = """      {
       "output_type": "display_data",
       "%(format)s": "%(base64)s"
      }"""

# Scroll lines array components
JINDEX = 0
JOFFSET = 1
JDIR = 2
JPARAMS = 3
JLINE = 4
JMARKUP = 5

JTYPE = 0
JOPTS = 1

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

def split_lines(text, chomp=False):
    lines = text.replace("\r\n","\n").replace("\r","\n").split("\n")
    if chomp and len(lines) > 1 and not lines[-1]:
        lines = lines[:-1]
    return lines

def join_lines(lines):
    if isinstance(lines, basestring):
        return lines
    else:
        return "".join(line if line.endswith("\n") else line+"\n" for line in lines[:-1])+lines[-1]

def nb_json(lines, ipy_format=False):
    if not ipy_format:
        return json.dumps("\n".join(lines))
    return json.dumps([line+"\n" for line in lines[:-1]] + lines[-1:])

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

def base64encode(s):
    if not isinstance(s, str):
        s = s.encode("utf-8", "replace")
    return base64.b64encode(s)

def shlex_split_str(line):
    # Avoid NULs introduced by shlex.split when splitting unicode
    return shlex.split(line if isinstance(line, str) else line.encode("utf-8", "replace"))

def shell_quote(token):
    ##return pipes.quote(token)
    # Use simplified quoting to more easily recognize file URLs etc.
    return token.replace("'", "\\'").replace(" ", "\\ ").replace(";", "\\;").replace("&", "\\&")

def shell_unquote(token):
    try:
        return shlex_split_str(token)[0]
    except Exception:
        return token

def safe_filename(name):
    return re.sub(r"[^a-zA-Z0-9_.\-+=@,]", "", name)

def prompt_offset(line, pdelim, meta=None):
    """Return offset at end of prompt (not including trailing space), or zero"""
    if not pdelim:
        return 0
    offset = 0
    if (meta and not meta[JCONTINUATION]) or (pdelim[0] and line.startswith(pdelim[0])):
        end_offset = line.find(pdelim[1])
        if end_offset >= 0:
            offset = end_offset + len(pdelim[1])
    return offset

def strip_prompt_lines(update_scroll, note_prompts):
    """Strip scroll entries starting with notebook prompt"""
    trunc_scroll = []
    block_scroll = []
    prev_prompt_entry = None
    for entry in update_scroll:
        line = entry[JLINE]
        has_prompt = False
        for prompt in note_prompts:
            if line.startswith(prompt):
                # Entry starts with prompt
                has_prompt = True
                break
        if has_prompt:
            # Prompt entry saved temporarily
            trunc_scroll += block_scroll
            block_scroll = []
            prev_prompt_entry = entry
        else:
            # Retain all non-prompt entries
            block_scroll.append(entry)
            if "error" in line.lower():
                if prev_prompt_entry is not None:
                    # Include previous prompt entry because of error
                    block_scroll = [prev_prompt_entry] + block_scroll
                    prev_prompt_entry = None

    return trunc_scroll + block_scroll

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
    """Return working directory of running process
    Note: This will return os.path.realpath of current directory (eliminating symbolic links),
    which may differ from the $PWD value
    """
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


ANGLE_BRACKET_RE = re.compile(r"^\s*<")
def parse_headers(text):
    """Parse gterm output and return (headers, content)"""
    if ANGLE_BRACKET_RE.match(text):
        # Raw HTML (starts with <...)
        headers = {"content_type": "text/html",
                   "x_gterm_response": "",
                   "x_gterm_parameters": {}}
        offset, directive, opt_dict = gtermapi.parse_gterm_directive(text)
        if offset:
            # gterm comment directive
            content = text[offset:]
            headers["x_gterm_parameters"] = opt_dict
            if directive == "data":
                headers["x_gterm_response"] = "create_blob"
                content_type, sep, tail = content.partition(";")
                encoding, sep2, content = tail.partition(",")
                headers["content_type"] = content_type
                assert encoding == "base64", "Invalid data URI encoding: "+encoding
                headers["x_gterm_encoding"] = encoding
                headers["content_length"] = len(base64.b64decode(content))
            else:
                headers["x_gterm_response"] = directive
                if "content_length" in headers:
                    headers["content_length"] = len(content)
        else:
            # Plain HTML
            content = text
        return (headers, content)

    # "MIME headers"
    headers = {}
    content = text
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
    comps = shlex_split_str(line)
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
                temcomp = shlex_split_str(buf[:ncomp])[0]
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

JSERVER = 0
JHOST = 1
JFILENAME = 2
JFILEPATH = 3
JQUERY = 4

def create_file_uri(url_comps):
    return gtermapi.FILE_URI_PREFIX + url_comps[JHOST] + url_comps[JFILEPATH] + url_comps[JQUERY]

def split_file_url(url, check_host_secret=None):
    """Return [protocol://server[:port], hostname, filename, fullpath, query] for file://host/path
    or http://server:port/_file/host/path, or /_file/host/path URLs.
    If not file URL, returns []
    If check_host_secret is specified, and file hmac matches, then hostname is set to the null string.
    """
    if not url:
        return []
    server_port = ""
    if url.startswith(gtermapi.FILE_URI_PREFIX):
        host_path = url[len(gtermapi.FILE_URI_PREFIX):]
    elif url.startswith(gtermapi.FILE_PREFIX):
        host_path = url[len(gtermapi.FILE_PREFIX):]
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
        if not url_path.startswith(gtermapi.FILE_PREFIX):
            return []
        host_path = url_path[len(gtermapi.FILE_PREFIX):]

    host_path, sep, tail = host_path.partition("?")
    query = sep + tail
    comps = host_path.split("/")
    hostname = comps[0]
    filepath = "/"+"/".join(comps[1:])
    filename = comps[-1]
    if check_host_secret:
        filehmac = "?hmac="+gtermapi.file_hmac(filepath, check_host_secret)
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
    def __init__(self, pdelim, fg_color=0, bg_color=7):
        self.pdelim = pdelim
        self.pre_offset = len(pdelim[0]) if pdelim else 0
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
        self.cur_note = 0
        self.blobs = {}
        self.delete_blob_ids = []

    def set_cur_note(self, cur_note):
        self.cur_note = cur_note
        if not cur_note:
            self.blobs = {}

    def prefill_buf(self, scroll_lines, redisplay=False):
        self.scroll_lines = scroll_lines[:]
        if redisplay:
            self.last_scroll_count = self.current_scroll_count
        self.current_scroll_count += len(scroll_lines)
        if not redisplay:
            self.last_scroll_count = self.current_scroll_count

    def clear_buf(self):
        self.last_scroll_count = self.current_scroll_count
        self.scroll_lines = []
        self.last_blob_id = ""
        self.full_update = True

    def add_blob(self, blob_id, content_type, content_b64):
        self.blobs[blob_id] = (str(content_type), content_b64)

    def get_blob_uri(self, blob_id):
        if blob_id not in self.blobs:
            return ""
        return "data:%s;base64,%s" % self.blobs[blob_id]

    def delete_blob(self, blob_id):
        if not blob_id:
            return
        self.delete_blob_ids.append(blob_id)
        if self.blobs and blob_id in self.blobs:
            del self.blobs[blob_id]

    def clear_last_entry(self, last_entry_index=None):
        if not self.scroll_lines or self.entry_index <= 0:
            return
        n = len(self.scroll_lines)-1
        entry_index, offset, dir, row_params, line, markup = self.scroll_lines[n]
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

        for scroll_line in self.scroll_lines[n:]:
            self.delete_blob(scroll_line[JPARAMS][JOPTS].get("blob"))

        self.scroll_lines[n:] = []
        if self.last_scroll_count > self.current_scroll_count:
            self.last_scroll_count = self.current_scroll_count

    def blank_last_entry(self):
        """Replace previous entry (usually edit or form) with blank pagelet"""
        if not self.scroll_lines:
            return
        assert not self.scroll_lines[-1][JOFFSET]
        self.scroll_lines[-1][JPARAMS] = ["pagelet", {"add_class": "",
                                                      "pagelet_id": "%d-%d" % (self.cur_note, self.current_scroll_count)} ]
        self.scroll_lines[-1][JLINE] = ""
        self.scroll_lines[-1][JMARKUP] = ""
        if self.current_scroll_count > 0 and self.last_scroll_count >= self.current_scroll_count:
            self.last_scroll_count = self.current_scroll_count - 1

    def scroll_buf_up(self, line, meta, offset=0, add_class="", row_params=["", {}], markup=None):
        row_params = [row_params[JTYPE], dict(row_params[JOPTS])]
        current_dir = ""
        overwrite = False
        new_blob_id = ""
        if offset:
            # Prompt line (i.e., command line)
            self.entry_index += 1
            current_dir = meta[JCURDIR] if meta else ""
            markup = command_markup(self.entry_index, current_dir, self.pre_offset, offset, line)
            if not self.cleared_last:
                self.cleared_current_dir = None
            self.cleared_last = False
        elif row_params[JTYPE]:
            # Non-plain text scrolling
            overwrite = bool(row_params[JOPTS].get("overwrite"))
            new_blob_id = row_params[JOPTS].get("blob") or ""
            if overwrite and self.last_blob_id:
                # Delete previous blob
                self.delete_blob(self.last_blob_id)
            self.last_blob_id = new_blob_id
            ##logging.warning("ABCscroll_buf_up: overwrite=%s, %s", overwrite, markup)

        cur_pagelet_id = "%d-%d" % (self.cur_note, self.current_scroll_count)
        prev_pagelet_opts = self.scroll_lines[-1][JPARAMS][JOPTS] if self.scroll_lines and self.scroll_lines[-1][JPARAMS][JTYPE] == "pagelet" else {}
        prev_edit_file = self.scroll_lines and self.scroll_lines[-1][JPARAMS][JTYPE] == "edit_file"

        row_params[JOPTS]["add_class"] = add_class
        ##logging.warning("ABCscroll_buf_up2: type=%s, line='%s', overwrite=%s, opts=%s, id=%s", row_params[JTYPE], line, overwrite, prev_pagelet_opts, cur_pagelet_id)
        if overwrite and prev_pagelet_opts and prev_pagelet_opts["pagelet_id"] == cur_pagelet_id:
            # Overwrite previous pagelet entry
            row_params[JOPTS]["pagelet_id"] = cur_pagelet_id
            self.scroll_lines[-1][JDIR] = current_dir
            self.scroll_lines[-1][JPARAMS] = row_params
            self.scroll_lines[-1][JLINE] = line
            self.scroll_lines[-1][JMARKUP] = markup
            if self.current_scroll_count > 0 and self.last_scroll_count >= self.current_scroll_count:
                self.last_scroll_count = self.current_scroll_count - 1
        else:
            # New scroll entry
            if prev_edit_file or prev_pagelet_opts.get("form_input"):
                self.blank_last_entry()
            self.current_scroll_count += 1
            row_params[JOPTS]["pagelet_id"] = "%d-%d" % (self.cur_note, self.current_scroll_count)
            self.scroll_lines.append([self.entry_index, offset, current_dir, row_params, line, markup])
            if len(self.scroll_lines) > MAX_SCROLL_LINES:
                old_entry_index, old_offset, old_dir, old_params, old_line, old_markup = self.scroll_lines.pop(0)
                self.delete_blob(old_params[JOPTS].get("blob"))
                while self.scroll_lines and self.scroll_lines[0][JINDEX] == old_entry_index:
                    self.scroll_lines.pop(0)
                    tem_entry_index, tem_offset, tem_dir, tem_params, tem_line, tem_markup = self.scroll_lines.pop(0)
                    self.delete_blob(tem_params[JOPTS].get("blob"))

    def append_scroll(self, scroll_lines):
        tem_lines = scroll_lines[:]
        for tem_line in tem_lines:
            tem_line[JINDEX] = self.entry_index
        self.scroll_lines += tem_lines
        self.current_scroll_count += len(tem_lines)

    def update(self, active_rows, width, height, cursorx, cursory, main_screen,
               alt_screen=None, pdelim=[], reconnecting=False):
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
                new_row_str = dump(new_row)
                opts = {"add_class": ""}
                offset = prompt_offset(new_row_str, pdelim, screen.meta[j])
                update_rows.append([j, offset, "", ["", opts], self.dumprichtext(new_row, trim=True), None])

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
    def __init__(self, term_name, fd, pid, screen_callback, height=25, width=80, winheight=0, winwidth=0,
                 cookie=0, shared_secret="", host="", pdelim=[], logfile=""):
        self.term_name = term_name
        self.fd = fd
        self.pid = pid
        self.screen_callback = screen_callback
        self.width = width
        self.height = height
        self.winwidth = winwidth
        self.winheight = winheight
        self.cookie = cookie
        self.shared_secret = shared_secret
        self.host = host
        self.pdelim = pdelim
        self.logfile = logfile
        self.screen_buf = ScreenBuf(pdelim)

        self.note_count = 0
        self.note_screen_buf = ScreenBuf("")
        self.reset_note()

        self.init()
        self.reset()
        self.current_dir = ""
        self.current_meta = None
        self.output_time = time.time()
        self.buf = ""
        self.alt_mode = False
        self.screen = self.main_screen
        self.trim_first_prompt = bool(pdelim)
        self.logchars = 0
        self.command_path = ""

    def reset_note(self):
        self.note_prompts = []
        self.note_expect_prompt = False
        self.note_found_prompt = False
        self.note_cells = None
        self.note_input = []
        self.note_file = ""
        self.note_shell = False
        self.note_dir = ""
        self.note_command = ""
        self.note_start = None
        self.note_slide = None

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
        # Reset screen buffers
        self.update_time = 0
        self.needs_updating = True
        self.main_screen = Screen(self.width, self.height)
        self.alt_screen  = Screen(self.width, self.height)
        self.scroll_top = 0
        self.scroll_bot = 0 if self.note_cells else self.height-1
        self.cursor_x_bak = self.cursor_x = 0
        self.cursor_y_bak = self.cursor_y = 0
        self.cursor_eol = 0
        self.current_nul = self.screen_buf.default_nul
        self.echobuf = ""
        self.echobuf_count = 0
        self.outbuf = ""
        self.active_rows = 0
        self.gterm_code = None
        self.gterm_buf = None
        self.gterm_buf_size = 0
        self.gterm_entry_index = None
        self.gterm_validated = False
        self.gterm_output_buf = []

    def resize(self, height, width, winheight=0, winwidth=0, force=False):
        reset_flag = force or (self.width != width or self.height != height)
        self.winwidth = winwidth
        self.winheight = winheight
        if reset_flag:
            min_width = min(self.width, width)
            saved_line = None
            if self.active_rows:
                if self.active_rows > 1:
                    self.scroll_screen(self.active_rows-1)
                # Save last line
                line = dump(self.main_screen.data[:min_width])
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

    def open_notebook(self, filepath, prompts=[], content=None):
        self.note_start = None
        self.note_count += 1
        at_shell = bool(self.active_rows and self.main_screen.meta[self.active_rows-1]) # At shell prompt
        self.note_dir = self.current_dir
        if at_shell:
            self.note_command = "bash"
        elif self.command_path:
            self.note_command = os.path.basename(self.command_path)
        else:
            self.note_command = ""
        if not prompts and self.note_command in gtermapi.PROMPTS_LIST:
            prompts = gtermapi.PROMPTS_LIST[self.note_command]
        if not prompts:
            # Search buffer to use current prompt
            try:
                line = dump(self.peek(self.cursor_y, 0, self.cursor_y, self.width), trim=True, encoded=True)
                comps = line.split()
                if comps and comps[0]:
                    prompts = [comps[0]+" "]
                    if prompts[0] == gtermapi.PROMPTS_LIST["python"][0]:
                        prompts += gtermapi.PROMPTS_LIST["python"][1:]
                    elif prompts[0] == gtermapi.PROMPTS_LIST["ipython"][0]:
                        prompts += gtermapi.PROMPTS_LIST["ipython"][1:]
                    elif at_shell:
                        prompts += ["> "]
                    elif prompts[-1] == gtermapi.PROMPTS_LIST["node"][0]:
                        # Handles node REPL shell
                        prompts += ["... "]
            except Exception:
                raise

        self.scroll_screen(self.active_rows)
        self.update()
        self.resize(self.height, self.width, self.winheight, self.winwidth, force=True)
        self.scroll_bot = 0
        self.note_screen_buf.clear_buf()
        self.note_screen_buf.set_cur_note(self.note_count)
        self.note_cells = {"maxIndex": 0, "curIndex": 0, "cellIndices": [], "cells": OrderedDict()}
        self.note_prompts = prompts

        self.note_file = filepath
        self.note_shell = at_shell
        self.screen_callback(self.term_name, "", "note_open", [self.note_file, self.note_dir, self.note_shell])
        self.note_file = filepath
        if content is None:
            if not filepath:
                content = ""
            else:
                fullname = os.path.expanduser(filepath)
                fullpath = fullname if fullname.startswith("/") else self.note_dir+"/"+fullname
                try:
                    with open(fullpath) as f:
                        content = f.read()
                except Exception, excp:
                    content = "Error in reading notebook file %s" % fullpath
                    logging.error("Error in reading notebook file %s" % fullpath)

        if content:
            if filepath.endswith(".ipynb") or filepath.endswith(".ipynb.json"):
                self.read_ipynb(content)
            else:
                self.read_md(content)

        if not self.note_cells["curIndex"]:
            self.add_cell("")

    def close_notebook(self, discard=False):
        self.note_start = None
        self.leave_cell()
        if not discard:
            for cell_index in self.note_cells["cellIndices"]:
                # Copy all cellInput and cellOutput to scroll buffer
                cell = self.note_cells["cells"][cell_index]
                if cell["cellType"] in MARKUP_TYPES:
                    if cell["cellInput"]:
                        row_params = ["markdown", {}]
                        self.screen_buf.scroll_buf_up("", "", row_params=row_params, add_class="gterm-cell-input",
                                                      markup="\n".join(cell["cellInput"]))
                else:
                    if cell["cellInput"]:
                        for line in cell["cellInput"]:
                            self.screen_buf.scroll_buf_up(line, "", add_class="gterm-cell-input")
                        if not cell["cellOutput"]:
                            self.screen_buf.scroll_buf_up(" ", "")
                    self.screen_buf.append_scroll(cell["cellOutput"])
        self.reset_note()
        self.note_screen_buf.set_cur_note(0)
        self.note_screen_buf.clear_buf()
        self.scroll_bot = self.height-1
        self.resize(self.height, self.width, self.winheight, self.winwidth, force=True)
        self.zero_screen()
        self.screen_callback(self.term_name, "", "note_close", [])
        self.update()

    def save_notebook(self, filepath, input_data="", params={}):
        fullname = os.path.expanduser(filepath)
        fullpath = fullname if fullname.startswith("/") else self.note_dir+"/"+fullname
        fig_suffix = safe_filename(os.path.splitext(os.path.basename(fullpath))[0])
        format = params.get("format", "")
        if filepath.endswith(".ipynb") or filepath.endswith(".ipynb.json"):
            format = "ipynb"
            ipy_format = filepath.endswith(".ipynb")
            fig_suffix, sep, tail = fig_suffix.rpartition(".")
        md_lines = []
        if format == "ipynb":
            md_lines += [IPYNB_JSON_HEADER % dict(name=fig_suffix, version_major=3, version_minor=0)]
        elif self.note_command:
            md_lines.append('<!--gterm notebook command=%s-->' % safe_filename(self.note_command))
        ref_blobs = OrderedDict()
        prompt_num = 0
        in_prompt = 0
        for j, cell_index in enumerate(self.note_cells["cellIndices"]):
            cell = self.note_cells["cells"][cell_index]
            if cell["cellIndex"] == self.note_cells["curIndex"]:
                # Current cell; copy output
                cell["cellInput"] = split_lines(input_data) if input_data else []
                if cell["cellType"] not in MARKUP_TYPES:
                    cell["cellOutput"] = strip_prompt_lines(self.note_screen_buf.scroll_lines, self.note_prompts)

            cell_out = False
            if format == "ipynb":
                if j:
                    md_lines[-1] += ","
                input_json = nb_json(cell["cellInput"], ipy_format)
                if cell["cellType"] in MARKUP_TYPES:
                    md_lines += [IPYNB_JSON_MARKDOWN % dict(source=input_json)]
                else:
                    prompt_num += 1
                    in_prompt = prompt_num
                    md_lines += [IPYNB_JSON_CODE0 % dict(input=input_json, lang="python")]
            elif cell["cellInput"]:
                if cell["cellType"] not in MARKUP_TYPES:
                    md_lines.append("```"+cell["cellType"])
                for line in cell["cellInput"]:
                    md_lines.append(line)
                if cell["cellType"] not in MARKUP_TYPES:
                    md_lines.append("```")
                md_lines.append ("")

            if cell["cellOutput"] and cell["cellType"] not in MARKUP_TYPES:
                out_lines = []
                for scroll_line in cell["cellOutput"]:
                    opts = scroll_line[JPARAMS][JOPTS]
                    blob_id = opts.get("blob")
                    if blob_id:
                        if out_lines:
                            if format == "ipynb":
                                if cell_out:
                                    md_lines[-1] += ","
                                prompt_num += 1
                                out_json = nb_json(out_lines, ipy_format)
                                md_lines += [IPYNB_JSON_PYOUT % dict(out_prompt=prompt_num, text=out_json)]
                            else:
                                md_lines += ["```output"] + out_lines + ["```"] + [""]
                            cell_out = True
                            out_lines = []
                        data_uri = self.note_screen_buf.get_blob_uri(blob_id)
                        if data_uri:
                            if format == "ipynb":
                                if cell_out:
                                    md_lines[-1] += ","
                                content_type, sep, tail = data_uri[len("data:"):].partition(";")
                                encoding, sep2, content = tail.partition(",")
                                md_lines += [IPYNB_JSON_DATA % dict(format=content_type.split("/")[1], base64=content)]
                                cell_out = True
                            else:
                                ref_id = "fig%d-%s" % (len(ref_blobs)+1, fig_suffix)
                                ref_blobs[ref_id] = data_uri
                                md_lines.append("![image][%s]" % ref_id)
                                md_lines.append ("")
                    else:
                        out_lines.append(scroll_line[JLINE])
                if out_lines:
                    if format == "ipynb":
                        if cell_out:
                            md_lines[-1] += ","
                        prompt_num += 1
                        out_json = nb_json(out_lines, ipy_format)
                        md_lines += [IPYNB_JSON_PYOUT % dict(out_prompt=prompt_num, text=out_json)]
                    else:
                        md_lines += ["```output"] + out_lines + ["```"] + [""]
                    cell_out = True
                    out_lines = []

            if format == "ipynb" and cell["cellType"] not in MARKUP_TYPES:
                md_lines += [IPYNB_JSON_CODE1 % dict(in_prompt=in_prompt)]

        if ref_blobs:
            for ref_id, ref_blob in ref_blobs.iteritems():
                md_lines.append("[%s]: %s" % (ref_id, ref_blob))

        if format == "ipynb":
            md_lines += [IPYNB_JSON_FOOTER]
        filedata = "\n".join(md_lines) + "\n"
        save_params = {"x_gterm_filepath": fullpath, "content_type": "text/x-markdown"}
        if params.get("location") == "remote":
            save_params["x_gterm_location"] = "remote"
        else:
            save_params["x_gterm_popstatus"] = params.get("popstatus", "")
        self.save_data(save_params, filedata)

    def read_ipynb(self, content):
        try:
            nb = json.loads(content)
            cells = nb["worksheets"][0]["cells"]
            for cell in cells:
                if cell["cell_type"] == "markdown":
                    self.add_cell("markdown", init_text=join_lines(cell["source"]))

                elif cell["cell_type"] == "code":
                    new_cell = self.add_cell(cell["language"], init_text=join_lines(cell["input"]))
                    for output in cell["outputs"]:
                        if output["output_type"] in ("pyout", "stream"):
                            lines = split_lines(output["text"], chomp=True) if isinstance(output["text"], basestring) else output["text"]
                            for line in lines:
                                if line.endswith("\n"):
                                    line = line[:-1]
                                self.note_screen_buf.scroll_buf_up(line, None)
                        elif output["output_type"] == "display_data":
                            blob_id = str(uuid.uuid4())
                            data_uri = "data:image/%s;base64,%s" % ("png", output["png"].replace("\n",""))
                            self.create_blob(blob_id, data_uri[len("data:"):])
                            markup = BLOCKIMGFORMAT % (blob_id, gtermapi.BLOB_PREFIX, blob_id, "image")
                            self.note_screen_buf.scroll_buf_up("", None, markup=markup,
                                                               row_params=["pagelet", {"blob": blob_id}])
                self.update()
        except Exception, excp:
            logging.warning("read_ipynb: %s", excp)


    def read_md(self, content):
        code_cell = None
        code_lines = None
        raw_lines = []
        leaving_block = False
        blob_ids = {}
        try:
            state = None
            for line in split_lines(content, chomp=True):
                if line.startswith("```"):
                    lang = line[len("```"):].strip()
                    if state is None:
                        # Entering fenced block
                        leaving_block = False
                        if raw_lines:
                            # Add raw cell
                            if code_cell:
                                self.update()
                                code_cell = None
                            self.add_cell("markdown", init_text="\n".join(raw_lines))
                            raw_lines = []
                        state = lang
                        if state == "output":
                            # New output block
                            if not code_cell:
                                # Ignore orphan output block
                                pass
                        else:
                            # New code block
                            code_lines = []
                    else:
                        # Leaving fenced block
                        leaving_block = True
                        if state == "output":
                            # Ignore orphan output block
                            pass
                        else:
                            # Leaving code block
                            self.update()
                            self.add_cell(state, init_text="\n".join(code_lines))
                            code_lines = None
                            code_cell = self.note_cells["cells"][self.note_cells["curIndex"]]
                        state = None
                elif state is not None:
                    # Within fenced block
                    if state == "output":
                        # Within output block
                        if code_cell:
                            self.note_screen_buf.scroll_buf_up(line, None)
                        else:
                            # Ignore orphan output block
                            pass
                    else:
                        # Within code block
                        code_lines.append(line)

                elif MD_IMAGE_RE.match(line):
                    # Inline image
                    leaving_block = True
                    match = MD_IMAGE_RE.match(line)
                    alt = match.group(1).strip() or "image"
                    ref_id = match.group(2).strip()
                    blob_id = str(uuid.uuid4())
                    blob_ids[ref_id] = blob_id
                    if code_cell:
                        markup = BLOCKIMGFORMAT % (blob_id, gtermapi.BLOB_PREFIX, blob_id, alt)
                        self.note_screen_buf.scroll_buf_up("", None, markup=markup,
                                                           row_params=["pagelet", {"blob": blob_id}])
                    else:
                        raw_lines.append("![%s](%slocal/%s)" % (alt, gtermapi.BLOB_PREFIX, blob_id))

                elif MD_REF_RE.match(line):
                    # Reference list
                    match = MD_REF_RE.match(line)
                    ref_id = match.group(1).strip()
                    if ref_id in blob_ids:
                        self.create_blob(blob_ids[ref_id], line[len(match.group(0)):])

                elif gtermapi.GTERM_DIRECTIVE_RE.match(line):
                    # gterm comment directive (currently just ignored)
                    offset, directive, opt_dict = gtermapi.parse_gterm_directive(line)

                elif line or not leaving_block:
                    # Non-blank line or not leaving block; handle raw line
                    leaving_block = False
                    if code_cell:
                        if line:
                            # New raw block (if not blank line)
                            self.update()
                            code_cell = None
                            raw_lines = [line]
                    elif line.rstrip() == gtermapi.PAGE_BREAK:
                        # Page break
                        if raw_lines:
                            # Split raw block
                            self.add_cell("markdown", init_text="\n".join(raw_lines))
                        self.add_cell("markdown", init_text=gtermapi.PAGE_BREAK)
                        raw_lines = []
                    elif line or raw_lines:
                        raw_lines.append(line)

            if raw_lines:
                # Add raw cell
                if code_cell:
                    self.update()
                    code_cell = None
                self.add_cell("markdown", init_text="\n".join(raw_lines))
                raw_lines = []
        except Exception, excp:
            logging.warning("read_md: %s", excp)

        self.update()

    def add_cell(self, new_cell_type="", init_text="", before_cell_number=0, filename=""):
        """ If before_cell_number is 0(-1), add new cell after(before) current cell
            If before_cell_number > 0, add new_cell before before_cell_number
        """
        if not new_cell_type:
            new_cell_type = gtermapi.LANGUAGES.get(self.note_command, "code")
        prev_index = self.note_cells["curIndex"]
        if before_cell_number in (-1, 0):
            before_cell_number += 2+self.note_cells["cellIndices"].index(prev_index) if prev_index else 1+len(self.note_cells["cellIndices"])

        if before_cell_number <= 0:
            return None

        self.leave_cell()
        self.note_cells["maxIndex"] += 1
        cell_index = self.note_cells["maxIndex"]
        new_cell = {"cellIndex": cell_index, "cellType": new_cell_type, "cellFile": filename, "cellInput": [], "cellOutput": []}
        new_cell["cellInput"] = split_lines(init_text) if init_text else []
        self.note_cells["cells"][cell_index] = new_cell
        self.note_cells["curIndex"] = cell_index

        if before_cell_number > len(self.note_cells["cellIndices"]):
            before_cell_index = 0
            self.note_cells["cellIndices"].append(cell_index)
        else:
            before_cell_index = self.note_cells["cellIndices"][before_cell_number-1]
            self.note_cells["cellIndices"].insert(before_cell_number-1, cell_index)

        self.screen_callback(self.term_name, "", "note_add_cell",
                             [cell_index, new_cell_type, before_cell_index, new_cell["cellInput"]])

        return new_cell

    def next_index(self, move_up=False, switch=False):
        """Return index of next cell down (or up), or 0. If switch, switch moving up or down, if necessary"""
        cur_index = self.note_cells["curIndex"]
        ncells = len(self.note_cells["cellIndices"])
        if not cur_index or ncells < 2:
            return 0

        cur_location = self.note_cells["cellIndices"].index(cur_index)

        if switch:
            if move_up and cur_location == 0:
                move_up = False
            elif not move_up and cur_location == ncells-1:
                move_up = True

        if move_up and cur_location > 0:
            return self.note_cells["cellIndices"][cur_location-1]
        elif not move_up and cur_location < ncells-1:
            return self.note_cells["cellIndices"][cur_location+1]

        return 0

    def is_page_break(self, cell_index):
        cell = self.note_cells["cells"][cell_index]
        return cell["cellType"] in MARKUP_TYPES and "\n".join(cell["cellInput"]).rstrip() == gtermapi.PAGE_BREAK

    def leave_cell(self, delete=False, move_up=False):
        """Leave current cell, deleting it if requested. Return index of new cell, or 0"""
        cur_index = self.note_cells["curIndex"]
        if not cur_index:
            return
        select_cell_index = self.next_index(move_up=move_up, switch=True)

        # Move all screen lines to scroll buffer
        cur_cell = self.note_cells["cells"][cur_index]
        self.scroll_screen(self.active_rows)
        if cur_cell["cellType"] not in MARKUP_TYPES:
            cur_cell["cellOutput"] = strip_prompt_lines(self.note_screen_buf.scroll_lines, self.note_prompts)
        self.note_screen_buf.clear_buf()
        self.note_cells["curIndex"] = 0
            
        if delete:
            assert len(self.note_cells["cells"]) > 1
            del self.note_cells["cells"][cur_index]
            self.note_cells["cellIndices"].remove(cur_index)

        return select_cell_index

    def switch_cell(self, cell_index=0, delete=False, move_up=False):
        """Switch to cell with cell_index (if zero, move up/down one cell)"""
        next_cell_index = self.leave_cell(delete=delete, move_up=move_up)
        if not cell_index:
            cell_index = next_cell_index
        self.note_input = []
        assert cell_index in self.note_cells["cells"]
        self.note_cells["curIndex"] = cell_index
        next_cell = self.note_cells["cells"][cell_index]
        if next_cell["cellType"] not in MARKUP_TYPES:
            self.note_screen_buf.prefill_buf(next_cell["cellOutput"])
        next_cell["cellOutput"] = []
        return cell_index

    def select_cell(self, cell_index=0, move_up=False):
        if not self.note_cells:
            return
        cur_index = self.note_cells["curIndex"]
        select_cell_index = self.switch_cell(cell_index, move_up=move_up)
        if cur_index != select_cell_index:
            self.screen_callback(self.term_name, "", "note_select_cell", [select_cell_index])

    def select_page(self, move=0, endpoint=False, slide=False):
        """Select page
        move = -1(up) or 0 (none) or 1 (down).
        If endpoint, move to endpoints (first/last)
        If slide, display page as slide.
        """
        if not self.note_cells:
            return
        cur_index = self.note_cells["curIndex"]
        select_cell_index = self.find_page_cell_index(move=move, endpoint=endpoint)
        if cur_index != select_cell_index:
            self.switch_cell(select_cell_index)
        last_cell_index = self.find_page_cell_index(last=True)
        if slide:
            self.note_slide = [select_cell_index, last_cell_index]
        else:
            self.note_slide = None
        self.screen_callback(self.term_name, "", "note_select_page", [select_cell_index, last_cell_index, slide])

    def find_page_cell_index(self, move=0, last=False, endpoint=False):
        """Locate first cell in page
        move = -1(up) or 0 (none) or 1 (down).
        If last, locate last cell in page.
        If endpoint, move to endpoints (first/last)
        """
        cur_index = self.note_cells["curIndex"]
        ncells = len(self.note_cells["cellIndices"])
        if not cur_index or ncells < 2:
            return cur_index

        if move == -1 and endpoint:
            return self.note_cells["cellIndices"][0]

        if move == 1 and endpoint and last:
            return self.note_cells["cellIndices"][-1]

        cur_location = self.note_cells["cellIndices"].index(cur_index)
        select_index = cur_index
        if move == 1 or last:
            first_index = None
            start_page = False
            for cell_index in self.note_cells["cellIndices"][cur_location+1:]:
                if self.is_page_break(cell_index):
                    start_page = True
                    if not endpoint and last:
                        return select_index
                else:
                    select_index = cell_index
                    if start_page:
                        first_index = cell_index
                        start_page = False
                        if not endpoint:
                            break
            if not last:
                if first_index is None:
                    return self.find_page_cell_index(0, last=False, endpoint=endpoint)
                else:
                    return first_index
        else:
            match_remaining = 1 if move else 0
            for cell_index in reversed(self.note_cells["cellIndices"][:cur_location]):
                if self.is_page_break(cell_index):
                    if not endpoint and not match_remaining:
                        return select_index
                    match_remaining = 0
                else:
                    select_index = cell_index
        return select_index

    def update_type(self, cell_type):
        cur_index = self.note_cells["curIndex"]
        if not cur_index:
            return
        cur_cell = self.note_cells["cells"][cur_index]
        cur_cell["cellType"] = cell_type
        cur_cell["cellOutput"] = []
        self.screen_callback(self.term_name, "", "note_update_type", [cur_index, cell_type])

    def move_cell(self, move_up=False):
        cur_index = self.note_cells["curIndex"]
        next_cell_index = self.next_index(move_up=move_up)
        if not next_cell_index:
            return
        cur_location = self.note_cells["cellIndices"].index(cur_index)
        next_location = self.note_cells["cellIndices"].index(next_cell_index)
        self.note_cells["cellIndices"][cur_location] = next_cell_index
        self.note_cells["cellIndices"][next_location] = cur_index
        self.screen_callback(self.term_name, "", "note_move_cell", [next_cell_index, move_up])

    def delete_cell(self, move_up=False):
        cur_index = self.note_cells["curIndex"]
        select_cell_index = self.switch_cell(delete=True, move_up=move_up)
        self.screen_callback(self.term_name, "", "note_delete_cell", [cur_index, select_cell_index])

    def merge_above(self):
        next_cell_index = self.next_index(move_up=True)
        if not next_cell_index:
            return
        cur_index = self.note_cells["curIndex"]
        cur_cell = self.note_cells["cells"][cur_index]
        next_cell = self.note_cells["cells"][next_cell_index]
        if cur_cell["cellType"] != next_cell["cellType"]:
            logging.warning("merge_cell: cell type mismatch %s != %s", cur_cell["cellType"], next_cell["cellType"])
            return
        next_cell["cellInput"] += cur_cell["cellInput"]
        next_cell["cellOutput"] = []
        self.screen_callback(self.term_name, "", "note_cell_value", ["\n".join(next_cell["cellInput"]), next_cell_index])
        self.delete_cell(move_up=True)

    def complete_cell(self, incomplete):
        if incomplete:
            self.note_screen_buf.clear_buf()
        self.zero_screen()
        self.cursor_x = 0

        if incomplete == "\x09":
            # Repeat TAB
            data = "\x09"
        else:
            data = "\x01\x0b"    # Ctrl-A Ctrl-K
            if incomplete:
                # TAB completion requested
                data += incomplete + "\x09"
        try:
            os.write(self.fd, data)
        except Exception, excp:
            pass

    def update_cell(self, cell_index, execute, input_data):
        cur_index = self.note_cells["curIndex"]
        if not cur_index:
            return
        assert cell_index == cur_index
        cur_cell = self.note_cells["cells"][cur_index]
        cur_cell["cellInput"] = split_lines(input_data)

        if not execute:
            return

        self.note_input = cur_cell["cellInput"][:]   # Must be a copy
        if self.note_input[-1]:
            # Add blank line to clear any indentation level
            self.note_input.append("")

        self.note_screen_buf.clear_buf()
        self.zero_screen()
        self.cursor_x = 0
        self.note_expect_prompt = False
        self.note_found_prompt = False

        # Send a blank line to clear any indentation level and trigger a prompt
        os.write(self.fd, "\n")

        if not self.note_prompts:
            # No prompt; transmit all input data
            while self.note_input:
                os.write(self.fd, self.note_input.pop(0)+"\n")

    def erase_output(self, all_cells):
        cur_index = self.note_cells["curIndex"]
        for cell in self.note_cells["cells"].itervalues():
            if not all_cells and cell["cellIndex"] != cur_index:
                continue
            cell["cellOutput"] = []

        # Clear screen buffer
        self.scroll_screen(self.active_rows)
        self.note_screen_buf.clear_buf()
        self.screen_callback(self.term_name, "", "note_erase_output", [0 if all_cells else cur_index])

    def clear(self):
        self.screen_buf.clear_buf()
        self.needs_updating = True

    def reconnect(self, response_id=""):
        self.update_callback(response_id=response_id)
        self.graphterm_output(response_id=response_id, from_buffer=True)

    def clear_last_entry(self, last_entry_index=None):
        self.screen_buf.clear_last_entry(last_entry_index=last_entry_index)

    def scroll_screen(self, scroll_rows=None):
        pdelim = [] if self.note_cells else self.pdelim
        if scroll_rows == None:
            scroll_rows = 0
            for j in range(self.active_rows-1,-1,-1):
                line = dump(self.main_screen.data[self.width*j:self.width*(j+1)])
                if prompt_offset(line, pdelim, self.main_screen.meta[j]):
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
            offset = prompt_offset(dump(row), pdelim, meta)
            if meta:
                # Concatenate rows for multiline command
                while cursor_y < scroll_rows-1 and self.main_screen.meta[cursor_y+1] and self.main_screen.meta[cursor_y+1][JCONTINUATION]:
                    cursor_y += 1
                    row += self.main_screen.data[self.width*cursor_y:self.width*cursor_y+self.width]
            if self.note_cells:
                self.note_screen_buf.scroll_buf_up(dump(row, trim=True, encoded=True), meta, offset=offset)
            else:
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

        while self.screen_buf.delete_blob_ids:
            self.screen_callback(self.term_name, "", "delete_blob", [self.screen_buf.delete_blob_ids.pop()])
        while self.note_screen_buf.delete_blob_ids:
            self.screen_callback(self.term_name, "", "delete_blob", [self.note_screen_buf.delete_blob_ids.pop()])

        self.update_callback()

    def update_callback(self, response_id=""):
        reconnecting = bool(response_id)
        if not self.note_cells or self.screen_buf.full_update or reconnecting:
            alt_screen = self.alt_screen if self.alt_mode else None
            if self.note_cells:
                active_rows, cursor_x, cursor_y = 0, 0, 0
            else:
                active_rows, cursor_x, cursor_y = self.active_rows, self.cursor_x, self.cursor_y
            full_update, update_rows, update_scroll = self.screen_buf.update(active_rows, self.width, self.height,
                                                                             cursor_x, cursor_y,
                                                                             self.main_screen,
                                                                             alt_screen=alt_screen,
                                                                             pdelim=self.pdelim,
                                                                             reconnecting=reconnecting)
            pre_offset = len(self.pdelim[0]) if self.pdelim else 0
            self.screen_callback(self.term_name, response_id, "row_update",
                                 [dict(alt_mode=self.alt_mode, reset=full_update,
                                       active_rows=self.active_rows, pre_offset=pre_offset),
                                  self.width, self.height,
                                  self.cursor_x, self.cursor_y,
                                  update_rows, update_scroll])
            if not self.note_cells and not reconnecting and (update_rows or update_scroll):
                self.gterm_output_buf = []

        if self.note_cells:
            if reconnecting:
                self.screen_callback(self.term_name, response_id, "note_open", [self.current_dir, self.note_shell])
                for cell_index in self.note_cells["cellIndices"]:
                    cell = self.note_cells["cells"][cell_index]
                    self.screen_callback(self.term_name, response_id, "note_add_cell",
                                         [cell["cellIndex"], cell["cellType"], 0,
                                          cell["cellInput"], cell["cellOutput"]])
                    if cell["cellIndex"] != self.note_cells["curIndex"]:
                        # Current cell will be updated later
                        self.screen_callback(self.term_name, response_id, "note_row_update",
                                             [dict(alt_mode=False, reset=True,
                                                   active_rows=self.active_rows, pre_offset=0),
                                              self.width, self.height,
                                              0, 0,
                                              [], cell["cellOutput"]])
                if self.note_slide:
                    self.screen_callback(self.term_name, "", "note_select_page", self.note_slide+[True])
                self.screen_callback(self.term_name, "", "note_select_cell", [self.note_cells["curIndex"]])

            full_update, update_rows, update_scroll = self.note_screen_buf.update(self.active_rows, self.width, self.height,
                                                                             self.cursor_x, self.cursor_y,
                                                                             self.main_screen,
                                                                             alt_screen=False,
                                                                             pdelim=[],
                                                                             reconnecting=reconnecting)

            update_scroll = strip_prompt_lines(update_scroll, self.note_prompts)

            self.screen_callback(self.term_name, response_id, "note_row_update",
                                 [dict(alt_mode=False, reset=full_update,                                                                                    active_rows=self.active_rows, pre_offset=0,
                                       note_prompt=self.note_found_prompt),
                                  self.width, self.height,
                                  self.cursor_x, self.cursor_y,
                                  update_rows, update_scroll])
            if not reconnecting and (update_rows or update_scroll):
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
        if y2 > y1:
            self.poke(y1, 0, self.peek(y1+1, 0, y2, self.width))
            self.screen.meta[y1:y2] = self.screen.meta[y1+1:y2+1]
        self.zero_lines(y2, y2)

    def scroll_down(self, y1, y2):
        if y2 > y1:
            self.poke(y1+1, 0, self.peek(y1, 0, y2-1, self.width))
            self.screen.meta[y1+1:y2+1] = self.screen.meta[y1:y2]
        self.zero_lines(y1, y1)

    def scroll_right(self, y, x):
        self.poke(y, x+1, self.peek(y, x, y, self.width-1))
        self.zero(y, x, y, x)

    def parse_command(self):
        if not self.alt_mode and self.current_meta and not self.current_meta[1]:
            # Parse command line
            try:
                line = dump(self.peek(self.cursor_y, 0, self.cursor_y, self.width), trim=True, encoded=True)
                offset = prompt_offset(line, self.pdelim, self.current_meta)
                args = shlex_split_str(line[offset:])
                self.command_path = args[0]
            except Exception:
                pass

    def cursor_down(self):
        if self.cursor_y >= self.scroll_top and self.cursor_y <= self.scroll_bot:
            self.cursor_eol = 0
            self.parse_command()
            q, r = divmod(self.cursor_y+1, self.scroll_bot+1)
            if q:
                if self.note_cells:
                    row = self.peek(self.scroll_top, 0, self.scroll_top, self.width)
                    self.note_screen_buf.scroll_buf_up(dump(row, trim=True, encoded=True),
                                                  self.screen.meta[self.scroll_top],
                                    offset=prompt_offset(dump(row), self.pdelim, self.screen.meta[self.scroll_top]))
                elif not self.alt_mode:
                    row = self.peek(self.scroll_top, 0, self.scroll_top, self.width)
                    self.screen_buf.scroll_buf_up(dump(row, trim=True, encoded=True),
                                                  self.screen.meta[self.scroll_top],
                                    offset=prompt_offset(dump(row), self.pdelim, self.screen.meta[self.scroll_top]))
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
        self.command_path = ""
        self.current_dir = current_directory
        if not self.active_rows or self.cursor_y+1 == self.active_rows:
            self.current_meta = (current_directory, 0)
            self.screen.meta[self.cursor_y] = self.current_meta

    def enter(self):
        """Called when CR or LF is received from the user to indicate possible end of command"""
        self.parse_command()
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
            if len(uchar) > 1:
                uchar = u"?"
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
                    scroll_rows = self.active_rows
                    if scroll_rows == 1 and self.cursor_y == 0:
                        # Special handling to skip echoed ^C before writing blank pagelet
                        line = dump(self.peek(self.cursor_y, 0, self.cursor_y, self.width), trim=True, encoded=True)
                        if line.endswith("^C"):
                            scroll_rows = 0
                    if scroll_rows:
                        self.scroll_screen(scroll_rows)
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
#           print "insert on"

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
#           print "insert off"

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
#           else:
#               print >> sys.stderr, "lineterm: CSI style ignore",l,i
#       print >> sys.stderr, 'lineterm: style: %r %x'%(l, self.current_nul)

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
            screen_buf = self.note_screen_buf if self.note_cells else self.screen_buf
            ##logging.warning("lineterm.Terminal.gterm_append: %s %s", response_type, response_params)

            if not self.gterm_validated:
                # Unvalidated markup; plain-text or escaped HTML content for security
                try:
                    import lxml.html
                    content = lxml.html.fromstring(content).text_content()
                    headers["content_type"] = "text/plain"
                except Exception:
                    content = cgi.escape(content)

                if response_type:
                    headers["x_gterm_response"] = "pagelet"
                    headers["x_gterm_parameters"] = {}
                    headers["content_length"] = len(content)
                    params = {"validated": self.gterm_validated, "headers": headers}
                    self.graphterm_output(params, content)
                else:
                    content_lines = split_lines(content)
                    screen_buf.scroll_buf_up(content_lines[0]+"...", None)
            else:
                # Validated data
                if response_type in ("create_blob", "edit_file", "open_notebook"):
                    try:
                        filepath = response_params.get("filepath", "")
                        if "content_length" in headers:
                            # Remote content provided
                            encoding = headers.get("x_gterm_encoding", "")
                            md5_digest = headers.get("x_gterm_digest", "")
                            if md5_digest and md5_digest != hashlib.md5(content).hexdigest():
                                raise Exception("File digest mismatch for %s: %s" % (response_type, filepath))

                            if response_type == "create_blob":
                                assert not content or encoding == "base64", "Invalid blob encoding"
                            else:
                                if encoding == "base64":
                                    # Only create blob content needs to remain encoded as Base64
                                    headers.pop("x_gterm_encoding", None)
                                    headers.pop("x_gterm_digest", None)
                                    content = base64.b64decode(content)
                                if len(content) != headers["content_length"]:
                                    raise Exception("Content length mismatch (%d!=%d) for %s: %s" % (len(content), headers["content_length"], response_type, filepath))

                        else:
                            # Read local file content
                            if filepath:
                                if not os.path.exists(filepath) or not os.path.isfile(filepath):
                                    raise Exception("File %s not found" % filepath)
                                filestats = os.stat(filepath)
                                if filestats.st_size > MAX_PAGELET_BYTES:
                                    raise Exception("File size (%d bytes) exceeds pagelet limit (%d bytes) for %s" % (filestats.st_size,  MAX_PAGELET_BYTES, filepath))
                                with open(filepath) as f:
                                    content = f.read()
                            else:
                                content = ""
                            headers["content_length"] = len(content)
                            if response_type == "create_blob":
                                # Encode create blob content to Base64
                                headers["x_gterm_encoding"] = "base64"
                                content = base64encode(content)

                        # TODO: use content to determine MIME type
                        basename, extension = os.path.splitext(filepath)
                        if "content_type" not in headers:
                            mimetype, encoding = mimetypes.guess_type(basename)
                            headers["content_type"] = mimetype
                        if "filetype" not in response_params:
                            if extension:
                                response_params["filetype"] = FILE_EXTENSIONS.get(extension[1:].lower(), "")
                            else:
                                response_params["filetype"] = ""
                    except Exception, excp:
                        ##traceback.print_exc()
                        content = "ERROR in reading data from file '%s': %s" % (filepath, excp)
                        response_type = "error_message"
                        headers["x_gterm_response"] = response_type
                        headers["x_gterm_parameters"] = {}
                        headers["content_type"] = "text/plain"

                if not response_type or response_type == "pagelet":
                    # Raw html display; append to scroll buffer
                    row_params = ["pagelet", headers["x_gterm_parameters"] or {}]
                    screen_buf.scroll_buf_up("", None, markup=content, row_params=row_params)
                    offset, directive, opt_dict = gtermapi.parse_gterm_directive(content)
                elif response_type == "create_blob":
                    # Note: blob content should be Base64 encoded
                    del headers["x_gterm_response"]
                    del headers["x_gterm_parameters"]
                    blob_id = response_params.get("blob")
                    if not blob_id:
                        logging.warning("No blob_id for blob data")
                    elif "content_length" not in headers:
                        logging.warning("No content_length specified for create_blob")
                    else:
                        # Note: blob content should be Base64 encoded
                        self.create_blob(blob_id, content, headers=headers)
                elif response_type == "frame_msg":
                    self.screen_callback(self.term_name, "", "frame_msg",
                     [response_params.get("user",""), response_params.get("frame",""), content])
                elif response_type == "save_notebook":
                    if self.note_cells:
                        filepath = response_params.get("filepath", "")
                        self.save_notebook(filepath, params=response_params)
                elif response_type == "open_notebook":
                    if not self.note_start and not self.note_cells:
                        prompts = response_params.get("prompts", [])
                        if not prompts:
                            command = os.path.basename(self.command_path) if self.command_path else ""
                            if command in gtermapi.PROMPTS_LIST:
                                prompts = gtermapi.PROMPTS_LIST[command][:]
                        if prompts:
                            self.note_start = (prompts[0], filepath, prompts, content)
                        else:
                            self.note_start = (">>> ", filepath, [], content)
                else:
                    headers["content_length"] = len(content)
                    params = {"validated": self.gterm_validated, "headers": headers}
                    self.graphterm_output(params, content)
        self.gterm_code = None
        self.gterm_buf = None
        self.gterm_buf_size = 0
        self.gterm_validated = False
        self.gterm_entry_index = None
        return retval

    def create_blob(self, blob_id, content, headers=None):
        """ If headers, content should be base64 encoded.
            Else, content should be of the data URI form: "image/png;base64,<base64>"
        """
        if headers:
            content_type = headers.get("content_type", "")
        else:
            content_type, sep, tail = content.partition(";")
            encoding, sep2, content = tail.partition(",")
            if encoding != "base64":
                logging.warning("Invalid encoding for data URI: %s", encoding)
                return ""
            content_type = content_type.strip()
            headers = {"content_type": content_type}

        if "content_length" not in headers:
            headers["content_length"] = len(base64.b64decode(content))

        if self.note_cells and content_type.startswith("image/"):
            self.note_screen_buf.add_blob(blob_id, content_type, content)

        self.screen_callback(self.term_name, "", "create_blob",
                             [blob_id, headers, content])
        return content_type

    def graphterm_output(self, params={}, content="", response_id="", from_buffer=False):
        if not from_buffer:
            self.gterm_output_buf = [params, base64encode(content) if content else ""]
        elif not self.gterm_output_buf:
            return
        self.screen_callback(self.term_name, response_id, "graphterm_output", self.gterm_output_buf)

    def save_data(self, save_params, filedata):
        params = save_params.copy()
        status = ""
        location = params.get("x_gterm_location", "")
        filepath = params.get("x_gterm_filepath", "")
        encoded = params.get("x_gterm_encoding") == "base64"
        if location != "remote":
            filepath = os.path.expanduser(filepath)
            if not filepath.startswith("/"):
                if self.current_dir:
                    filepath = self.current_dir + "/" + filepath
                else:
                    filepath = getcwd(self.pid) + "/" + filepath
            try:
                with open(filepath, "w") as f:
                    f.write(base64.b64decode(filedata) if encoded else filedata)
            except Exception, excp:
                status = str(excp)

            if params.get("x_gterm_popstatus"):
                self.screen_callback(self.term_name, "", "save_status", [filepath, status])

            if params.get("x_gterm_sendstatus"):
                params["x_gterm_status"] = status
                self.pty_write(json.dumps(params)+"\n\n")
        else:
            send_data = filedata if encoded else base64encode(filedata)
            params["x_gterm_length"] = len(send_data)
            if send_data:
                params["x_gterm_digest"] = hashlib.md5(send_data).hexdigest()
            try:
                self.pty_write(json.dumps(params)+"\n\n")
                if send_data:
                    self.pty_write(send_data)
            except (IOError, OSError), excp:
                print >> sys.stderr, "lineterm: Error in writing to %s (%s %s)" % (self.term_name, excp.__class__, excp)
                self.screen_callback(self.term_name, "", "save_status", [filepath, str(excp)])
                

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
                                         "fileicon": "/_static/images/tango-folder.png",
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
        offset = prompt_offset(line, self.pdelim, (cwd, 0))

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
            remote_dest = bool(dest_comps and dest_comps[JHOST])
            if expect_url and remote_dest:
                dest_paste = create_file_uri(dest_comps)
            else:
                dest_paste = relative_file_url(dest_url, cwd)
            if command == "gcp" and not (file_url_comps and file_url_comps[JHOST]) and not remote_dest:
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
                    cmd_text = shell_unquote(text)
                    validated = False
                    if cmd_text.startswith("file://"):
                        cmd_text, sep, tail = cmd_text[len("file://"):].partition("?")
                        if cmd_text.startswith("local/"):
                            cmd_text = cmd_text[len("local"):]
                        elif not cmd_text.startswith("/"):
                            raise Exception("Command '%s' not valid" % text)
                        validated = tail and tail == ("hmac="+gtermapi.file_hmac(cmd_text, self.shared_secret))
                    if not pre_line and not validated and not which(cmd_text, add_path=[Exec_path]):
                        # Check for command in path only if no text in line
                        # NOTE: Can use blank space in command line to disable this check
                        raise Exception("Command '%s' not found" % text)
                    command_prefix = shell_quote(cmd_text)
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
            text = shell_quote(text)
            if expect_filename and command_prefix.find("%(path)") >= 0:
                paste_text = command_prefix.replace("%(path)", text)
            else:
                paste_text = command_prefix+space_prefix+text+" "
            if dest_paste:
                if paste_text and paste_text[-1] != " ":
                    paste_text += " "
                paste_text += shell_quote(dest_paste)
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
        nbytes = len(data)
        offset = 0
        while offset < nbytes:
            # Need to break data up into chunks; otherwise it hangs the pty
            count = min(CHUNK_BYTES, nbytes-offset)
            retry = 50
            while count > 0:
                try:
                    sent = os.write(self.fd, data[offset:offset+count])
                    if not sent:
                        raise Exception("Failed to write to terminal")
                    offset += sent
                    count -= sent
                except OSError, excp:
                    if excp.errno != errno.EAGAIN:
                        raise excp
                    retry -= 1
                    if retry > 0:
                        time.sleep(0.01)
                    else:
                        raise excp

    def pty_read(self, data):
        if self.trim_first_prompt:
            self.trim_first_prompt = False
            # Fix for the very first prompt not being set
            if data.startswith("> "):
                data = data[2:]
            elif data.startswith("\r\x1b[K> "):
                data = data[6:]
        self.write(data)
        reply = self.read()
        if reply:
            # Send terminal response
            os.write(self.fd, reply)
        if self.note_input or self.note_expect_prompt or self.note_start:
            line = dump(self.peek(self.cursor_y, 0, self.cursor_y, self.width), trim=True, encoded=True)
            if self.note_input or self.note_expect_prompt:
                if self.note_shell:
                    prompt_found = bool(prompt_offset(line, self.pdelim, self.main_screen.meta[0]))
                else:
                    prompt_found = any(line.startswith(prompt) for prompt in self.note_prompts)
                if prompt_found:
                    # Prompt found
                    if self.note_input:
                        # transmit buffered notebook cell line
                        os.write(self.fd, self.note_input.pop(0)+"\n")
                        self.note_expect_prompt = not self.note_input
                    else:
                        self.note_expect_prompt = False
                        self.note_found_prompt = True
            elif self.note_start and line.startswith(self.note_start[0]):
                self.open_notebook(self.note_start[1], prompts=self.note_start[2], content=self.note_start[3])

class Multiplex(object):
    def __init__(self, screen_callback, command=None, shared_secret="",
                 host="", server_url="", term_type="linux", api_version="",
                 widget_port=0, prompt_list=[], lc_export=False, logfile="", app_name="graphterm"):
        """ prompt_list = [prefix, suffix, format, remote_format]
        """
        ##signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        self.screen_callback = screen_callback
        self.command = command
        self.shared_secret = shared_secret
        self.host = host
        self.server_url = server_url
        self.prompt_list = prompt_list
        self.pdelim = prompt_list[:2] if len(prompt_list) >= 2 else []
        self.term_type = term_type
        self.api_version = api_version
        self.widget_port = widget_port
        self.lc_export = lc_export
        self.logfile = logfile
        self.app_name = app_name
        self.proc = {}
        self.lock = threading.RLock()
        self.thread = threading.Thread(target=self.loop)
        self.alive = 1
        self.check_kill_idle = False
        self.name_count = 0
        self.thread.start()

    def terminal(self, term_name=None, height=25, width=80, winheight=0, winwidth=0, parent="", command=""):
        """Return (tty_name, cookie) for existing or newly created pty"""
        command = command or self.command
        with self.lock:
            if term_name:
                term = self.proc.get(term_name)
                if term:
                    self.set_size(term_name, height, width, winheight, winwidth)
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

            term_dir = ""
            if parent:
                parent_term = self.proc.get(parent)
                if parent_term:
                    term_dir = parent_term.current_dir or ""

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
                        if var == "PATH" and Exec_path not in env[var]:
                            # Prepend app bin directory to path
                            env[var] = Exec_path + ":" + env[var]
                env["COLUMNS"] = str(width)
                env["LINES"] = str(height)
                env.update( dict(self.term_env(term_name, cookie, height, width, winheight, winwidth)) )

                if term_dir:
                    try:
                        os.chdir(term_dir)
                    except Exception:
                        term_dir = ""
                if not term_dir:
                    # cd to HOME
                    os.chdir(os.path.expanduser("~"))
                os.execvpe(cmd[0], cmd, env)
            else:
                global Exec_errmsg
                fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
                self.proc[term_name] = Terminal(term_name, fd, pid, self.screen_callback,
                                                height=height, width=width,
                                                winheight=winheight, winwidth=winwidth,
                                                cookie=cookie, host=self.host,
                                                shared_secret=self.shared_secret,
                                                pdelim=self.pdelim, logfile=self.logfile)
                self.set_size(term_name, height, width, winheight, winwidth)
                if not is_executable(Gls_path) and not Exec_errmsg:
                    Exec_errmsg = True
                    self.screen_callback(term_name, "", "alert", ["File %s is not executable. Did you 'sudo gterm_setup' after 'sudo easy_install graphterm'?" % Gls_path])
                return term_name, cookie

    def term_env(self, term_name, cookie, height, width, winheight, winwidth, export=False):
        env = []
        env.append( ("TERM", self.term_type or TERM_TYPE) )
        env.append( ("GRAPHTERM_COOKIE", str(cookie)) )
        env.append( ("GRAPHTERM_SHARED_SECRET", self.shared_secret) )
        env.append( ("GRAPHTERM_PATH", "%s/%s" % (self.host, term_name)) )
        dimensions = "%dx%d" % (width, height)
        if winwidth or winheight:
            dimensions += ";%dx%d" % (winwidth, winheight)
        env.append( ("GRAPHTERM_DIMENSIONS", dimensions) )

        if self.server_url:
            env.append( ("GRAPHTERM_URL", self.server_url) )

        if self.api_version:
            env.append( ("GRAPHTERM_API", self.api_version) )

        if self.widget_port:
            env.append( ("GRAPHTERM_SOCKET", "/dev/tcp/localhost/%d" % self.widget_port) )

        prompt_fmt, export_prompt_fmt = "", ""
        if self.prompt_list:
            prompt_fmt = self.prompt_list[0]+self.prompt_list[2]+self.prompt_list[1]+" "
            if len(self.prompt_list) >= 4:
                export_prompt_fmt = self.prompt_list[0]+self.prompt_list[3]+self.prompt_list[1]+" "
            else:
                export_prompt_fmt = prompt_fmt
            env.append( ("GRAPHTERM_PROMPT", export_prompt_fmt if export else prompt_fmt) )
            ##env.append( ("PROMPT_COMMAND", "export PS1=$GRAPHTERM_PROMPT; unset PROMPT_COMMAND") )
            cmd_fmt = EXPT_PROMPT_CMD if export else BASH_PROMPT_CMD
            env.append( ("PROMPT_COMMAND", cmd_fmt % (GRAPHTERM_SCREEN_CODES[0], GRAPHTERM_SCREEN_CODES[0]) ) )

        env.append( ("GRAPHTERM_DIR", File_dir) )

        if self.lc_export:
            # Export some environment variables as LC_* (hack to enable SSH forwarding)
            env_dict = dict(env)
            env.append( ("LC_GRAPHTERM_EXPORT", socket.getfqdn() or "unknown") )
            if export_prompt_fmt:
                env.append( ("LC_GRAPHTERM_PROMPT", export_prompt_fmt) )
                env.append( ("LC_PROMPT_COMMAND", env_dict["PROMPT_COMMAND"]) )
            for name in LC_EXPORT_ENV:
                if name in env_dict:
                    env.append( ("LC_"+name, env_dict[name]) )
        return env

    def export_environment(self, term_name, profile=False):
        term = self.proc.get(term_name)
        if term:
            if profile:
                try:
                    with open(Exec_path+"/gprofile") as f:
                        content = f.read()
                    term.pty_write('''[[ "$PATH" != */graphterm/* ]] && cat << 'END_OF_FILE' >> ~/.bash_profile\n%s\nEND_OF_FILE\n''' % content)
                except Exception:
                    term.pty_write('## Failed to read file %s\n' % (Exec_path+"/gprofile"))
                return
            term.pty_write('[ "$GRAPHTERM_COOKIE" ] || export GRAPHTERM_EXPORT="%s"\n' % (socket.getfqdn() or "unknown",))
            for name, value in self.term_env(term_name, term.cookie, term.height, term.width,
                                             term.winheight, term.winwidth, export=True):
                try:
                    if name in ("GRAPHTERM_DIR",):
                        term.pty_write( ('[ "$%s" ] || ' % name) + ("export %s='%s'\n" % (name, value)) )
                    else:
                        term.pty_write( "export %s='%s'\n" % (name, value) )  # Keep inner single quotes to handle PROMPT_COMMAND
                except Exception:
                    print >> sys.stderr, "lineterm: Error exporting environment to %s" % term_name
                    break
            term.pty_write('[[ "$PATH" != */graphterm/* ]] && [ -d "$GRAPHTERM_DIR" ] && export PATH="$GRAPHTERM_DIR/%s:$PATH"\n' % BINDIR)

    def set_size(self, term_name, height, width, winheight=0, winwidth=0):
        # python bug http://python.org/sf/1112949 on amd64
        term = self.proc.get(term_name)
        if term:
            term.resize(height, width, winheight=winheight, winwidth=winwidth)
            # Hack for buggy TIOCSWINSZ handling: treat large unsigned positive int32 values as negative (same bits)
            winsz = termios.TIOCSWINSZ if termios.TIOCSWINSZ < 0 else struct.unpack('i',struct.pack('I',termios.TIOCSWINSZ))[0]
            fcntl.ioctl(term.fd, winsz, struct.pack("HHHH",height,width,0,0))

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
                term.pty_read(data)
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
            except (IOError, OSError), excp:
                print >> sys.stderr, "lineterm: Error in writing to %s (%s %s); closing it" % (term_name, excp.__class__, excp)
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

    def save_data(self, term_name, save_params, filedata):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return
            term.save_data(save_params, filedata)

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

    def open_notebook(self, term_name, filepath, prompts, content):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.open_notebook(filepath, prompts, content)

    def close_notebook(self, term_name, discard):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.close_notebook(discard)

    def save_notebook(self, term_name, filepath, input_data, params):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.save_notebook(filepath, input_data, params)

    def add_cell(self, term_name, new_cell_type, init_text, before_cell_number):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.add_cell(new_cell_type, init_text, before_cell_number)

    def select_cell(self, term_name, cell_index, move_up):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.select_cell(cell_index, move_up)

    def select_page(self, term_name, move_up, endpoint, slide):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.select_page(move_up, endpoint, slide)

    def move_cell(self, term_name, move_up):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.move_cell(move_up)

    def update_type(self, term_name, cell_type):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.update_type(cell_type)

    def delete_cell(self, term_name, move_up):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.delete_cell(move_up)

    def merge_above(self, term_name):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.merge_above()

    def complete_cell(self, term_name, incomplete):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.complete_cell(incomplete)

    def update_cell(self, term_name, cur_index, execute, input_data):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.update_cell(cur_index, execute, input_data)

    def erase_output(self, term_name, all_cells):
        with self.lock:
            term = self.proc.get(term_name)
            if not term:
                return ""
            return term.erase_output(all_cells)

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
            for row_num, row_offset, row_dir, row_params, row_span, row_markup in update_rows:
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
