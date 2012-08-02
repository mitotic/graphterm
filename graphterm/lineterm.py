#!/usr/bin/env python

""" Lineterm: Line-oriented pseudo-tty wrapper
Derived from the public-domain Ajaxterm code, v0.11 (2008-11-13).
  https://github.com/antonylesuisse/qweb
  http://antony.lesuisse.org/software/ajaxterm/
The contents of this file remain in the public-domain.
"""

from __future__ import with_statement

import array,cgi,copy,fcntl,glob,logging,mimetypes,optparse,os,pty,random,re,signal,select,sys,threading,time,termios,tty,struct,pwd

import base64
import json
import Queue
import shlex
import subprocess
import traceback

MAX_SCROLL_LINES = 500

IDLE_TIMEOUT = 300      # Idle timeout in seconds
UPDATE_INTERVAL = 0.05  # Fullscreen update time interval
TERM_TYPE = "linux"     # "screen" would be a better default terminal, but arrow keys do not always work

COPY_ENV = ["HOME", "LOGNAME", "PATH", "SECURITYSESSIONID", "SHELL", "SSH_AUTH_SOCK", "USER", "USERNAME"]

ALTERNATE_SCREEN_CODES = (47, 1047, 1049) # http://rtfm.etla.org/xterm/ctlseq.html
GRAPHTERM_SCREEN_CODES = (1150, 1155)

FILE_EXTENSIONS = {"css": "css", "htm": "html", "html": "html", "js": "javascript", "py": "python",
                   "xml": "xml"}

FILE_COMMANDS = set(["cd", "cp", "mv", "rm", "gcp", "gimages", "gls", "gopen", "gvi"])
REMOTE_FILE_COMMANDS = set(["gcp"])
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
Exec_path = os.path.join(os.path.dirname(__file__), BINDIR)
Gls_path = os.path.join(Exec_path, "gls")
Exec_errmsg = False

def dump(data, trim=False):
	"""Return string from array of int data, trimming NULs, if need be"""
	line = "".join(chr(i & 255) for i in data)
	return line.rstrip("\x00") if trim else line

def prompt_offset(line, prompt, meta=None):
	"""Return offset at end of prompt (not including trailing space), or zero"""
	offset = 0
	if meta or (prompt and prompt[0] and line.startswith(prompt[0])):
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
def split_file_uri(uri):
	"""Return triplet [hostname, filename, fullpath, query] for file://host/path URIs
	If not file URI, returns []
	"""
	if not uri.startswith(FILE_URI_PREFIX):
		return []
	host_path = uri[len(FILE_URI_PREFIX):]
	j = host_path.find("?")
	if j >= 0:
		query = host_path[j:]
		host_path = host_path[:j]
	else:
		query = ""
	comps = host_path.split("/")
	return [comps[0], comps[-1], "/"+"/".join(comps[1:]), query]
	
