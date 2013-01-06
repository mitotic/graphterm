GraphTerm Help (from the README file)
*********************************************************************************
.. sectnum::
.. contents::


Documentation and Support
=========================================================

Documentation and updates can be found on the project home page,
`code.mindmeldr.com/graphterm <http://code.mindmeldr.com/graphterm>`_,
which also has some
`tutorials and examples <http://code.mindmeldr.com/graphterm/graphterm-tutorials>`_
for using GraphTerm. You can also use the following command::

  glandslide -o graphterm-talk1.md | giframe

to view a slideshow about GraphTerm within GraphTerm (type``h`` for
help and ``q`` to quit).

There is a `Google Groups mailing list <https://groups.google.com/group/graphterm>`_
for announcements of new releases, posting questions related to
GraphTerm etc. You can also follow `@graphterm <https://twitter.com/intent/user?screen_name=graphterm>`_ on Twitter for updates.

To report bugs and other issues, use the Github `Issue Tracker <https://github.com/mitotic/graphterm/issues>`_.


Usage
=================================

To start the ``GraphTerm`` server, use the command::

  gtermserver --auth_code=none

Type  ``gtermserver -h`` to view all options. You can use the
``--daemon=start`` option to run it in the background.

Once the server is running, you can open a terminal window on the
localhost in the following ways:

 - Specify the ``--terminal`` option when starting ``gtermserver``

 - Use the ``gterm`` command in any terminal

 - Within a GraphTerm window, you can use the ``New`` menu option, or
   use the keyboard shortcut *Ctrl-Alt-T* to create a new GraphTerm window

To open a remote terminal window, open up a browser of your
choice that supports websockets, such as Google Chrome,
Firefox, or Safari (Chrome works best), and enter the following URL::

  http://localhost:8900

Once within the ``graphterm`` browser page, select the host you
wish to connect to and create a new terminal session on the host.

Once you have a terminal, try out the following commands::

  gls <directory>
  gvi <text-filename>

These are graphterm-aware scripts that imitate
basic features of the standard ``ls`` and ``vi`` commands.
To display images as thumbnails, use the ``gls -i ...`` command.
Use the ``-h`` option to display help information for these commands,
and read the
`UsingGraphicalFeatures tutorial <http://code.mindmeldr.com/graphterm/graphterm-tutorials/graphterm-tutorial-graphical>`_ for usage examples.

You can use the command ``which gls`` to determine the directory
containing graphterm-aware commands, to browse
for other commands, which include:

   ``giframe [filename|URL]``    To view files/URLs (or HTML from stdin) in
   inline *iframe*

   ``gimage [-f] [filenames]``     To view images inline, or as a
   fullpage slideshow (with ``-f`` option)

   ``glandslide``    A GraphTerm-aware version of Landslide, a web-based slideshow program

   ``gmatplot.py``   A ``matplotlib`` plotting demo

   ``yweather [location]`` To view weather forecasts

   ``gtweet [-s keywords]|tweet``  To send, search, or receive tweets

(There is also a sample ``gcowsay`` command which can be downloaded
separately from its `Github repository <https://github.com/mitotic/gcowsay>`_)


Visual cues
-----------------------------------------------------------

In the default theme, *blue* color denotes text that can be *clicked*
or *tapped*. The action triggered by clicking depends upon two
factors, whether there is text in the current command line,
and whether the Control modifier in the *Bottom menu* is active.
Click on the last displayed prompt to toggle display of the *Bottom
menu*. Clicking on other prompts toggles display of the command
output (unless the Control modifier is used, in which case the
entire command line is copied and pasted.)


Navigating folders/opening files
----------------------------------------------------------------------

You can navigate folders in GraphTerm just like you would do in a GUI,
while retaining the ability to drop back to the CLI at any time.
*If the current command line is empty,*
clicking on a folder or filename displayed by the ``gls`` command will
change the current directory to the folder, or cause the file to be
opened.
*If you have typed anything at all in the current command line,
even if it is just a space*, the clicking action will cause text to be
pasted into the command line, without any
command being executed. You can edit the pasted text, then press the
Enter key to execute it.

