GraphTerm: A Graphical Terminal Interface
*********************************************************************************
.. contents::

Introduction
=============================

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

The interface is designed to be touch-friendly for use with
tablets, relying upon command re-use to minimize the need for
a keyboard. It preserves history for all commands,
whether entered by typing, clicking, or tapping.
It is also themable using CSS.

Images of GraphTerm in action can be found in `screenshots <https://github.com/mitotic/graphterm/blob/master/SCREENSHOTS.rst>`_ 
and in this `YouTube Video <http://youtu.be/TvO1SnEpwfE>`_.
Here is a sample screenshot illustrating graphical ``gls`` and ``cat`` command
output using a 3D  perspective theme (captured on OS X Lion, using Google Chrome).

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-stars3d.png
   :align: center
   :width: 90%
   :figwidth: 70%


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

You can also try out ``GraphTerm`` without installing it, after
untarring the source tarball (or checking out the source from ``github``). You can
run the server ``gtermserver.py`` in the ``graphterm``
subdirectory of the distribution, after you have installed the ``tornado`` module
in your system (or in the ``graphterm`` subdirectory).

You can browse the ``GraphTerm`` source code, and download the development
version, at `Github <https://github.com/mitotic/graphterm>`_.


Documentation and Support
=========================================================

Usage info and other documentation can be found on the project home page,
`code.mindmeldr.com/graphterm <http://code.mindmeldr.com/graphterm>`_,
which also has some
`tutorials and talks <http://code.mindmeldr.com/graphterm/tutorials.html>`_
for using GraphTerm.

You can also use the following command::

  glandslide -o graphterm-talk1.md | giframe -f

to view a slideshow about GraphTerm within GraphTerm (type ``h`` for
help and ``q`` to quit)..

**NEW**
There is a `Google Groups mailing list <https://groups.google.com/group/graphterm>`_
for announcements of new releases, posting questions related to
GraphTerm etc. You can also follow `@graphterm <https://twitter.com/intent/user?screen_name=graphterm>`_ on Twitter for updates.

To report bugs and other issues, use the Github `Issue Tracker <https://github.com/mitotic/graphterm/issues>`_.



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
<http://tango.freedesktop.org>`_, and graphical editing uses the
`Ajax.org Cloud9 Editor <http://ace.ajax.org>`_ as well as
`CKEditor <http://ckeditor.com>`_

The 3D perspective mode was inspired by Sean Slinsky's `Star Wars
Opening Crawl with CSS3 <http://www.seanslinsky.com/star-wars-crawl-with-css3>`_.

Other packaged open source components include the
`Landslide <https://github.com/adamzap/landslide>`_
presentation program and portions of the Online Python Tutorial from
`pythontutor.com <http://pythontutor.com>`_

``GraphTerm`` was developed as part of the `Mindmeldr <http://mindmeldr.com>`_ project, which is aimed at improving classroom interaction.


License
=====================

``GraphTerm`` is distributed as open source under the `BSD-license <http://www.opensource.org/licenses/bsd-license.php>`_.

