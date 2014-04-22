.. _virtual-setup:

*********************************************************************************
 Setting up a Virtual Computer Lab in the cloud
*********************************************************************************
.. contents::

.. index:: virtual computer lab, cloud computing, cloud instance, Amazon EC2


This section describes how to configure a Virtual Computer Lab using
GraphTerm on a Linux server. If you do not already have a Linux server
available, you can easily create one on demand using Amazon Web
Services (AWS). Most of the AWS configuration steps described below
are automatically carried out by the ``ec2launch`` command. (If you are
using a different cloud computing service, you can either modify
``ec2launch`` or write your own script to configure the server.)

A companion section provides information on :doc:`virtual-lab` after
it has been set up. It can be printed and distributed to the users to
serve as a quick start guide.

The GraphTerm distribution includes the convenience scripts
``ec2launch, ec2list, ec2scp,`` and ``ec2ssh`` to launch and monitor
AWS Elastic Computing Cloud (EC2) instances running a GraphTerm
server. You will need to have an AWS account to use these scripts, and
also need to install the ``boto`` python module. (These scripts are
routinely used during GraphTerm development to test new versions by
running them in the "cloud". )

Quick setup
--------------------------------------------------------------------------------------------

The following steps allow you to quickly launch a "virtual computer lab"
with multi-user support and the option of *Google Authentication*.

 1. Install ``graphterm`` on your computer using the following two commands:

    ``easy_install graphterm``

    ``gterm_setup``

 2. If this computer is a pristine Linux/Mac server where you want to run the
    multiuser GraphTerm server, with automatic new user creation,
    configure an user (named, say, ``ubuntu``) with
    `password-less <http://askubuntu.com/questions/192050/how-to-run-sudo-command-with-no-password>`_
    ``sudo`` privileges, use the following command to start the
    GraphTerm server and then *skip to Step 9*:

   ``sudo gtermserver --daemon=start --widget_port=-1 --auth_type=multiuser --auto_users --super_users=ubuntu --port=80 --host=server_domain_name_or_ip``

 3. If you do not already have a server, you should obtain an `AWS <http://aws.amazon.com/>`_ account by
    `clicking here <http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html>`_.
    The AWS account will be linked to your standard Amazon account.

 4. Create an SSH key pair to access your AWS instances by `clicking here <http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html>`_. You
    need to name the key pair ``ec2key`` to be able to use the
    ``ec2ssh`` and ``ec2scp`` commands bundled with GraphTerm.

 5. Run graphterm on your local (single-user) computer:

    ``gtermserver --auth_type=none``

    The above command should automatically open up a GraphTerm window in
    your browser. You can also open one using the URL http://localhost:8900
    (*Note:* This is insecure on a shared, multi-user, computer; omit
    the ``--auth_type=none`` server option in that case.)

 6. Run the following command within the graphterm window to create a Linux server:

    ``ec2launch``

    The first time, you will be asked to enter your AWS access
    credentials, which will be stored in the local file ``~/.boto``.
    Then run the command again, enter a tagname (e.g., ``testlab``),
    choose ``auth_type`` as ``multiuser``, and select the ``pylab``
    and ``netcdf`` options. When you press the *submit* button, the
    generated command line should look something like this:

    ``ec2launch -f --type=m3.medium --key_name=ec2key --ami=ami-2f8f9246 --gmail_addr=user@gmail.com --auth_type=multiuser --pylab --netcdf testlab``

 7. After the new AWS Linux server has completed configuration, which
    can take several minutes, its IP address and *server domain name*
    will be displayed. If all went well, and you provided your GMail
    address, you should be able to login to the server using the URL
    ``http://server_domain_name`` and username ``ubuntu``, and *skip
    to Step 14.*

 8. If something went wrong, or you are not using Google
    Authentication, type the following command using the new domain name to
    login to the password-less super user account ``ubuntu``:

    ``ec2ssh ubuntu@server_domain_name``

 9.  Run the following command on the server to verify that ``gtermserver`` is running:

    ``ps -ef | grep gtermserver``

    If not, check for errors in the AWS setup procedure by typing ``sudo tail /root/ec2launch.log``

 10.  Run the following command on the server to display the *master access code*:

    ``cat ~/.graphterm/@server_domain_name_gterm_auth.txt``

    (Ignore the port number following the hexadecimal access code.)

 11. Use the URL http://server_domain_name to open a new graphtem window on the
    server, with the super user name (``ubuntu`` in our case) and the *master access code*

 12. Optionally, use the command ``gls --download $GTERM_DIR/bin/gterm.py`` to
     download the executable script ``gterm.py`` to your local computer
     and save the master access code in the local file
     ``~/.graphterm/@server_domain_name_gterm_auth.txt``. Then use the
     following local command to easily create remote graphterm windows:

    ``gterm.py -u ubuntu --browser=Firefox http://server_domain_name``

 13. Alternatively, if you wish to use your *GMail* account to
     authenticate, enter your *GMail* address in the file
     ``~/.graphterm/gterm_email.txt`` on the server. (If you selected
     the ``gmail_addr`` option during ``ec2launch``, this file would
     already have been created.)

 14. Run the following command in the server graphterm window to display the group access code which should be entered by new users:

    ``cat ~/.graphterm/gterm_gcode.txt``

    Distribute this code and a printed copy of :doc:`virtual-lab` to
    all lab users.

 15. If using AWS, run the following command on your local graphterm window to list and/or kill your instances:

    ``ec2list``

