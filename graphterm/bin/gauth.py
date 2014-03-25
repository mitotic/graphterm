#!/usr/bin/env python
#

"""
gauth: Display graphterm authentication code for user
"""

import os
import sys
import urllib

import gterm

def main():
    usage = "usage: %prog [-h ... ] username"
    parser = gterm.FormParser(usage=usage, title="Display graphterm authentication code for user: ", command="gauth")
    parser.add_argument(label="", help="Username")
    parser.add_option("admin", "ubuntu", short="a", help="Admin username (default: ubuntu)")
    parser.add_option("mail", False, short="m", help="Display info for mailing etc.")
    parser.add_option("group", False, short="g", help="Display group code")
    parser.add_option("server", "localhost", short="s", help="External server name (default: localhost)")
    parser.add_option("write", False, short="w", help="Write authentication file for user (for superuser use)")

    (options, args) = parser.parse_args()

    if not args and not options.group:
        sys.exit(parser.get_usage())

    user = "" if options.group else args[0]

    if options.admin:
        admin_dir = os.path.join(os.path.expanduser("~"+options.admin), gterm.APP_DIRNAME)
    else:
        admin_dir = gterm.App_dir

    auth_code, port = gterm.read_auth_code(appdir=admin_dir, server=options.server)
    user_code = gterm.user_hmac(auth_code, "", key_version="grp") if options.group else gterm.user_hmac(auth_code, user, key_version="1")

    if options.mail:
        mail_body = "\nUser: "+user+"\n" if user else "\nGroup "
        mail_body += "Code: "+gterm.dashify(user_code)+"\n"
        mail_body += "URL: "+gterm.URL+"\n"
        mail_url = 'mailto:?subject=Graphterm%20code&body='+urllib.quote(mail_body)
        if gterm.Lterm_cookie:
            gterm.wrap_write(mail_body.replace("\n","<br>")+'<p>Click <a href="'+mail_url+'">here</a> to email it')
        else:
            print mail_body
    elif options.write:
        user_dir = os.path.join(os.path.expanduser("~"+user), gterm.APP_DIRNAME)
        gterm.create_app_directory(appdir=user_dir)
        gterm.write_auth_code(user_code, appdir=user_dir, user=user, server=options.server)
    else:
        print gterm.dashify(user_code)

if __name__ == "__main__":
    main()
