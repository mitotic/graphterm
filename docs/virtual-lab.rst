.. _virtual-lab:

*********************************************************************************
 Virtual Computer Lab using GraphTerm: Tips for Students
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
logging in later. If you forget your personal access code, the
instructor can retrieve it for you. If you have a Mac/Linux
desktop/laptop, you can download the executable python script
``$GTERM_DIR/bin/gterm.py`` and type the following command on your
desktop/laptop::

    gterm.py -u user http://hostname.domain:8900

to open a terminal on the remote server without having to type in the
access code (after the first time).

Creating  and leaving terminal sessions
-------------------------------------------------------------------------------------------

After logging in, choose the host that has the same name as your user
name, and then you can connect to an existing terminal session or
create a new terminal session. You can choose a specific name for a
new terminal session, or type the special name ``new`` to
automatically choose names like ``tty1``, ``tty2`` etc. You can also
create new terminals as needed using the *terminal->new* menu option.
You can type standard Unix commands, like ``cd``, ``ls``, ``cp``
etc. in the terminal. Often, it is preferable to use the
GraphTerm-aware ``gls`` command, instead of the standard ``ls``
command, as it allows you to navigate directories by clicking.

To leave a terminal session, use the *terminal->detach* option, which
will return you to the list of terminals. Detaching a terminal still
keeps it alive, and you connect to it at a later time, without losing
its state. For example, you can create a terminal at work, and later
connect to it from home.


Troubleshooting
-------------------------------------------------------------------------------------------

If the terminal is unresponsive (i.e., appears to "hang"), check the
following:

 - Are you in the notebook mode? If so, the notebook name will appear
   on the top, with the prefix "NB". To exit the notebook mode, use
   *Control-C* and then use *Control-D* to exit the python
   interpreter. (Remember to save the notebook before exiting, if
   necessary.)

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

There is also an experimental option, *share->tandem*, which allows two
people to control a terminal simultaneously. However, sometimes this
can lead to unpredictable effects, due to the time lags between
terminal operations.



Pasting text into the terminal
--------------------------------------------------------------------------------------------

To paste copied text into the terminal, click on the *red cursor* and
then use the standard paste command on your computer (*Command-V* on
the Mac and *Control-V* on other systems).

If the keyboard command does not work, you can try the *terminal->paste
special* menu option.


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
session. For beginning users, it may be simpler to stay in the notebook
mode all the time, and avoid the the python command line altogether.


Opening python notebooks in GraphTerm
--------------------------------------------------------------------------------------------

To open a new python notebook, use the menu command
*notebook->new->pylab* 

To open an existing notebook, use the ``gls`` command to list your
notebooks, e,g.:

    gls *.ipynb

Then click on the notebook that you wish to open.

Alternatively, you can also the ``gopen`` command:

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
command:

    exit()




Downloading files
---------------------------------------------------------------------------------------------

To download files use the ``gls --download`` command:

    gls --download filename

Then right-click (or control-click) on the filename to download
it. You can download notebook files using the above method and then submit
it.

*Note:* Sometimes the browser appends ``.html`` to the downloaded
filename. For example, ``a.ipynb`` may be downloaded as
``a.ipynb.html``. You may ocassionally need to rename the downloaded file
by gently clicking on the name in the Finder window and deleting the
``.html`` extension.


Uploading  files
---------------------------------------------------------------------------------------------

Use the ``gupload`` command to upload files to the remote
terminal. First ``cd`` to the directory where you want to upload the
file and type:

    gupload optional_filename

Then select (or drag-and-drop) the file from your local computer.
If you do not provide a filename, the original filename will be used.