Icon display
------------------------------

Select ``icons`` in the top menu to activate icon display for commands like
``gls``.


Themes
---------------------------------------------------------------------------------------

Themes, selected using the top menu, are a work in progress, especially the 3-D perspective theme
(which only works on Chrome/Safari).


Copy/paste
---------------------------------------------------------------------------------------

*Click on the cursor* before beginning the paste operation (on the command line,
a box will appear at the cursor location). Then use the
browser's paste menu command or a keyboard shortcut (like *Command/Control-V*) to
paste the text. Alternatively, you can use the *Actions->Paste special* menu item.


Drag and drop
-------------------------------------------------------------------------
Sort of works! You can drag a filename (*grabbing the icon does not
work*) and drop it on a folder, an executable, or the command line.
For drag-and-drop between two GraphTerm windows running on the same
host, the file will be moved to the destination folder. For windows
on two different hosts, the file will be copied.
(Graphical feedback for this operation is not properly implemented at
this time. Look at the command line for the feedback.)

Command recall
---------------------------------------------------------------------------------------

If the command line is empty, *up/down arrows* will use the underlying
shell for command recall (like Control-P and Control-N). If the
command line contains any text, including whitespace,
*up/down arrows* will cause GraphTerm to search for matching
previous commands that begin with the text already typed (ignoring
any leading whitespace). You can use the *right arrow* to
complete the recalled command (for editing) or use the *Enter* key
to execute it. Typing any other key, including the *left arrow*,
will cancel the command recall process. 

iPad usage
---------------------------------------------------------------------------------------

Click on the cursor to display virtual keyboard on the iPad. The
*Bottom menu*, exposed by clicking on the lowermost prompt, can be
quite useful on the iPad.

Choosing the terminal type
---------------------------------------------------------------------------------------

The default terminal type is set to ``xterm``, but it may not always
work properly. You can also try out the terminal types ``screen`` or
``linux``,  which may work better for some purposes.
You can use the ``--term_type`` option when running the server to set
the default terminal type, or use the ``export TERM=screen`` command.
(Fully supporting these terminal types is a work in progress.)

Multiple hosts
---------------------------------------------------------------------------------------

More than one host can connect to the GraphTerm server. The local
host is connected by default (but this can be disabled using the
``--nolocal`` option). To connect an additional host, run the
following command on the computer you wish to connect::

     gtermhost --server_addr=<serveraddr> <hostname>

where ``serveraddr`` is the address or name of the computer where the
GraphTerm server is running (which defaults to localhost). You can use the
``--daemon=start`` option to run the ``gtermhost`` command
in the background. By default, the Graphterm
server listens for host connections on port 8899. *The multiple host
feature should only be used within a secure network, not on the public internet.*

NOTE: Unlike the ``sshd`` server, the ``gtermhost`` command is designed to
be run by a normal user, not a privileged user. So different users can
connect to the GraphTerm server pretending to be different "hosts"
on the same computer. (If you are running a Python server, it can
connect directly to the GraphTerm server as a "host", allowing it to
be dynamically introspected and debugged using `otrace <http://code.mindmeldr.com/otrace>`_.)


Sessions and "screensharing"
---------------------------------------------------------------------------------------

For each host, sessions are assigned default names like ``tty1``
etc. You can also create unique session names simply by using it in an
URL, e.g.::

      http://localhost:8900/local/mysession

Anyone with access to the GraphTerm server can use the session URL
to connect to it. This is like "screensharing", but more efficient,
because only the content is shared, not the graphical themes.
The first user to create a session "owns" it, until they detach from
it. Others connecting to the same session have read-only access,
unless they "steal" the session (see the *Action* menu).
For example, if you forgot to detach your session at work, you can
``ssh`` to your desktop from home, use SSH port forwarding (see below)
to securely access your work desktop, and then steal the
session using your home browser.

