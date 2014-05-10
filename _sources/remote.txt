*********************************************************************************
Remote access and SSH
*********************************************************************************
.. contents::


.. index:: remote access, ssh

Remote logins
--------------------------------------------------------------------------------------------

One of the most powerful features of GraphTerm is that basic inline
image display and the notebook mode of GraphTerm work transparently
across multiple SSH login boundaries. For example, in your GraphTerm
window you can SSH to a remote computer and display a plot using
python as follows::

    local$ ssh user@remote_server

    remote$ python -i $GTERM_DIR/bin/gpylab.py

    >>> plot([1,2])

assuming the requisite files (see below) are present in the remote
``$GTERM_DIR/bin`` directory. You don't need to start a server on the
remote computer because all communication occurs via the standard
input/output of the remote python interpreter. In addition to
displaying inline graphics, you can switch to notebook mode simply by
typing *Shift-Enter*, just like you would on your local computer.
(Note that saving/reading notebook files will take place on your
current local directory, not on the remote system.)

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-ssh-plot.png
   :align: center
   :width: 90%
   :figwidth: 85%


Remote installation
--------------------------------------------------------------------------------------------

A minimalist remote installation of the GraphTerm environment requires
copying six files from the local ``$GTERM_DIR/bin`` directory to the
directory ``~/graphterm/bin`` on the remote computer::

    cd $GTERM_DIR/bin
    ssh user@remote_server mkdir -p graphterm/bin
    scp gterm.py gmatplot.py gpylab.py gimage galiases gprofile user@remote_server:graphterm/bin

If you will be using R, also copy the file ``gterm.R``. Then, append the
following line to your remote ``~/.profile`` or ``~/.bash_profile`` setup::

    source ~/graphterm/bin/gprofile

and the following line to ``~/.bashrc``::

    source ~/graphterm/bin/galiases

These scripts define convenient aliases like ``gpython`` and add
``~/graphterm/bin`` to your PATH variable, so that you can use the
``gimage`` command to display inline images.

For a more complete configuration, you can install GraphTerm in your
home directory on the remote system, even if you never plan to run the
server. Download the ``graphterm-version.tar.gz`` source tarball from
https://pypi.python.org/pypi/graphterm, untar it and copy the
subdirectory ``graphterm`` to ``~/graphterm``. (If you have root
access, you can choose to install ``graphterm`` for all users on the
remote computer using ``sudo pip install graphterm``.)


.. index:: port forwarding

Port forwarding
--------------------------------------------------------------------------------------------

The more advanced features of GraphTerm are explicitly disabled from
working across SSH login boundaries for security reasons.  If you need
the full suite of features, the most secure way to access the
GraphTerm server running on a remote computer is to use SSH port
forwarding. For example, if you are connecting to your work computer
from home, and wish to connect to the GraphTerm server running as
``localhost`` on your work computer, use the command::

   ssh -L 8901:localhost:8900 user@work-computer

This will allow you to connect to ``http://localhost:8901`` on the browser
on your home computer to access GraphTerm running on your work
computer. If using *singleuser* authentication, copy the file
``~/.graphterm/_gterm_auth.txt`` from work to home as
``~/.graphterm/@server_name_gterm_auth.txt``, and use
the ``gterm`` command::

    gterm  --server server_name --port 8900 http://localhost:8901


.. index:: reverse port forwarding

Reverse port forwarding
--------------------------------------------------------------------------------------------

A completely different approach is to use reverse forwarding.
*Warning: If the remote computer is insecure, reverse forwarding
should be used caution, and preferably with multiuser authentication
(without the user_setup option).* Install GraphTerm on the remote
computer and run the ``gtermhost`` program remotely to allow it to
connect to the ``gtermserver`` running on your local computer using
SSH reverse port forwarding, e.g.::

    gauth remote1 | ssh user@remote1 'cat > ~/.graphterm/remote1_gterm_auth.txt' 
    ssh -R 8799:localhost:8899 user@remote1 gtermhost --server_port 8799 --remote_port=8899 remote1

In this case, the remote computer will appear as another host on your
local GraphTerm server. 

*Note: Do not do the following unless you trust the remote machine.
A malicious remote program could execute commands on your
local computer if it has access to the GraphTerm window.*
If you do not wish to have a GraphTerm process running on
the remote machine, you can still use many features though GraphTerm
running on your local machine, because all communication takes place
via the standard output of the remote process. One quick solution is
use the *terminal/export environment* menu option to set the Bash
shell environment variables on the remote computer. This will allow
some, but not all, of GraphTerm's features to work on the remote
session. A more permanent solution involves the following three steps:

 - Start the local GraphTerm server using the ``--lc_export=graphterm`` or
   ``--lc_export=telephone`` options, which export the GraphTerm environment
   via the ``LC_*`` environment variables which are typically transmitted
   across SSH tunnels.

 - Copy the ``$GTERM_DIR/bin`` directory to ``~/graphterm`` on the
   remote machine to allow the GraphTerm toolchain to be accessed:

   ``ssh user@remote_server mkdir graphterm``

   ``scp -pr $GTERM_DIR/bin user@remote_server:graphterm``

   Alternatively, you could simply install GraphTerm on the
   remote machine, even if you are never planning to start the server.

 - Append the file
   `$GTERM_DIR/bin/gprofile <https://github.com/mitotic/graphterm/blob/master/graphterm/bin/gprofile>`_
   to your ``.profile`` on the remote machine:

   ``cat gprofile >> ~/.profile``

   Although this script can usually detect your GraphTerm installation
   directory, sometimes you may need to modify the last few lines to
   ensure that the GraphTerm toolchain is included in your ``PATH`` on
   the remote machine. This would allow commands like ``gls`` to work.
