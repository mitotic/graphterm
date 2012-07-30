GraphTerm: A Graphical Terminal Interface
*********************************************************************************
.. sectnum::
.. contents::

Introduction
=============================

``GraphTerm`` is a browser-based graphical terminal interface, that
aims to seamlessly blend the command line and graphical user
interfaces. The goal is to be fully backwards compatible with
``xterm``.  You should be able to use it just like a regular terminal
interface, accessing additional features only as needed. GraphTerm builds
upon two earlier projects, 
`XMLTerm <http://www.xml.com/pub/a/2000/06/07/xmlterm/index.html>`_
which implemented a terminal using the Mozilla framework and
`AjaxTerm <https://github.com/antonylesuisse/qweb/tree/master/ajaxterm>`_
which is an AJAX/Python terminal implementation. (Another recent
project along these lines is  `TermKit <http://acko.net/blog/on-termkit/>`_.)

In addition to terminal features, GraphTerm implements file "finder"
or "explorer" features, and also some of the detached terminal
features of ``GNU screen``. GraphTerm is designed to
be touch-friendly, by facilitating command re-use to minimize
the use of the keyboard.

GraphTerm is a *terminal server*, not just a terminal. Multiple users can connect to
the terminal server simultaneously and share terminal sessions for collaboration.
Also, multiple computers can connect to a single terminal server, allowing
an user to manage them without having to log into each one
separately.

Images of GraphTerm in action can be found in `screenshots <https://github.com/mitotic/graphterm/blob/master/SCREENSHOTS.rst>`_ 
and in this `YouTube Video <http://youtu.be/JBMexdwXN8w>`_.
Here is a sample screenshot illustrating graphical ``gls`` and ``cat`` command
output using a 3D  perspective theme (captured on OS X Lion, using Google Chrome).

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-stars3d.png
   :align: center
   :width: 90%
   :figwidth: 70%


GraphTerm Design Goals:
---------------------------------------------

 - Full backwards compatibility with xterm

 - Incremental feature set

 - Minimalist no-frills graphical UI

 - Minimize use of keyboard (tab/menu completion)

 - Touch-friendly

 - Cloud friendly

 - Platform-independent browser client

 - Easy sharing/collaboration

      
GraphTerm Features:
--------------------------------------------

 - Clickable text: text displayed on terminal becomes clickable or "tappable"

 - Seamlessly blend text and (optional) graphics

 - History of all commands, entered by typing, clicking, or tapping

 - Multiple users can collaborate on a single terminal  window

 - Multiple computers can be accessed from a single browser window

 - Drag and drop

 - Themable using CSS (including 3D perspectives)



Installation
==============================

To install ``GraphTerm``, you need to have Python 2.6+ and the Bash
shell on your Mac/Linux/Unix computer. For a quick install, if the python
``setuptools`` module is already installed on your system,
use the following commands::

   sudo easy_install graphterm
   sudo gterm_setup

(If ``setuptools`` is not installed, consider installing it using
``apt-get install -y python-setuptools`` on Debian Linux systems
or its equivalent on other systems.)

For a manual install procedure, download the release tarball from the
`Python Package Index <http://pypi.python.org/pypi/graphterm>`_, untar,
and execute the following command in the ``graphterm-<version>`` directory::

   python setup.py install

For the manual install, you will also need to install the ``tornado``
web server, which can be downloaded from
`https://github.com/downloads/facebook/tornado/tornado-2.3.tar.gz <https://github.com/downloads/facebook/tornado/tornado-2.3.tar.gz>`_

You can also try out ``GraphTerm`` without installing it, by
running the server ``gtermserver.py`` in the ``graphterm``
subdirectory,  provided you have the ``tornado`` module
installed in your system (or in the ``graphterm`` subdirectory).

You can browse/fork the ``GraphTerm`` source code, and download the latest
version, at `Github <https://github.com/mitotic/graphterm>`_.


Usage
=================================

To start the ``GraphTerm`` server, use the command::

  gtermserver --auth_code=none

(You can use the ``--daemon=start`` option to run it in the background.)
Then, open up a browser that supports websockets, such as Google
Chrome, Firefox, or Safari (Chrome works best), and enter the
following URL::

  http://localhost:8900

Alternatively, you can use the ``gterm`` command to open up the
browser window.

