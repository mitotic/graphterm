#!/usr/bin/env python

"""
gterm: API module for GraphTerm-aware programs; also serves as terminal launcher
"""

# The code in this particular file (gterm.py) is
# released in the public domain, so that it maybe
# re-used in other projects without any restrictions.
# It was developed as part of the GraphTerm project
#    https://github.com/mitotic/graphterm

import base64
import StringIO
import getpass
import hashlib
import hmac
import json
import logging
import mimetypes
import os
import Queue
import random
import re
import stat
import subprocess
import sys
import termios
import threading
import tty
import urllib
import urllib2
import urlparse
import uuid

from optparse import OptionParser

API_VERSION = "0.51.0"
API_MIN_VERSION = "0.51"

HEX_DIGITS = 16          # Digits to be retained for HMAC, auth_code etc
SIGN_HEXDIGITS = 16      # User-entered keys (should match packetserver setup)

GT_PREFIX = "GTERM_"

LOCAL_HOST = "local"

##SHELL_CMD = "bash -l"
SHELL_CMD = "/bin/bash"

DEFAULT_HTTP_PORT = 8900
DEFAULT_HOST_PORT = DEFAULT_HTTP_PORT - 1

WIDGET_BASE_PORT = 8000
NB_BASE_PORT = 10000

Bin_dir = os.path.dirname(__file__)

# Short prompt (long prompt with directory metadata fills most of row):
#    unique prompt prefix (maybe null), unique prompt suffix (non-null), prompt body, remote prompt body
DEFAULT_PROMPTS = ["", "$", "\W", "\h:\W"]

def env(name, default="", lc=False):
    if not lc:
        return os.getenv(GT_PREFIX+name, default)
    return os.getenv(GT_PREFIX+name, "") or os.getenv("LC_"+GT_PREFIX+name, default)

Version_str, sep, Min_version_str = env("API").partition("/")

Lterm_cookie = env("COOKIE", lc=True)
Export_host = env("EXPORT") or (not env("COOKIE") and os.getenv("LC_"+GT_PREFIX+"EXPORT", ""))
Path = env("PATH", lc=True)
Dimensions = env("DIMENSIONS", lc=True) # colsxrows[;widthxheight]
Shared_secret = env("SHARED_SECRET", lc=True)
URL = env("URL", "http://localhost:%d" % DEFAULT_HTTP_PORT)
Blob_server = env("BLOB_SERVER", "")

Server, _, Server_port = urlparse.urlparse(URL)[1].partition(":")
if Server_port:
    Server_port = int(Server_port)
else:
    Server_port = 443 if URL.startswith("https:") else 80

_, Host, Session = Path.split("/") if Path else ("", "", "") 
Html_escapes = ["\x1b[?1155;%sh" % Lterm_cookie,
                "\x1b[?1155l"]

INTERPRETERS = {"python": ("py", "python", (">>> ", "... ")),
                "ipython": ("py", "python", ("In ", "   ...: ", "   ....: ", "   .....: ", "   ......: ")), # Works up to 10,000 prompts
                "idl": ("pro", "idl", ("IDL> ",)),
                "ncl": ("ncl", "ncl", ("ncl ",)),
                "node": ("js", "javascript", ("> ", "... ", ".... ", "..... ", "...... ", "....... ", "........ ", "......... ")),
                "R": ("R", "R", ("> ", "+ ")),
                "bash": ("sh", "bash", ()),
            }

EXTENSIONS   = dict((prog, values[0]) for prog, values in INTERPRETERS.items())
LANGUAGES    = dict((prog, values[1]) for prog, values in INTERPRETERS.items())
PROMPTS_LIST = dict((prog, values[2]) for prog, values in INTERPRETERS.items() if values[2])
EXTN2LANG    = dict((values[0], values[1]) for prog, values in INTERPRETERS.items())
EXTN2PROG    = dict((values[0], prog) for prog, values in INTERPRETERS.items() if prog != "ipython")

PAGE_BREAK = "---"

BLOB_PATH = "_blob"
FILE_PATH = "_file"
STATIC_PATH = "_static"

BLOB_PREFIX = "/"+BLOB_PATH+"/"
FILE_PREFIX = "/"+FILE_PATH+"/"
STATIC_PREFIX = "/"+STATIC_PATH+"/"
FILE_URI_PREFIX = "file://"

SETUP_USER_CMD = os.path.join(Bin_dir, "gterm_user_setup")

DEFAULT_HOME_VOLUME = "/home"

APP_DIRNAME = ".graphterm"
APP_AUTH_FILENAME = "_gterm_auth.txt"
APP_EMAIL_FILENAME = "gterm_email.txt"
APP_GROUPCODE_FILENAME = "gterm_gcode.txt"
APP_GROUPS_FILENAME = "gterm_groups.json"
APP_PREFS_FILENAME = "gterm_prefs.json"
APP_SECRET_FILENAME = "gterm_secret"
SIGN_SEP = "|"

def get_app_dir(user=""):
    return os.path.join(os.path.expanduser("~"+user), APP_DIRNAME)
    