def relative_file_uri(file_uri, cwd):
	filepath = split_file_uri(file_uri)[2]
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
	fullpath = os.path.join(current_dir, text)
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
	if cmd.startswith("./") and current_dir:
		marked_up += path_markup(cmd[2:], current_dir, command=True)
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
	def __init__(self, prompt):
		self.prompt = prompt
		self.pre_offset = len(prompt[0]) if prompt else 0
		self.width = None
		self.height = None
		self.cursorx = None
		self.cursory = None
		self.main_screen = None
		self.alt_screen = None
		self.current_scroll_count = 0
		self.last_scroll_count = 0
		self.entry_index = 0
		self.scroll_lines = []
		self.cleared_current_dir = None
		self.cleared_last = False
		self.full_update = True

		# Init 0-256 to latin1 and html translation table
		self.trl1=""
		for i in range(256):
			if i==10:
				self.trl1+=chr(i)
			elif i<32:
				self.trl1+=" "
			elif i<127 or i>160:
				self.trl1+=chr(i)
			else:
				self.trl1+="?"
		self.trhtml=""
		for i in range(256):
			if i==0x0a or (i>32 and i<127) or i>160:
				self.trhtml+=chr(i)
			elif i<=32:
				self.trhtml+="\xa0"
			else:
				self.trhtml+="?"

	def reconnect(self):
		self.last_scroll_count = self.current_scroll_count - len(self.scroll_lines)
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
			current_dir = meta or ""
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
		   alt_screen=None, prompt=[]):
		""" Returns full_update, update_rows, update_scroll
		"""
		full_update = self.full_update
		self.full_update = False

		if width != self.width or height != self.height:
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

		self.cursorx = cursorx
		self.cursory = cursory
		self.main_screen = main_screen.make_copy() if main_screen else None
		self.alt_screen = alt_screen.make_copy() if alt_screen else None
		if self.last_scroll_count < self.current_scroll_count:
			update_scroll = self.scroll_lines[self.last_scroll_count-self.current_scroll_count:]
		else:
			update_scroll = []
		self.last_scroll_count = self.current_scroll_count
		return full_update, update_rows, update_scroll

	def dumplatin1(self, data, trim=False):
		return dump(data, trim=trim).translate(self.trl1)

	def dumprichtext(self, data, trim=False):
		span = ""
		span_list = []
		style_list = []
		span_style, span_bg, span_fg = 0x0007, -1, -1
		for i in data:
			q, c = divmod(i, 256)
			if span_style != q:
				if span:
					span_list.append((style_list, span.translate(self.trl1)))
					span = ""
				span_style = q
				style_list = []
				if span_style & 0x0008:
					style_list.append("bold")
				if span_style & 0x0700:
					style_list.append("inverse")
			span += chr(c)
		if span:
			if trim:
				span = span.rstrip("\x00")
			if span:
				span_list.append((style_list, span.translate(self.trl1)))
		return span_list

	def dumphtml(self, data, trim=False, color=1):
		h=self.height
		w=self.width
		r=""
		span=""
		span_bg,span_fg=-1,-1
		for i in range(h*w):
			q,c=divmod(data[i],256)
			if color:
				bg,fg=divmod(q,256)
			else:
				bg,fg=0,7
			if i==self.cursor_y*w+self.cursor_x:
				bg,fg=1,7
			if (bg!=span_bg or fg!=span_fg or i==h*w-1):
				if len(span):
					r+='<span class="f%d b%d">%s</span>'%(span_fg,span_bg,cgi.escape(span.translate(self.trhtml)))
				span=""
				span_bg,span_fg=bg,fg
			span+=chr(c)
			if i%w==w-1:
				span+='\n'
		r='<?xml version="1.0" encoding="ISO-8859-1"?><pre class="term">%s</pre>'%r
		if self.last_html==r:
			return '<?xml version="1.0"?><idem></idem>'
		else:
			self.last_html=r
#			print >> sys.stderr, "lineterm: dumphtml ", self
			return r

	def __repr__(self):
		d = self.dumplatin1(self.main_screen.data)
		r = ""
		for i in range(self.height):
			r += "|%s|\n"%d[self.width*i:self.width*(i+1)]
		return r

class Screen(object):
	def __init__(self, width, height, data=None, meta=None):
		self.width = width
		self.height = height
		self.data = data or array.array('i', [0x000000]*(width*height))
		self.meta = [None] * height

	def make_copy(self):
		return Screen(self.width, self.height, data=copy.copy(self.data), meta=copy.copy(self.meta))

