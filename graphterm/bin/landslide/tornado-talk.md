Tornado Web Server
======================

R. Saravanan

sarava@mitotic.org

PyTexas, College Station, Texas, Sep 16, 2012


![tornado](http://www.tornadoweb.org/static/tornado.png)

---

C10K problem
===============================

10,000 concurrent connections
--------------------------------------------

- Multi-threaded web servers (like Apache)

    - 1 thread per-client with blocking I/O
    - Pool of worker threads
 
- Asynchronous web servers
    - Single-threaded
    - Non-blocking network I/O
    - Python: asyncore, twisted, tornado, gevent*
    - Others: nginx, node.js

---

Tornado Web Server
===================================================================

- Asynchronous python library
    - Web server with simple templating
    - Async networking (similar to Twisted)
    - Authentication (OAuth: Facebook, Twitter, Google, ..)
    - WSGI
    - Can be used in Google App Engine

- Relatively lightweight; easy to understand

- History
    - Developed by Friendfeed/Facebook
    - Open sourced in 2009
    - Used by: Friendfeed/Facebook, Quora, Bitly, Hipmunk, …

---

Hello World using Tornado
====================================================

    !python
    import tornado.ioloop
    import tornado.web

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world")

    application = tornado.web.Application([
        (r"/", MainHandler),
    ])

    if __name__ == "__main__":
        application.listen(8888)
        tornado.ioloop.IOLoop.instance().start()


---

Two ways of handling async requests
=====================================================================

    !python
    class AsyncHandler(RequestHandler):
        @asynchronous
        def get(self):
            http_client = AsyncHTTPClient()
            http_client.fetch("http://example.com", callback=self.on_fetch)
    
        def on_fetch(self, response):
            do_something_with_response(response)
            self.render("template.html")
    
    class GenAsyncHandler(RequestHandler):
        @asynchronous
        @gen.engine
        def get(self):
            http_client = AsyncHTTPClient()
            response = yield gen.Task(http_client.fetch, "http://example.com")
            do_something_with_response(response)
            self.render("template.html")

---

Websockets
===================================================================

- Bi-directional HTTP
    - Like TCP
    - Send and receive messages (packets) instead of request/response

- Protocol
    - Draft protocol (version 76): May 2010
    - Final version: December 2011 (RFC 6455)

---

Websocket handling in Tornado
==================================================================

    !python
    class EchoWebSocket(websocket.WebSocketHandler):
        def open(self):
            print "WebSocket opened"

        def on_message(self, message):
            self.write_message(u"You said: " + message)

        def on_close(self):
            print "WebSocket closed"

Javascript

    !javascript
    var ws = new WebSocket("ws://localhost:8888/websocket");
    ws.onopen = function() {
       ws.send("Hello, world");
    };
    ws.onmessage = function (evt) {
       alert(evt.data);
    };


---

The End
==========================

.qr: 450|http://tornadoweb.org

