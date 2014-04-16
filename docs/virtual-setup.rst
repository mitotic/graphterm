.. _virtual-setup:

*********************************************************************************
 Setting up a Virtual Computer Lab in the cloud
*********************************************************************************
.. contents::

.. index:: virtual computer lab, cloud computing, cloud instance, Amazon EC2


This section describes how to configure a Virtual Computer Lab using
GraphTerm on a Linux server. If you are using the Amazon Web Services
(AWS), most of these configuration steps described below are
automatically carried out by the ``ec2launch`` command. If you are
using a different cloud computing service, you can either modify
``ec2launch`` or write your own script to configure the server.

The GraphTerm distribution includes the scripts ``ec2launch, ec2list,
ec2scp,`` and ``ec2ssh`` to launch and monitor AWS Elastic Computing
Cloud (EC2) instances running a GraphTerm server. These scripts are
used to test new versions of GraphTerm by running them in the "cloud".
You will need to have an AWS account to use these scripts, and also
need to install the ``boto`` python module.

A companion section provides information on :doc:`virtual-lab` after
it has been set up. It can be printed and distributed to the users to
serve as a quick start guide.

Quick setup
--------------------------------------------------------------------------------------------

The following steps allow yout quickly launch a "virtual computer lab"
with multi-user support.

 1. If you do not have an `AWS <http://aws.amazon.com/>`_ account,  get one by
    `clicking here <http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html>`_
    The AWS account will be linked to your standard Amazon account.

 2. Create an SSH key pair to access your AWS instances by `clicking here <http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html>`_. You
    need to name the key pair ``ec2key`` to be able to use the
    ``ec2ssh`` and ``ec2scp`` commands.

 3. Install ``graphterm`` on your local computer using the following commands:

    ``easy_install graphterm``
    ``gterm_setup``

 4. Run graphterm on your local computer:

    ``gtermserver --auth_type=none``

    The above command should automatically open up a GraphTerm window in
    your browser. You can open one using the URL http://localhost:8900

 5. Run the following command within the graphterm window:

    ``ec2launch``

    The first time, you will be asked to enter your AWS access credentials, which will
    be stored in the local file ``~/.boto``.  Also, enter the SSH key
    pair name. Choose ``auth_type`` as ``multiuser``.

 6. After cloud server has completed configuration, which can take
    several minutes, type the following command using the domain name of
    the newly created server to login to the password-less super user account ``ubuntu``:

    ``ec2ssh ubuntu@aws_domain_name``

 7.  Run the following command on the AWS instance to verify that the graphterm server is running:

    ``ps -ef|grep gtermserver``

 8.  Run the following command in the AWS instance to display the *master access code*:

    ``cat ~/.graphterm/@aws_domain_name_gterm_auth.txt``

 9. Use the URL http://aws_domain_name to open a new graphtem window on the AWS
    server, with  user name ``ubuntu`` and the *master access code*

 10. Run the following command in the AWS graphterm window to display  the group access code:

    ``gauth -g -m ubuntu``

 11. Use the command ``gls --download $GTERM_DIR/bin/gterm.py`` to
     download the executable script ``gterm.py`` to your local computer
     and save the master access code in the local file
     ``~/.graphterm/@aws_domain_name_gterm_auth.txt`` to use the
     following local command to create remote graphterm windows:

    ``gterm.py -u ubuntu --browser=Firefox http://aws_domain_name``

 12. Run the following command on your local computer to list and/or kill your AWS instances:

    ``ec2list``

Domain name and IP address
--------------------------------------------------------------------------------------------

A server needs a domain name or IP address to be accessible. When you
start up a new cloud server, it is usually assigned a dynamic IP
address. For temporary use, i.e., during the up-time of the server,
you can simply use this IP address to create an URL for the server
like ``https://1.2.3.4:8900``. AWS also provides a long temporary
domain name that can also be used to create an URL.

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
local (single-user) computer as described in the Quickstart
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
   shared or public computer. You will need to enter the code found in
   the file ``~/.graphterm/_gterm_auth.txt`` to access the server.

   *none*: This requires no authentication, and is meant to be used on a
   private computer with a single-user.

   *name*: This also requires no authentication, but new users choose a
   unique username. This is meant for demonstration purposes and all
   users share the same Unix account.

   *multiuser*: This option allows new users enter enter a group
   authentication code, along with a unique user name. This creates a
   new Unix account for the user and generates a unique access code
   that will be used the next time the user logs in. The super user
   can view all the access codes using the ``gauth`` command.

Once you fill in the form for ``ec2launch`` and submit it, a command
line will be automatically generated, with the specified options, to launch
the instance. You may need to wait several minutes for the instance
setup to complete, depending upon the compute power of the
instance. To launch another instance with slightly different
properties, you can simply recall the command line from history and
edit it. (If you wish to re-display the form, add the option ``--form``
to the recalled command line.)

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

    gtermserver --daemon=start --widget_port=-1 --auth_type=multiuser --auto_users --super_users=ubuntu --allow_embedding --nb_server --https --external_port=443 --host=domain_or_ip

The above options configure the server for multiuser authentication,
with https. (``ec2launch`` automatically configures port forwarding
from port 443 to the default graphterm port 8900.)

By default, running an Ubuntu linux instance on AWS
creates an account with username ``ubuntu`` with password-less
``sudo`` privileges. By default, GraphTerm server is run from this
account. An account with password-less ``sudo`` privileges is required
for new users to be created automatically (``--auto_users`` option).
AWS automatically creates such an account, named ``ubuntu``,  as described
`here <http://askubuntu.com/questions/192050/how-to-run-sudo-command-with-no-password>`_.

To automatically start the server when the computer is rebooted, copy
the ``gtermserver`` command line to the executable file ``/etc/init.d/graphterm`` on a Ubuntu
server, or equivalent for other linux flavors (``ec2launch``
automatically does this).


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

on the server. The super user can also use the ``gterm_user_setup``
script to manually configure new users.


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


Administering the GraphTerm server
--------------------------------------------------------------------------------------------

The ``gadmin`` command performs administrative actions to manage
users::

    # Display status for all terminals with path name matching python regexp
    gadmin -a sessions [regexp]

Configuring groups
--------------------------------------------------------------------------------------------

In the multiuser authentication mode, user groups can be configured
the file ``~/.graphterm/gterm_groups.json`` containing a JSON formatted
dictionary, e.g.::

    {"group1": ["user1", "user2"],
     "group2": ["user3", "user4", "user5"]}


Secondary cloud instances
--------------------------------------------------------------------------------------------

Secondary cloud instances can connect to the GraphTerm server on
the primary instance using the command::

    gtermhost --daemon=start --server_addr=<server_domain_or_address> <secondary_host_name>

*Note:* It would be better to use an internal (non-public) network address to
connect secondary cloud instances.
