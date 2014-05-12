.. _README:

README
==================================================================
 
.. contents::

Introduction
----------------------------------------------------------------------------------------------

``GraphTerm`` is a browser-based graphical terminal interface, that
aims to seamlessly blend the command line and graphical user
interfaces. You can use it just like a regular terminal,
backwards-compatible with ``xterm``, and access the additional
graphical features as needed. These features can help impove your
terminal workflow by integrating graphical operations with the
command line and letting you view images and HTML output inline.

GraphTerm has several funky features, but two of the most useful
practical applications are:

 - an **inline data visualization tool** for plotting with Python or R
   that can work seamlessly across SSH login
   boundaries, with an optional notebook interface. (For remote
   access, it also serves as a detachable terminal, like
   ``tmux`` or ``screen``.)

 - a **virtual computer lab** for teaching and demonstrations. The
   GraphTerm server can be set up in the cloud and accessed by
   multiple users using their laptop/mobile browsers, with Google
   Authentication. The lab instructor can
   `monitor all the users'  terminals <http://code.mindmeldr.com/graphterm/screenshots.html#dashboard-for-a-virtual-computer-lab-viewing-user-terminals>`_
   via a "dashboard", and users can collaborate with each other by
   sharing terminals and notebooks.


 **Screenshot 1: Inline plotting on a remote machine (via SSH)**

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-ssh-plot.png
   :align: center
   :width: 90%
   :figwidth: 85%

.. raw:: html

   <hr style="margin-bottom: 3em;">
..

 **Screenshot 2: Monitoring multiple user terminals in a "virtual computer lab"**

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gadmin-terminals.png
   :align: center
   :width: 90%
   :figwidth: 85%


GraphTerm builds upon two earlier projects, 
`XMLTerm <http://www.xml.com/pub/a/2000/06/07/xmlterm/index.html>`_
which implemented a terminal using the Mozilla framework and
`AjaxTerm <https://github.com/antonylesuisse/qweb/tree/master/ajaxterm>`_
which is an AJAX/Python terminal implementation. (Other recent
projects along these lines include  `TermKit <http://acko.net/blog/on-termkit/>`_
and `Terminology <http://www.enlightenment.org/p.php?p=about/terminology>`_.)

A GraphTerm terminal window is just a web page served from the
GraphTerm server program. Multiple users can connect
simultaneously to the web server to share terminal sessions.
Multiple hosts can also connect to the server (on a different port),
allowing a single user to access all of them via the browser.
The GraphTerm server acts as a *router*, sending input from browser
windows for different users to the appropriate terminal (pseudo-tty)
sessions running on different hosts, and transmitting the
terminal output back to the browser windows.

The interface is designed to be touch-friendly for use with
tablets, with tappable links and command re-use to minimize the need for
a keyboard. It preserves history for all commands,
whether entered by typing, clicking, or tapping.
It is also themable using CSS.

You can use the GraphTerm API to build "mashups" of web applications
that work seamlessly within the terminal.  Sample mashups include:

 - ``greveal``: Inline version of ``reveal.js`` to display Markdown files as slideshows
 - ``gtutor``: Inline version of `pythontutor.com <http://pythontutor.com>`_ for visual tracing of python programs
 - ``yweather``: Using Yahoo weather API to display weather

Images of GraphTerm in action can be found in `screenshots <https://github.com/mitotic/graphterm/blob/master/docs/screenshots.rst>`_ 
and in this `YouTube Video <http://youtu.be/TvO1SnEpwfE>`_.
Here is a sample screenshot showing the output of the
`metro.sh <https://github.com/mitotic/graphterm/blob/master/graphterm/bin/metro.sh>`_
command, which embeds six smaller terminals within the main terminal, running
six different commands from the GraphTerm toolchain: (i) live twitter stream output using
``gtweet``, (ii) weather info using ``yweather``,
(ii) slideshow from markdown file using ``greveal`` and *reveal.js*,
(iv) word cloud using ``d3cloud`` and *d3.js*, (v) inline graphics using ``gmatplot.py``,
and (vi) notebook mode using the standard python interpreter.


 **Screenshot 3: Embedding terminals within GraphTerm**

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-metro.jpg
   :align: center
   :width: 90%
   :figwidth: 100%

.. _installation:

Installation
----------------------------------------------------------------------------------------------

To install ``GraphTerm``, you need to have Python 2.6+ and the Bash
shell on your Mac/Linux/Unix computer. For a quick install, use one of
the following two options::

   sudo pip install graphterm
        OR
   sudo easy_install graphterm; sudo gterm_setup

If you wish to install GraphTerm as a non-root user within an Anaconda
or Enthought Python environment, you can omit the ``sudo`` prefix.

For a manual install procedure, download the release tarball from the
`Python Package Index <http://pypi.python.org/pypi/graphterm>`_, untar,
and execute the following command in the ``graphterm-<version>`` directory::

   python setup.py install

For the manual install, you will also need to install the ``tornado``
web server, which can be downloaded from
`http://www.tornadoweb.org <http://www.tornadoweb.org>`_

You can also try out GraphTerm without installing it, by untarring the
source tarball (or checking out the source from ``github``). You can
run the server as ``./gtermserver.py`` within the ``graphterm``
subdirectory of the distribution, after you have installed the
``tornado`` package on your system (or within the ``graphterm``
subdirectory of the source distribution). In this case, certain
commands in the ``graphterm/bin`` subdirectory, such as ``gterm`` and
``gauth``, would need to be accessed as ``gterm.py`` and ``gauth.py`` respectively.

