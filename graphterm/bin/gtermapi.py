"""
gtermapi: API module for gterm-aware programs
"""

# The code in this particular file (gtermapi.py) is
# released in the public domain, so that it maybe
# re-used in other projects without any restrictions.
# It was developed as part of the GraphTerm project
#    https://github.com/mitotic/graphterm

import base64
import StringIO
import hashlib
import hmac
import json
import mimetypes
import os
import Queue
import random
import subprocess
import sys
import termios
import threading
import tty
import uuid

from optparse import OptionParser

API_VERSION = "0.32.0"
API_MIN_VERSION = "0.31"

HEX_DIGITS = 16


Version_str, sep, Min_version_str = os.getenv("GRAPHTERM_API", "").partition("/")

Export_host = os.getenv("GRAPHTERM_EXPORT", "")
Lterm_cookie = os.getenv("GRAPHTERM_COOKIE", "")
Shared_secret = os.getenv("GRAPHTERM_SHARED_SECRET", "")
Path = os.getenv("GRAPHTERM_PATH", "")
URL = os.getenv("GRAPHTERM_URL", "http://localhost:8900")

Host, Session = Path.split("/") if Path else ("", "") 
Html_escapes = ["\x1b[?1155;%sh" % Lterm_cookie,
                "\x1b[?1155l"]

App_dir = os.path.join(os.path.expanduser("~"), ".graphterm")
Gterm_secret_file = os.path.join(App_dir, "graphterm_secret")

def split_version(version_str):
    """Splits version string "major.minor.revision" and returns list of ints [major, minor]"""
    if not version_str:
        return [0, 0]
    return map(int, version_str.split(".")[:2])

Min_version = split_version(Min_version_str or Version_str) 
Api_version = split_version(API_VERSION)

def wrap(html, headers={}):
    """Wrap html, with headers, between escape sequences"""
    return Html_escapes[0] + json.dumps(headers) + "\n\n" + html + Html_escapes[1]

def write(data):
    """Write data to stdout and flush"""
    if Api_version < Min_version:
        raise Exception("Obsolete API version %s (need %d.%d+)" % (API_VERSION, Min_version[0], Min_version[1]))

    sys.stdout.write(data)
    sys.stdout.flush()

def wrap_write(content, headers={}):
    """Wrap content, with headers, and write to stdout"""
    write(wrap(content, headers=headers))

def write_html(html, display="block", dir="", add_headers={}):
    """Write html pagelet to stdout"""
    params = {"display": display,
              "scroll": "top",
              "current_directory": dir}
    params.update(add_headers)
    html_headers = {"content_type": "text/html",
                    "x_gterm_response": "pagelet",
                    "x_gterm_parameters": params
                    }
    wrap_write(html, headers=html_headers)

def write_form(html, command="", dir=""):
    """Write form pagelet to stdout"""
    html_headers = {"content_type": "text/html",
                    "x_gterm_response": "pagelet",
                    "x_gterm_parameters": {"display": "fullpage", "scroll": "top", "current_directory": dir,
                                           "form_input": True, "form_command": command}
                    }
    wrap_write(html, headers=html_headers)

def write_blank(display="fullpage"):
    """Write blank pagelet to stdout"""
    write_html("", display=display)

def open_url(url, target="_blank"):
    """Open url in new window"""
    url_headers = {"x_gterm_response": "open_url",
                   "x_gterm_parameters": {"url": url, "target": target}
                   }
    wrap_write("", headers=url_headers)

def get_file_url(filepath, relative=False, exists=False):
    """Construct file URL by expanding/normalizing filepath, with hmac cookie suffix.
    If relative, return '/file/host/path'
    """
    if not filepath.startswith("/"):
        filepath = os.path.normcase(os.path.abspath(os.path.expanduser(filepath)))
        
    if exists and not os.path.exists(filepath):
        return None

    filehmac = "?hmac="+hmac.new(str(Shared_secret), filepath, digestmod=hashlib.sha256).hexdigest()[:HEX_DIGITS]
    if relative:
        return "/file/" + Host + filepath + filehmac
    else:
        return "file://" + ("" if Host == "local" else Host) + filepath + filehmac

