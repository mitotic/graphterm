.. _README:

README
==================================================================
 
.. contents::

.. index:: introduction

Introduction
----------------------------------------------------------------------------------------------

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

A GraphTerm terminal window is just a web page served from the
GraphTerm server program. Multiple users can connect
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

 - an **inline data visualization tool** to view output from plotting
   libraries like ``matplotlib``

 - a **notebook interface** for data analysis and documentation (like
   the *Mathematica* or *iPython* Notebook interface, but at the shell
   level).

 - a **collaborative terminal** that can be remotely accessed
   by multiple users simultaneously, to run programs, edit files etc.

 - a web-based **remote desktop** that supports a simple GUI
   without the need for installing VNC or X-windows on the remote host

 - a **detachable terminal multiplexer**, sort of like GNU ``screen`` or
   ``tmux``

 - a **simple presentation tool** for webcasting images as slideshows
   (and receiving live feedback)

 - a **management console** for a cluster of real or virtual hosts,
   with wildcard access to hosts/sessions (e.g., to manage a virtual
   computer lab using cloud instances),

The interface is designed to be touch-friendly for use with
tablets, with tappable links and command re-use to minimize the need for
a keyboard. It preserves history for all commands,
whether entered by typing, clicking, or tapping.
It is also themable using CSS.

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

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-metro.jpg
   :align: center
   :width: 90%
   :figwidth: 100%

.. index:: installation

.. _installation:

Installation
----------------------------------------------------------------------------------------------

To install ``GraphTerm``, you need to have Python 2.6+ and the Bash
shell on your Mac/Linux/Unix computer. For a quick install, if the python
``setuptools`` module is already installed on your system,
use the following two commands::

   sudo easy_install graphterm
   sudo gterm_setup            # Sets up the command toolchain

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

You can also try out ``GraphTerm`` without installing it, after
untarring the source tarball (or checking out the source from ``github``). You can
run the server as ``./gtermserver.py`` in the ``graphterm``
subdirectory of the distribution, after you have installed the ``tornado`` package
in your system (or in the ``graphterm`` subdirectory).

You can browse the ``GraphTerm`` source code, and download the development
version, at `Github <https://github.com/mitotic/graphterm>`_.

.. index:: quick start

Quick Start
----------------------------------------------------------------------------------------------

To start the ``GraphTerm`` server, use the command::

  gtermserver --auth_code=none

Once the server is running, you can open a GraphTerm terminal window
using a browser that supports websockets, such as Google Chrome,
Firefox, Safari, or IE10 (Chrome works best), and entering the following URL::

  http://localhost:8900

Once you have a terminal, try out the following commands::

   gls <directory>
   gvi <text-filename>

These are commands in the GraphTerm toolchain that imitate
basic features of the standard ``ls`` and ``vi`` commands.
See `Getting Started with GraphTerm <http://code.mindmeldr.com/graphterm/start.html>`_
and the
`Using Graphical Features
<http://code.mindmeldr.com/graphterm/UsingGraphicalFeatures.html>`_
tutorials for more info on using GraphTerm.

.. index:: documentation, support

Documentation and Support
----------------------------------------------------------------------------------------------

Usage info and other documentation can be found on the project home page,
`code.mindmeldr.com/graphterm <http://code.mindmeldr.com/graphterm>`_.
See the `Tutorials and Talks <http://code.mindmeldr.com/graphterm/tutorials.html>`_
page for more advanced usage examples.

You can also use the following command::

  glandslide -o graphterm-talk1.md | gframe -f

to view a slideshow about GraphTerm within GraphTerm (type ``h`` for
help and ``q`` to quit)..

There is a `Google Groups mailing list <https://groups.google.com/group/graphterm>`_
for announcements of new releases, posting questions related to
GraphTerm etc. You can also follow `@graphterm <https://twitter.com/intent/user?screen_name=graphterm>`_ on Twitter for updates.

To report bugs and other issues, use the Github `Issue Tracker <https://github.com/mitotic/graphterm/issues>`_.

.. index:: caveats, limitations

Caveats and Limitations
----------------------------------------------------------------------------------------------

 - *Reliability:*  This software has not been subject to extensive testing. Use at your own risk.

 - *Platforms:*  The ``GraphTerm`` client should work on most recent browsers that support Websockets, such as Google Chrome, Firefox, and Safari. The ``GraphTerm`` server is pure-python, but with some OS-specific calls for file,  shell, and   terminal-related operations. It has been tested only on Linux and  Mac OS X so far.

 - *Current limitations:*
          * Support for ``xterm`` escape sequences is incomplete.
          * Most features of GraphTerm only work with the bash shell, not with C-shell, due the need for PROMPT_COMMAND to keep track of the current working directory.
          * At the moment, you cannot customize the shell prompt. (You
            should be able to so in the future.)

.. index:: credits

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

.. index:: license

License
----------------------------------------------------------------------------------------------

``GraphTerm`` is distributed as open source under the `BSD-license <http://www.opensource.org/licenses/bsd-license.php>`_.