Domain name and IP address
--------------------------------------------------------------------------------------------

A server needs a domain name or IP address to be accessible. When you
start up a new cloud server, it is usually assigned a dynamic IP
address. For temporary use, i.e., during the up-time of the server,
you can simply use this IP address to create an URL for the server
like ``https://1.2.3.4:8900``. AWS also provides a long instance
domain name that can be used to create an URL.

For a prettier and more permanent URL, you need to register a domain
name, say ``example.com``, with a domain registrar like NameCheap.com,
GoDaddy.com, or Gandi.net (for about $10-20 per year). A single domain
registration is sufficient for any number of servers, as you can
always create subdomains. For a single server, you can update the IP
address associated with the domain on the nameservers of the
registrar.

Alternatively, you can enable the Amazon Route 53 service `Route 53
<http://aws.amazon.com/route53/faqs/#Getting_started_with_Route_53>`_
service and create a hosted zone for your domain `example.com``.  This
will allow the ``ec2launch`` script to automatically assign subdomain
names like ``sub.example.com`` to your servers. Ensure that the
nameserver records for ``example.com`` at your domain registrar
point to the AWS nameservers for the hosted zone.

Network security and port access
--------------------------------------------------------------------------------------------

The cloud server should be configured to allow access to certain
network ports, particularly ports 22 (ssh), 80 (http), and 443
(https). If you plan to enable running of the "public" IPython
notebook server, you should also allow access to the port range
10000-12000. The ``ec2launch`` script automatically sets up an AWS
security group to allow access to these ports.

*Note:* If you have trouble
accessing the instance, check to make sure that the AWS `security group
<http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html>`_
associated with the cloud instance allows access to inbound TCP port
22 (for SSH access).


Launching a server instance
--------------------------------------------------------------------------------------------

To create an AWS instance, you should first run GraphTerm on your
local (single-user) computer as described in the Quick setup
instructions. You will be presented with a web form to enter
configuration details of the instance to be launched. You can specify
a simple *tag name* to identify each server. If you have set-up the
Route 53 service, you can specify a the tag name is of the form
``subdomain.example.com`` to automatically associate the subdomain
with the server IP address. You can also specify whether to install
additional packages, like ``pylab`` for plotting or ``R`` for
statistical analysis.

An important configuration choice is the authentication type
(``auth_type``), which may be one of ``local``, ``none``, ``name``, or ``multiuser``.

   *local*: Local authentication type is meant for a single user on a
   shared computer. You will need to enter the code found in
   the file ``~/.graphterm/_gterm_auth.txt`` to access the server, or
   use the ``gterm`` command to open new GraphTerm windows.

   *none*: This requires no authentication, and is meant to be used on a
   private computer with a single user.

   *name*: This also requires no authentication, but new users choose a
   unique username. This is meant for demonstration purposes and all
   users share the same Unix account.

   *multiuser*: This option allows new users enter enter a group
   authentication code, along with a unique user name. This creates a
   new Unix account for the user and generates a unique access code
   that will be used the next time the user logs in. The super user
   can view all the access codes using the ``gauth`` command. (If the
   users choose to use Google Authentication, they will also be able to
   login using their GMail account.)

Once you fill in the form for ``ec2launch`` and submit it, a command
line will be automatically generated, with the specified options, to launch
the instance. You may need to wait several minutes for the instance
setup to complete, depending upon the compute power of the
instance. To launch another instance with slightly different
properties, you can simply recall the command line from history and
edit it. (If you wish to force re-display of the ``ec2launch`` form to
edit the command visually, include the ``--form`` option in the
recalled command line and execute it.)

Managing instances
--------------------------------------------------------------------------------------------

The ``ec2list`` command can be used to list all running instances, and
also to terminate them (using the ``kill`` link).


Starting and stopping GraphTerm server
--------------------------------------------------------------------------------------------
 
By default, a publicly accessible ``graphterm`` server will be
automatically started on the new instance (and after reboots). Once
the instance is running, you can access the GraphTerm server at
``http://domain_name_or_ip_address``. You can log in to the instance
using the command ``ec2ssh ubuntu@domain_name``, or copy files to it
using ``ec2scp file ubuntu@domain_name:``

To stop a running server, type::

    gtermserver --daemon=stop

If you are not using ``ec2launch``, you can start the server explicitly from the command line, e.g.::

    gtermserver --daemon=start --widget_port=-1 --auth_type=multiuser --auto_users --super_users=ubuntu --allow_embed --nb_server --https --external_port=443 --host=domain_or_ip

The above options configure the server for multiuser authentication,
with https. (``ec2launch`` automatically configures port forwarding
from port 443 to the default graphterm port 8900, enabling even
non-privileged users to run ``gtermserver``.) 

An account with password-less ``sudo`` privileges is required for new
users to be created automatically (``--auto_users`` option).  Running
an Ubuntu linux instance on AWS automatically creates such an account,
named ``ubuntu``, as described `here
<http://askubuntu.com/questions/192050/how-to-run-sudo-command-with-no-password>`_.
By default, GraphTerm server is run from this account. The
``auto_users`` option creates a file named
``~/.graphterm/AUTO_ADD_USERS`` which can be deleted to suppress
auto-user creation while the server is running.