def make_blob_url(blob_id=""):
    blob_id = blob_id or str(uuid.uuid4())
    return (blob_id, "/blob/"+Host+"/"+blob_id)

def create_blob(content=None, from_file="", content_type="", blob_id=""):
    """Create blob and returns URL to blob"""
    if content is None:
        if not from_file:
            print >> sys.stderr, "Error: No content and no file to create blob"
            return None
        fullname = os.path.expanduser(from_file)
        filepath = os.path.normcase(os.path.abspath(fullname))

        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            print >> sys.stderr, "File %s not found" % from_file
            return None

        try:
            with open(filepath) as fp:
                content = fp.read()
        except Exception, excp:
            print >> sys.stderr, "Error in reading file %s: %s" % (from_file, excp)
            return None

        if not content_type:
            content_type, encoding = mimetypes.guess_type(filepath)

    content_type = content_type or "text/html"
    params = {}
    blob_id, blob_url = make_blob_url(blob_id)
    params["blob_id"] = blob_id
    headers = {"x_gterm_response": "create_blob",
               "x_gterm_parameters": params,
               "content_type": content_type,
               "content_length": len(content)
               }

    wrap_write(base64.b64encode(content), headers=headers)
    return blob_url
    
class BlobStringIO(StringIO.StringIO):
    def __init__(self, content_type="text/html"):
        self.content_type = content_type
        self.blob_id, self.blob_url = make_blob_url()
        StringIO.StringIO.__init__(self)

    def close(self):
        blob_url = create_blob(self.getvalue(), content_type=self.content_type, blob_id=self.blob_id)
        StringIO.StringIO.close(self)
        assert blob_url == self.blob_url
        return blob_url
        
def preload_images(urls):
    params = {"urls": urls}
    headers = {"x_gterm_response": "preload_images",
               "x_gterm_parameters": params
               }

    wrap_write("", headers=headers)

FILE_URI_PREFIX = "file://"
FILE_PREFIX = "/file/"

JSERVER = 0
JHOST = 1
JFILENAME = 2
JFILEPATH = 3
JQUERY = 4

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

def read_form_input(form_html):
    write_form(form_html)
    saved_settings = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setraw(sys.stdin.fileno())
        form_data = raw_input()
        return json.loads(form_data) if form_data.strip() else None
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, saved_settings)

Form_template =  """<div id="gterm-form-%s" class="gterm-form"><span class="gterm-form-title">%s</span> %s
<input id="gterm-form-command-%s" class="gterm-form-button gterm-form-command" type="submit" data-gtermformnames="%s"></input>  <input class="gterm-form-button gterm-form-cancel" type="button" value="Cancel"></input>
</div>"""


Label_template = """<span class="gterm-form-label %s" data-gtermhelp="%s">%s</span>"""

Input_text_template = """<input id="gterm_%s_%s" name="%s" class="gterm-form-input%s" type="text" value="%s" autocomplete="off" %s></input>"""

Input_checkbox_template = """<input id="gterm_%s_%s" name="%s" class="gterm-form-input%s" type="checkbox" %s></input>"""

Select_template = """<select id="gterm_%s_%s" name="%s" class="gterm-form-input%s" size=1>
%s
</select>"""
Select_option_template = """<option value="%s" %s>%s</option>"""

