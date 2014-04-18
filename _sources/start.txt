*********************************************************************************
Getting started with GraphTerm
*********************************************************************************
.. contents::


Running GraphTerm
====================================================

To install ``GraphTerm``, you need to have Python 2.6+ and the Bash
shell on your Mac/Linux/Unix computer. For a quick install, if the python
``setuptools`` module is already installed on your system,
use the following two commands::

   sudo easy_install graphterm
   sudo gterm_setup            # Sets up the command toolchain

(See the :ref:`installation` section of the :doc:`README` file for
more installation options.)

To start the ``GraphTerm`` server, use the command::

    gtermserver --terminal --auth_type=none

This will run the  server and open a GraphTerm terminal window
using the default browser. For multi-user computers,
omit the ``--auth_type=none`` option
when starting the server, and enter the authentication code stored in
the file ``~/.graphterm/_gterm_auth.txt`` as needed. (The ``gterm``
command can automatically enter this code for you.)

You can access the GraphTerm server
using a browser that supports websockets, such as Google Chrome,
Firefox, Safari, or IE10 (Chrome works best), by entering the following URL::

    http://localhost:8900

In the ``graphterm`` browser page, select the GraphTerm host you
wish to connect to and create a new terminal session. (Note: The GraphTerm
host is different from the network hostname for the server.)
Within a GraphTerm window, you can use *terminal/new* menu option, or
type the command ``gmenu new``, to create a new GraphTerm session 

You can also open additional GraphTerm terminal windows using
the ``gterm`` command::

    gterm [session_name]
    gterm -u ubuntu --browser="Google Chrome" https://example.com:8900

where the terminal session name argument is optional.

Type  ``gtermserver -h`` to view all options for starting the server.
You can use the
``--daemon=start`` option to run the server in the background. The
``--host=hostname`` option is useful for listening on a public IP address instead
of the default ``localhost``. The ``--lc_export`` option can be used to
export the GraphTerm environment across SSH via the locale variables
(which sometimes works).
The ``--auth_type=none`` no authentication option is useful for
teaching or demonstration purposes, or on a single-user lapttop/desktop,
where security is not important.
Another useful no authentication option is ``--auth_type=name``
which enables simple name-based sharing. (For more on running publicly
accessible GraphTerm servers on the cloud, see :ref:`virtual-setup`.)

Within the terminal, try out the following commands::

   hello_gterm.sh
   gls <directory>
   gvi <text-filename>

The ``gls`` and ``gvi`` commands in the GraphTerm toolchain imitate
basic features of the standard ``ls`` and ``vi`` commands.
(*Note:* You need to execute the ``sudo gterm_setup`` command
to be able to use the GraphTerm toolchain. Otherwise, you will
encounter a ``Permission denied`` error.)
To display images as thumbnails, use the ``gls -i ...`` command.
Use the ``-h`` option to display help information for these commands,
and read the
`UsingGraphicalFeatures tutorial <http://code.mindmeldr.com/graphterm/UsingGraphicalFeatures.html>`_ for usage examples.

.. index:: graphterm-aware commands, toolchain

.. _toolchain:

Command Toolchain
====================================================

GraphTerm is bundled with a command toolchain that allow access to
many graphical features from the command line.

