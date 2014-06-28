.. _virtual-lab:

*********************************************************************************
Using the GraphTerm Virtual Computer Lab
*********************************************************************************
.. contents::

.. index:: virtual computer lab, logging in


Logging in
--------------------------------------------------------------------------------------------

Open the URL provided by the instructor (usually of the form
``http://hostname.domain``) in your web browser. (Google Chrome works
best, but Firefox, Safari, or IE10 would also work.) Then type in the user
name and the access code. If you are creating a new account, you will
need to enter the *group access code* obtained from your
instructor. Select a user name that will be meaningful to the
instructor, like your first initial followed by your last name (all
lower-case), e.g., ``jsmith`` for Jim Smith.  If you have a *Google
GMail* account, you can choose to link it to your GraphTerm server
account for password-less logins by clicking the *Google Auth* button.
(You will still need to enter the group access code the very first
time to create your new account and link it to your GMail account.)

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-login.png
   :align: center
   :width: 90%
   :figwidth: 85%
 
*Note:* If the URL is of the ``https//...`` form, you may encounter
warning messages about untrusted certificates, and be asked to make an
exception. The instructor may ask you to ignore these warnings and
accept the certificate, if the GraphTerm server has been configured to
use a self-signed certificate. **Also, self-signed certificates do not
work with Safari on the Mac; use Chrome or Firefox instead.**

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-new-acct.png
   :align: center
   :width: 90%
   :figwidth: 85%
 
If you just created a new user account, note down your user name and
personal access code, as you will need it for logging in later (unless
you are using Google Authentication). You may optionally enter your email
address at this point. If you forget your personal access code, the
instructor can retrieve it for you.

If you have a Mac/Linux desktop/laptop, you can download the
executable python script ``$GTERM_DIR/bin/gterm.py`` and type the
following command on your desktop/laptop::

    gterm.py -u user http://hostname.domain

to open a terminal on the remote server without having to type in the
access code (after the first time).

*On Windows:* The Google Chrome and Firefox browsers work best, but
Internet Explorer 10 should also be usable, with some limitations.


Creating and leaving terminal sessions
-------------------------------------------------------------------------------------------

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-host-list.png
   :align: center
   :width: 95%
   :figwidth: 90%
 
After logging in, choose the host that has the same name as your user
name, and then you can connect to an existing terminal session or
create a new terminal session. You can choose a specific name for a
new terminal session, or type the special name ``new`` to
automatically choose names like ``tty1``, ``tty2`` etc. You can also
create new terminals as needed using the *terminal/new* menu option.

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-create-session.png
   :align: center
   :width: 95%
   :figwidth: 90%
 
You can type standard Unix commands, like ``cd``, ``ls``, ``cp``
etc. in the terminal. The *command* menu lists some commonly used
commands. Often, it is preferable to use the GraphTerm-aware ``gls``
command, instead of the standard ``ls`` command, as it allows you to
navigate directories by clicking.

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-new-session.png
   :align: center
   :width: 95%
   :figwidth: 90%
 
To leave a terminal session, use the *terminal/detach* option, which
will return you to the list of terminals. Detaching a terminal still
keeps it alive, and you connect to it at a later time, without losing
its state. For example, you can create a terminal at work, and later
connect to it from home.


Troubleshooting
-------------------------------------------------------------------------------------------

If the terminal is unresponsive (i.e., appears to "hang"), try one or
more of the following:
 
 - Do what you would normally do in a Unix terminal, type
   ``Control-C``  to interrupt the currently running program. You can
   also use the *command/interrupt* menu option instead.

 - If you are in the fullscreen graphics mode (e.g., using
   ``gframe``), you may need to click on the top of the terminal
   portion of the window to get the input focus out of the embedded
   frame and then type ``Control-C``.  You can also try the
   *command/parent interrupt* menu option to interrupt the currently
   running program in the parent window.

 - Are you in the notebook mode? If so, the notebook name will appear
   on the top, with the prefix "NB". To exit the notebook mode, use
   the *notebook/quit* menu option, or type *Control-C* and then type
   *Control-D* to exit the python interpreter. (Remember to save the
   notebook before exiting, if necessary.)

 - Use the *terminal/reload* menu option or the browser's reload
   button to reload the web page. *Copy/paste any displayed code in
   notebook cells before reloading, as you may lose it.*


Sharing terminal sessions
-------------------------------------------------------------------------------------------

If your instructor has enabled sharing for all, or created sharing
groups, you can view and control terminals belonging to other users,
who will appear as additional hosts.

You can *watch* someone else's terminal, without controlling it,
simply by selecting a different host from the list.  You can also
*steal* control of someone else's terminal, if the terminal owner has
previously unchecked the *share/locked* menu option. (To regain
control, the terminal owner would have to steal it back.)

*Chatting*: Using the *command/chat* option, you can enable chat
communication between all watchers for a terminal session.  The
command needs to be invoked at the shell prompt, *before* running the
python interpreter or opening a notebook, and it displays a *chat*
button near the top right corner. When chatting, an *alert* button
also becomes available to attract the attention of the watchers
(which may include the instructor).

There is also an experimental option for unlocked terminals,
*share/tandem*, which allows two people to control a terminal
simultaneously. However, sometimes this can lead to unpredictable
results, due to the time lags between terminal operations by multiple
users.


Pasting text into the terminal
--------------------------------------------------------------------------------------------

To paste copied text into the terminal, click on the *red cursor* and
then use the standard paste command on your computer (*Command-V* on
the Mac and *Control-V* on other systems). If the keyboard command
does not work, you can try the *terminal/paste special* menu option.

.. index:: notebook mode


GraphTerm Notebook interface
--------------------------------------------------------------------------------------------