class Terminal(object):
	def __init__(self, term_name, fd, pid, screen_callback, height=25, width=80, cookie=0, host="",
		     prompt=[], logfile=""):
		self.term_name = term_name
		self.fd = fd
		self.pid = pid
		self.screen_callback = screen_callback
		self.width = width
		self.height = height
		self.cookie = cookie
		self.host = host
		self.prompt = prompt
		self.logfile = logfile
		self.init()
		self.reset()
		self.output_time = time.time()
		self.screen_buf = ScreenBuf(prompt)
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
		self.style = 0x000700
		self.outbuf = ""
		self.last_html = ""
		self.active_rows = 0
		self.gterm_code = None
		self.gterm_buf = None
		self.gterm_entry_index = None
		self.gterm_validated = False

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
					saved_line = [len(line.rstrip('\x00')), self.main_screen.meta[0], self.main_screen.data[:min_width]]
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

	def reconnect(self):
		self.screen_buf.reconnect()
		self.needs_updating = True

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
		for cursor_y in range(scroll_rows):
			row = self.main_screen.data[self.width*cursor_y:self.width*cursor_y+self.width]
			self.screen_buf.scroll_buf_up(self.screen_buf.dumplatin1(row, trim=True),
						      self.main_screen.meta[cursor_y],
				                      offset=prompt_offset(dump(row), self.prompt, self.main_screen.meta[cursor_y]))

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

		alt_screen = self.alt_screen if self.alt_mode else None
		if not self.alt_mode:
			self.scroll_screen()

		full_update, update_rows, update_scroll = self.screen_buf.update(self.active_rows, self.width, self.height,
										 self.cursor_x, self.cursor_y,
										 self.main_screen,
										 alt_screen=alt_screen,
			                                                         prompt=self.prompt)
		pre_offset = len(self.prompt[0]) if self.prompt else 0
		self.screen_callback(self.term_name, "row_update",
				     [self.alt_mode, full_update, self.active_rows,
				      self.width, self.height,
				      self.cursor_x, self.cursor_y, pre_offset,
				      update_rows, update_scroll])

	def zero(self, y1, x1, y2, x2, screen=None):
		if screen is None: screen = self.screen
		w = self.width*(y2-y1) + x2 - x1 + 1
		z = array.array('i', [0x000000]*w)
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
					self.screen_buf.scroll_buf_up(self.screen_buf.dumplatin1(self.peek(self.scroll_top, 0, self.scroll_top, self.width), trim=True), self.screen.meta[self.scroll_top])
				self.scroll_up(self.scroll_top, self.scroll_bot)
				self.cursor_y = self.scroll_bot
			else:
				self.cursor_y = r

			if not self.alt_mode:
				self.active_rows = max(self.cursor_y+1, self.active_rows)

	def cursor_right(self):
		q, r = divmod(self.cursor_x+1, self.width)
		if q:
			self.cursor_eol = 1
		else:
			self.cursor_x = r

	def expect_prompt(self, current_directory):
		if not self.active_rows or self.cursor_y+1 == self.active_rows:
			self.screen.meta[self.cursor_y] = current_directory
	
	def echo(self, c):
		if self.logfile and self.logchars < MAX_LOG_CHARS:
			with open(self.logfile, "a") as logf:
				if not self.logchars:
					logf.write("TXT:")
				logf.write(c)
				self.logchars += 1
				if self.logchars == MAX_LOG_CHARS:
					logf.write("\n")
		if self.cursor_eol:
			self.cursor_down()
			self.cursor_x = 0
		self.screen.data[(self.cursor_y*self.width)+self.cursor_x] = self.style|ord(c)
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
				self.gterm_entry_index = self.screen_buf.entry_index+1
				if self.gterm_code != GRAPHTERM_SCREEN_CODES[0]:
					self.scroll_screen(self.active_rows)
					if self.logfile:
						with open(self.logfile, "a") as logf:
							logf.write("GTERMMODE\n")

		elif l[0] in ALTERNATE_SCREEN_CODES:
			self.alt_mode = True
			self.screen = self.alt_screen
			self.style = 0x000700
			self.zero_screen()
			if self.logfile:
				with open(self.logfile, "a") as logf:
					logf.write("ALTMODE\n")
		elif l[0] == 4:
			pass
#			print "insert on"

	def csi_l(self, l):
		"""Reset private mode"""
		if l[0] in GRAPHTERM_SCREEN_CODES:
			pass # No-op (mode already exited in escape)

		elif l[0] in ALTERNATE_SCREEN_CODES:
			self.alt_mode = False
			self.screen = self.main_screen
			self.style = 0x000700
			self.cursor_y = max(0, self.active_rows-1)
			self.cursor_x = 0
			if self.logfile:
				with open(self.logfile, "a") as logf:
					logf.write("NORMODE\n")
		elif l[0] == 4:
			pass
#			print "insert off"

	def csi_m(self, l):
		"""Select Graphic Rendition"""
		for i in l:
			if i==0 or i==39 or i==49 or i==27:
				# Normal
				self.style = 0x000700
			elif i==1:
				# Bold
				self.style = (self.style|0x000800)
			elif i==7:
				# Inverse
				self.style = 0x070000
			elif i>=30 and i<=37:
				# Foreground Black(30), Red, Green, Yellow, Blue, Magenta, Cyan, White
				c = i-30
				self.style = (self.style&0xff08ff)|(c<<8)
			elif i>=40 and i<=47:
				# Background Black(30), Red, Green, Yellow, Blue, Magenta, Cyan, White
				c = i-40
				self.style = (self.style&0x00ffff)|(c<<16)