App_dir = get_app_dir() # For current user
App_email_file = os.path.join(App_dir, APP_EMAIL_FILENAME)
App_secret_file = os.path.join(App_dir, APP_SECRET_FILENAME)

def dashify(s, n=4):
    s = undashify(s)
    return "-".join(s[j:j+n] for j in range(0, len(s), n))

def undashify(s):
    return s.replace("-", "")

def auth_token(secret, connection_id, host, port, client_nonce, server_nonce):
    """Return (client_token, server_token)"""
    SIGN_SEP = "|"
    prefix = SIGN_SEP.join([connection_id, host.lower(), str(port), client_nonce, server_nonce]) + SIGN_SEP
    return [hmac.new(str(secret), prefix+conn_type, digestmod=hashlib.sha256).hexdigest()[:24] for conn_type in ("client", "server")]

def create_app_directory(appdir=App_dir):
    if not os.path.exists(appdir):
        try:
            # Create App directory
            os.mkdir(appdir, 0700)
        except OSError, excp:
            print >> sys.stderr, "Error in creating app directory %s: %s" % (appdir, excp)
    
    if os.path.isdir(appdir) and os.stat(appdir).st_mode != 0700:
        # Protect App directory
        os.chmod(appdir, 0700)

def is_user(username, home_volume=""):
    return os.path.exists((home_volume or DEFAULT_HOME_VOLUME)+"/"+username)

def read_email(appdir=App_dir):
    email_file = os.path.join(appdir, APP_EMAIL_FILENAME)
    if not os.path.exists(email_file):
        return ""
    try:
        with open(email_file) as f:
            return f.read().strip().lower()
    except Exception, excp:
        logging.warning("Error in reading email from %s: %s", email_file, excp)
        return ""

def write_email(addr, appdir=App_dir):
    email_file = os.path.join(appdir, APP_EMAIL_FILENAME)
    try:
        with open(email_file, "w") as f:
            f.write(addr+"\n")
            return email_file
    except Exception, excp:
        logging.error("Error in writing email to %s: %s", email_file, excp)
        return ""

def get_auth_filename(appdir=App_dir, user="", server=""):
    prefix = user or ""
    if server and server != "localhost":
        prefix += "@" + server
    return os.path.join(appdir, prefix+APP_AUTH_FILENAME)

def read_auth_code(appdir=App_dir, user="", server=""):
    auth_file = get_auth_filename(appdir=appdir, user=user, server=server)
    with open(auth_file) as f:
        comps = f.read().strip().split()
        auth_code = undashify(comps[0])
        port = int(comps[1]) if len(comps) > 1 else None
        assert auth_code, "Null authentication code in file "+auth_file
        return auth_code, port

def write_auth_code(code, appdir=App_dir, user="", server="", port=None):
    auth_file = get_auth_filename(appdir=appdir, user=user, server=server)
    with open(auth_file, "w") as f:
        f.write(dashify(code))
        if port and port != DEFAULT_HOST_PORT:
            f.write(" "+str(port))
        f.write("\n")
    os.chmod(auth_file, stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)

def clear_auth_code(appdir=App_dir, user="", server=""):
    auth_file = get_auth_filename(appdir=appdir, user=user, server=server)
    try:
        os.remove(auth_file)
    except Exception:
        pass

def read_groups(user=""):
    group_file = os.path.join(get_app_dir(user), APP_GROUPS_FILENAME)
    groups = {}
    membership = {}
    if os.path.exists(group_file):
        with open(group_file) as f:
            try:
                groups = json.loads(f.read())
                for group, members in groups.iteritems():
                    for member in members:
                        membership[member] = group
            except Exception, excp:
                sys.exit("Error in reading group from %s: %s" % (group_file, excp))
    return groups, membership

def read_prefs(user=""):
    prefs_file = os.path.join(get_app_dir(user), APP_PREFS_FILENAME)
    prefs = {}
    if os.path.exists(prefs_file):
        with open(prefs_file) as f:
            try:
                prefs = json.loads(f.read())
            except Exception, excp:
                logging.error("Error in reading prefs from %s: %s" % (prefs_file, excp))
    return prefs

def write_prefs(prefs_dict, user=""):
    prefs_file = os.path.join(get_app_dir(user), APP_PREFS_FILENAME)
    try:
        with open(prefs_file, "w") as f:
            f.write(json.dumps(prefs_dict)+"\n")
        return prefs_file, "Saved preferences"
    except Exception, excp:
        logging.error("Error in writing prefs to %s: %s", prefs_file, excp)
        return prefs_file, "ERROR in saving prefs"

def compute_hmac(key, message, hex_digits=HEX_DIGITS):
    return hmac.new(str(key), message, digestmod=hashlib.sha256).hexdigest()[:hex_digits]

def user_hmac(key, user, key_version=None):
    # Note: should use the same format as packetserver.RPCLink.sign_token
    return compute_hmac(key, str(key_version)+SIGN_SEP+user, hex_digits=SIGN_HEXDIGITS)

