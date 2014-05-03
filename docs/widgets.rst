*********************************************************************************
Widgets, sockets, and interactivity
*********************************************************************************

.. index:: sockets, widgets

A widget appears as an overlay on the terminal (like
*picture-in-picture* for TVs, or dashboard widgets on the Mac). This
is an experimental feature which allows programs running in the background
to display information overlaid on the terminal. (It may be disabled using the
``--widget-port=0`` option.) The widget is accessed by
redirecting ``stdout`` to a Bash ``tcp`` socket device whose address
is stored in the environment variable ``GTERM_SOCKET``.  For example,
the following command will run a background job to open a new terminal
in an overlay *iframe*::

    gframe -f --opacity=0.2 http://localhost:8900/local/new > $GTERM_SOCKET &

You can use the overlay terminal just like a regular terminal,
including having recursive overlays within the overlay! To delete the
widget, just close the socket connection by killing the background
job. (You can use the ``fg`` command to bring the job to the
foreground and then kill it.)

A simple example of a live feed widget is to combine ``gfeed`` with
``tail -f``::

    tail -f output.log | gfeed > $GTERM_SOCKET &

The above feed will display the new lines appended to the file ``output.log``.

Another example of widget use is to display live audience feedback on
the screen during a presentation, sort of like a "twitter feed". The
widget background job should be started before using ``greveal`` to make
a presentation::

  gchat 2> $GTERM_SOCKET 0<&2 | gfeed > $GTERM_SOCKET &
  greveal $GTERM_DIR/bin/landslide/graphterm-talk1.md | gframe -f

The first command uses ``gchat`` to capture feedback from others
viewing the terminal session as a stream of lines from
$GTERM_SOCKET. The viewers use the overlaid *chat* button
to provide feedback. The ``stdout`` from ``gchat`` is piped to
``gfeed`` which displays its ``stdin`` stream as a  "live feed"
overlay, also via $GTERM_SOCKET.

To display a live twitter feed as an overlay on a presentation, you can use the
commands::

  gtweet -w -f -s topic > $GTERM_SOCKET &
  greveal $GTERM_DIR/bin/landslide/graphterm-talk1.md | gframe -f

