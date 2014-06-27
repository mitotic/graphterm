.. _troubleshooting:

Troubleshooting FAQ
==================================================================

.. index:: troubleshooting

.. contents::
 
Terminal
----------------------------------------------------------------------------------------------

.. index:: control c, frozen screen, hung terminal, unresponsive terminal, reconnect

My terminal is unresponsive?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
   the *notebook-quit* menu option, or type *Control-C* and then type
   *Control-D* to exit the python interpreter. (Remember to save the
   notebook before exiting, if necessary.)

 - Use the *terminal/reload* menu option or the browser's reload
   button to reload the web page. *Copy/paste any displayed code in
   notebook cells before reloading, as you may lose it.*

 - As a last resort, you can try the *terminal/reconnect* option,
   which takes over 15 seconds to reconnect the terminal. This may
   help when updating configuration changes etc.

.. index:: permission denied
 
I get the error message "bash: ... gls: Permission denied" on the terminal?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``sudo easy_install ...`` command does not set the execute permission for
commands like ``gls``. You need to execute the command ``sudo gterm_setup``
after installation to set the permissions. (The ``python setup.py
install`` command automatically sets permissions.)

.. index:: no such file or directory
 
I get the error message "bash: gls: No such file or directory" on the terminal?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The environment variable ``GTERM_DIR`` contains the directory
where ``gls`` and other commands are located. GraphTerm tries to set
the ``PATH`` variable to automatically include this directory. But
sometimes this may fail, in which case you would need to modify you
shell initialization files to include ``$GTERM_DIR`` in ``$PATH``.
(The menu command *terminal/export environment* may also help in this
situation.)

.. index:: remote login, ssh
 
When  I log into another computer using SSH from my GraphTerm window, why do many features no longer work?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is normal behavior. Other than inline images and the notebook
mode, most graphical features only work on the computer that the
``gtermserver`` (or ``gtermhost``) program is running on.  However,
you can use the *terminal/export environment* menu command to set
shell environment variables on a *trusted* remote computer to restore
some, but not all, of GraphTerm features. (For more details and a
discussion of the security implications, see the :doc:`remote`
section.)

 
.. index:: terminal size, resize, line wrap
 
The terminal does not display long lines properly; they are either wrapped too short or they overflow the window?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Try one or more of the following commands to resize the terminal:

 - the menu option *view/resize*

 - the Unix command ``resize``

(You will need control of the terminal for the resizing commands to work properly.)


.. index:: copy/paste, paste
 
How do I paste text?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For certain browsers (e.g., desktop Chrome/Firefox), the usual
*Command-V* or *Control-V* key sequence should directly paste text
from the clipboard.  Alternatively, for some browsers, you can *click
on the cursor* before beginning the paste operation and then paste the
text directly.  This second technique may not always work well for
text copied from non-plain text sources, such as a web page. A
workaround for this case is to paste the text into a temporary
location as plain text (such as in a plain text editor), and then
copy/paste it from there to GraphTerm.

If the above do not work, you can use the keyboard shortcut
*Control-O* to open a popup window, paste the text into the popup
window using the browser's paste menu command or a keyboard shortcut,
such as *Command/Control-V*, and then type *Control-O* again to insert
the text at the GraphTerm cursor location.  (The popup paste window
can also be accessed using the *terminal/paste special* menu item.)


Inline graphics and notebook mode
----------------------------------------------------------------------------------------------

.. index:: inline graphics


My inline graphics plot does not appear?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If using ``gpylab.py``, try adding a ``show(False)`` function call to display a new
image or ``show()`` to overwrite a previous image. You can also use
``display(fig)`` to display a figure.


.. index:: notebook format

How do I specify the format for saving a notebook?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The notebook save file format is determined by the filename extension,
i.e., use ``.ipynb`` for compatibility with IPython Notebook or
``.py.gnb.md`` for Markdown compatibility.


Session sharing
----------------------------------------------------------------------------------------------

.. index:: sharing


Others cannot see or access my terminal for sharing?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Disable the *share/private* option to share your terminal.


Server
----------------------------------------------------------------------------------------------------

I'm running the GraphTerm server on a remote computer, but I'm unable to access it using my browser?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure that you have included the port number in the URL, e.g., ``http//example.com:8900``
Also, ensure that any firewall on the server allows incoming
connections to the default port 8900 .

.. index:: server port

Can I run the GraphTerm server on port 80 (or 443)?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You would need run the server as the root user, which is not recommended
at this stage of GraphTerm development. A better way to achieve this is
to redirect traffic from port 80 to port 8900. On a Linux server, this
can be achieved by executing a single command (as root)::

  iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to 8900


.. index:: google authentication

How do I get Google Authentication to work?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Follow the instructions at the URL ``http://server_domain_name/_gauth``


.. index:: Windows
 
Using GraphTerm on Windows
----------------------------------------------------------------------------------------------------

 
Does GraphTerm work on Windows?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The GraphTerm client should work on a Windows browser that supports Websockets,
like the  latest versions of Chrome/Firefox/Safari or IE10. The
GraphTerm server is currently not supported on Windows. (Although the
server is written in pure python, it needs access to the
pseudo-terminal device that is only supported on Unix/Linux.)


GraphTerm fails to load properly on Windows?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure that you are using a browser that supports Websockets, like the
latest versions of Chrome/Firefox/Safari or IE10.
Some Anti-virus programs block Websockets on the browser. You may need to
turn them off, or allow access to the domain where the GraphTerm
server is running.

.. index:: ipad, android, virtual keyboard

Using GraphTerm on tablets
-------------------------------------------------------------------------------

How do I access the virtual keyboard on iPad/Android?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

GraphTerm can be used on touch devices (phones/tablets), with some
limitations. Use the *view/footer* menu to enter keyboard input, send
special characters, access arrow keys etc. Tap the *Kbrd* in the
footer to display the keyboard.

*Note:* You should turn off the *Autocapitalize* and *Autocorrect*
features in the language/keyboard settings if you want to do a lot of
typing on touch devices.