def file_hmac(filepath, host_secret):
    return compute_hmac(host_secret, filepath)

def split_version(version_str):
    """Splits version string "major.minor.revision" and returns list of ints [major, minor]"""
    if not version_str:
        return [0, 0]
    return map(int, version_str.split(".")[:2])

Min_version = split_version(Min_version_str or Version_str) 
Api_version = split_version(API_VERSION)

EMAIL_RE = re.compile(r'([\w\-\.\+]+@(\w[\w\-]+\.)+[\w\-]+)') # Simple regexp, but allows underscore in domain names

GTERM_DIRECTIVE_RE = re.compile(r"^\s*<!--gterm\s+(\w+)(\s.*)?-->")
def parse_gterm_directive(text):
    """Return (offset, directive, opt_dict)"""
    match = GTERM_DIRECTIVE_RE.match(text)
    if not match:
        return (0, "",{})
    # gterm directive
    offset = len(match.group(0))
    directive = match.group(1)
    opts = match.group(2) or ""
    opt_comps = opts.strip().split()
    opt_dict = {}
    while opt_comps:
        # Parse options
        opt_comp = opt_comps.pop(0)
        opt_name, sep, opt_value = opt_comp.partition("=")
        opt_dict[opt_name] = urllib.unquote(opt_value)

    return (offset, directive, opt_dict)

def wrap(html, headers={}):
    """Wrap html, with headers, between escape sequences"""
    return Html_escapes[0] + json.dumps(headers) + "\n\n" + html + Html_escapes[1]

def write(data, stderr=False):
    """Write data to stdout and flush"""
    if Api_version < Min_version:
        raise Exception("Obsolete API version %s (need %d.%d+)" % (API_VERSION, Min_version[0], Min_version[1]))

    if stderr:
        sys.stderr.write(data)
        sys.stderr.flush()
    else:
        sys.stdout.write(data)
        sys.stdout.flush()

def raw_wrap_write(html, stderr=False):
    """Wrap and write html, without headers, between escape sequences"""
    write(Html_escapes[0]+html+Html_escapes[1], stderr=stderr)

def wrap_write(content, headers={}, stderr=False):
    """Wrap content, with headers, and write to stdout"""
    write(wrap(content, headers=headers), stderr=stderr)

def wrap_encoded_file_or_data(filepath, content=None, headers={}, stderr=False):
    """Send local filepath or transmit remote Base64-encoded file content"""
    if content is None and (not Export_host or not filepath):
        # Local file or empty file
        wrap_write("", headers=headers, stderr=stderr)
    else:
        # Not local file
        if content is None:
            try:
                with open(filepath) as fp:
                    content = fp.read()
            except Exception, excp:
                print >> sys.stderr, "Error in reading file %s: %s" % (filepath, excp)
                return None

        headers.update({"x_gterm_encoding": "base64",
                        "content_length": len(content)
                        })
        b64_content = base64.b64encode(content)
        if content:
            headers["x_gterm_digest"] = hashlib.md5(b64_content).hexdigest()
        wrap_write(b64_content, headers=headers, stderr=stderr)

def write_html(html, stderr=False):
    """Write raw html to stdout"""
    html_headers = {"content_type": "text/html"}
    wrap_write(html, headers=html_headers, stderr=stderr)

def write_pagelet_old(html, display="block", dir="", add_headers={}, stderr=False):
    """Write html pagelet to stdout"""
    params = {"display": display,
              "scroll": "top",
              "current_directory": dir}
    params.update(add_headers)
    html_headers = {"content_type": "text/html",
                    "x_gterm_response": "pagelet",
                    "x_gterm_parameters": params
                    }
    wrap_write(html, headers=html_headers, stderr=stderr)

def write_pagelet(html, display="block", overwrite=False, dir="", add_headers={}, stderr=False):
    """Write scrollable and overwriteable html pagelet to stdout"""
    params = "scroll=top"
    if display:
        params += " display=" + urllib.quote(display)
    if overwrite:
        params += " overwrite=yes"
    if dir:
        params += " current_dir=" + urllib.quote(dir)
    for header, value in add_headers.iteritems():
        params += " " + header + "=" + urllib.quote(str(value))

    PAGELETFORMAT = '<!--gterm pagelet %s-->'
    prefix = PAGELETFORMAT % (params,)
    raw_wrap_write(prefix+html, stderr=stderr)

def write_form(html, command="", dir="", stderr=False):
    """Write form pagelet to stdout"""
    html_headers = {"content_type": "text/html",
                    "x_gterm_response": "pagelet",
                    "x_gterm_parameters": {"display": "fullpage", "scroll": "top", "current_directory": dir,
                                           "form_input": True, "form_command": command}
                    }
    wrap_write(html, headers=html_headers, stderr=stderr)

def write_blank_old(display="fullpage", stderr=False):
    """Write blank pagelet to stdout"""
    write_pagelet_old("", display=display, stderr=stderr)

