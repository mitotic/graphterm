#!/usr/bin/env python

import os, socket, ssl, sys, pprint, time

host_port = ('localhost', 8899)

ssl_options = {"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": os.getenv("HOME")+"/.ssh/localhost.crt"}

if 0:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # require a certificate from the server
    ssl_sock = ssl.wrap_socket(s, **ssl_options)

    ssl_sock.connect(host_port)

    pprint.pprint(ssl_sock.getpeercert())
    # note that closing the SSLSocket will also close the underlying socket
    ssl_sock.close()

def on_connect():
    print "Connected"
    time.sleep(5)
    
import tornado.iostream, tornado.ioloop

if 0:
    stream = tornado.iostream.SSLIOStream(socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0),
                                          ssl_options=ssl_options)

    stream.connect(host_port, on_connect)

    sys.exit(0)

import packetserver

class MyClient(packetserver.PacketClient):
    _all_connections = {}
    def __init__(self, host, port, lterm_cookie="", io_loop=None, ssl_options={}):
        super(MyClient, self).__init__(host, port, io_loop=io_loop,
                                             ssl_options=ssl_options, max_packet_buf=3,
                                             reconnect_sec=300, server_type="frame")

conn2 = MyClient.get_client("conn2", connect=host_port, connect_kw={"ssl_options": ssl_options})

tornado.ioloop.IOLoop.instance().start()


print "conn2", conn2
