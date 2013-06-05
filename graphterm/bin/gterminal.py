#!/usr/bin/env python

"""gterm: GraphTerm client launcher
"""

import hashlib
import hmac
import logging
import os
import random
import sys

import tornado.httpclient

import gtermapi

Http_addr = "localhost"
Http_port = 8900

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

def auth_request(http_addr, http_port, nonce, timeout=None, client_auth=False, protocol="http"):
    """Simulate user form submission by executing a HTTP request"""

    cert_dir = gtermapi.App_dir
    server_name = "localhost"
    client_prefix = server_name + "-gterm-local"
    ca_certs = cert_dir+"/"+server_name+".crt"
    
    ssl_options = {}
    if client_auth:
	client_cert = cert_dir+"/"+client_prefix+".crt"
	client_key = cert_dir+"/"+client_prefix+".key"
	ssl_options.update(client_cert=client_cert, client_key=client_key)
	
    url = "%s://%s:%s/_auth/?nonce=%s" % (protocol, http_addr, http_port, nonce)
    request = tornado.httpclient.HTTPRequest(url, validate_cert=True, ca_certs=ca_certs,
					     **ssl_options)
    http_client = tornado.httpclient.HTTPClient()
    try:
	response = http_client.fetch(request)
	if response.error:
	    print >> sys.stderr, "HTTPClient ERROR response.error ", response.error
	    return None
	return response.body
    except tornado.httpclient.HTTPError, excp:
	print >> sys.stderr, "HTTPClient ERROR ", excp
    return None

def auth_token(secret, connection_id, client_nonce, server_nonce):
    """Return (client_token, server_token)"""
    SIGN_SEP = "|"
    prefix = SIGN_SEP.join([connection_id, client_nonce, server_nonce]) + SIGN_SEP
    return [hmac.new(str(secret), prefix+conn_type, digestmod=hashlib.sha256).hexdigest()[:24] for conn_type in ("client", "server")]

def main():
    global Http_addr, Http_port
    from optparse import OptionParser
    usage = "usage: gterm [-h ... options] [[host/]session]"
    parser = OptionParser(usage=usage)

    parser.add_option("", "--https", dest="https", action="store_true",
                      help="Use SSL (TLS) connections for security")
    parser.add_option("", "--server_auth", dest="server_auth", action="store_true",
                      help="Authenticate server before opening gterm window")
    parser.add_option("", "--client_cert", dest="client_cert", default="",
                      help="Path to client CA cert (or '.')")
    parser.add_option("", "--term_type", dest="term_type", default="",
                      help="Terminal type (linux/screen/xterm) NOT YET IMPLEMENTED")

    (options, args) = parser.parse_args()
    protocol = "https" if options.https else "http"

    path = ""
    if args:
        if "/" in args[0]:
            path = args[0]
        else:
            path = (gtermapi.Host or "local") + "/" + args[0]

    if gtermapi.Lterm_cookie:
        # Open new terminal window from within graphterm window
        path = path or (gtermapi.Host + "/" + "new")
        url = gtermapi.URL + "/" + path
        target = "_blank" if url.endswith("/new") else path
        gtermapi.open_url(url, target=target)
        return

    if options.server_auth:
        # Authenticate server
        if not os.path.exists(gtermapi.Gterm_secret_file):
            print >> sys.stderr, "gterm: Server not running (no secret file); use 'gtermserver' command to start it."
            sys.exit(1)

        try:
            with open(gtermapi.Gterm_secret_file) as f:
                Http_port, Gterm_pid, Gterm_secret = f.read().split()
                Http_port = int(Http_port)
                Gterm_pid = int(Gterm_pid)
        except Exception, excp:
            print >> sys.stderr, "gterm: Error in reading %s: %s" % (gtermapi.Gterm_secret_file, excp)
            sys.exit(1)

        if os.getuid() != getuid(Gterm_pid):
            print >> sys.stderr, "gterm: Server not running (invalid pid); use 'gtermserver' command to start it."
            sys.exit(1)

        client_nonce = "1%018d" % random.randrange(0, 10**18)   # 1 prefix to keep leading zeros when stringified

        resp = auth_request(Http_addr, Http_port, client_nonce, protocol=protocol)
        if not resp:
            print >> sys.stderr, "gterm: Auth HTTTP Request failed"
            sys.exit(1)

        server_nonce, received_token = resp.split(":")
        client_token, server_token = auth_token(Gterm_secret, "graphterm", client_nonce, server_nonce)
        if received_token != client_token:
            print >> sys.stderr, "gterm: Server failed to authenticate itself"
            sys.exit(1)

        # TODO: Send server token to server in URL to authenticate
        ##print >> sys.stderr, "**********snonce", server_nonce, client_token, server_token

    # Open graphterm window using browser
    url = "%s://%s:%d" % (protocol, Http_addr, Http_port)
    if path:
        url += "/" + path

    std_out, std_err = gtermapi.open_browser(url)
    if std_err:
        print >> sys.stderr, "gterm: ERROR in opening browser window '%s' - %s\n Check if server is running. If not, start it with 'gtermserver' command." % (" ".join(command_args), std_err)
        sys.exit(1)

    # TODO: Create minimal browser window (without URL box etc.)
    # by searching directly for browser executables, or using open, xdg-open, or gnome-open
    # For security, closing websocket should close out (or at least about:blank) the terminal window
    # (to prevent reconnecting to malicious server)

if __name__ == "__main__":
    main()
