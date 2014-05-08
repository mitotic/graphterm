#!/usr/bin/env python

import os, sys

import about

BINDIR = "bin"
Exec_path = os.path.abspath(os.path.join(os.path.dirname(__file__), BINDIR))

def setup_bindir():
    print >> sys.stderr, "Configuring", Exec_path
    for dirpath, dirnames, filenames in os.walk(Exec_path):
        for filename in filenames:
            if not filename.startswith(".") and not filename.endswith(".pyc"):
	        os.chmod(os.path.join(dirpath, filename), 0755)

def main():
    from optparse import OptionParser

    usage = "usage: %prog [--no_profile]"
    parser = OptionParser(usage=usage)
    parser.add_option("-n", "--no_profile", action="store_true", dest="no_profile", default=False,
                      help="Do not append shell initialization commands to user/system profile")

    (options, args) = parser.parse_args()

    try:
        setup_bindir()
    except Exception, excp:
        pass

    if not options.no_profile:
        try:
            profile_path = os.path.join(Exec_path, "gprofile")
            profile_lines = "\n# Appended by GraphTerm %s installer\n[ -r %s ] && source %s\n" % (about.version, profile_path, profile_path)

            aliases_path = os.path.join(Exec_path, "galiases")
            aliases_lines = "\n# Appended by GraphTerm %s installer\n[ -r %s ] && source %s\n" % (about.version, aliases_path, aliases_path)

            pfile, afile = "", ""
            if os.geteuid():
                pfile = os.path.join(os.path.expanduser("~"), ".profile")
                afile = os.path.join(os.path.expanduser("~"), ".bashrc")
            else:
                if os.path.isfile("/etc/profile"):
                    pfile = "/etc/profile"

                if os.path.isfile("/etc/bashrc"):
                    afile = "/etc/bashrc"
                elif os.path.isfile("/etc/bash.bashrc"):
                    afile = "/etc/bash.bashrc"

            if pfile:
                try:
                    with open(pfile, "a") as f:
                        f.write(profile_lines)
                    print >> sys.stderr, "Appended shell environment setup to", pfile
                except Exception, excp:
                    pass

            if afile:
                try:
                    with open(afile, "a") as f:
                        f.write(aliases_lines)
                    print >> sys.stderr, "Appended shell aliases setup to", afile
                except Exception, excp:
                    pass

        except Exception, excp:
            print >> sys.stderr, "Error in updating shell setup", excp
                
if __name__ == "__main__":
    main()
