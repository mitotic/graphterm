#!/usr/bin/env python
#

"""
gauth: Display graphterm authentication code for user
"""

import getpass
import os
import pwd
import sys
import urllib

import gterm

def main():
    username = getpass.getuser()
    usage = "usage: %prog [-h ... ] username"
    parser = gterm.FormParser(usage=usage, title="Display graphterm authentication code for user: ", command="gauth")
    parser.add_argument(label="", help="Username")
    parser.add_option("admin", username, short="a", help="Admin username (default: %s)" % username)
    parser.add_option("head", "", help="Head portion of message")
    parser.add_option("mail", False, short="m", help="Display info for mailing etc.")
    parser.add_option("notebook", False, short="n", help="Display notebook URL")
    parser.add_option("group", False, short="g", help="Display group code")
    parser.add_option("subject", "GraphTerm remote access", help="Email subject line")
    parser.add_option("server", "", short="s", help="External server name")
    parser.add_option("tail", "", help="Tail portion of message")
    parser.add_option("write", False, short="w", help="Write authentication file for user (for superuser use)")

    (options, args) = parser.parse_args()

    if not args and not options.group:
        sys.exit(parser.get_usage())

    server = options.server or gterm.Server

    user = "" if options.group else args[0]

    if options.admin:
        admin_dir = os.path.join(os.path.expanduser("~"+options.admin), gterm.APP_DIRNAME)
    else:
        admin_dir = gterm.App_dir

    auth_code, port = gterm.read_auth_code(appdir=admin_dir, server=server)
    user_code = gterm.user_hmac(auth_code, "", key_version="grp") if options.group else gterm.user_hmac(auth_code, user, key_version="1")

    if options.mail:
        mail_body = options.head+"\n" if options.head else ""
        mail_body += "\nUser: "+user+"\n" if user else "\nGroup "
        mail_body += "Code: "+gterm.dashify(user_code)+"\n"
        mail_body += "URL: "+gterm.URL+"\n"
        email_addr = ""
        if user:
            if options.notebook:
                prefix, sep, suffix = gterm.URL.rpartition(":")
                mail_body += "Notebook URL: %s:%d\n" % (prefix if suffix.isdigit() else gterm.URL, gterm.NB_BASE_PORT+pwd.getpwnam(user).pw_uid)
            try:
                with open(os.path.join(os.path.expanduser("~"+user), gterm.APP_DIRNAME, gterm.APP_EMAIL_FILENAME), "r") as f:
                    email_addr = f.read().strip()
            except Exception, excp:
                pass
        mail_body += "\n"+options.tail+"\n" if options.tail else ""
        mail_url = 'mailto:'+email_addr+'?subject='+urllib.quote(options.subject)+'&body='+urllib.quote(mail_body)
        if gterm.Lterm_cookie:
            gterm.wrap_write(mail_body.replace("\n","<br>")+'<p>Click <a href="'+mail_url+'">here</a> to email it')
        else:
            print mail_body
    elif options.write:
        user_dir = os.path.join(os.path.expanduser("~"+user), gterm.APP_DIRNAME)
        gterm.create_app_directory(appdir=user_dir)
        gterm.write_auth_code(user_code, appdir=user_dir, user=user, server=server)
    else:
        print gterm.dashify(user_code)

if __name__ == "__main__":
    main()