def write_blank(display="fullpage", exit_page=False, stderr=False):
    """Write blank scrollable pagelet to stdout"""
    add_headers = {}
    if exit_page:
        add_headers["exit_page"] = "yes"
    write_pagelet("", display=display, overwrite=True, add_headers=add_headers, stderr=stderr)

def display_blockimg_old(url, overwrite=False, alt="", stderr=False):
    """Display block image in a sequence.
    New image display causes previous images to be hidden.
    Display of hidden images can be toggled by clicking.
    """
    alt_attr = ' alt="'+alt+'"' if alt else ''
    IMGFORMAT = '<span class="gterm-togglelink"><em>&lt;'+(alt or 'image')+'&gt;</em></span><img class="gterm-blockimg gterm-togglelink" src="%s"'+alt_attr+'><br>'
    add_headers = {"classes": "gterm-blockseq"}
    if overwrite:
        add_headers["block"] = "overwrite"
    write_pagelet_old(IMGFORMAT % url, add_headers=add_headers, stderr=stderr)

def display_blockimg(url, overwrite=False, toggle=False, alt="", stderr=False):
    """Display image from url, overwriting previous image, if desired.
    toggle allows images to be hidden by clicking.
    """
    blob_id = get_blob_id(url)
    params = ""
    if overwrite:
        params += " overwrite=yes"
    if blob_id:
        params += " blob=" + urllib.quote(blob_id)

    toggleblock_class = 'gterm-toggleblock' if toggle else ''
    togglelink_class = 'gterm-togglelink' if toggle else ''
    togglespan = '<span class="'+togglelink_class+'"><em>&lt;'+(alt or 'image')+'&gt;</em></span>' if toggle else ''
    alt_attr = ' alt="'+alt+'"' if alt else ''
    BLOCKIMGFORMAT = '<!--gterm pagelet %s--><div class="gterm-blockhtml '+toggleblock_class+'">'+togglespan+'<img class="gterm-blockimg '+togglelink_class+'" src="%s"'+alt_attr+'></div>'
    html = BLOCKIMGFORMAT % (params, url)
        
    raw_wrap_write(html, stderr=stderr)

def open_url(url, target="_blank", stderr=False):
    """Open url in new window"""
    url_headers = {"x_gterm_response": "open_url",
                   "x_gterm_parameters": {"url": url, "target": target}
                   }
    wrap_write("", headers=url_headers, stderr=stderr)

def auto_print(text):
    """Auto print line output from interpreter shell"""
    headers = {"x_gterm_response": "auto_print",
               "x_gterm_parameters": {}
               }
    wrap_write(text, headers=headers)

def in_ipython():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

def edit_file(filename="", dir="", content=None, create=False, editor="ace", stderr=False):
    """Edit file"""
    filepath = ""
    if filename:
        fullname = os.path.expanduser(filename)
        filepath = os.path.normcase(os.path.abspath(fullname))

        if content is None:
            if not os.path.exists(filepath):
                if create:
                    content = ""
                else:
                    print >> sys.stderr, "File %s not found" % filename
                    return None
            elif not os.path.isfile(filepath):
                print >> sys.stderr, "File %s not a plain file" % filename
                return None

    params = {"filepath": filepath, "editor": editor, "modify": True, "command": "", "current_directory": dir}
    if Export_host:
        params["location"] = "remote"

    headers = {"x_gterm_response": "edit_file",
               "x_gterm_parameters": params
               }

    wrap_encoded_file_or_data(filepath, content=content, headers=headers, stderr=stderr)

    if Export_host:
        errmsg, headers, content = receive_data(stderr=stderr)
        if errmsg:
            print >> sys.stderr, "Error in saving file:", errmsg
        else:
            if not filepath:
                filepath = headers.get("x_gterm_filepath", "")
            if filepath:
                with open(filepath, "w") as f:
                    f.write(content)
                print >> sys.stderr, "Saved ", filepath
            else:
                print >> sys.stderr, "Error in saving file: No file path"

def open_notebook(filename="", dir="", content=None, command_path="", prompts=[], stderr=False):
    """Open notebook"""
    filepath = ""
    if filename:
        fullname = os.path.expanduser(filename)
        filepath = os.path.normcase(os.path.abspath(fullname))

        if content is None and (not os.path.exists(filepath) or not os.path.isfile(filepath)):
            print >> sys.stderr, "File %s not found" % filename
            return None

    if not command_path:
        command_path = "ipython" if in_ipython() else "python"

    if not prompts and command_path:
        command = os.path.basename(command_path)
        if command in PROMPTS_LIST:
            prompts = PROMPTS_LIST[command][:]

    headers = {"x_gterm_response": "open_notebook",
               "x_gterm_parameters": {"filepath": filepath, "prompts": prompts, "current_directory": dir}
               }

    wrap_encoded_file_or_data(filepath, content=content, headers=headers, stderr=stderr)

