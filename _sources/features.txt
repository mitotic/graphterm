*********************************************************************************
GraphTerm toolchain and features
*********************************************************************************
.. contents::



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

   ``d3cloud [file]`` Display file (or stdin) content as a word
   cloud (see  :ref:`d3cloud_shot`)

   ``gbrowse [filename|URL]``    View files/URLs in a separate browser window

   ``gcp source dest`` Copy command supporting drag-and-drop for source/destination

   ``gdownload filename(s)`` Download piped data and files from terminal to desktop

   ``gfeed`` Display *stdin* input lines as a "feed"

   ``gframe [-f] [filename|URL]``    View files/URLs (or HTML from stdin) within
   an inline *iframe*  (see  :ref:`d3cloud_shot`)

   ``gimage [-f] [filenames]``     View images inline, or as a
   fullpage slideshow (with ``-f`` option)

   ``gjs javascript command``   Execute Javascript in the client browser

   ``glandslide [options] file.md``   A GraphTerm-aware version of
   Landslide, a web-based slideshow program  (see  :ref:`landslide_shot`)

   ``gload terminal_name`` Load a new terminal in the current window

   ``gls [-i] [filenames]``   Generate clickable directory listing

   ``gmatplot.py``   An inline ``matplotlib`` plotting package (see  :ref:`matplotlib_shot`)

   ``gmenu item subitem``   To access the menubar from the command line

   ``gncplot --variable=air --lon=0 --time=0 --lev=1000,0 air.mon.ltm.nc`` 2-D visualization of variables from a netCDF file

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

   ``gupload [filename|directory]`` Upload files from desktop into
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

.. index:: themes

.. _themes:

Themes
--------------------------------------------------------------------------------------------

Themes, selected using the menubar, are a work in progress. There is a
simple *dark* theme available, which can be modified by editing the
file ``graphterm/www/themes.dark.css``. The 3-D perspective theme is a
very primitive implementation which only works on Chrome/Safari (see
:ref:`stars3d_shot`).


.. index:: preferences, defaults

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


Slideshows, tracing etc.
===============================================================

.. index:: slideshows

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
The convenience command ``pdf2png`` can be used to convert a PDF file
to a set of images for viewing as a slide show::

  pdf2png slides.pdf; gimage -f slides-*.png


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

 
Webcasting, embedding, wildcards etc.
================================================================

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
