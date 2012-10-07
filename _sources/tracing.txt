*********************************************************************************
 Using GraphTerm with OTrace
*********************************************************************************
.. contents::


GraphTerm was originally developed as a graphical front-end for
`otrace <http://code.mindmeldr.com/otrace>`_,
an object-oriented python debugger. Any Python program
can serve as a "host" and be connected to the GraphTerm server
using the ``gotrace`` command::

  gotrace example.py

The above command loads ``example.py`` as a module and connects
to the GraphTerm server for debugging. This program will appear in
the list of hosts under the name ``example``. Open the terminal session
``example/osh`` to connect to the *otrace* console, and issue
the ``run <function>`` command to begin executing a function in
``example.py``. You can also initiate program execution
directly from the command line as follows::

  gotrace -f test example.py arg1 arg2
 
The above command executes the function ``test(arg=[])`` in
``example.py``, where ``arg`` is a list of string arguments from
the command line.

If you wish to use the *otrace* console features for multiplexing,
without actually needing to a debug a program, you can use
the ``--oshell`` option when using ``gtermhost`` to connect
to the server.

(You can also embed code in a Python program to directly connect
to the GraphTerm server for monitoring/debugging. See
``gotrace.py`` to find out how it can be done.)

