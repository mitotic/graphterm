*********************************************************************************
Getting started
*********************************************************************************
.. contents::


Running GraphTerm
====================================================

To install ``GraphTerm``, you need to have Python 2.6+ and the Bash
shell on your Mac/Linux/Unix computer. For a quick install, use one of
the following two options::

   sudo pip install graphterm
        OR
   sudo easy_install graphterm; sudo gterm_setup

Omit the ``sudo`` if you are installing as a non-root user within
an Anaconda or Enthought Python environment, for example.
(See the :ref:`installation` section of the :doc:`README` file for
additional installation options, including source installs.)

To start the ``GraphTerm`` server, use the command::

    gtermserver --terminal --auth_type=none

This will run the  server and open a GraphTerm terminal window
using the default browser. For multi-user computers,
omit the ``--auth_type=none`` option
when starting the server, and enter the authentication code stored in
the file ``~/.graphterm/_gterm_auth.txt`` as needed.

You can access the GraphTerm server using any browser that supports
websockets. Google Chrome works best, but Firefox, Safari, or IE10
are also supported. Start by entering the following URL::

    http://localhost:8900

In the ``graphterm`` browser page, select the GraphTerm *host* you
wish to connect to and create a new terminal session. (Note: The GraphTerm
*host* is different from the network hostname for the server.)
Within a GraphTerm window, you can use *terminal/new* menu option
to create a new GraphTerm session.

You can also open additional GraphTerm terminal windows using
the ``gterm`` command::

    gterm --noauth [session_name]
    gterm -u ubuntu --browser="Google Chrome" https://example.com:8900

where the terminal session name argument is optional.  (This
command can automatically process authentication codes from your
``~/.graphterm`` directory.)

Type ``gtermserver -h`` to view all options for starting the server.
You can use the ``--daemon=start`` option to run the server in the
background. The ``--host=hostname`` option is useful for listening on
a public IP address instead of the default ``localhost``.  The
``--auth_type=none`` no authentication mode is useful for teaching
or demonstration purposes, or on a single-user lapttop/desktop, where
security is not important.  Another useful no authentication mode is
``--auth_type=name`` which enables simple name-based sharing. (For
more on running publicly accessible GraphTerm servers,
see :ref:`virtual-setup`.)

Within the terminal, try out the following commands::

   hello_gterm.sh
   gls <directory>
   gvi <text-filename>

The ``gls`` and ``gvi`` commands in the GraphTerm toolchain imitate
basic features of the standard ``ls`` and ``vi`` commands (see
:doc:`features`).  (*Note:* You need to execute the ``gterm_setup``
command to be able to use the GraphTerm
toolchain. Otherwise, you will encounter a ``Permission denied``
error.)  To display images as thumbnails, use the ``gls -i ...``
command.  Use the ``-h`` option to display help information for these
commands, and read the tutorial :doc:`UsingGraphicalFeatures`
for usage examples.

If you wish to use GraphTerm to set up up a virtual computer lab for
multiple users, see the section :doc:`virtual-setup`. To use
GraphTerm features on remote systems and via SSH, see
:doc:`remote`.


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
features in the language/keyboard settings if you plan to do a lot of
typing on touch devices.


Inline graphics and notebook mode
===============================================================

GraphTerm supports inline graphics display with ``matplotlib`` and
``pandas`` Python packages (see below) and also with R (see
:doc:`R`). It also supports a lightweight notebook interface.

.. index:: inline graphics, matplotlib, gpython, gipython

.. _inline_graphics:

Inline plots using matplotlib
--------------------------------------------------------------------------------------------

Assuming you have ``matplotlib`` installed, the ``gpylab`` module in the
``$GTERM_DIR/bin`` directory can be used to start up the python
interpreter in ``pylab`` mode for inline graphics within the
GraphTerm terminal::

    python -i $GTERM_DIR/bin/gpylab.py
    >>> plot([1,2,4])
    >>> plot([1,3,9])     # Overplot
    >>> figure()          # Clear figure
    >>> plot([1,3,9])
    >>> newfig()          # New figure
    >>> plot([1,4,12])

Inline graphics also works with the ``ipython`` command in a similar
manner. Instead of typing the long python command line above, you can use the
shortcut commands ``gpython`` or ``gipython``, e.g.::

    gpython
    >>> plot([1,2], [3,6])

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-inline-plot.png
   :align: center
   :width: 90%
   :figwidth: 85%

Run ``$GTERM_DIR/bin/gmatplot.py`` for a demo of inline graphics (see  :ref:`matplotlib_shot`).
See the function ``main`` in this file for sample plotting code.

 - Use ``figure(...)`` to clear current image
 - Use ``newfig(...)`` to create blank image
 - Use ``resize_newfig(...)`` to create resize blank image
 - Use ``show()`` to update image
 - Use ``show(False)`` to display as new image
 - Use ``display(fig)`` to display figure
 - Use ``ioff()`` to disable interactive mode
 - Use ``gterm.nbmode(False)`` to re-enable default expression printing behaviour


