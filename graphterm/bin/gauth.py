#!/usr/bin/env python
#

"""
gauth: Display graphterm authentication code for user
"""

import os
import sys
from optparse import OptionParser

import gterm

def main():
    usage = "usage: %prog [-a admin_username] username"
    parser = OptionParser(usage=usage)
    parser.add_option("-a", "--admin", dest="admin", default="",
                      help="Admin username")
    parser.add_option("-w", "--write",
                      action="store_true", dest="write", default=False,
                      help="Write authentication file for user (for superuser use)")

    (options, args) = parser.parse_args()

    if not args:
        print >> sys.stderr, parser.get_usage()
        sys.exit(1)

    user = args[0]

    if options.admin:
        admin_dir = os.path.join(os.path.expanduser("~"+options.admin), gterm.APP_DIRNAME)
    else:
        admin_dir = gterm.App_dir

    auth_code, port = gterm.read_auth_code(appdir=admin_dir)
    user_code = gterm.dashify(gterm.user_hmac(auth_code, user, key_version="1"))
    if not options.write:
        print user_code
    else:
        user_dir = os.path.join(os.path.expanduser("~"+user), gterm.APP_DIRNAME)
        gterm.create_app_directory(appdir=user_dir)
        gterm.write_auth_code(user_code, appdir=user_dir, user=user)

if __name__ == "__main__":
    main()
