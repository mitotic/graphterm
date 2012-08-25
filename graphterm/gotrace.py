#!/usr/bin/env python

"""gotrace: Graphical otrace launcher
"""

import logging
import os
import signal
import sys
import threading
import time
import traceback

import gtermhost

def main(args=None):
    import imp
    global Gterm_host, Host_secret, Trace_shell

    if args is None:
         args = sys.argv[1:]

    funcname = ""
    server = "localhost"
    hostname = ""
    j = 0
    while j < len(args)-1:
        if args[j] == "-f":
            funcname = args[j+1]
        elif args[j] == "-n":
            hostname = args[j+1]
        elif args[j] == "-s":
            server = args[j+1]
        else:
            break
        j += 2

    if j >= len(args):
        print >> sys.stderr, "Usage: gotrace [-f function_name] [-n hostname] [-s server_addr[:port] (default: localhost:%d)] program_file [arg1 arg2 ...]" % gtermhost.DEFAULT_HOST_PORT
        sys.exit(1)

    filepath = args[j]
    args = args[j+1:]
    
    if not os.path.isfile(filepath) or not os.access(filepath, os.R_OK):
        print >> sys.stderr, "gotrace: Unable to read file %s" % filepath
        sys.exit(1)

    abspath = os.path.abspath(filepath)
    filedir, basename = os.path.split(abspath)
    modname, extension = os.path.splitext(basename)

    if not hostname:
        hostname = modname

    if ":" in server:
        server, sep, port = server.partition(":")
        port = int(port)
    else:
        port = gtermhost.DEFAULT_HOST_PORT

    # Load program as module
    modfile, modpath, moddesc = imp.find_module(modname, [filedir])
    modobj = imp.load_module(modname, modfile, modpath, moddesc)

    orig_funcobj = getattr(modobj, funcname, None) if funcname else None
    if funcname and not callable(orig_funcobj):
        print >> sys.stderr, "gotrace: Program %s does not have function named '%s'" % (filepath, funcname)
        sys.exit(1)
        
    # Connect to gterm as host, invoking OShell
    oshell_globals = modobj.__dict__

    Gterm_host, Host_secret, Trace_shell = gtermhost.gterm_connect(hostname, server,
                                                         server_port=port,
                                                         connect_kw={},
                                                         oshell_globals=oshell_globals,
                                                         oshell_thread=True,
                                                         oshell_unsafe=True,
                                                         oshell_init=modname+".trc")
    def host_shutdown():
        print >> sys.stderr, "Shutting down"
        gtermhost.gterm_shutdown(Trace_shell)

    def sigterm(signal, frame):
        logging.warning("SIGTERM signal received")
        host_shutdown()

    signal.signal(signal.SIGTERM, sigterm)

    try:
        if funcname:
            # Delay to ensure tracing has started
            time.sleep(1)

            # Call function in module (may be wrapped, if being traced)
            funcobj = getattr(modobj, funcname)
            if args:
                funcobj(args)
            else:
                funcobj()
        else:
            # Blocks until run command is issued
            Trace_shell.loop(wait_to_run=True)

    except Exception, excp:
        traceback.print_exc()
        print >> sys.stderr, "\nType ^C to abort"
        Trace_shell.execute("cd ~~")
        while not Trace_shell.shutting_down:
            time.sleep(1)

    finally:
        host_shutdown()
    
if __name__ == "__main__":
     main(args=sys.argv[1:])