Two ways to use the notebook interface are supported in the virtual
computer lab:

 1. Using the *lightweight* :ref:`notebook_mode` built into the
 remote GraphTerm terminal.

 2. Running the IPython Notebook server on the remote computer and
 accessing it using a browser on your local computer (see next section
 for detailed instructions).

The GraphTerm notebook interface is implemented as a wrapper on top of
the standard python command line interface. It provides basic notebook
functionality, but is not a full-featured environment like IPython
Notebook. It does support the same notebook format, which means that
you can create simple notebooks in GraphTerm, save them as ``.ipynb``
files and open them later using IPython Notebook, and *vice versa*.
The GraphTerm notebook interface is integrated into the terminal,
which allow seamless switching between the python command line and
notebook mode, as well as "live sharing" of notebooks across shared
terminals.


Running IPython Notebook server
--------------------------------------------------------------------------------------------

To access the full features of the IPython Notebook, you can run your
own password-protected public IPython Notebook server on the remote
machine using the ``gnbserver`` command (*if the instructor has
enabled this option*). You can then access it using your local browser,
with an URL of the form ``https://hostname.domain:port``, where
``port`` is the port number output by the ``gnbserver`` command. The
notebook password is the same as the access code for your user
account.

*Note:* If each user is running their own copy of the IPython Notebook
server, it can degrade performance on a shared computer. Please
consider shutting down the server when you are not using it.


Opening Python notebooks in GraphTerm
--------------------------------------------------------------------------------------------

To open a new python notebook, use the menu command
*notebook/new/pylab* 

To open an existing notebook, use the ``gls`` command to list your
notebooks, e,g.::

    gls *.ipynb

Then click on the notebook that you wish to open.
Alternatively, you can use the ``gpython`` or ``gopen`` commands::

    gpython notebook.ipynb


.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-nb.png
   :align: center
   :width: 90%
   :figwidth: 85%


Once you have opened a notebook, you can enter code in the notebook
cells.  Type either *Control-Enter* to execute code in-place, or
*Shift-Enter* to execute and move to the next cell (creating a new
cell, if necessary). You can also use the *run* button on the top
menu, which behaves like *Shift-Enter* but does not create new
cells. Other notebook operations can be carried out using the
*notebook* menu or the keyboard shortcuts listed under *help/notebook
shortcuts*.


Saving and exiting python notebooks
--------------------------------------------------------------------------------------------

To save the notebook, use the menu command *notebook/save*

To exit the notebook mode, you can simply type *Control-C* or use the
*notebook/quit* menu option. This returns you to the python command
line, with the chevron (>>>) prompt.

To exit the python command line, type *Control-D* or the following
command::

    >>> exit()



Downloading files
---------------------------------------------------------------------------------------------

To download files, use the ``gdownload`` command::

    gdownload filename(s)

Right-click (or control-click) on the displayed link to download. On
some browsers, like Chrome, directly clicking on the link would also
work.  If more than one file (or a directory) is specified for downloading,
the command automatically creates a zip archive. This works well
for archive sizes of 1-2 MB, but for larger archives, you should create the
archive yourself using the ``zip`` command and then download the
single archive file.

You can also download multiple files, one-at-a-time, using the
following command::

    gls --download filenames

Click on the displayed filenames to download.

*Note:* Browsers other than Chrome typically append ``.html`` or ``.htm``
to the downloaded filename. For example, file ``abc.ipynb`` may be downloaded
as ``abc.ipynb.html``. If needed, you can rename the downloaded file by
gently clicking on the name in the Finder window and deleting the
``.html`` extension.


Uploading  files
---------------------------------------------------------------------------------------------

Use the ``gupload`` command to upload files to the remote
terminal. First ``cd`` to the directory where you want to upload the
file and type::

    gupload optional_filename

Then select (or drag-and-drop) the file from your local computer.
If you do not provide a filename, the original filename will be used.
This command works well for file sizes of a few MB, but can be
quite slow for larger files.

*On Windows:* Drag-and-drop for files currently does not work with IE10.


SSH key access
---------------------------------------------------------------------------------------------

If you have an SSH client on your local computer, upload the public key
file (usually ``id_rsa.pub``) using the ``gupload`` command as
``~/.ssh/authorized_keys`` to enable SSH access to your account::

    ssh username@server_domain


Keyboard shortcuts
---------------------------------------------------------------------------------------------

The special keystroke *Control-J*, followed by a sequence of letters,
can be used to access all menu commands from the keyboard. The letter
to be typed is highlighted and is usually, but not always, the first
letter of the menu item to be selected. For example, the key sequence
*Control-J t c* can be used to clear the terminal and the sequence
*Control-J c i* can be used to send a *Control-C interrupt*.

In notebook mode, several keyboard shortcuts with the prefix
*Control-m* are also available, similar to IPython Notebook. See
*help/notebook shortcuts* menu option for more info.


Windows-specific tips
---------------------------------------------------------------------------------------------

The Google Chrome and Firefox browsers work best on Windows, but
Internet Explorer 10 should also be usable, with some limitations.

The Unix *Control-C* and *Control-D* key combinations do not always
work as expected in Windows browsers. To send *Control-C* or
*Control-D*, you can use the menu options, or the keyboard shortcuts
prefixed with *Control-J*.

The *up-arrow* and *down-arrow* keys for command recall do not work
with IE10.


Tips for Android/iPhone/IPad
---------------------------------------------------------------------------------------------

GraphTerm can be used on touch devices (phones/tablets), with some
limitations. Use the *view/footer* menu to enter keyboard input, send
special characters, access arrow keys etc. Tap the *Kbrd* in the
footer to display the keyboard.

*Note:* You should turn off the *Autocapitalize* and *Autocorrect*
features in the language/keyboard settings if you want to do a lot of
typing on touch devices.