def save_notebook(filename="", dir="", stderr=False):
    """Save notebook"""
    filepath = ""
    if filename:
        fullname = os.path.expanduser(filename)
        filepath = os.path.normcase(os.path.abspath(fullname))

    params = {"filepath": filepath, "current_directory": dir, "popstatus": "alert"}
    if Export_host:
        params["location"] = "remote"

    headers = {"x_gterm_response": "save_notebook",
               "x_gterm_parameters": params
               }
    wrap_write("", headers=headers, stderr=stderr)

    if Export_host:
        errmsg, headers, content = receive_data(stderr=stderr)
        if errmsg:
            print >> sys.stderr, "Error in saving notebook:", errmsg
        else:
            if not filepath:
                filepath = headers.get("x_gterm_filepath", "")
            if filepath:
                with open(filepath, "w") as f:
                    f.write(content)
                print >> sys.stderr, "Saved ", filepath
            else:
                print >> sys.stderr, "Error in saving notebook: No file path"

def menu_op(target, value=None, stderr=False):
    """Invoke menu operation"""
    headers = {"x_gterm_response": "menu_op",
               "x_gterm_parameters": {"target": target, "value": value}
               }
    wrap_write("", headers=headers, stderr=stderr)

def get_file_url(filepath, relative=False, exists=False, plain=False):
    """Construct file URL by expanding/normalizing filepath, with hmac cookie suffix.
    If relative, return '/_file/host/path'
    """
    if not filepath.startswith("/"):
        filepath = os.path.normcase(os.path.abspath(os.path.expanduser(filepath)))
        
    if exists and not os.path.exists(filepath):
        return None

    if plain and not os.path.isfile(filepath):
        return None

    filehmac = "?hmac="+file_hmac(filepath, Shared_secret)
    if relative:
        return FILE_PREFIX + Host + filepath + filehmac
    else:
        return "file://" + ("" if Host == "local" else Host) + filepath + filehmac

def make_blob_url(blob_id="", host=""):
    blob_id = blob_id or str(uuid.uuid4())
    return blob_id, get_blob_url(blob_id, host=host)

def get_blob_id(blob_url):
    if blob_url.startswith("/"):
        path = blob_url
    else:
        try:
            scheme, netloc, path, query, fragment = urlparse.urlsplit(import_url)
        except Exception, excp:
            return ""

    if path.startswith(BLOB_PREFIX):
        return path.split("/")[3]
    else:
        return ""

def get_blob_url(blob_id, host=""):
    host = host or Host
    assert host, "Null host for blob url"
    if "*" in Blob_server:
        subdomain = "blob-"+hmac.new("wildcard", blob_id, digestmod=hashlib.md5).hexdigest()[:12]
        return Blob_server.replace("*", subdomain)+BLOB_PREFIX+host+"/"+blob_id
    else:
        return Blob_server+BLOB_PREFIX+host+"/"+blob_id

def create_blob(content=None, from_file="", content_type="", blob_id="", stderr=False):
    """Create blob and returns URL to blob"""
    filepath = ""
    if from_file:
        fullname = os.path.expanduser(from_file)
        filepath = os.path.normcase(os.path.abspath(fullname))

        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            print >> sys.stderr, "File %s not found" % from_file
            return None
    elif content is None:
        print >> sys.stderr, "Error: No content and no file to create blob from"
        return None

    if not content_type and filepath:
        content_type, encoding = mimetypes.guess_type(filepath)

    blob_id, blob_url = make_blob_url(blob_id)
    params = dict(blob=blob_id, filepath=filepath)
    headers = {"x_gterm_response": "create_blob",
               "x_gterm_parameters": params,
               "content_type": content_type}

    wrap_encoded_file_or_data(filepath, content=content, headers=headers, stderr=stderr)
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
        
def preload_images(urls, stderr=False):
    params = {"urls": urls}
    headers = {"x_gterm_response": "preload_images",
               "x_gterm_parameters": params
               }

    wrap_write("", headers=headers, stderr=stderr)

JSERVER = 0
JHOST = 1
JFILENAME = 2
JFILEPATH = 3
JQUERY = 4