.. index:: pandas, DataFrame

.. _pandas_mode:
 

Inline tables using pandas
--------------------------------------------------------------------------------------------

GraphTerm can display ``pandas`` DataFrame objects as a table using
HTML::

    gpython
    >>> import pandas as pd
    >>> d = {'one' : [1., 2., 3., 4.],
    >>> 'two' : [4., 3., 2., 1.]}
    >>> pd.DataFrame(d)

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-pandas.png
   :align: center
   :width: 90%
   :figwidth: 85%

.. index:: notebook mode

.. _notebook_mode:
 
Notebook mode
--------------------------------------------------------------------------------------------

GraphTerm supports a notebook mode, where code can be entered in
multiple cells and executed separately in each cell to display the
output (see :ref:`notebook_shot`). Currently, the notebook mode can be
used with the shell (``bash``), or while running python
(``python/ipython``) and ``R`` interpreters (see :doc:`R`). You can
create new notebooks using the *notebook/new* menu option and then
selecting the language.

You can try using the notebook mode with any other shell-like
program (such as ``IDL`` or ``ncl``) which has a unique prompt by
typing *Shift-Enter* after starting the program. Type *Control-Enter*
instead, if you wish to read a notebook file and/or customize the
interpreter prompts.  Alternatively, you can select
*notebook/new/default* menu option after starting the program (this
works even with the ``bash`` shell!).

To open an existing notebook, use the ``gls`` command to list your
notebooks, e,g.::

    gls *.ipynb

Then click on the notebook that you wish to open.
Alternatively, you can use the ``gpython`` or ``gopen`` commands
python notebooks::

    gpython notebook.ipynb

For other languages, you will need to start the interpreter and then
use the *notebook/open* menu option.

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-nb.png
   :align: center
   :width: 90%
   :figwidth: 85%

Within notebook mode, type either *Control-Enter* to execute code
in-place, or *Shift-Enter* to execute and move to the next cell
(creating a new cell, if necessary). You can also use the *run* button
on the top menu, which behaves like *Shift-Enter* but does not create
new cells. Other notebook operations can be carried out using the
*notebook* menu or the keyboard shortcuts listed under *help/notebook
shortcuts*.

Notebook cells can also contain descriptive text in `Markdown
<http://daringfireball.net/projects/markdown>`_ format. The
*notebook/markdown* menu option can be used to toggle a cell between
code and Markdown mode and *double-clicking* on the rendered text
displays the editable Markdown cell.

The *notebook/save* menu option can be used to save notebooks either
in the IPython Notebook format (``*.ipynb``) or in the :doc:`format`
(``*.py.gnb.md``). The filename determines which format is used.  You
can exit the notebook mode using *notebook/quit* in the top menu bar,
or by typing *Control-C*, to return to the terminal mode.

 
Sharing and security
================================================================


.. index:: sessions, screensharing

.. _screensharing:

Terminal sessions and "screensharing"
--------------------------------------------------------------------------------------------

For each host, terminal sessions are assigned default names like
``tty1``, ``tty2`` etc. You can also create unique terminal session names simply by using it in an
URL, e.g.::

      http://localhost:8900/local/mysession

The first user to create a session "owns" it, and can make the session
publicly available by disabling the *share/private* menubar option.
The public session URL can then be shared
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
to securely access your work desktop, and then *steal* the
session using your home browser (see :doc:`remote`).

Normally, only a single user has control of a terminal session at a
time. There is a *share/tandem* option that can be enabled to allow
multiple users to control the terminal session at the same
time. However, this could sometimes have unpredictable effects.


.. index:: security

Security
--------------------------------------------------------------------------------------------


You should normally run GraphTerm logged in as a regular user, using
the default ``--auth_type=singleuser`` option, which requires an access
code for HMAC authentication. Using the ``gterm`` command to create a
new terminal provides convenience and additional security, as the
command validates the server and handles authentication before
opening a new terminal. On a single user computer, such as a laptop,
the ``--auth_type=none`` option, with no access code, can be used
instead.

Although GraphTerm can be run as a public server, this feature is best
used for teaching and demonstration purposes. In this case, the
``--auth_type=name`` option can be used, if all users can share an
account, with no access code. The ``--auth_type=multiuser`` option,
which requires the server to run with root privileges, is suitable for
a multiple user lab setting, providing a choice of either access code
HMAC authentication or Google Authentication. The
``--auth_type=login`` option, which is permitted only with a
*localhost* server or with HTTPS, implements the standard password
login.  The ``--nolocal`` option can be used to disable root access
via the browser. The HTTPS protocol can be enabled for the public
server, using either self-signed or authoritative certificates, to
provide additional security. (See see :doc:`virtual-setup` for more on
authentication options.)

When working with sensitive information, it would be best to run the
server on ``localhost`` (the default) and use SSH port forwarding to
connect to it from other computers as needed (see :doc:`remote`).