Once within the ``graphterm`` browser page, select the host you
wish to connect to and create a new terminal session on the host.
Then try out the following commands::

  gls <directory>
  gvi  <text-filename>
  gweather

The first two are graphterm-aware scripts that imitate
basic features of the standard ``ls`` and ``vi`` commands.

*Usage Tips:*

 - *Terminal type:* The default terminal type is set to ``linux``,
   but it has a poor fullscreen mode and command history does
   not work properly. You can try out the terminal types ``screen``
   or ``xterm``, which may work better for some purposes.
   Use the ``--term_type`` option to set the default terminal type.
   (Fully supporting these terminal types is a work in progress.)

 - *Sessions and sharing:* For each host, sessions are assigned default names like
   ``tty1`` etc. You can also create unique session names simply by using
   it in an URL, e.g.::

      http://localhost:8900/local/mysession

    The first user to create a session "owns" it. Others connecting to the
    same session have read-only access (unless they "steal" the session).

 - *Multiple hosts:* More than one host can connect to the ``graphterm`` server.
   The local host is connected by default. To connect an additional
   host, run the following command on the host you wish to connect::

     gtermhost <serveraddr> <hostname>

    where ``serveraddr`` is the address or name of the computer where
    the server is running. You can use the ``--daemon=start`` option to
    run the command in the background. (By default, the server listens for host
    connections on port 8899.) 

 - *Security:* The ``--auth_code`` option can be used to specify
   an authentication code required for users connecting to the server.
   Although multiple hosts can connect to the terminal  server,
   initially,  it would be  best to use ``graphterm`` to simply  connect
   to ``localhost``,  on a computer with only trusted users.
   (*Note:* Users can always use SSH port forwarding to securely connect
   to the ``graphterm`` server listening as ``localhost`` on a remote
   computer, e.g.. ``ssh -L 8900:localhost:8900 user@example.com``)
   *Do not run the server as root*. As the code matures,
   security can be improved through the use of SSL certificates
   and server/client authentication. 
   These features are implemented in the code, but have not been
   properly configured/tested.

 - *Visual cues:* In the default theme, *blue* color denotes text that can
   be *clicked* or *tapped*. The action triggered by clicking depends on
   several factors, such as whether there is text in the current command
   line, and whether the Control modifier in the *Bottom menu* is active.
   Click on the last displayed prompt to toggle display of the *Bottom menu*.
   Clicking on other prompts toggles display of the command output
   (unless the Control modifier is used, in which case the command line
   is copied and pasted.)

 - *Copy/paste:* Click on the cursor to paste text from the clipboard.

 - *Drag and drop:* Sort of works within a window and across two
   windows. You can drag filenames (text-only) and drop them on
   folders, executables, or the command line. Visual feedback can
   be confusing.

 - *Command recall:* Use *up/down arrows* after partially typing a
   command to search for matching commands, and use *right arrow*
   for completion.

 - *Touch devices:* Click on the cursor to display virtual keyboard
   on the ipad etc.

 - *Themes:* Themes are a work in progress, especially the 3-D
   perspective theme (which only works on Chrome/Safari).



Support
=============================

 - Report bugs and other issues using the Github `Issue Tracker <https://github.com/mitotic/graphterm/issues>`_.

 - Additional documentation and updates will be made available on the project home page,
   `info.mindmeldr.com/code/graphterm <http://info.mindmeldr.com/code/graphterm>`_.


Implementation
==========================================

The GraphTerm server written in pure python, using the
`Tornado  web  framework <http://tornadoweb.org>`_,
with websocket support. The GraphTerm client uses standard
HTML5+Javascript+CSS.

GraphTerm extends the ``xterm`` terminal API by adding a
new control sequence for programs to transmit a CGI-like HTTP response
through standard output (via a websocket) to be displayed in the
browser window. GraphTerm-aware programs can interact with the
user using HTML forms etc.


API for GraphTerm-aware programs
==========================================