def split_file_url(url, check_host_secret=None):
	"""Return [protocol://server[:port], hostname, filename, fullpath, query] for file://host/path
        or http://server:port/_file/host/path, or /_file/host/path URLs.
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
            fhmac = "?hmac="+file_hmac(filepath, check_host_secret)
            if query.lower() == fhmac.lower():
                hostname = ""
	return [server_port, hostname, filename, filepath, query]

def read_form_input(form_html, stderr=False):
    write_form(form_html, stderr=stderr)

    assert sys.stdin.isatty()
    saved_settings = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setraw(sys.stdin.fileno())
        form_data = raw_input()
        return json.loads(form_data) if form_data.strip() else None
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, saved_settings)

def setup_logging(log_level=logging.ERROR, filename="", file_level=None):
    file_level = file_level or log_level
    logger = logging.getLogger()
    logger.setLevel(min(log_level, file_level))

    formatter = logging.Formatter("%(levelname).1s%(asctime)s %(module).8s.%(lineno).04d %(message)s",
                                  "%y%m%d/%H:%M")

    if logger.handlers:
        for handler in logger.handlers:
            handler.setLevel(log_level)
            handler.setFormatter(formatter)
    else:
        # Console handler
        chandler = logging.StreamHandler()
        chandler.setLevel(log_level)
        chandler.setFormatter(formatter)
        logger.addHandler(chandler)

    if filename:
        # File handler
        fhandler = logging.FileHandler(filename)
        fhandler.setLevel(file_level)
        fhandler.setFormatter(formatter)
        logger.addHandler(fhandler)

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

    def create_input_html(self, id_suffix, prefill_opts={}):
        input_list = []
        first_arg = True
        arg_count = len(self.arg_list)
        for j, opt_info in enumerate(self.arg_list + self.opt_list):
            opt_name, opt_default, opt_short, opt_label, opt_help = opt_info
            opt_curval = prefill_opts.get(opt_name, opt_default)
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
                if opt_curval:
                    attrs += " checked"
                input_html = Input_checkbox_template % (id_suffix, opt_name, opt_name, classes, attrs)

            elif isinstance(opt_default, (basestring, float, int, long)):
                if first_arg:
                    attrs += ' autofocus="autofocus"'
                input_html = Input_text_template % (id_suffix, opt_name, opt_name, classes, str(opt_curval).replace('"', "&quot;"), attrs)

            elif isinstance(opt_default, (list, tuple)):
                opt_list = []
                for opt_value in opt_default:
                    opt_sel = "selected" if opt_value == opt_curval else ""
                    opt_list.append(Select_option_template % (opt_value, opt_sel, opt_value or "Select..."))
                input_html = Select_template % (id_suffix, opt_name, opt_name, classes, "\n".join(opt_list))

            if j >= arg_count:
                input_list.append("<tr><td>%s<td>%s\n" % (label_html, input_html))
            else:
                input_list.append("<div>%s%s</div>\n" % (label_html, input_html) )

            first_arg = False

        if self.opt_list:
            input_list.append("</table>\n")
            
        return "\n".join(input_list)

    def create_form(self, id_suffix=None, prefill=None):
        """
        id_suffix: Form id suffix
        prefill: (options, args) for prefilling
        """
        if not id_suffix:
            id_suffix = "1%09d" % random.randrange(0, 10**9)
        prefill_opts = {}
        if prefill:
            for j, argval in enumerate(prefill[1]):
                prefill_opts["arg"+str(j+1)] = argval
            for opt_info in self.opt_list:
                if hasattr(prefill[0], opt_info[0]):
                    prefill_opts[opt_info[0]] = getattr(prefill[0], opt_info[0])
        opt_names = ",".join(x[0] for x in (self.arg_list+self.opt_list))
        input_html = self.create_input_html(id_suffix, prefill_opts=prefill_opts)
        return Form_template % (id_suffix, self.title, input_html, id_suffix, opt_names) 
        
    def parse_args(self, args=None, stderr=False):
        if sys.stdin.isatty() and args is None and (len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] == "-g")):
            stdfile = sys.stderr if stderr else sys.stdout
            if stdfile.isatty() and Lterm_cookie:
                assert self.command
                write_form(self.create_form(), command=self.command, stderr=stderr)
            elif not stderr:
                print >> sys.stderr, self.get_usage()
            sys.exit(1)

        if self.parser:
            return self.parser.parse_args(args=args)
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

def open_browser(url, browser=""):
    if sys.platform.startswith("linux"):
        command_args = ["xdg-open"]
    else:
        command_args = ["open"]
        if browser:
            command_args += ["-a", browser]

    command_args.append(url)

    return command_output(command_args, timeout=5)

CHUNK_BYTES = 4096
def receive_data(stderr=False, verbose=False):
    """Receive from client via stdin, returning (errmsg, headers, content)"""
    saved_stdin = sys.stdin.fileno()
    saved_settings = termios.tcgetattr(saved_stdin)

    try:
        # Raw tty input without echo
        tty.setraw(saved_stdin)
        line = ""
        header_line = ""
        header_start = False
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x03" or ch == "\x04": # ^C/^D
                return ("Interrupted", None, None)
            if not header_start:
                if ch == "{":
                    header_start = True
                    line = ch
                continue
            if ch != "\n":
                line += ch
                continue
            if line:
                header_line += line
                line = ""
            else:
                # Terminal null line
                break

        if verbose and not stderr:
            print >> sys.stderr, "header=%s\n" % (header_line,)

        # Process headers
        if not header_line:
            return ("No headers", None, None)

        headers = json.loads(header_line)

        content_type = headers.get("content_type", "")
        if content_type.startswith("none/"):
            return ("Null content", None, None)

        if "x_gterm_length" not in headers:
            return ("No expected length", None, None)

        expect_length = headers["x_gterm_length"]
        if verbose and not stderr:
            print >> sys.stderr, "type=%s, expect_len=%s\n" % (content_type, expect_length)

        if not expect_length:
            return ("", headers, "")

        md5_digest = headers.get("x_gterm_digest", "")

        count = expect_length
        assert not (count % 4)
        prefix = ""
        content_list = []
        digest_buf = hashlib.md5()
        while count > 0:
            chunk = sys.stdin.read(min(count, CHUNK_BYTES))
            assert chunk
            count = count - len(chunk)
            line = prefix + chunk
            prefix = ""
            offset = len(line) % 4
            if offset:
                prefix = line[-offset:]
                line = line[:-offset]
            if verbose and not stderr:
                print >> sys.stderr, "line(%d,%s)=%s" % (len(chunk), count, line,)
            digest_buf.update(line)
            content_list.append(base64.b64decode(line))
        assert not prefix
        if digest_buf.hexdigest() != md5_digest:
            return ("MD5 digest mismatch", headers, None)
        else:
            return ("", headers, "".join(content_list))
    except Exception, excp:
        if verbose and not stderr:
            print >> sys.stderr, "receive_data: ERROR %s" % excp
        return (str(excp), None, None)
    finally:
        termios.tcsetattr(saved_stdin, termios.TCSADRAIN, saved_settings)

def getuid(pid):
    """Return uid of running process"""
    command_args = ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fu"]
    std_out, std_err = command_output(command_args, timeout=1)
    if std_err:
        logging.warning("getuid: ERROR %s", std_err)
        return None
    try:
        return int(std_out.split("\n")[1][1:])
    except Exception, excp:
        logging.warning("getuid: ERROR %s", excp)
        return None

def auth_request(http_addr, http_port, nonce, timeout=None, client_auth=False, user="", protocol="http"):
    """Simulate user form submission by executing a HTTP request"""
    url = "%s://%s:%s/_auth/?nonce=%s" % (protocol, http_addr, http_port, nonce)
    if user:
        url += "&user=" + user

    if not client_auth:
        try:
            response = urllib2.urlopen(url)
            return response.read()
        except Exception, excp:
            print >> sys.stderr, "Error in accessing URL %s: %s" % (url, excp)
            return None

    import tornado.httpclient

    cert_dir = App_dir
    server_name = "localhost"
    client_prefix = server_name + "-gterm-local"
    ca_certs = cert_dir+"/"+server_name+".crt"
    
    ssl_options = {}
    if client_auth:
	client_cert = cert_dir+"/"+client_prefix+".crt"
	client_key = cert_dir+"/"+client_prefix+".key"
	ssl_options.update(client_cert=client_cert, client_key=client_key)

    request = tornado.httpclient.HTTPRequest(url, validate_cert=True, ca_certs=ca_certs,
					     **ssl_options)
    http_client = tornado.httpclient.HTTPClient()
    try:
	response = http_client.fetch(request)
	if response.error:
	    print >> sys.stderr, "HTTPClient ERROR response.error", response.error
	    return None
	return response.body
    except tornado.httpclient.HTTPError, excp:
        print >> sys.stderr, "Error in accessing URL %s: %s" % (url, excp)
    return None

def enable_tab_completion():
    # https://news.ycombinator.com/item?id=5658062
    try:
        import readline
    except ImportError:
        pass
    else:
        import rlcompleter
        readline.parse_and_bind("tab: complete")
        if sys.platform == 'darwin':
            readline.parse_and_bind("bind ^I rl_complete")

Saved_displayhook = sys.displayhook

try:
    import pandas
except ImportError:
    pandas = None

def auto_display(expr):
    if "display_hook" in globals():
        expr = globals()["display_hook"](expr)
    if pandas and isinstance(expr, pandas.core.frame.DataFrame):
        wrap_write(expr.to_html())
        return
    if hasattr(expr, "_repr_html_"):
        wrap_write(expr._repr_html_())
        return
    if expr is not None:
        auto_print(repr(expr)+"\n")

def nbmode(enable=True):
    global Saved_displayhook
    if enable:
        # Control automatic printing of expressions
        Saved_displayhook = sys.displayhook
        sys.displayhook = auto_display
        print >> sys.stderr, "NOTE: Enabled notebook mode (affects auto printing of expressions)"
        print >> sys.stderr, "      To disable, use gterm.nbmode(False)"
    else:
        print >> sys.stderr, "NOTE: Disabled notebook mode"
        sys.displayhook = Saved_displayhook

def process_args(args=None):
    """Process args, returning True if notebook is opened"""
    from optparse import OptionParser
    usage = "usage: %prog notebook.ipynb"
    parser = OptionParser(usage=usage)
    (options, my_args) = parser.parse_args(args=args)

    if my_args:
        filepath = my_args[0]
        if filepath.endswith(".md") or filepath.endswith(".ipynb") or filepath.endswith(".ipynb.json"):
            if filepath.startswith("http:") or filepath.startswith("https:"):
                response = urllib2.urlopen(filepath)
                content = response.read()
                filepath = os.path.basename(filepath)
            else:
                content = None
            # Switch to notebook mode (after prompt is displayed)
            open_notebook(filepath, content=content)
            return True
    return False

def nb_setup():
    nbmode()
    process_args()

def main():
    global Http_addr, Http_port
    from optparse import OptionParser
    usage = "usage: gterm [-h ... options] [URL | [/host/]session]"
    parser = OptionParser(usage=usage)

    parser.add_option("", "--https", dest="https", action="store_true",
                      help="Use SSL (TLS) connections for security")
    parser.add_option("-n", "--noauth", dest="noauth", action="store_true",
                      help="No authentication required")
    parser.add_option("-r", "--read_code", dest="read_code", action="store_true",
                      help="Read access code from terminal")
    parser.add_option("-b", "--browser", dest="browser", default="",
                      help="Browser application name (OS X only)")
    parser.add_option("-u", "--user", dest="user", default="",
                      help="User name")
    parser.add_option("-p", "--port", dest="port", default=0,
                      help="Remote server port", type="int")
    parser.add_option("", "--client_cert", dest="client_cert", default="",
                      help="Path to client CA cert (or '.')")
    #parser.add_option("", "--term_type", dest="term_type", default="",
    #                  help="Terminal type (linux/screen/xterm) NOT YET IMPLEMENTED")

    (options, args) = parser.parse_args()
    protocol = "https" if options.https else "http"
    server = ""
    path = ""
    port = None
    if args:
        if args[0] and ":" not in args[0]:
            if args[0][0].isalpha():
                path = (Host or "local") + "/" + args[0]
            elif args[0].startswith("/"):
                path = args[0][1:]
        else:
            try:
                comps = urlparse.urlparse(args[0])
                server, sep, port = comps[1].partition(":")
                if port:
                    port = int(port)
            except Exception, excp:
                sys.exit("Invalid URL argument: "+str(excp))
            protocol = comps[0]
            if not port:
                port = 443 if protocol == "https" else 80
            path = comps[2][1:]

    if not server and Lterm_cookie:
        # Open new terminal window from within graphterm window
        path = path or (Host + "/" + "new")
        url = URL + "/" + path
        target = "_blank" if url.endswith("/new") else path
        open_url(url, target=target)
        return

    auth_file = get_auth_filename(user=options.user, server=server)
    auth_user = options.user
    read_code = options.read_code
    if options.noauth:
        auth_code = "none"
        auth_user = ""
    elif read_code:
        auth_code = undashify(getpass.getpass("Access code: "))
    else:
        try:
            # Read user access code
            auth_code, tem_port = read_auth_code(user=options.user, server=server)
        except Exception, excp:
            try:
                # Read master access code
                auth_code, tem_port = read_auth_code(server=server)
                auth_user = ""
            except Exception, excp:
                print >> sys.stderr, "Unable to read auth file", auth_file 
                auth_code = undashify(getpass.getpass("Access code: "))
                read_code = True

        port = port or tem_port

    Http_addr = server or "localhost"
    Http_port = options.port or port or DEFAULT_HTTP_PORT

    client_nonce = "1%018d" % random.randrange(0, 10**18)   # 1 prefix to keep leading zeros when stringified

    resp = auth_request(Http_addr, Http_port, client_nonce, user=auth_user, protocol=protocol)
    if not resp:
        print >> sys.stderr, "\ngterm: Authentication request to GraphTerm server %s:%s failed" % (Http_addr, Http_port)
        print >> sys.stderr, "gterm: Server may not be running; use 'gtermserver' command to start it."
        sys.exit(1)

    server_nonce, received_token = resp.split(":")
    client_token, server_token = auth_token(auth_code, "graphterm", Http_addr, Http_port, client_nonce, server_nonce)
    if received_token != client_token:
        print >> sys.stderr, "gterm: GraphTerm server %s:%s failed to authenticate itself (Check port number and auth code in %s)" % (Http_addr, Http_port, auth_file)
        sys.exit(1)

    ##print >> sys.stderr, "**********snonce", server_nonce, client_token, server_token

    if read_code:
        confirm = raw_input("Save validated access code? (y/[n]): ").strip()
        if confirm.lower().startswith("y"):
            write_auth_code(auth_code, user=options.user, server=Http_addr, port=Http_port)
            print >> sys.stderr, "Access code saved to file", auth_file
    # Open graphterm window using browser
    url = "%s://%s" % (protocol, Http_addr)
    if (protocol == "http" and Http_port == 80) or (protocol == "https" and Http_port == 443):
        pass
    else:
        url += ":" + str(Http_port) 

    if path:
        url += "/" + path
    code = compute_hmac(auth_code, server_nonce)
    url += "/?cauth="+server_nonce+"&code="+code
    if options.user:
        url += "&user="+options.user

    std_out, std_err = open_browser(url, browser=options.browser)
    if std_err:
        print >> sys.stderr, "gterm: ERROR in opening browser window '%s' - %s\n Check if server is running. If not, start it with 'gtermserver' command." % (url, std_err)
        sys.exit(1)

    # TODO: Create minimal browser window (without URL box etc.)
    # by searching directly for browser executables, or using open, xdg-open, or gnome-open
    # For security, closing websocket should close out (or at least about:blank) the terminal window
    # (to prevent reconnecting to malicious server)

if __name__ == "__main__":
    if sys.flags.interactive:
        nb_setup()
    else:
        main()
