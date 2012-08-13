"""
gtermapi: Common code for gterm-aware programs
"""

import hashlib
import hmac
import json
import os
import random
import sys
import termios
import tty

from optparse import OptionParser

HEX_DIGITS = 16

Lterm_cookie = os.getenv("GRAPHTERM_COOKIE", "")
Shared_secret = os.getenv("GRAPHTERM_SHARED_SECRET", "")
Path = os.getenv("GRAPHTERM_PATH", "")
Host, Session = Path.split("/") if Path else ("", "") 
Html_escapes = ["\x1b[?1155;%sh" % Lterm_cookie,
                "\x1b[?1155l"]

def wrap(html, headers={}):
    """Wrap html, with headers, between escape sequences"""
    return Html_escapes[0] + json.dumps(headers) + "\n\n" + html + Html_escapes[1]

def write(data):
    """Write data to stdout and flush"""
    sys.stdout.write(data)
    sys.stdout.flush()

def wrap_write(html, headers={}):
    """Wrap html, with headers, and write to stdout"""
    write(wrap(html, headers=headers))

def write_html(html, display="block", dir=""):
    """Write html pagelet to stdout"""
    html_headers = {"content_type": "text/html",
                    "x_gterm_response": "pagelet",
                    "x_gterm_parameters": {"display": display, "scroll": "top", "current_directory": dir}
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

def open_url(url):
    """Open url in new window"""
    blank_headers = {"x_gterm_response": "open_url",
                     "x_gterm_parameters": {"url": url}
                     }
    wrap_write("", headers=blank_headers)

def get_file_url(filepath, relative=False):
    """Construct file URL with hmac cookie suffix. If relative, return '/file/host/path'"""
    filehmac = "?hmac="+hmac.new(str(Shared_secret), filepath, digestmod=hashlib.sha256).hexdigest()[:HEX_DIGITS]
    if relative:
        return "/file/" + Host + filepath + filehmac
    else:
        return "file://" + ("" if Host == "local" else Host) + filepath + filehmac

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


Label_template = """<span class="gterm-form-label" data-gtermhelp="%s">%s</span>"""

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

            label_html = Label_template % (opt_help, label)
            attrs = ""
            classes = ""
            if j < arg_count:
                classes += ' gterm-input-arg'
            if isinstance(opt_default, basestring):
                if first_arg:
                    attrs += ' autofocus="autofocus"'
                input_html = Input_text_template % (id_suffix, opt_name, opt_name, classes, opt_default.replace('"', "&quot;"), attrs)

            elif isinstance(opt_default, bool):
                if opt_default:
                    attrs += " checked"
                input_html = Input_checkbox_template % (id_suffix, opt_name, opt_name, classes, attrs)

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
