*********************************************************************************
 API for writing GraphTerm-aware programs
*********************************************************************************
.. contents::



A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_
writes to to the standard output in a format similar to a HTTP
response, preceded and followed by
``xterm``-like *escape sequences*::

  \x1b[?1155;<cookie>h
  {"content_type": "text/html", ...}

  <div>
  ...
  </div>
  \x1b[?1155l

where ``<cookie>`` denotes a numeric value stored in the environment
variable ``GRAPHTERM_COOKIE``. (The random cookie is a security
measure that prevents malicious files from accessing GraphTerm.)
The opening escape sequence is followed by a *dictionary* of header
names and values, using JSON format. This is followed by a blank line,
and then any data (such as the HTML fragment to be displayed).

A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_
can be written in any language, much like a CGI script.
The program `helloworld.sh <https://github.com/mitotic/graphterm/blob/master/helloworld.sh>`_
is a simple example.
See also the programs ``gls``, ``gimage``, ``giframe``, ``gvi``, ``gfeed``,
``yweather``, ``ec2launch`` and ``ec2list`` for examples
of GraphTerm API usage. You can use the ``which gls``
command to figure out where these programs are located.
The file ``gtermapi.py`` contains many helper functions for accessing
the GraphTerm API. See also the
`gcowsay <https://github.com/mitotic/gcowsay>`_ program for an
example of a stand-alone GraphTerm-aware command.