NOTE: Although GraphTerm supports multiple users, it currently
assumes a cooperative environment, where everyone trusts everyone
else. (This may change in the future.)


Wildcard sessions and multiplexing
---------------------------------------------------------------------------------------

A session path is of the form ``session_host/session_name``. You can
use the shell wildcard patterns ``*, ?, []`` in the session path. For
example, you can open a wildcard session for multiple hosts using the URL::

      http://localhost:8900/*/tty1

For normal shell terminals, a wildcard session will open a "blank" window,
but any input you type in it will be broadcast to all sessions
matching the pattern. (To receive visual feedback,
you will need to view one or more of the matching sessions at the
same time.)

For ``otrace`` debugging sessions of the form ``*/osh``, GraphTerm
will multiplex the input and output in wildcard terminals. Your input
will be echoed and broadcast, and output from each of the matching
sessions will be displayed, preceded by an identifying header
(with the special string ``ditto`` used to indicate repeated output).
See the *otrace* integration section for more information.

NOTE: Multiplexed input/output display cannot be easily implemented for
regular shell terminals.

Webcasting
---------------------------------------------------------------------------------------

If you enable the *Webcast* in the top menu, anyone can use the
session URL to view the session, without the need for
authentication, but will not be able to steal it. *Use this feature
with caution to avoid exposing exposing sensitive data.*

Slideshows
---------------------------------------------------------------------------------------

The ``glandslide`` command, which is a slightly modified version of the
web-based slide slideshow program `Landslide <https://github.com/adamzap/landslide>`_,
can be used to create a slideshow from Markdown (.md) or reStructured
Text (.rst) files. A few sample ``.md`` files are provided in the
``graphterm/bin/landslide`` directory of the distribution. To view a slideshow about
GraphTerm, type::

  glandslide -o graphterm-talk1.md | giframe

Type ``h`` for help and ``q`` to quite the slideshow. (The unmodified
Landslide program can also be used, with the ``-i`` option, but remote sharing will not work.)

The ``gimage`` command, which displays images inline, can also be used for
slideshows and simple presentations. Just ``cd`` to a directory
that has the images for a slideshow, and type::

  gimage -f

To select a subset of images in the directory, you can use a wildcard
pattern. For publicly webcasting a slideshow, use the ``-b`` option.

Widgets, sockets, and interactivity
--------------------------------------------------------------------------------------

A widget appears as an overlay on the terminal (like
*picture-in-picture* for TVs, or dashboard widgets on the Mac). This is an
experimental feature that allows programs running in the background to
display information overlaid on the terminal. The widget is accessed
by redirecting ``stdout`` to a Bash ``tcp`` socket device whose
address is stored in the environment variable ``GRAPHTERM_SOCKET``.
For example, the following command will run a background job
to open a new terminal in an overlay *iframe*::

  giframe --opacity=0.2 http://localhost:8900/local/new > $GRAPHTERM_SOCKET &

You can use the overlay terminal just like a regular terminal, including
having recursive overlays within the overlay!

A specific example of widget use is to display live feedback on the
screen during a presentation. You can try it out in a directory that
contains your presentation slides as images::

  gfeedback 2> $GRAPHTERM_SOCKET 0<&2 | gfeed > $GRAPHTERM_SOCKET &
  gimage -f

The first command uses ``gfeedback`` to capture feedback from others
viewing the terminal session as a stream of lines from
$GRAPHTERM_SOCKET. The viewers use the overlaid *feedback* button
to provide feedback. The ``stdout`` from ``gfeedback`` is piped to
``gfeed`` which displays its ``stdin`` stream as a  "live feed"
overlay, also via $GRAPHTERM_SOCKET.
(The ``gimage -f`` command displays all the images in the directory as a
slideshow.)

To display a live twitter feed as an overlay on a presentation, you can use the commands::

   gtweet -f -s topic > $GRAPHTERM_SOCKET &
   gimage -f