You can browse the ``GraphTerm`` source code, and download the development
version, at `Github <https://github.com/mitotic/graphterm>`_.

Quick Start
----------------------------------------------------------------------------------------------

To start the ``GraphTerm`` server, use the command::

    gtermserver --terminal --auth_type=none

This will run the  server and open a GraphTerm terminal window
using the default browser. For multi-user computers,
omit the ``--auth_type=none`` option
when starting the server, and enter the authentication code stored in
the file ``~/.graphterm/_gterm_auth.txt`` as needed. (The ``gterm``
command can automatically enter this code for you.)

You can access the GraphTerm server using any browser that supports
websockets. Google Chrome works best, but Firefox, Safari, or IE10
are also supported. Start by entering the following URL::

    http://localhost:8900

In the ``graphterm`` browser page, select the GraphTerm host you
wish to connect to and create a new terminal session. (Note: The GraphTerm
host is different from the network hostname for the server.)
Within a GraphTerm window, you can use *terminal/new* menu option, or
type the command ``gmenu new``, to create a new GraphTerm session 

You can also open additional GraphTerm terminal windows using
the ``gterm`` command::

    gterm --noauth [session_name]

where the terminal session name argument is optional.

Once you have a terminal, try out the following commands::

    gls <directory>
    gvi <text-filename>

These are commands in the GraphTerm toolchain that imitate
basic features of the standard ``ls`` and ``vi`` commands.
(*Note:* You need to execute the ``sudo gterm_setup`` command
to be able to use the GraphTerm toolchain. Otherwise, you will
encounter a ``Permission denied`` error.)
See `Getting Started with GraphTerm <http://code.mindmeldr.com/graphterm/start.html>`_
for more info on using GraphTerm. You can also
`set up a virtual computer lab
<http://code.mindmeldr.com/graphterm/virtual-setup.html>`_
using GraphTerm.

Documentation and Support
----------------------------------------------------------------------------------------------

Usage info and other documentation can be found on the project home page,
`code.mindmeldr.com/graphterm <http://code.mindmeldr.com/graphterm>`_.
See the `Tutorials and Talks <http://code.mindmeldr.com/graphterm/tutorials.html>`_
page for more advanced usage examples.

You can also use the following command::

  greveal $GTERM_DIR/bin/landslide/graphterm-talk1.md | gframe -f

to view a slideshow about GraphTerm within GraphTerm.
Type ``b`` three times in quick succession to exit the slideshow.

There is a `Google Groups mailing list <https://groups.google.com/group/graphterm>`_
for announcements of new releases, posting questions related to
GraphTerm etc. You can also follow `@graphterm <https://twitter.com/intent/user?screen_name=graphterm>`_ on Twitter for updates.

To report bugs and other issues, use the Github `Issue Tracker <https://github.com/mitotic/graphterm/issues>`_.

Caveats and Limitations
----------------------------------------------------------------------------------------------

 - *Reliability:*  This software has not been subject to extensive testing. Use at your own risk.

 - *Platforms:*  The ``GraphTerm`` client should work on most recent browsers that support Websockets, such as Google Chrome, Firefox, and Safari. The ``GraphTerm`` server is pure-python, but with some OS-specific calls for file,  shell, and  terminal-related operations. It has been tested only on Linux and  Mac OS X so far.

 - *Current limitations:*
          * Support for ``xterm`` escape sequences is incomplete.
          * Most features of GraphTerm only work with the bash shell, not with C-shell, due the need for PROMPT_COMMAND to keep track of the current working directory.
          * At the moment, you cannot customize the shell prompt. (You
            should be able to so in the future.)

Credits
----------------------------------------------------------------------------------------------

``GraphTerm`` is inspired by two earlier projects that implement the
terminal interface within the browser,
`XMLTerm <http://www.xml.com/pub/a/2000/06/07/xmlterm/index.html>`_ and
`AjaxTerm <https://github.com/antonylesuisse/qweb/tree/master/ajaxterm>`_. 
It borrows many of the ideas from *XMLTerm* and re-uses chunks of code from
*AjaxTerm*. The server uses the asynchronous `Tornado web framework
<http://tornadoweb.org>`_ and the client uses `jQuery <http://jquery.com>`_.

The ``gls`` command uses icons from the `Tango Icon Library
<http://tango.freedesktop.org>`_, and graphical editing uses the
`Ajax.org Cloud9 Editor <http://ace.ajax.org>`_ as well as
`CKEditor <http://ckeditor.com>`_

The 3D perspective mode was inspired by Sean Slinsky's `Star Wars
Opening Crawl with CSS3 <http://www.seanslinsky.com/star-wars-crawl-with-css3>`_.

Other packaged open source components include:

 - `d3.js <http://d3js.org/>`_  Data driven documents

 - `Landslide <https://github.com/adamzap/landslide>`_ presentation
   program

 - Online Python Tutorial from `pythontutor.com <http://pythontutor.com>`_

 - `Pagedown <http://code.google.com/p/pagedown/>`_ Javascript
   Markdown converter

 - `Superfish <http://users.tpg.com.au/j_birch/plugins/superfish/>`_
   menu plugin

 - `underscore.js <http://underscorejs.org/>`_ utility library


``GraphTerm`` was developed as part of the `Mindmeldr <http://mindmeldr.com>`_ project, which is aimed at improving classroom interaction.

License
----------------------------------------------------------------------------------------------

``GraphTerm`` is distributed as open source under the `BSD-license <http://www.opensource.org/licenses/bsd-license.php>`_.

