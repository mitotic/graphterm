.. graphterm documentation master file, created by
   sphinx-quickstart on Sat Oct  6 10:23:49 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GraphTerm: A Graphical Terminal Interface
===================================================

.. raw:: html

  <iframe allowtransparency="true" frameborder="0" scrolling="no"
  src="https://platform.twitter.com/widgets/tweet_button.html?url=http://code.mindmeldr.com/graphterm&via=graphterm&text=GraphTerm,%20A%20Graphical%20Terminal%20Interface&count=none"
  style="width:80px; height:27px;"></iframe>
  <iframe src="//www.facebook.com/plugins/like.php?href=http%3A%2F%2Fcode.mindmeldr.com%2Fgraphterm&amp;send=false&amp;layout=standard&amp;width=100&amp;show_faces=false&amp;action=like&amp;colorscheme=light&amp;font&amp;height=35" scrolling="no" frameborder="0" style="border:none; overflow:hidden; width:53px; height:30px;" allowTransparency="true"></iframe>

*Updates:*
   1. You can join the Google Groups
   `mailing list <https://groups.google.com/group/graphterm>`_
   or follow `@graphterm <https://twitter.com/intent/user?screen_name=graphterm>`_
   on Twitter for updates.
   2. The latest version is `0.33.0 <http://pypi.python.org/pypi/graphterm>`_,
   released September 30, 2012. See the
   `Release Notes <http://code.mindmeldr.com/graphterm/release-notes>`_

``GraphTerm`` is a browser-based graphical terminal interface, that
aims to seamlessly blend the command line and graphical user
interfaces. The goal is to provide a fully backwards-compatible terminal
emulator for ``xterm``.  You should be able to use it just like a regular terminal
interface, accessing additional graphical features only as needed. GraphTerm builds
upon two earlier projects, 
`XMLTerm <http://www.xml.com/pub/a/2000/06/07/xmlterm/index.html>`_
which implemented a terminal using the Mozilla framework and
`AjaxTerm <https://github.com/antonylesuisse/qweb/tree/master/ajaxterm>`_
which is an AJAX/Python terminal implementation. (Another recent
project along these lines is  `TermKit <http://acko.net/blog/on-termkit/>`_.)
For more information, see the following:

.. toctree::
   :maxdepth: 1

   README <README>
   Using GraphTerm <usage>
   Troubleshooting <troubleshooting>
   Implementation <implementation>
   Screenshots <screenshots>
   Release Notes <release-notes>
   Tutorials and talks <tutorials>
   Demo video <http://youtu.be/TvO1SnEpwfE>
   PyPI Package Index (for downloading and installing) <http://pypi.python.org/pypi/graphterm>
   Source code at Github <https://github.com/mitotic/graphterm>
   advanced

A GraphTerm terminal window is just a web page served from the
GraphTerm web server program. Multiple users can connect
simultaneously to the web server to share terminal sessions.
Multiple hosts can also connect to the server (on a different port),
allowing a single user to access all of them via the browser.
The GraphTerm server acts as a *router*, sending input from browser
windows for different users to the appropriate terminal (pseudo-tty)
sessions running on different hosts, and transmitting the
terminal output back to the browser windows.
 
This flexible, networked implementation allows for several possible
applications for GraphTerm, such as:

 - an **enhanced terminal** that combines the command line with basic
   GUI operations like navigating folders, file drag-and-drop,
   displaying images etc.

 - a web-based **remote desktop** that supports a simple GUI
   without the need for installing VNC or X-windows on the remote host

 - a **detachable terminal multiplexer**, sort of like GNU ``screen`` or
   ``tmux``

 - an **inline data visualization tool** to view output from plotting
   libraries like ``matplotlib``

 - a **collaborative terminal** that can be remotely accessed
   by multiple users simultaneously, to run programs, edit files etc.

 - a **simple presentation tool** for webcasting images as slideshows
   (and receiving live feedback)

 - a **management console** for a cluster of real or virtual hosts,
   with wildcard access to hosts/sessions (e.g., to manage a virtual
   computer lab using cloud instances),
 
The interface is designed to be touch-friendly for use with tablets,
relying upon command re-use to minimize the need for a keyboard.
It preserves history for all commands, whether entered by typing,
clicking, or tapping. It is also themable using CSS.

You can find more information on installing and using GraphTerm in the
`README <http://code.mindmeldr.com/graphterm/README.html>`_ file.
Images of GraphTerm in action can be found in
`screenshots <http://code.mindmeldr.com/graphterm/screenshots.html>`_
and in this
`YouTube Video <http://youtu.be/JBMexdwXN8w>`_.
For updates, join the Google Groups
`mailing list <https://groups.google.com/group/graphterm>`_  or

.. raw:: html

  <iframe allowtransparency="true" frameborder="0" scrolling="no"
  src="https://platform.twitter.com/widgets/follow_button.html?screen_name=graphterm&count=none"
  style="width:130px; height:20px;"></iframe><p>

Here is a sample screenshot illustrating graphical ``gls`` and ``cat`` command
output using a 3D perspective theme (captured on OS X Lion, using Google Chrome).

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-stars3d.png
   :align: center
   :width: 95%
   :figwidth: 95%