Security
---------------------------------------------------------------------------------------

*The GraphTerm is not yet ready to be executed with root privileges*.
Run it logged in as a regular user. The ``--auth_code`` option can be
used to specify an authentication code required for users connecting
to the server. Although multiple hosts can connect to the terminal
server, initially, it would be best to use ``graphterm`` to just connect to
``localhost``, on a computer with only trusted users. You can always
use SSH port forwarding (see below) to securely connect to the
GraphTerm server for remote access.
As the code matures, security will be improved through
the use of SSL certificates and server/client authentication.
(SSL/https support is already built in. Feel free to experiment with
it, although it is not yet ready for everyday use.)


SSH and port forwarding
---------------------------------------------------------------------------------

If you login to a remote computer using SSH, you can use the
*Action -> Export Environment*  menu option to set the Bash shell
environment variables on the remote computer. This will allow
some, but not all, of GraphTerm's features to work on the remote
session. If you wish to use more features, set the ``PATH`` environment
variable on the remote machine to allow access to ``gls`` and other
commands, and also use reverse port forwarding to forward your
local port(s) to the remote computer, e.g.::

   ssh -R 8898:localhost:8898 user@remote-computer

Currently, the most secure way to access the GraphTerm server running
on a remote computer is to use SSH port forwarding. For example, if
you are connecting to your work computer from home, and wish to
connect to the GraphTerm server running as ``localhost`` on your work
computer, use the command::

   ssh -L 8900:localhost:8900 user@work-computer

This will allow you to connect to ``http://localhost:8900`` on the browser
on your home computer to access GraphTerm running on your work computer.


*otrace* integration
===============================

GraphTerm was originally developed as a graphical front-end for
`otrace <http://code.mindmeldr.com/otrace>`_,
an object-oriented python debugger. Any Python program
can serve as a "host" and be connected to the GraphTerm server
using the ``gotrace`` command::

  gotrace example.py

The above command loads ``example.py`` as a module and connects
to the GraphTerm server for debugging. This program will appear in
the list of hosts under the name ``example``. Open the terminal session
``example/osh`` to connect to the *otrace* console, and issue
the ``run <function>`` command to begin executing a function in
``example.py``. You can also initiate program execution
directly from the command line as follows::

  gotrace -f test example.py arg1 arg2
 
The above command executes the function ``test(arg=[])`` in
``example.py``, where ``arg`` is a list of string arguments from
the command line.

If you wish to use the *otrace* console features for multiplexing,
without actually needing to a debug a program, you can use
the ``--oshell`` option when using ``gtermhost`` to connect
to the server.

(You can also embed code in a Python program to directly connect
to the GraphTerm server for monitoring/debugging. See
``gotrace.py`` to find out how it can be done.)


Cloud integration
===============================

The GraphTerm distribution includes the scripts ``ec2launch, ec2list, ec2scp,``
and ``ec2ssh`` to launch and monitor Amazon Web Services EC2
instances. These are the scripts used to test new
versions of GraphTerm by running them in the "cloud".
You will need to have an Amazon AWS
account to use these scripts, and also need to install
the ``boto`` python module. 

To create an instance, use the ``ec2launch`` command.
You will be presented with a "web form" to enter details of the instance
to be launched. Once you fill in the form and submit it, a command
line will be automatically created, with command options, to launch
the instance. To launch another instance with slightly different
properties, you can simply recall the command line and edit it.
Ensure that the security group associated with the cloud instance
allows access to inbound TCP port 22 (for SSH access), 8900
(for GraphTerm users to connect), and
port 8899 (for GraphTerm hosts to connect).

To *temporarily* run a publicly accessible GraphTerm server for
demonstration or teaching purposes, log in to the instance using
the command ``ec2ssh ubuntu@instance_address``, wait a few
minutes for ``tornado`` and ``graphterm`` packages to finish
installing, and then issue the following command::

   gtermserver --daemon=start --auth_code=none --host=<primary_domain_or_address>

