Use GraphTerm as a remote terminal (like screen or tmux)
***************************************************************************************
.. sectnum::
.. contents::


Introduction
======================================================================

GraphTerm provides the basic capabilities of *detached terminal* programs like
``screen`` and ``tmux``. The GraphTerm terminal window is just a web page,
served by ``gtermserver``. Therefore, it can be accessed from any computer
with access to the server, either locally or remotely. All you need to do
is to load the URL for the terminal session on a new computer, and you can
continue working from the point where you stopped previously.

A typical use of GraphTerm would be to run
``gtermserver`` on your work computer, and access it locally at work
and remotely from home. For security, it would be best to run the server
as ``localhost`` on the work computer, and use SSH port forwarding to
connect to it from other computers.

Another use of GraphTerm would be to run the server on managing host of a computer
cluster, or a group of cloud instances. Other hosts can connect to the managing
host using the ``gtermhost`` command. *In this case, the hosts should
connect via a private network, not the the public internet.* The state of the terminal is
stored on the host machine, not on ``gtermserver``. You can restart ``gtermserver``
and the hosts will automatically reconnect.



Accessing graphTerm from a remote computer using SSH
======================================================================================

Assume that you will be running ``gtermserver`` on your ``work-computer`` as
``localhost`` listening on the default port 8900 using the command::

  gtermserver --auth_code=none

At work, you will use the URL ``http://localhost:8900/local/tty1`` to access
your terminal session ``tty1``.

To access your work terminal from home, connect to your work computer using SSH::

  ssh -L 8901:localhost:8900 user@work-computer

The above command maps your work computer port 8900 to your home computer port 8901.
(There is also a ``-R`` option that provides a reverse port mapping, which can be useful if
you can log into your desktop from your laptop, and wish to access
your laptop files using the desktop browser, by mapping laptop port 8900 to
desktop port 8901.)

After establishing the SSH connection, you can access your work terminal session from
home using the URL::

  http://localhost:8901/local/tty1

(If you forgot to detach your work terminal before leaving, use the
*Action->Steal session* menu option to steal control of the session.)

If you have multiple terminals open, use the URL ``http://localhost:8901/local`` to
see a list of all the available terminal sessions.

Connecting multiple hosts to gtermserver
======================================================================================


The ``gtermhost`` command can be used to connect from any computer to
``gtermserver`` running on a management cmputer as follows:

     gtermhost <serveraddr> <hostname>

where ``serveraddr`` is the address or name of the computer where
``gtermserver`` is running. (By default, it listens for host
connections on port 8899.) You can use SSH tunneling to
access ``gtermserver`` on the management computer, and thus access the
hosts, which should be on a secure private network.

NOTE: Unlike the ``sshd`` server, the ``gtermhost`` command is designed to
be run by a normal user, not a privileged user. So different users can
connect to ``gtermserver`` pretending to be different "hosts"
on the same computer. 