The toolchain commands can communicate with each other using pipes
and may be written any language,
e.g., Bash shell script, Python etc.
The commands reside in the directory ``$GTERM_DIR/bin`` and include the following:

   ``d3cloud [file]`` To display file (or stdin) content as a word
   cloud (see  :ref:`d3cloud_shot`)

   ``gbrowse [filename|URL]``    To view files/URLs in a separate browser window

   ``gcp source dest`` Copy command supporting drag-and-drop for source/destination

   ``gfeed`` Display *stdin* input lines as a "feed"

   ``gframe [-f] [filename|URL]``    To view files/URLs (or HTML from stdin) within
   an inline *iframe*  (see  :ref:`d3cloud_shot`)

   ``gimage [-f] [filenames]``     To view images inline, or as a
   fullpage slideshow (with ``-f`` option)

   ``gjs javascript command``   Execute Javascript in the client browser

   ``glandslide [options] file.md``   A GraphTerm-aware version of
   Landslide, a web-based slideshow program  (see  :ref:`landslide_shot`)

   ``gload terminal_name`` Load a new terminal in the current window

   ``gls [-i] [filenames]``   Generate clickable directory listing

   ``gmatplot.py``   An inline ``matplotlib`` plotting package (see  :ref:`matplotlib_shot`)

   ``gmenu item subitem``   To access the menubar from the command line

   ``gopen filename``    To open a file using the OS-specific ``open`` command

   ``gqrcode URL|text``    Display inline QR code

   ``greveal [options] file.md``    A GraphTerm-aware interface to `reveal.js <https://github.com/hakimel/reveal.js/>`_, a web-based slideshow program

   ``gsh terminal_name command args`` Execute command in the specified terminal (all output appears in terminal_name

   ``gsnowflake.py``  An inline plotting demo for the SVG module ``svgwrite``

   ``gterm`` Launch new GraphTerm windows (from outside browser)

   ``gtutor [...] example.py``  A command-line version of the Online
   Python Tutorial  at `pythontutor.com <http://pythontutor.com>`_
   (see :ref:`pytutor_shot`)

   ``gtweet [-s keywords] | tweet``  To send, search, or receive
   tweets  (see  :ref:`tweet_shot`)

   ``gupload [filename|directory]`` To upload files from desktop into
   the terminal

   ``gvi filename``   Open file using a browser-based visual editor

   ``hello_gterm.sh`` Hello World program that displays inline HTML text and image

   ``ystock stock_symbol`` To view a graph of stock price history

   ``yweather [location]`` To view weather forecasts (see  :ref:`weather_shot`)



Using the terminal
================================================================

.. index:: visual cues

Visual cues
--------------------------------------------------------------------------------------------

In the default theme, *blue* color denotes text that can be *clicked*
or *tapped* (see  :ref:`ls_shot`). The action triggered by clicking depends upon two
factors, whether there is text in the current command line,
and whether the Control modifier in the *Footer menu* is active.
Click on the last displayed prompt to toggle display of the *Footer menu*.
Clicking on other prompts toggles display of the command
output (unless the Control modifier is used, in which case the
entire command line is copied and pasted.)

.. index:: folders, opening files, navigating folders

Navigating folders/opening files
--------------------------------------------------------------------------------------------

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



.. index:: icons, images

Image and Icon display
--------------------------------------------------------------------------------------------

To display images inline, use the ``gimage`` command.
To activate icon display for commands like ``gls``, select
``view/icons`` in the menubar. By default, ``gls`` does not
display thumbnail icons of image files. (You can use ``gls -i`` to
force thumbnail icon display, but it can be a bit slow if there are a
large number of images.)


.. index:: menu shortcut

Menu shortcuts
--------------------------------------------------------------------------------------------

All the items in the top menubar can be accessed by typing *Control-J*
followed by a single letter for each level of menu selection. The
letter to be typed will be highlighted when you type *Control-J* and
is usually, but not always, the first letter of the item name. For example,
the sequence *Control-J t c* will select the menu item *terminal/clear*

The menubar can also be accessed from the
command line, using the ``gmenu`` command, e.g.::

    gmenu terminal clear

A single-word menu name is typed to select each menu level, and
preceding level names may be omitted, as long as there is no ambiguity, e.g.::

    gmenu clear


.. index:: command history

Command recall
--------------------------------------------------------------------------------------------

If the command line is empty, *up/down arrows* will use the underlying
shell for command recall (like Control-P and Control-N). If the
command line contains any text, including whitespace,
*up/down arrows* will cause GraphTerm to search for matching
previous commands that begin with the text already typed (ignoring
any leading whitespace). You can use the *right arrow* to
complete the recalled command (for editing) or use the *Enter* key
to execute it. Typing any other key, including the *left arrow*,
will cancel the command recall process. 

.. index:: copy/paste, paste

Copy/paste
--------------------------------------------------------------------------------------------

For certain browsers (e.g., desktop Chrome/Firefox),
the usual *Command-V* or *Control-V* key sequence should directly
paste text from the clipboard.
Alternatively, for some browsers, you can *click on the cursor*
before beginning the paste operation and then paste the text directly.
This second technique may not always work well for text copied from non-plain
text sources, such as a web page. A
workaround for this case is to paste the text into a temporary
location as plain text (such as in a plain text editor), and then
copy/paste it from there to GraphTerm.

If the above do not work, you can use the keyboard shortcut
*Control-O* to open a popup window, paste the text into the popup
window using the browser's paste menu command or a keyboard shortcut,
such as *Command/Control-V*, and then type *Control-O* again to insert
the text at the GraphTerm cursor location.  (The popup paste window
can also be accessed using the *terminal/paste special* menu item.)

.. index:: drag and drop

Drag and drop
--------------------------------------------------------------------------------------------

Sort of works! You can drag a filename (*grabbing the icon does not
work*) and drop it on a folder, an executable, or the command line.
For drag-and-drop between two GraphTerm windows running on the same
host, the file will be moved to the destination folder. For windows
on two different hosts, the file will be copied.
(Graphical feedback for this operation is not properly implemented at
this time. Look at the command line for the feedback.)

.. index:: ipad, android, tablet

iPad/Android tablet usage
--------------------------------------------------------------------------------------------

GraphTerm can be used on touch devices (phones/tablets), with some
limitations. Use the *view/footer* menu to enter keyboard input, send
special characters, access arrow keys etc. Tap the *Kbrd* in the
footer to display the keyboard.
(The *Footer menu* display can also be toggled by clicking on the last
displayed prompt.)

*Note:* You should turn off the *Autocapitalize* and *Autocorrect*
features in the language/keyboard settings if you want to do a lot of
typing on touch devices.


.. index:: themes

.. _themes:

Themes
--------------------------------------------------------------------------------------------

Themes, selected using the menubar, are a work in progress. There is a
simple *dark* theme available, which can be modified by editing the
file ``graphterm/www/themes.dark.css``. The 3-D perspective theme is a
very primitive implementation which only works on Chrome/Safari (see
:ref:`stars3d_shot`).


.. index:: preferences, prefs, defaults

.. _preferences:

Preferences
--------------------------------------------------------------------------------------------

Default terminal preferences, such as font size and themes, are stored
in the file ``gterm_prefs.json`` in your home directory.  The *view/save*
menu option can be used to save the current terminal configuration as
the default preference.

.. index:: terminal type

Choosing the terminal type
--------------------------------------------------------------------------------------------

The default terminal type is set to ``xterm``, but it may not always
work properly. You can also try out the terminal types ``screen`` or
``linux``,  which may work better for some purposes.
You can use the ``--term_type`` option when running the server to set
the default terminal type, or use the ``export TERM=screen`` command.
(Fully supporting these terminal types is a work in progress.)


Inline graphics, notebooks, slideshows, tracing etc.
===============================================================

.. index:: inline graphics, matplotlib

.. _inline_graphics:

Inline plots using matplotlib
--------------------------------------------------------------------------------------------

If you have ``matplotlib`` installed, the ``gpylab`` module in the
``$GTERM_DIR/bin`` directory can be used to start up the python
interpreter in ``pylab`` mode for inline graphics within the
GraphTerm terminal::

    python -i $GTERM_DIR/bin/gpylab.py
    >>> plot([1,2,4])

Run ``$GTERM_DIR/bin/gmatplot.py`` for a demo of inline graphics (see  :ref:`matplotlib_shot`).
See the function ``main`` in this file for sample plotting code.

 - Use ``ioff()`` to disable interactive mode
 - Use ``show()`` to update image
 - Use ``show(False)`` to display new image
 - Use ``display(fig)`` to display figure
 - Use ``resize_fig()`` to resize figure


.. index:: pandas, DataFrame

.. _pandas_mode:
 

Inline tables using pandas
--------------------------------------------------------------------------------------------

GraphTerm can display ``pandas`` DataFrame objects as a table using
HTML::

    python -i $GTERM_DIR/bin/gpylab.py
    >>> import pandas as pd
    >>> d = {'one' : [1., 2., 3., 4.],
    >>> 'two' : [4., 3., 2., 1.]}
    >>> pd.DataFrame(d)


.. index:: notebook

.. _notebook_mode:
 
Notebook mode
--------------------------------------------------------------------------------------------

GraphTerm supports a notebook mode, where code can be entered in
multiple cells and executed separately in each cell to display the
output. Cells can also contain comment text in `Markdown
<http://daringfireball.net/projects/markdown>`_ format.
Currently, the notebook mode can be used with the shell (``bash``),
or while running python (``python/ipython``) and ``R`` interpreters
(see `Using GraphTerm with R <http://code.mindmeldr.com/graphterm/R.html>`_).
Clicking on files with extensions
``*.ipynb``, ``*.py.md`` or ``*.R.md`` displayed in ``gls`` output
will automatically open a notebook using the appropriate program.
You can also try using the notebook mode 
with any other shell-like program (such as ``IDL`` or ``ncl``) which has a unique
prompt by typing *Shift-Enter* after starting the program. 

To enter the notebook mode, run the appropriate program and when the
program prompt appears,
select *notebook/new* on the top menu bar, or
type *Shift-Enter* (or *Control-Enter*, if you wish to read a notebook
file and/or specify the interpreter prompts).
You can also start up the python interpreter to load a notebook file, in
``*.ipynb`` or ``*.md`` format, from the command line::

    python -i $GTERM_DIR/bin/gpylab.py $GTERM_DIR/notebooks/SineWave.ipynb

(see  :ref:`notebook_shot`). 

Within notebook mode,
use *Shift-Enter* to execute a cell and move to the next, or
*Control-Enter* for in-place execution.
Additional keyboard shortcuts are listed
in the *help* menu, and are in many cases identical to that used by
`IPython Notebook <http://ipython.org/notebook.html>`_.

Notebooks can be saved any time using the IPython Notebook
(``*.ipynb``) or Markdown (``*.md``)
formats. The filename determines the format.
You can exit the notebook mode using
*notebook/quit* in the top menu bar, or by typing *Control-C*,
to return to the terminal mode.


.. index:: slides, slideshows

.. _slideshows:

Slideshows
--------------------------------------------------------------------------------------------


The ``glandslide`` command, which is a slightly modified version of the
web-based slideshow program `Landslide <https://github.com/adamzap/landslide>`_,
can be used to create a slideshow from Markdown (.md) or reStructured
Text (.rst) files (see  :ref:`landslide_shot`). A few sample ``.md`` files are provided in the
``$GTERM_DIR/bin/landslide`` directory of the distribution. To view a slideshow about
GraphTerm, type::

  glandslide -o $GTERM_DIR/bin/landslide/graphterm-talk1.md | gframe -f

Type ``h`` for help and ``q`` to quit the slideshow. (The unmodified
Landslide program can also be used, but remote sharing will not work.)

The ``greveal`` command can be used to display Markdown files as
slideshows using `reveal.js <https://github.com/hakimel/reveal.js/>`_::

    greveal $GTERM_DIR/bin/landslide/graphterm-talk1.md | gframe -f

Type ``b`` three times in quick succession to exit the slideshow.

The ``gimage`` command, which displays images inline, can also be used for
slideshows and simple presentations. Just ``cd`` to a directory
that has the images for a slideshow, and type::

  gimage -f

To select a subset of images in the directory, you can use a wildcard
pattern. For publicly webcasting a slideshow, use the ``-b`` option.


.. index:: execution tracing, online python tutor, python tutor

.. _python_tutor:

Code tracing using Python Tutor
--------------------------------------------------------------------------------------------


The command ``gtutor`` implements a command-line version of the
Online Python Tutorial from `pythontutor.com <http://pythontutor.com>`_.
It produces HTML output that can be piped to ``gframe`` for inline
display (see  :ref:`pytutor_shot`).
To trace the execution of a sample program ``example.py``, use it as follows::

  gtutor example.py | gframe -f

More sample programs may be found in the directory ``$GTERM_DIR/bin/pytutor/example-code``.
Of course, you can use ``gtutor`` to trace any other (small) python program as well.
Type ``gtutor -h`` to display the command line options.
*Note:* By default, ``gtutor`` accesses the browser CSS/JS files from
`pythontutor.com <http://pythontutor.com>`_.
To use ``gtutor`` in an offline-mode, you will need to specify the
``--offline`` option and also download the Online Python Tutorial
code from GitHub and copy/rename the main source directory
(currently ``v3``) as ``$GTERM_DIR/www/pytutor`` so that GraphTerm
can serve the CSS/JS files locally.

*Advanced usage:* You can embed tutorials within a Landslide/Markdown
presentation by including an ``iframe`` HTML element in the
presentation file, with the ``src`` attribute set to a graphterm
URL, such as ``http://localhost:8900/local/tutorial``. This will open
up a graphterm window where you can either run ``gtutor`` interactively or
use ``gframe -f`` to display an HTML file created previously using ``gtutor``.

 
Sharing, embedding, remote access, and security
================================================================


.. index:: sessions, screensharing

.. _screensharing:

Sessions and "screensharing"
--------------------------------------------------------------------------------------------

For each host, terminal sessions are assigned default names like
``tty1``, ``tty2`` etc. You can also create unique terminal session names simply by using it in an
URL, e.g.::

      http://localhost:8900/local/mysession/?qauth=code

The ``qauth`` value is a security code. It is optional and if you omit it
the browser will re-generate it for you by
requiring you to click on a link. (This requirement prevents
unauthorized access to the terminal URL from other web sites.)

The first user to create a session "owns" it, and can make the session
publicly available by disabling the *share/private* menubar option.
The public session URL (without the ``qauth`` code) can then be shared
with other users connected to the same GraphTerm server,
to provide read-only access to the terminal.
(This is like "screensharing", but more efficient,
because only the content is shared, not the theme/style data.)

If the session owner has unlocked the
session by disabling the *share/lock* menubar option,
other users can also *steal*
control of the session using the menubar button
(or using the *share/control* menu item).

For example, if you forgot to detach your session at work, you can
``ssh`` to your desktop from home, use SSH port forwarding
(see :ref:`ssh`) to securely access your work desktop, and then *steal* the
session using your home browser.

Normally, only a single user has control of a terminal session at a
time. There is a *share/tandem* option that can be enabled to allow
multiple users to control the terminal session at the same
time. However, this could sometimes have unpredictable effects.

NOTE: Although GraphTerm supports multiple users, it currently
assumes a cooperative environment, where everyone trusts everyone
else. This may change in the future.


.. index:: webcasting

Webcasting
--------------------------------------------------------------------------------------------


If you enable the *share/webcast* in the menubar, anyone can use the
session URL to view the session, without the need for
authentication, but will not be able to steal it.
*This feature is somewhat experimental; use it with caution to avoid exposing sensitive data.*

.. index:: embedding

.. _embedding:

Embedding and remote terminal commands
--------------------------------------------------------------------------------------------

Additional GraphTerm terminals can be embedded within any GraphTerm
terminal. For example, the following command::

    gframe -b -t terma termb

creates two terminals, ``terma`` and ``termb`` and embeds them within
the current terminal. The demo script
`metro.sh <https://github.com/mitotic/graphterm/blob/master/graphterm/bin/metro.sh>`_
illustrates the embedding of multiple terminals, each running a
different command (see screenshot :ref:`metro_shot`). The script also demonstrates the use of the ``gsh``
command to execute commands remotely on a terminal, e.g.::

    gsh terma yweather -f austin

The terminal name argument for ``gsh`` can be a wildcard
expression, e.g. ``'term*'``. Unlike ``ssh``, the ``gsh`` command does
not display the output of the remote command. You will need to view it
in the remote terminal. To load a remote terminal in the current
browser window, you can use::

    gload terma


.. index:: multiplexing, wildcard sessions

.. _wildcard:

Wildcard sessions and multiplexing
--------------------------------------------------------------------------------------------


A terminal session path is of the form ``session_host/session_name``. You can
use the shell wildcard patterns ``*, ?, []`` in the session path. For
example, you can open a wildcard session for multiple hosts using the URL::

      http://localhost:8900/*/tty1/?qauth=code

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

.. index:: multiple hosts

Multiple hosts
--------------------------------------------------------------------------------------------

More than one host can connect to the GraphTerm server. The ``localhost``
is connected by default (but this can be disabled using the
``--nolocal`` option). To connect an additional host, run the
following command on the computer you wish to connect::

     gtermhost --server_addr=<serveraddr> <hostname>

where ``serveraddr`` is the address or name of the computer where the
GraphTerm server is running. You can use the
``--daemon=start`` option to run the ``gtermhost`` command
in the background. By default, the Graphterm
server listens for host connections on port 8899. *The multiple host
feature should only be used within a secure network, not on the public internet.*

NOTE: Unlike the ``sshd`` server, the ``gtermhost`` command is designed to
be run by a normal user, not a privileged user. So different users can
connect to the GraphTerm server on ``localhost`` pretending to be different "hosts"
on the same computer. (If you are running a Python server, it can
connect directly to the GraphTerm server as a "host", allowing it to
be dynamically introspected and debugged using `otrace <http://code.mindmeldr.com/otrace>`_.)

.. index:: security

Security
--------------------------------------------------------------------------------------------


*The GraphTerm is not yet ready to be executed with root privileges*.
You should typically run it logged in as a regular user.
The ``--auth_type=local`` (default) and ``--auth_type=multiuser`` options should
be used for security, as they require an authentication code to create
a new terminal. Using the ``gterm`` command to create a new terminal
provides additional security, as the command validates the server
before opening a new terminal.
The ``--auth_type=none`` and ``--auth_type=name`` options
should only be used for teaching or demonstration purposes (or
on computers where only trusted users have access).

Although multiple hosts can connect to the terminal
server, initially, it would be best to use ``graphterm`` to just connect to
``localhost``, on a computer with only trusted users. You can always
use SSH port forwarding (see below) to securely connect to the
GraphTerm server for remote access.
As the code matures, security will be improved through
the use of SSL certificates and server/client authentication.
(SSL/https support is already built in. Feel free to experiment with
it, although it is not yet ready for everyday use.)

.. index:: ssh, port forwarding, remote access

.. _ssh:

SSH, port forwarding, and remote access
--------------------------------------------------------------------------------------------

Currently, the most secure way to access the GraphTerm server running
on a remote computer is to use SSH port forwarding. For example, if
you are connecting to your work computer from home, and wish to
connect to the GraphTerm server running as ``localhost`` on your work
computer, use the command::

   ssh -L 8901:localhost:8900 user@work-computer

This will allow you to connect to ``http://localhost:8901`` on the browser
on your home computer to access GraphTerm running on your work computer.

A completely different approach is to install GraphTerm on the remote
computer and run the ``gtermhost`` program remotely to allow it to
connect to the ``gtermserver`` running on your local computer using
SSH reverse port forwarding, e.g.::

   ssh -R 8899:localhost:8899 user@remote1 gtermhost remote1

In this case, the remote computer will appear as another host on your
local GraphTerm server. *Warning: If the remote computer is insecure,
reverse forwarding should not be used.*

If you do not wish to have a GraphTerm process running on
the remote machine, you can still use many features though GraphTerm
running on your local machine, because all communication takes place
via the standard output of the remote process. One quick solution is
use the *terminal/export environment* menu option to set the Bash
shell environment variables on the remote computer. This will allow
some, but not all, of GraphTerm's features to work on the remote
session.

A more permanent solution involves the following three steps:

 - Start the local GraphTerm server using the ``--lc_export``
   option. which exports the GraphTerm environment via the ``LC-*``
   environment variables which are often transmitted across SSH
   tunnels.

 - Copy the ``$GTERM_DIR/bin`` directory to your account on the remote
   machine to allow the GraphTerm toolchain to be
   accessed. Alternatively, you could simply install GraphTerm on the
   remote machine, even if you are never planning to start the server.

 - Append the file
   `$GTERM_DIR/bin/gprofile <https://github.com/mitotic/graphterm/blob/master/graphterm/bin/gprofile>`_
   to your ``.bash_profile`` on the remote machine, and uncomment/modify the
   last few lines so that ``$GTERM_DIR`` points to the parent of the
   directory where the toolchain files are installed. This ensures
   that the GraphTerm toolchain is included in your ``PATH`` on the remote
   machine, allowing commands like ``gls`` to work.
