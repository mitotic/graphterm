GraphTerm Implementation
*********************************************************************************
.. sectnum::
.. contents::


.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-architecture.png
   :align: center
   :width: 90%
   :figwidth: 70%

The GraphTerm server written in pure python, using the
`Tornado  web  framework <http://tornadoweb.org>`_,
with websocket support. The GraphTerm client uses standard
HTML5+Javascript+CSS (with jQuery).

The GraphTerm server may be run on your desktop or on a remote
computer. Users create and access terminal sessions by the connecting to
the Graphterm server on port 8900, either directly or through SSH
port forwarding.
By default, the localhost on the computer where the GraphTerm server
is running is available for opening terminal sessions. Other computers
can also connect to the GraphTerm server, on a different port (8899),
to make them accessible as hosts for connection from the browser.

A pseudo-tty (``pty``) is opened on the host for each terminal
session. By setting the ``PROMP_COMMAND`` environment variable, GraphTerm
determines when the ``stdout`` of the previous command ends, and the
``prompt`` for the new command begins.

The connection between the browser and the GraphTerm server is
implemented using websockets (bi-directional HTTP). The GraphTerm
server acts as a router sending input from controlling browser terminal sessions
to the appropriate ``pty`` on the host computer, and transmitting
output from each ``pty`` to all connected browser terminal sessions.

GraphTerm extends the ``xterm`` terminal API by adding a
new control sequence for programs to transmit a CGI-like HTTP response
through standard output (via a websocket) to be displayed in the
browser window. GraphTerm-aware programs can interact with the
user using HTML forms etc.
