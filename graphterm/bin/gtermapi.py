"""
gtermapi: Common code for gterm-aware programs
"""

import hashlib
import hmac
import json
import os
import random
import sys

HEX_DIGITS = 16

Lterm_cookie = os.getenv("GRAPHTERM_COOKIE", "")
Host = os.getenv("GRAPHTERM_HOST", "")
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
                    "x_gterm_parameters": {"scroll": "top", "display": display, "current_directory": dir}
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

def get_file_url(filepath):
    """Construct fie URL with hmac cookie suffix"""
    filehmac = "?hmac="+hmac.new(str(Lterm_cookie), filepath, digestmod=hashlib.sha256).hexdigest()[:HEX_DIGITS]
    return "/file/" + Host + filepath + filehmac

Form_template =  """<div id="gterm-form-%s" class="gterm-form">%s %s
<input id="gterm-form-command-%s" class="gterm-form-button gterm-form-command" type="submit" data-gtermformcmd="%s" data-gtermformargs="%s"></input>  <input class="gterm-form-button gterm-form-cancel" type="button" value="Cancel"></input>
</div>"""

Input_text_template = """<div><span class="gterm-form-label" data-gtermhelp="%s">%s</span><input id="gterm_%s_%s" name="%s" class="gterm-form-input" type="text" autocomplete="off" %s></input></div>"""

Select_template = """<div><span class="gterm-form-label" data-gtermhelp="%s">%s</span><select id="gterm_%s_%s" name="%s" class="gterm-form-input" size=1>
%s
</select></div>"""
Select_option_template = """<option value="%s" %s>%s</option>"""

def create_input_html(id_suffix, arg_list):
    input_list = []
    first_arg = True
    for opt_name, opt_default, opt_help in arg_list:
        if isinstance(opt_default, basestring):
            opt_label = "" if opt_name.startswith("arg") else (opt_name+": ")
            extras = ' autofocus="autofocus"' if first_arg else ""

            input_list.append(Input_text_template % (opt_help, opt_label, id_suffix, opt_name, opt_name, extras))
        elif isinstance(opt_default, (list, tuple)):
            opt_list = []
            opt_sel = "selected"
            for opt_value in opt_default:
                opt_list.append(Select_option_template % (opt_value, opt_sel, opt_value or "Select..."))
                opt_sel = ""
            input_list.append(Select_template % (opt_help, opt_name+": ", id_suffix, opt_name, opt_name,
                                                 "\n".join(opt_list)))
        first_arg = False

    return "\n".join(input_list)
    
def create_form(id_suffix, arg_list, title=""):
    opt_names = ",".join(x[0] for x in arg_list)
    input_html = create_input_html(id_suffix, arg_list)
    return Form_template % (id_suffix, title, input_html, id_suffix, "ec2launch -f", opt_names) 

def add_options(parser, arg_list, title=""):
    """Returns form html, after adding options"""
    for opt_name, opt_default, opt_help in arg_list:
        default= opt_default[0] if isinstance(opt_default, (list, tuple)) else opt_default
        parser.add_option("", "--"+opt_name, dest=opt_name, default=default,
                          help=opt_help)
    id_suffix = "1%09d" % random.randrange(0, 10**9)    
    return create_form(id_suffix, arg_list, title=title)
