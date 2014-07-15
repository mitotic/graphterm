*********************************************************************************
 Extending GraphTerm
*********************************************************************************

.. contents::

.. index:: extending GraphTerm, API, hello_gterm.sh, graphterm-aware
	   commands, toolchain

The GraphTerm toolchain can be extended by writing additional
executable commands in any language, much like a `CGI
<http://en.wikipedia.org/wiki/Common_Gateway_Interface>`_ script.  The
program `hello_gterm.sh
<https://github.com/mitotic/graphterm/blob/master/graphterm/bin/hello_gterm.sh>`_
is a simple example.  See also the programs ``gls``, ``gimage``,
``gframe``, ``gvi``, ``gfeed``, ``yweather``, ``ec2launch`` and
``ec2list`` for examples of GraphTerm API usage. You can use the
``which gls`` command to figure out where these programs are located.
The file ``gterm.py`` contains many helper functions for accessing the
GraphTerm API.

*Note:* The GraphTerm Application Programming Interface (API) is
rather poorly documented, because it is still evolving. If you
develop a non-trivial application using this API, please be aware that
some of the details may change.

GraphTerm comment directive
-----------------------------------------------------------------------

A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_
communicates with GraphTerm following the standard protocol for Unix
programs to communicate with the terminal, i.e., by writing some text
to the standard output, prefixed and suffixed by special *escape*
sequences. The prefix sequence is the string ``\x1b[?1155;<cookie>h``
and the suffix sequence is ``\x1b[?1155l``, where ``\x1b`` denotes the
Escape character and ``<cookie>`` denotes a numeric value stored in the
environment variable ``GTERM_COOKIE``. This is a security measure that
prevents malicious files from accessing GraphTerm. Only executable
scripts and programs will be able generate the special escape
sequences.

*Note*: On a remote machine accessed via SSH, the cookie value will
not be available. In that case, the dummy value ``0`` may be used to
access basic GraphTerm features like displaying images and HTML within
a frame. (For security reasons, advanced features of GraphTerm, such
as command execution, cannot be accessed using the dummy cookie value
of zero.)

If the text output by the program (excluding the escape sequences)
starts with the left-angle bracket (``<``), it is interpreted as being
an HTML fragment to be displayed within GraphTerm as output of the
command. For example, outputting the following string will display the
text ``Hello World`` in bold face::

  \x1b[?1155;<cookie>h<b>Hello World!</b>\x1b[?1155l

The output HTML fragment may optionally begin with a special
*Graphterm directive* which looks like an HTML comment line::

  \x1b[?1155;<cookie>h<!--gterm clear_terminal-->\x1b[?1155l

The above string, if output by a program, will clear output from
the terminal. The GraphTerm always begins with string
``<!--gterm`` and ends with ``-->``, like an HTML comment line. The
directive begins with an action (``clear_terminal``) and may be
followed by optional arguments of the form ``name=value``.

The basic actions and optional arguments are:

  ``data display=block|fullwindow autoerase=yes overwrite=yes exit_page=yes``   (display data URI content; typically used for images) 

  ``pagelet display=block overwrite=yes``   (display arbitrary HTML page fragment
  from content following the directive)

The ``overwrite`` option allows previously displayed content to be
overwritten, enabling simple animations etc. The ``autoerase`` option
automatically erases the content when the command ends.
The ``data`` action allows
`data URIs <http://en.wikipedia.org/wiki/Data_URI_scheme>`_ to be
displayed (even across SSH logins).
The ``pagelet`` action allows arbitrary HTML fragments to be displayed
inline. The following python command will display inline HTML::

  print "\x1b[?1155;<cookie>h"+"<!--gterm pagelet display=block-->"+"<b>Hello World!</b>"+"\x1b[?1155l"

The ``data`` and ``pagelet`` actions are unprivileged, i.e., they can
be executed even with a dummy cookie value of 0. However, pagelets without a valid
cookie value are treated specially, because they are untrusted. They
are always displayed in the full window mode, using a separate "web
origin" for security. For example, the following Python ``print``
statement will display an inline image from a data URL::

  print "\x1b[?1155;0h"+"<!--gterm data -->"+"image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="+"\x1b[?1155l"

The sample program ``hello_world.sh`` in ``$GTERM_DIR/bin`` displays
the above string. Executing the program across an SSH login will
still display the red dot.

A displayed inline image can be overwritten. The following line
will overwrite the last displayed image with a new image containing a
single white pixel::

  print "\x1b[?1155;0h"+"<!--gterm data overwrite=yes-->"+"image/gif;base64,R0lGODlhAQABAIAAAP///wAAACwAAAAAAQABAAACAkQBADs="+"\x1b[?1155l"


Other useful actions are:

  ``clear_terminal``   (*gclear*: clear the terminal) 

  ``error_message``    (display content as plain text error message in browser window)

  ``menu_op target=view_menubar value=on|off`` (*gmenu*: execute menu operation) 

  ``nb_clear all=yes`` (clear notebook cell output)

  ``open_url width=400 height=300 target=...``    (*gopen*: open URL)


GraphTerm JSON headers
-----------------------------------------------------------------------

The HTML comment directive format is the simplest way for programs to
communicate with GraphTerm, and would suffice for most purposes. An
alternative JSON header format is also available to handle more
complex options, data etc.::

  \x1b[?1155;<cookie>h
  {"content_type": "text/html",
   "x_gterm_response": "pagelet",
   "x_gterm_parameters": {"display": "fullwindow"}
  }

  <div>
  Hello World!
  </div>
  \x1b[?1155l

This is equivalent to the HTML comment directive::

  <!--gterm pagelet display=fullwindow--><div>Hello World!</div>

Note that for the JSON header format, the opening escape sequence is
followed by a *dictionary* of header names and values, using JSON
format. This must be followed by a single *blank line* and then any
content data (such as the HTML fragment to be displayed).


gterm API module
-----------------------------------------------------------------------

The Python module ``$GTERM_DIR/bin/gterm.py`` contains many
convenience functions for accessing the textual GraphTerm API. The
following Python code will display some raw HTML followed by an
image::

  import grapherm.bin.gterm as gterm

  gterm.write_html("<b>Hello Wordl!</b>")

  with open("sample.png") as f:
      content = f.read()
  gterm.display_data("image/png", content, display="block")

See the toolchain programs ``gimage``, ``gframe``, etc. for examples
of this API usage.

The file ``$GTERM_DIR/bin/gterm.R`` provides convenience wrapper
functions for ``R``.


Clickable links for generating commands
-----------------------------------------------------------------------

A program can display clickable HTML links that can automatically
generate a command line and paste it into the terminal. See the
``ec2list`` and ``gls`` programs for examples of this usage. Basically
a clickable HTML ``<a>`` element is identified by the ``class``
attribute ``gterm-click`` and also contains a special attribute
``data-gtermcmd`` that represents the command to be executed. If this
command ends with a space, the displayed text of the element (such as
a file name) is appended as an argument to the command. (If the
``href`` attribute of the ``<a>`` element represents a file URI, then
the file path is appended instead.) To insert the argument elsewhere
in the command, the special escape sequence ``%[arg]`` can be used in
the command string. See the script ``hello_gterm.sh`` or the sample
Python code below::

  import graphterm.bin.gterm as gterm

  html = '<hr><a class="gterm-link gterm-click" href="" data-gtermmime="" data-gtermcmd="echo %[arg] echoed" data-gtermconfirm="Execute echo command?">Clickable Command</a><hr>'

  gterm.write_html(html)

.. index:: command line parsing

Mapping command line arguments to HTML form elements
-----------------------------------------------------------------------

Any Python program that parses command line options and arguments can
be trivially modified to generate an HTML form to request input. The
``gterm`` module provides a ``FormParser`` object that can be used as
an almost drop-in replacement for standard command line parsing using
``optparse.OptionParser``. Here's some example code of this usage
(modified from ``ec2launch``)::

    import sys
    import grapherm.bin.gterm as gterm

    # Create FormParser object
    form_parser = gterm.FormParser(usage=usage, title="Create Amazon EC2 instance with hostname: ", command="ec2launch -f")

    # First argument (required)
    form_parser.add_argument(label="", help="Instance tagname")

    # Choice option
    form_parser.add_option("type", ("m3.medium", "m3.large", "c3.large"), help="Instance type")

    # String option
    form_parser.add_option("gmail_addr", "", help="Full gmail address, user@gmail.com")

    # Boolean option
    form_parser.add_option("https", False, help="Use https for security")

    # Raw options (not displayed in form)
    form_parser.add_option("form", False, help="Force form display", raw=True)
    form_parser.add_option("fullpage", False, short="f", help="Fullpage display", raw=True)
    form_parser.add_option("text", False, short="t", help="Text only", raw=True)

    (options, args) = form_parser.parse_args()

    if not gterm.Lterm_cookie or not sys.stdout.isatty():
        # Not running within GraphTerm or stdout is piped; text only
        options.text = True

    if not args or options.form:
        # Invoked with no arguments or with force form display option
        if options.text:
            # Display text help and quit
            sys.exit(form_parser.get_usage())
        # Display form, prefilling it if need be
        gterm.write_form(form_parser.create_form(prefill=(options, args) if options.form else None), command="ec2launch -f")
        sys.exit(1)

    # ... code for processing arguments and options


See the source for toolchain commands ``ec2launch``, ``gadmin``,
``gframe``, ``gncplot``, ``greveal``, and ``ystock`` for more
examples.