class FormParser(object):
    def __init__(self, usage="", title="", command="", noparser=False):
        self.usage = usage
        self.title = title
        self.command = command
        self.parser = None if noparser else OptionParser(usage=usage)
        self.arg_list = []
        self.opt_list = []

    def get_usage(self):
        return self.parser.get_usage() if self.parser else self.usage
    
    def add_argument(self, default_value="", label="", help=""):
        iarg = len(self.arg_list) + 1
        self.arg_list.append(("arg%d" % iarg, default_value, "", label, help))

    def add_option(self, name, default_value="", short="", label="", help="", raw=False):
        if name.startswith("arg") and name[3:].isdigit():
            raise Exception("Option name %s conflicts with argument name" % name)

        if not raw:
            self.opt_list.append((name, default_value, short, label, help))

        if self.parser:
            default = default_value[0] if isinstance(default_value, (list, tuple)) else default_value
            short = "-" + short if short else ""
            if isinstance(default, bool):
                self.parser.add_option(short, "--"+name, dest=name, default=default,
                                  help=help, action=("store_false" if default else "store_true"))
            else:
                self.parser.add_option(short, "--"+name, dest=name, default=default,
                                       help=help)

    def create_input_html(self, id_suffix):
        input_list = []
        first_arg = True
        arg_count = len(self.arg_list)
        for j, opt_info in enumerate(self.arg_list + self.opt_list):
            opt_name, opt_default, opt_short, opt_label, opt_help = opt_info
            if opt_label:
                label = opt_label
            elif j < arg_count:
                label = ""
            elif isinstance(opt_default, bool):
                label = "--"+opt_name
            else:
                label = "--"+opt_name+"="

            if j == arg_count:
                input_list.append("<table>\n")

            label_html = Label_template % ("gterm-help-link" if opt_help else "", opt_help, label)
            attrs = ""
            classes = ""
            if j < arg_count:
                classes += ' gterm-input-arg'
            if isinstance(opt_default, bool):
                if opt_default:
                    attrs += " checked"
                input_html = Input_checkbox_template % (id_suffix, opt_name, opt_name, classes, attrs)

            elif isinstance(opt_default, (basestring, float, int, long)):
                if first_arg:
                    attrs += ' autofocus="autofocus"'
                input_html = Input_text_template % (id_suffix, opt_name, opt_name, classes, str(opt_default).replace('"', "&quot;"), attrs)

            elif isinstance(opt_default, (list, tuple)):
                opt_list = []
                opt_sel = "selected"
                for opt_value in opt_default:
                    opt_list.append(Select_option_template % (opt_value, opt_sel, opt_value or "Select..."))
                    opt_sel = ""
                input_html = Select_template % (id_suffix, opt_name, opt_name, classes, "\n".join(opt_list))

            if j >= arg_count:
                input_list.append("<tr><td>%s<td>%s\n" % (label_html, input_html))
            else:
                input_list.append("<div>%s%s</div>\n" % (label_html, input_html) )

            first_arg = False

        if self.opt_list:
            input_list.append("</table>\n")
            
        return "\n".join(input_list)

    def create_form(self, id_suffix=None):
        if not id_suffix:
            id_suffix = "1%09d" % random.randrange(0, 10**9)    
        opt_names = ",".join(x[0] for x in (self.arg_list+self.opt_list))
        input_html = self.create_input_html(id_suffix)
        return Form_template % (id_suffix, self.title, input_html, id_suffix, opt_names) 
        
    def parse_args(self):
        if len(sys.argv) < 2:
            if sys.stdout.isatty() and Lterm_cookie:
                assert self.command
                write_form(self.create_form(), command=self.command)
            else:
                print >> sys.stderr, self.get_usage()
            sys.exit(1)

        if self.parser:
            return self.parser.parse_args()
        else:
            return None, None

    def read_input(self, trim=False):
        assert not self.command and sys.stdout.isatty()
        form_values = read_form_input(self.create_form())
        if form_values and trim:
            form_values = dict((k,v.strip()) for k, v in form_values.items())
        return form_values


def command_output(command_args, **kwargs):
	""" Executes a command and returns the string tuple (stdout, stderr)
	keyword argument timeout can be specified to time out command (defaults to 1 sec)
	"""
	timeout = kwargs.pop("timeout", 1)
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

def open_browser(url):
    if sys.platform.startswith("linux"):
        command_args = ["xdg-open", url]
    else:
        command_args = ["open", url]

    return command_output(command_args, timeout=5)

