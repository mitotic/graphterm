#!/usr/bin/env python

import os, sys

BINDIR = "bin"
Exec_path = os.path.join(os.path.dirname(__file__), BINDIR)

def setup_bindir():
    print >> sys.stderr, "Configuring", Exec_path
    for dirpath, dirnames, filenames in os.walk(Exec_path):
        for filename in filenames:
            if not filename.startswith(".") and not filename.endswith(".pyc"):
	        os.chmod(os.path.join(dirpath, filename), 0555)

def main():
    setup_bindir()

if __name__ == "__main__":
    main()
