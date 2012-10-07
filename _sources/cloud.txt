*********************************************************************************
 GraphTerm in the cloud
*********************************************************************************
.. contents::



The GraphTerm distribution includes the scripts ``ec2launch, ec2list, ec2scp,``
and ``ec2ssh`` to launch and monitor Amazon Web Services EC2
instances. These are the scripts used to test new
versions of GraphTerm by running them in the "cloud".
You will need to have an Amazon AWS
account to use these scripts, and also need to install
the ``boto`` python module. 

To create an instance, use the ``ec2launch`` command.
You will be presented with a "web form" to enter details of the instance
to be launched. Once you fill in the form and submit it, a command
line will be automatically created, with command options, to launch
the instance. To launch another instance with slightly different
properties, you can simply recall the command line and edit it.
Ensure that the security group associated with the cloud instance
allows access to inbound TCP port 22 (for SSH access), 8900
(for GraphTerm users to connect), and
port 8899 (for GraphTerm hosts to connect).

To *temporarily* run a publicly accessible GraphTerm server for
demonstration or teaching purposes, log in to the instance using
the command ``ec2ssh ubuntu@instance_address``, wait a few
minutes for ``tornado`` and ``graphterm`` packages to finish
installing, and then issue the following command::

   gtermserver --daemon=start --auth_code=none --host=<primary_domain_or_address>

*Note: This is totally insecure and should not be used for handling any sensitive information.*

Secondary cloud instances should connect to the GraphTerm server on
the primary instance using the command::

   gtermhost --daemon=start --server_addr=<primary_domain_or_address> <secondary_host_name>

For increased security in a publicly-accessible server,
you can use a cryptic authentication code,
and also use *https* instead of *http*, with SSL certificates.
Since GraphTerm is currently in *alpha* status,
security cannot be guaranteed even with these options enabled.
(To avoid these problems, use SSH port forwarding to access GraphTerm
on ``localhost`` whenever possble.)