A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_
writes to to the standard output in a format similar to a HTTP
response, preceded and followed by
``xterm``-like *escape sequences*::

  \x1b[?1155;<cookie>h
  {"content_type": "text/html", ...}

  <table>
  ...
  </table>
  \x1b[?1155l

where ``<cookie>`` denotes a numeric value stored in the environment
variable ``GRAPHTERM_COOKIE``. (The random cookie is a security
measure that prevents malicious files from accessing GraphTerm.)
The opening escape sequence is followed by a *dictionary* of header
names and values, using JSON format. This is followed by a blank line,
and then any data (such as the HTML fragment to be displayed).

A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_
can be written in any language, much like a CGI script.
See the programs ``gls``, ``gvi``, ``gweather``, ``ec2launch`` and
``ec2list`` for examples of GraphTerm API usage.


Cloud integration
===============================

The GraphTerm distribution includes the scripts ``ec2launch, ec2list, ec2scp,``
and ``ec2ssh`` to launch and monitor Amazon Web Services EC2 instances
to run GraphTerm in the "cloud". You will need to have an Amazon AWS
account to use these scripts, and also need to install the ``boto`` python module. 
To create an instance, use the command::

   ec2instance <instance_tagname>

To *temporarily* run a publicly accessible GraphTerm server for
demonstration or teaching purposes, use the following command on the instance::

   gtermserver --daemon=start --auth_code=none --host=<primary_domain_or_address>

*Note: This is totally insecure and should not be used for handling any sensitive information.*
Ensure that the security group associated with the cloud instance
allows access to inbound TCP port 22 (for SSH access), 8900 (for GraphTerm users to connect), and
port 8899 (for GraphTerm hosts to connect). Also, when using ``ec2scp`` and ``sc2ssh``
to access the instance, ensure that you specify the appropriate login name (e.g., ``ubuntu``
for Ubuntu distribution).
Secondary cloud instances should connect to the GraphTerm server on
the primary instance using the command::

   gtermhost --daemon=start <primary_domain_or_address> <secondary_host_name>

For increased security in a publicly-accessible server, you will need to use a cryptic authentication code,
and also use *https* instead of *http*, with SSL cettificates . Since GraphTerm is currently in
*alpha* status, security cannot be guaranteed even with these options enabled.
(To avoid these problems, use SSH port forwarding to access GraphTerm
on ``localhost`` whenever possble.)

*otrace* integration
===============================

GraphTerm was originally developed as a graphical front-end for
`otrace <http://info.mindmeldr.com/code/otrace>`_,
an object-oriented python debugger. Use the ``--oshell``
option when connecting a host to the server enables ``otrace``
debugging features, allowing access to the innards of the
program running on the host.


Caveats and limitations
===============================

 - *Reliability:*  This software has not been subject to extensive testing. Use at your own risk.

 - *Platforms:*  The ``GraphTerm`` client should work on most recent browsers that support Websockets, such as Google Chrome, Firefox, and Safari. The ``GraphTerm`` server is pure-python, but with some OS-specific calls for file,  shell, and   terminal-related operations. It has been tested only on Linux and  Mac OS X so far.

 - *Current limitations:*
          * Support for ``xterm`` escape sequences is incomplete.
          * Most features of GraphTerm only work with the bash shell, not with C-shell, due the need for PROMPT_COMMAND to keep track of the current working directory.
          * At the moment, you cannot customize the shell prompt. (You
            should be able to in the future.)

Credits
===============================

``GraphTerm`` is inspired by two earlier projects that implement the
terminal interface within the browser,
`XMLTerm <http://www.xml.com/pub/a/2000/06/07/xmlterm/index.html>`_ and
`AjaxTerm <https://github.com/antonylesuisse/qweb/tree/master/ajaxterm>`_. 
It borrows many of the ideas from *XMLTerm* and re-uses chunks of code from
*AjaxTerm*.

The ``gls`` command uses icons from the `Tango Icon Library <http://tango.freedesktop.org>`_ 

 Graphical editing uses the `Ajax.org Cloud9 Editor <http://ace.ajax.org>`_

The 3D perspective mode was inspired by Sean Slinsky's `Star Wars
Opening Crawl with CSS3 <http://www.seanslinsky.com/star-wars-crawl-with-css3>`_.

``GraphTerm`` was developed as part of the `Mindmeldr <http://mindmeldr.com>`_ project, which is aimed at improving classroom interaction.


License
=====================

``GraphTerm`` is distributed as open source under the `BSD-license <http://www.opensource.org/licenses/bsd-license.php>`_.