To automatically start the server when the computer is rebooted, copy
the ``gtermserver`` command line to the executable file ``/etc/init.d/graphterm`` on a Ubuntu
server, or equivalent for other linux flavors (``ec2launch``
automatically does this for AWS).


Access codes
--------------------------------------------------------------------------------------------

The *master access code* is stored in the file
``~/.graphterm/@server_gterm_auth.txt`` in the home directory of the super
user, and can be used to sign in as any user. (To generate new random
access codes, simply delete this file.)  To display the access code
for a particular user, use the following command within a GraphTerm on
the remore machine::

    gauth -m username

The user-specific access code is also save in the user's home
directory in ``~user/.graphterm/user@server_gterm_auth.txt``.

To avoid having to type in the access code every time, you can
download the executable python script ``$GTERM_DIR/bin/gterm.py``
to your desktop/laptop computer. You can then type the following command::

    gterm.py -u user http://server_domain

to open a terminal on the remote server. You will be asked for the
access code the first time, and then it can be saved in your
local ``~/.graphterm`` directory for future use.

To display the group access code (needed to generate new accounts), type::

    gauth -g -m super_username

on the server.

The super user can also use the shell script ``gterm_user_setup``
in ``$GTERM_DIR/bin`` to manually configure new users::

    sudo gterm_user_setup username activate server_domain user_email

*Note:* This script may need to be modified to work on non-AWS servers.

Using https
--------------------------------------------------------------------------------------------

You can run the ``gtermserver`` with the ``--https`` option enabled
for limited security. By default, it will create a self-signed
certificate stored in ``~/.graphterm/localhost.pem``. Inform users
that self-signed certificates will generate multiple browser warning
messages.  (For maximum security, you can purchase a domain
certificate signed by an authority, which is often available through
the domain registrar.)


Running a public IPython Notebook server
--------------------------------------------------------------------------------------------

Specifying the ``--nb_server`` when starting up the GraphTerm server
enables a menu option allowing each user to run to run the the
``gnbserver`` command which starts up a public IPython Notebook server
listening on a unique port number that is tied to the user's Unix user
ID. (A similar option for ``ec2launch`` opens up these ports for
public access.)

If using ``https``, the self-signed certificate created for the
GraphTerm server can be re-used for the IPython public notebook
server, by copying the file ``~/.graphterm/localhost.pem`` to
``/var/graphterm/localhost.pem`` to make it accessible to all users.


Administering the virtual computer lab
--------------------------------------------------------------------------------------------

The ``gadmin`` command (a work in progress) performs administrative
actions to manage users::

    # Display status for all terminals with path name matching python regexp
    gadmin -a sessions [regexp]

Clicking on the displayed terminal list will open up the terminal for
viewing (see :ref:`gadmin_users_shot`).

You can also view multiple user terminals embedded in your own
terminal using the ``gframe`` command (see :ref:`gadmin_terminals_shot`)::

    gframe --rowheight 300 --border --columns 3 --terminal /bob/quiz1 /jane/quiz1 /jose/quiz1



Configuring groups
--------------------------------------------------------------------------------------------

In the multiuser authentication mode, user groups can be configured
the file ``~/.graphterm/gterm_groups.json`` containing a JSON formatted
dictionary, e.g.::

    {"group1": ["user1", "user2"],
     "group2": ["user3", "user4", "user5"]}

Users in the same group can see each others' terminals for collaboration.

Secondary cloud instances
--------------------------------------------------------------------------------------------

Secondary cloud instances can connect to the GraphTerm server on
the primary instance using the command::

    gtermhost --daemon=start --server_addr=<server_domain_or_address> <secondary_host_name>

*Note:* It would be better to use an internal (non-public) network address to
connect secondary cloud instances.