#			else:
#				print >> sys.stderr, "lineterm: CSI style ignore",l,i
#		print >> sys.stderr, 'lineterm: style: %r %x'%(l, self.style)

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
#		if self.buf=='': print >> sys.stderr, "lineterm: ESC %r\n"%e

	def gterm_append(self, s):
		prefix, sep, suffix = s.partition('\x1b')
		self.gterm_buf.append(prefix)
		if not sep:
			return ""
		retval = sep + suffix
		# ESCAPE sequence encountered; terminate
		if self.gterm_code == GRAPHTERM_SCREEN_CODES[0]:
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
						with open(filepath) as f:
							content = f.read()
				        except Exception, excp:
						content = "ERROR in opening file '%s': %s" % (filepath, excp)
						headers["x_gterm_response"] = "error_message"
						headers["x_gterm_parameters"] = {}
						headers["content_type"] = "text/plain"
			elif response_type != "edit_file":
				# Display non-validated input as plain text
				headers["x_gterm_response"] = "pagelet"
				headers["x_gterm_parameters"] = {}
				try:
					import lxml.html
					content = lxml.html.fromstring(content).text_content()
					headers["content_type"] = "text/plain"
				except Exception:
					content = cgi.escape(content)
			
			if self.gterm_validated or response_type != "edit_file":
				headers["content_length"] = len(content)
				params = {"validated": self.gterm_validated, "headers": headers}
				self.screen_callback(self.term_name, "graphterm_output", [params,
                                     base64.b64encode(content) if content else ""])
		self.gterm_code = None
		self.gterm_buf = None
		self.gterm_validated = False
		self.gterm_entry_index = None
		return retval

	def save_file(self, filepath, filedata):
		status = ""
		try:
			with open(filepath, "w") as f:
				f.write(filedata)
		except Exception, excp:
			status = str(excp)
		self.screen_callback(self.term_name, "save_status", [filepath, status])

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
		directory = directory or self.screen.meta[self.active_rows-1] or getcwd(self.pid)
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
		self.screen_callback(self.term_name, "graphterm_output", [params, content])

	def click_paste(self, text, file_uri="", options={}):
		"""Paste text or filename (and command) into command line.
		Different behavior depending upon whether command line is empty or not.
		If not text, create text from filepath, normalizing if need be.
		options = {command: "", clear_last: 0/n, normalize: null/true/false, enter: false/true
		If clear_last and command line is empty, clear last entry (can also be numeric string).
		Normalize may be None (for default behavior), False or True.
		if enter, append newline to text.
		"""
		if not self.active_rows:
			# Not at command line
			return
		command = options.get("command", "")
		dest_uri = options.get("dest_uri", "")
		clear_last = options.get("clear_last", 0)
		normalize = options.get("normalize", None)
		enter = options.get("enter", False)

		line = dump(self.peek(self.active_rows-1, 0, self.active_rows-1, self.width), trim=True)
		cwd = self.screen.meta[self.active_rows-1] or getcwd(self.pid)
		offset = prompt_offset(line, self.prompt, cwd)

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
		expect_uri = (command in REMOTE_FILE_COMMANDS)
		if not text and file_uri:
			text = file_uri if expect_uri else split_file_uri(file_uri)[2]

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
			if pre_line and pre_line[0] == " ":
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
				if pre_line[-1] != " ":
					space_prefix = " "

		if cwd and normalize and expect_filename and file_uri:
			# Check if file URI represents subdirectory of CWD
			if expect_uri:
				text = file_uri
			else:
				normpath = relative_file_uri(file_uri, cwd)
				if not normpath.startswith("/"):
					text = normpath

		if text or command_prefix:
			text = text.replace(" ", "\\ ")
			if expect_filename and command_prefix.find("%(path)") >= 0:
				paste_text = command_prefix.replace("%(path)", text)
			else:
				paste_text = command_prefix+space_prefix+text+" "
			if dest_uri:
				if paste_text and paste_text[-1] != " ":
					paste_text += " "
				paste_text += dest_uri if expect_uri else relative_file_uri(dest_uri, cwd)
			if enter and offset and not pre_line and command:
				# Empty command line with pasted command
				paste_text += "\n"
			try:
				os.write(self.fd, paste_text)
			except Exception, excp:
				print >> sys.stderr, "lineterm: Error in click_paste: %s" % excp

	def write(self, s):
		self.output_time = time.time()
		if self.gterm_buf is not None:
			s = self.gterm_append(s)
		if not s:
			return
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

		
class Multiplex(object):
	def __init__(self, screen_callback, command=None, cookie=0, host="", prompt=[], logfile="",
		     term_type="linux", app_name="graphterm"):
		""" prompt = [prefix, format, suffix]
		"""
		##signal.signal(signal.SIGCHLD, signal.SIG_IGN)
		self.screen_callback = screen_callback
		self.command = command
		self.cookie = cookie
		self.host = host
		self.prompt = prompt
		self.logfile = logfile
		self.term_type = term_type
		self.app_name = app_name
		self.proc = {}
		self.lock = threading.RLock()
		self.thread = threading.Thread(target=self.loop)
		self.alive = 1
		self.check_kill_idle = False
		self.name_count = 0
		self.thread.start()

	def terminal(self, term_name=None, command="", height=25, width=80):
		"""Create new pty, return tty name, or just return name for existing pty"""
		command = command or self.command
		with self.lock:
			if not term_name:
				self.name_count += 1
				term_name = "tty%s" % self.name_count

			if term_name in self.proc:
				self.set_size(term_name, height, width)
				return term_name

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
				for var in COPY_ENV:
					val = os.getenv(var)
					if val is not None:
						env[var] = val
						if var == "PATH":
							# Prepend app bin directory to path
							env[var] = Exec_path + ":" + env[var]
				env["COLUMNS"] = str(width)
				env["LINES"] = str(height)
				env["TERM"] = self.term_type or TERM_TYPE
				env["GRAPHTERM_COOKIE"] = str(self.cookie)
				env["GRAPHTERM_HOST"] = str(self.host)
				if self.prompt:
					env["GRAPHTERM_PROMPT"] = "".join(self.prompt) + " "
					##env["PROMPT_COMMAND"] = "export PS1=$GRAPHTERM_PROMPT; unset PROMPT_COMMAND"
					env["PROMPT_COMMAND"] = 'export PS1=$GRAPHTERM_PROMPT; echo -n "\033[?%s;${GRAPHTERM_COOKIE}h$PWD\033[?%s;l"' % (GRAPHTERM_SCREEN_CODES[0], GRAPHTERM_SCREEN_CODES[0])

				# cd to HOME
 				os.chdir(os.path.expanduser("~"))
				os.execvpe(cmd[0], cmd, env)
			else:
				global Exec_errmsg
				fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
				self.proc[term_name] = Terminal(term_name, fd, pid, self.screen_callback,
								height=height, width=width,
								cookie=self.cookie, host=self.host,
					                        prompt=self.prompt, logfile=self.logfile)
				self.set_size(term_name, height, width)
				if not is_executable(Gls_path) and not Exec_errmsg:
					Exec_errmsg = True
					self.screen_callback(term_name, "errmsg", ["File %s is not executable. Did you 'sudo gterm_setup' after 'sudo easy_install graphterm'?" % Gls_path])
				return term_name

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
				os.write(term.fd, data)
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
				return term.screen_buf.dumplatin1(data, trim=trim)
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

	def click_paste(self, term_name, text, file_uri="", options={}):
		with self.lock:
			term = self.proc.get(term_name)
			if not term:
				return
			term.click_paste(text, file_uri=file_uri, options=options)

	def reconnect(self, term_name):
		with self.lock:
			term = self.proc.get(term_name)
			if not term:
				return
			term.reconnect()

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
	def screen_callback(term_name, command, arg):
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
			##	with open(Log_file, "a") as logf:
			##		logf.write("CALLBACK:(%d,%d) %d\n" % (cursorx, cursory, active_rows))
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
