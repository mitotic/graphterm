*********************************************************************************
Widgets, sockets, and interactivity
*********************************************************************************

.. index:: sockets, widgets

A widget appears as an overlay on the terminal (like
*picture-in-picture* for TVs, or dashboard widgets on the Mac). This is an
experimental feature that allows programs running in the background to
display information overlaid on the terminal. The widget is accessed
by redirecting ``stdout`` to a Bash ``tcp`` socket device whose
address is stored in the environment variable ``GTERM_SOCKET``.
For example, the following command will run a background job
to open a new terminal in an overlay *iframe*::

  gframe -f --opacity=0.2 http://localhost:8900/local/new > $GTERM_SOCKET &

You can use the overlay terminal just like a regular terminal, including
having recursive overlays within the overlay!

A specific example of widget use is to display live feedback on the
screen during a presentation. You can try it out in a directory that
contains your presentation slides as images::

  gfeedback 2> $GTERM_SOCKET 0<&2 | gfeed > $GTERM_SOCKET &
  gimage -f

The first command uses ``gfeedback`` to capture feedback from others
viewing the terminal session as a stream of lines from
$GTERM_SOCKET. The viewers use the overlaid *feedback* button
to provide feedback. The ``stdout`` from ``gfeedback`` is piped to
``gfeed`` which displays its ``stdin`` stream as a  "live feed"
overlay, also via $GTERM_SOCKET.
(The ``gimage -f`` command displays all the images in the directory as a
slideshow.)

To display a live twitter feed as an overlay on a presentation, you can use the commands::

   gtweet -w -f -s topic > $GTERM_SOCKET &
   gimage -f

