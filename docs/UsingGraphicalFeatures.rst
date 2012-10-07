Using the graphical features of GraphTerm
***************************************************************************************
.. contents::

Introduction
======================================================================

If you are a long-time command line user, you can continue to use
GraphTerm just like ``xterm`` (except for any bugs), and perhaps
use the remote access or sharing features. However, that
would defeat the main goal of GraphTerm, which is to enhance the
command line with GUI-like features. You may need to
remind yourself occasionally that GraphTerm provides alternative ways to
accomplish some of the typical command line tasks, such as directory
navigation. Some of these GraphTerm "extensions" may
improve your productivity, and some may not! This tutorial explains
novel ways in which you can interact with the
computer using GraphTerm. (See the
`README <http://code.mindmeldr.com/graphterm/README.html>`_
file for basic instructions on installing and starting up GraphTerm.)


Changing directories
========================================================================

When you open up a new GraphTerm window, you can ``cd`` to the
directory you want by clicking on the Home "button" and then clicking
your way to the directory (with or without icons enabled). Once you
reach the directory, just type any command you wish to execute there.

In the middle of a terminal session, if you wish to change directories
graphically, use the ``gls`` command, which accepts optional wild card
arguments to filter the files it will display. You can also scroll
back, and click on the directory in any previously displayed ``gls``
output to switch to that directory. (NOTE: The current command line
needs to be empty for this graphical directory switching to work.)

Opening files
========================================================================

The ``gopen <filename>`` command will open any file on the local
computer, i.e., where the shell is running, using the default
program associated with it. (``gopen`` simply invokes the correct
*open* command for different platforms, e.g., ``xdg-open`` on Linux,
and ``open`` on OS X. On OS X, you can use the command "``gopen .``"
to open a Finder window showing the current directory.) For text files, 
``gopen`` invokes the ``gvi`` command, which opens up an AJAX
text editor which can be used remotely on the browser. For image
files, ``gopen`` invokes the ``gimage`` command to display the image.

``gopen`` opens files on the local computer, i.e., where the shell is
running. The ``gbrowse`` command can be used instead of ``gopen``
to open the files using the browser itself. This will work for
images and PDF documents. The advantage of ``gbrowse`` is
that it will work even remotely, i.e., across SSH tunnels. (*NOTE:
You will need to allow popups from "localhost" for this to
work.*)
 
If you click on a doument file displayed in ``gls`` output, the
``gopen/gbrowse/gvi`` command will be executed by default,
provided the current command line is empty.


Constructing a new command line
==========================================================================

If the current command line *contains even a single character*,
which may be a space, then clicking on ``gls`` output does not change
directories or open files. Instead, the relative file or directory path is
pasted as text at the end of the current command line, followed by a
space. For example, a common operation is to duplicate a file and
rename it as a backup copy with a slightly different name. You can do
that in GraphTerm by first typing  ``cp`` in the command line and
clicking on the displayed filename (or icon) twice, resulting in a
command line of the form::

   cp filepath filepath

You can then edit the second filepath to modify it, and press Enter to
execute the copy command.


Moving and copying files
==========================================================================

To move a file to a different directory, you can simply drag the
filename displayed in ``gls`` output and drop it on the destination
directory, in the same terminal window or in a different terminal
window. (NOTE: At present, the drag-and-drop implementation has some
limitations. You can only drag the actual text for the filename, not
the icon associated with the file, although the drop operation can
occur over the destination directory icon. There is no clear graphical
feedback when the file is dropped on the destination
directory. However, you will see the ``mv file dir`` command appear on
the command line when the operation is successful.)

If the current command line is not empty, the drag-and-drop operation
will simply insert the ``mv file dir`` command without actually executing
it. You can edit the command line to modify it, and then execute it.

Drag-and-drop also works between two different hosts, except that the
file is copied, instead of being moved. For remote hosts, you can
right-click on the displayed file, and download it to your desktop
just like any hyperlinked file on a web page. You should soon be able
to drag-and-drop a file from your desktop into a directory displayed
in a GraphTerm window to upload it (*this is yet to be implemented*).

Scrolling to the top/bottom quickly
==========================================================================

Expose the bottom menu bar by clicking on the lowest displayed
prompt, and then click *Top* in the menu bar to scroll to the top.
To scroll back to the bottom, click *Bottom* on the top menubar.


Sending special characters on the iPad
==========================================================================

Expose the bottom menu bar (by clicking on the last prompt) and use *Key*
drop-down menu to send special characters like TAB and ESCAPE.

 
Viewing HTML inline
==========================================================================

Use the ``giframe [-f] filename|URL`` command to render inline HTML
from a file or URL (or ``command | giframe`` to render HTML generated by ``command``).


Viewing image files
==========================================================================

Use the ``gimage`` command to view images inline. You can also use the
``gls -i`` command to include thumbnails of images in the directory
listing. (``gls`` does not display thumbnails by default because it
needs to load the entire image file to display each "thumbnail".)


Sharing slideshows/presentations
==========================================================================

The command ``gimage -f`` can be used to view images in
fullscreen mode, i.e., as a slide show. If you omit the filename argument,
all the images in the current directory will be displayed. (If you
enable the webcast feature, and use the ``-b`` option for ``gimage``,
anyone with access to the session URL can view the slideshow!)


Twitter client for live audience feedback
======================================================================

A GraphTerm-aware demo Twitter client, ``gtweet``, is included in the
distribution. It can be used during a lecture or presentation to allow
the audience to respond interactively. To use it, you need have a
Twitter account, and create your own "Twitter app" associated with
that account. It will take you only a couple of minutes to create the
app at  `dev.twitter.com <https://dev.twitter.com>`_. (You can
give it any name you like.) The first time you use the client, you
will be prompted to enter the access credentials associated
with your Twitter app.

Once the app is setup, the Twitter client can be used as follows::

  # Post a tweet from your account
  gtweet My first tweet
  # Display all tweets mentioning "python"
  gtweet --search python
  # Display direct messages and tweets directed to the user
  gtweet --recv

By default, the Twitter client displays tweets graphically using
the fullscreen (``-f``) option, although it also has text (``--text``)
and CSV format (``--csv``) output options. You can also combine the
the fullscreen and the text/csv options to save a copy of all the displayed
tweets by redirecting ``stderr`` to a file, as follows::

  gtweet -f --csv --search python 2> tweets.csv

