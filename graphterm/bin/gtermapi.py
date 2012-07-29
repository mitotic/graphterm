"""
gtermapi: Common code gterm-aware programs
"""

import os
import random

Lterm_cookie = os.getenv("GRAPHTERM_COOKIE", "")
Html_escapes = ["\x1b[?1155;%sh" % Lterm_cookie,
                "\x1b[?1155l"]

def wrap(html):
    return Html_escapes[0] + html + Html_escapes[1]

Form_template =  """<div id="gterm-form-%s" class="gterm-form">%s %s
<input id="gterm-form-command-%s" class="gterm-form-button gterm-form-command" type="submit" data-gtermformcmd="%s" data-gtermformargs="%s"></input>  <input class="gterm-form-button gterm-form-cancel" type="button" value="Cancel"></input>
</div>"""

Input_text_template = """<span class="gterm-form-label" data-gtermhelp="%s">%s</span><input id="gterm_%s_%s" name="%s" class="gterm-form-input" type="text" autocomplete="off" %s></input>"""

Select_template = """<span class="gterm-form-label" data-gtermhelp="%s">%s</span><select id="gterm_%s_%s" name="%s" class="gterm-form-input" size=1>
%s
</select>"""
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