*Note: This is totally insecure and should not be used for handling any sensitive information.*

Secondary cloud instances should connect to the GraphTerm server on
the primary instance using the command::

   gtermhost --daemon=start --server_addr=<primary_domain_or_address> <secondary_host_name>

For increased security in a publicly-accessible server,
you can use a cryptic authentication code,
and also use *https* instead of *http*, with SSL certificates.
Since GraphTerm is currently in *alpha* status,
security cannot be guaranteed even with these options enabled.
(To avoid these problems, use SSH port forwarding to access GraphTerm
on ``localhost`` whenever possble.)


API for GraphTerm-aware programs
==========================================

A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_
writes to to the standard output in a format similar to a HTTP
response, preceded and followed by
``xterm``-like *escape sequences*::

  \x1b[?1155;<cookie>h
  {"content_type": "text/html", ...}

  <div>
  ...
  </div>
  \x1b[?1155l

where ``<cookie>`` denotes a numeric value stored in the environment
variable ``GRAPHTERM_COOKIE``. (The random cookie is a security
measure that prevents malicious files from accessing GraphTerm.)
The opening escape sequence is followed by a *dictionary* of header
names and values, using JSON format. This is followed by a blank line,
and then any data (such as the HTML fragment to be displayed).

A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_
can be written in any language, much like a CGI script.
See the programs ``gls``, ``gimage``, ``giframe``, ``gvi``, ``gfeed``,
``yweather``, ``ec2launch`` and ``ec2list`` for examples
of GraphTerm API usage. You can use the ``which gls``
command to figure out where these programs are located.
The file ``gtermapi.py`` contains many helper functions for accessing
the GraphTerm API. See also the
`gcowsay <https://github.com/mitotic/gcowsay>`_ program for an
example of a stand-alone GraphTerm-aware command.

Implementation
==========================================

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


Caveats and limitations
===============================

 - *Reliability:*  This software has not been subject to extensive testing. Use at your own risk.

 - *Platforms:*  The ``GraphTerm`` client should work on most recent browsers that support Websockets, such as Google Chrome, Firefox, and Safari. The ``GraphTerm`` server is pure-python, but with some OS-specific calls for file,  shell, and   terminal-related operations. It has been tested only on Linux and  Mac OS X so far.

 - *Current limitations:*
          * Support for ``xterm`` escape sequences is incomplete.
          * Most features of GraphTerm only work with the bash shell, not with C-shell, due the need for PROMPT_COMMAND to keep track of the current working directory.
          * At the moment, you cannot customize the shell prompt. (You
            should be able to so in the future.)

Credits
===============================

``GraphTerm`` is inspired by two earlier projects that implement the
terminal interface within the browser,
`XMLTerm <http://www.xml.com/pub/a/2000/06/07/xmlterm/index.html>`_ and
`AjaxTerm <https://github.com/antonylesuisse/qweb/tree/master/ajaxterm>`_. 
It borrows many of the ideas from *XMLTerm* and re-uses chunks of code from
*AjaxTerm*. The server uses the asynchronous `Tornado web framework
<http://tornadoweb.org>`_ and the client uses `jQuery <http://jquery.com>`_.

The ``gls`` command uses icons from the `Tango Icon Library
<http://tango.freedesktop.org>`_, and graphical editing uses the `Ajax.org Cloud9 Editor <http://ace.ajax.org>`_

The 3D perspective mode was inspired by Sean Slinsky's `Star Wars
Opening Crawl with CSS3 <http://www.seanslinsky.com/star-wars-crawl-with-css3>`_.

``GraphTerm`` was developed as part of the `Mindmeldr <http://mindmeldr.com>`_ project, which is aimed at improving classroom interaction.


License
=====================

``GraphTerm`` is distributed as open source under the `BSD-license <http://www.opensource.org/licenses/bsd-license.php>`_.

