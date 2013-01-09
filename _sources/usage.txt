*********************************************************************************
 Using GraphTerm
*********************************************************************************
.. contents::


Introduction
====================================================

(See the README file for information on installing GraphTerm.)

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
`UsingGraphicalFeatures tutorial <http://code.mindmeldr.com/graphterm/UsingGraphicalFeatures.html>`_ for usage examples.

You can use the command ``which gls`` to determine the directory
containing graphterm-aware commands, to browse
for other commands, which include:

   ``giframe [-f] [filename|URL]``    To view files/URLs (or HTML from stdin) in
   inline *iframe*

   ``gimage [-f] [filenames]``     To view images inline, or as a
   fullpage slideshow (with ``-f`` option)

   ``glandslide``    A GraphTerm-aware version of Landslide, a web-based slideshow program

   ``gtutor [...] example.py``  A command-line version of the Online Python Tutorial  at `pythontutor.com <http://pythontutor.com>`_

   ``gmatplot.py``   An inline ``matplotlib`` plotting demo

   ``gsnowflake.py``  An inline plotting demo for the SVG module ``svgwrite``

   ``yweather [location]`` To view weather forecasts

   ``gtweet [-s keywords]|tweet``  To send, search, or receive tweets

(There is also a sample ``gcowsay`` command which can be downloaded
separately from its `Github repository <https://github.com/mitotic/gcowsay>`_)


Visual cues
================================================================

In the default theme, *blue* color denotes text that can be *clicked*
or *tapped*. The action triggered by clicking depends upon two
factors, whether there is text in the current command line,
and whether the Control modifier in the *Bottom menu* is active.
Click on the last displayed prompt to toggle display of the *Bottom
menu*. Clicking on other prompts toggles display of the command
output (unless the Control modifier is used, in which case the
entire command line is copied and pasted.)


Navigating folders/opening files
================================================================

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
================================================================

Select ``icons`` in the top menu to activate icon display for commands like
``gls``.


Themes
================================================================


Themes, selected using the top menu, are a work in progress, especially the 3-D perspective theme
(which only works on Chrome/Safari).


Copy/paste
================================================================

For certain browsers (e.g., desktop Chrome/Safari),
the usual *Command-V* or *Control-V* key sequence should directly
paste text from the clipboard. If that doesn't work, there are a couple
of other ways to paste text.
First, you can use the keyboard shortcut *Control-T* to open a
popup window, paste the text into the popup window using the
browser's paste menu command or a keyboard shortcut,
such as *Command/Control-V*, and then type *Control-T* again to
insert the text at the GraphTerm cursor location.
(The popup paste window can also be accessed from the *Actions* menu.)
Alternatively, for some browsers, and on the iPad, you can *click on the cursor*
before beginning the paste operation and then paste the text directly.
This second technique may not always work well for text copied from non-plain
text sources, such as a web page.


Drag and drop
================================================================

Sort of works! You can drag a filename (*grabbing the icon does not
work*) and drop it on a folder, an executable, or the command line.
For drag-and-drop between two GraphTerm windows running on the same
host, the file will be moved to the destination folder. For windows
on two different hosts, the file will be copied.
(Graphical feedback for this operation is not properly implemented at
this time. Look at the command line for the feedback.)

Command recall
================================================================


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
================================================================


Click on the cursor to display virtual keyboard on the iPad. The
*Bottom menu*, exposed by clicking on the lowermost prompt, can be
quite useful on the iPad.

Choosing the terminal type
================================================================


The default terminal type is set to ``xterm``, but it may not always
work properly. You can also try out the terminal types ``screen`` or
``linux``,  which may work better for some purposes.
You can use the ``--term_type`` option when running the server to set
the default terminal type, or use the ``export TERM=screen`` command.
(Fully supporting these terminal types is a work in progress.)


Multiple hosts
================================================================

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
================================================================

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
================================================================


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
================================================================


If you enable the *Webcast* in the top menu, anyone can use the
session URL to view the session, without the need for
authentication, but will not be able to steal it. *Use this feature
with caution to avoid exposing exposing sensitive data.*

Slideshows
================================================================


The ``glandslide`` command, which is a slightly modified version of the
web-based slide slideshow program `Landslide <https://github.com/adamzap/landslide>`_,
can be used to create a slideshow from Markdown (.md) or reStructured
Text (.rst) files. A few sample ``.md`` files are provided in the
``graphterm/bin/landslide`` directory of the distribution. To view a slideshow about
GraphTerm, type::

  glandslide -o graphterm-talk1.md | giframe -f

Type ``h`` for help and ``q`` to quit the slideshow. (The unmodified
Landslide program can also be used, with the ``-i`` option, but remote sharing will not work.)

The ``gimage`` command, which displays images inline, can also be used for
slideshows and simple presentations. Just ``cd`` to a directory
that has the images for a slideshow, and type::

  gimage -f

To select a subset of images in the directory, you can use a wildcard
pattern. For publicly webcasting a slideshow, use the ``-b`` option.

Command-line version of pythontutor.com
================================================================


The command ``gtutor`` implements a command-line version of the
Online Python Tutorial from `pythontutor.com <http://pythontutor.com>`_.
It produces HTML output that can be piped to ``giframe`` for inline display.
To trace the execution of a sample program ``example.py``, use it as follows::

  gtutor example.py | giframe -f

More sample programs may be found in the directory ``$GRAPHTERM_DIR/bin/pytutor/example-code``.
Of course, you can use ``gtutor`` to trace any other (small) python program as well.
Type ``gtutor -h`` to display the command line options.
*Note:* By default, ``gtutor`` accesses the browser CSS/JS files from
`pythontutor.com <http://pythontutor.com>`_.
To use ``gtutor`` in an offline-mode, you will need to specify the
``--offline`` option and also download the Online Python Tutorial
code from GitHub and copy/rename the main source directory
(currently ``v3``) as ``$GRAPHTERM_DIR/www/pytutor`` so that GraphTerm
can serve the CSS/JS files locally.

*Advanced usage:* You can embed tutorials within a Landslide/Markdown
presentation by including an ``iframe`` HTML element in the
presentation file, with the ``src`` attribute set to a graphterm
URL, such as ``http://localhost:8900/local/tutorial``. This will open
up a graphterm window where you can either run ``gtutor`` interactively or
use ``giframe -f`` to display an HTML file created previously using ``gtutor``.

 
Widgets, sockets, and interactivity
================================================================


A widget appears as an overlay on the terminal (like
*picture-in-picture* for TVs, or dashboard widgets on the Mac). This is an
experimental feature that allows programs running in the background to
display information overlaid on the terminal. The widget is accessed
by redirecting ``stdout`` to a Bash ``tcp`` socket device whose
address is stored in the environment variable ``GRAPHTERM_SOCKET``.
For example, the following command will run a background job
to open a new terminal in an overlay *iframe*::

  giframe -f --opacity=0.2 http://localhost:8900/local/new > $GRAPHTERM_SOCKET &

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
================================================================


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
================================================================


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
