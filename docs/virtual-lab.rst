.. _virtual-lab:

*********************************************************************************
 Virtual Computer Lab using GraphTerm
*********************************************************************************
.. contents::

.. index:: virtual computer lab, remote terminal, remote access


Logging in
--------------------------------------------------------------------------------------------

Open the URL provided by the instructor (usually of the form
``http://hostname.domain:8900``) in your web browser. Then type in the user
name and the access code. If you are creating a new account, you will
need to obtain the *group access code* from the instructor. 

If you just created a new user account, note down your user name and
personal access code, or email it to yourself. You will need it for
logging in later. (If you forget your personal access code, the
instructor can retrieve it for you.)

*On Windows:* The Google Chrome and Firefox browsers work best, but
Internet Explorer 10 should also be usable, with some limitations.


Creating  and leaving terminal sessions
-------------------------------------------------------------------------------------------

After logging in, choose the host that has the same name as your user
name, and then you can connect to an existing terminal session or
create a new terminal session. You can choose a specific name for a
new terminal session, or type the special name ``new`` to
automatically choose names like ``tty1``, ``tty2`` etc. You can also
create new terminals as needed using the *terminal->new* menu option.

You can type standard Unix commands, like ``cd``, ``ls``, ``cp``
etc. in the terminal. The *command* menu lists some commonly used
commands. Often, it is preferable to use the GraphTerm-aware ``gls``
command, instead of the standard ``ls`` command, as it allows you to
navigate directories by clicking.

To leave a terminal session, use the *terminal->detach* option, which
will return you to the list of terminals. Detaching a terminal still
keeps it alive, and you connect to it at a later time, without losing
its state. For example, you can create a terminal at work, and later
connect to it from home.


Troubleshooting
-------------------------------------------------------------------------------------------

If the terminal is unresponsive (i.e., appears to "hang"), try one or
more of the following:

 - Are you in the notebook mode? If so, the notebook name will appear
   on the top, with the prefix "NB". To exit the notebook mode, use
   the *notebook-quit* menu option, or type *Control-C* and then type
   *Control-D* to exit the python interpreter. (Remember to save the
   notebook before exiting, if necessary.)

 - Use the *command->interrupt* menu option or type *Control-C* to
   interrupt the currently running program.

 - For embedded frames or "fullscreen" programs. use the
   *command->parent interrupt* menu option to interrupt the currently
   running program in the parent window.

 - Use the *terminal->reload* menu option or the browser's reload
   button to reload the web page.


Sharing terminal sessions
-------------------------------------------------------------------------------------------

If your instructor has enabled sharing for all, or created sharing
groups, you can view and control terminals belonging to other users,
who will appear as additional hosts.

You can *watch* someone else's terminal, without controlling it, if
the *share->locked* menu option is not set. Using the
*terminal->action->chat* option, you can enable chat communication
between all watchers for a terminal session. If chatting is enabled,
an *alert* button also becomes available to attract the attention of
the watchers (which may include the instructor).

You can also *steal* control of someone else's terminal, if the
*share->locked* menu option is not set. To regain control, the
terminal owner would have to steal it back.

There is an experimental option, *share->tandem*, which allows two
people to control a terminal simultaneously. However, sometimes this
can lead to unpredictable effects, due to the time lags between
terminal operations.


Pasting text into the terminal
--------------------------------------------------------------------------------------------

To paste copied text into the terminal, click on the *red cursor* and
then use the standard paste command on your computer (*Command-V* on
the Mac and *Control-V* on other systems). If the keyboard command
does not work, you can try the *terminal->paste special* menu option.


Running IPython Notebook server
--------------------------------------------------------------------------------------------

If your instructor has permitted it, you can run your own
password-proteced public IPython Notebook server on the remote machine
using the ``gnbserver`` command. You can access it using your browser,
with an URL of the form ``http://hostname.domain:port``, where
``port`` is the port number output by the ``gnbserver`` command. The
notebook password is the same as the access code for your user
account.


GraphTerm notebook interface
--------------------------------------------------------------------------------------------

GraphTerm provides a *lightweight* notebook interface that mimics the
basic features of the IPython Notebook. You can create simple
notebooks in GraphTerm, save them as ``.ipynb`` files and open them
later using IPython Notebook, and *vice versa*.  Unlike the
self-contained IPython Notebook interface, the GraphTerm notebook
interface is a wrapper on top of the standard python command line
interface. You can switch back and forth between the
command line mode and the notebook mode, as needed, during a single
session. (For beginning users, it may be simpler to stay in the notebook
mode all the time, and avoid the the python command line altogether.)


Opening python notebooks in GraphTerm
--------------------------------------------------------------------------------------------

To open a new python notebook, use the menu command
*notebook->new->pylab* 

To open an existing notebook, use the ``gls`` command to list your
notebooks, e,g.::

    gls *.ipynb

Then click on the notebook that you wish to open.

Alternatively, you can also the ``gopen`` command::

    gopen notebook.ipynb

Once you have opened a notebook, you can use *Control-Enter* or
*Shift-Enter* key combinations to work with cells.

Saving and exiting python notebooks
--------------------------------------------------------------------------------------------

To save the notebook, use the menu command *notebook->save*

To exit the notebook mode, you can simply type *Control-C* or use the
*notebook->quit* menu option. This returns you to the python command
line, with the chevron (>>>) prompt.

To exit the python command line, type *Control-D* or the following
command::

    >>> exit()


Downloading files
---------------------------------------------------------------------------------------------

To download files use the ``gls --download`` command::

    gls --download filename

Then right-click (or control-click) on the filename to download it. On
some browsers, like Chrome, directly clicking on the link would also
work well. (You may download notebook files using the above method for
submission.)

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

*On Windows:* Drag-and-drop for files currently does not work with IE10.

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
*help->notebook shortcuts* menu option for more info.


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
limitations. Use the *view->footer* menu to enter keyboard input, send
special characters, access arrow keys etc. Tap the *Kbrd* in the
footer to display the keyboard.

*Note:* You should turn off the *Autocapitalize* and *Autocorrect*
features in the language/keyboard settings if you want to do a lot of
typing on touch devices.