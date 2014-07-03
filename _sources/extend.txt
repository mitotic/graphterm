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

If the text output by the program (excluding the escape sequences)
starts with the left-angle bracket (``<``), it is interpreted as being
an HTML fragment to be displayed within GraphTerm as output of the
command. For example, outputting the following string will display the
text ``Hello World`` in bold face::

  \x1b[?1155;<cookie>h<b>Hello World!</b>\x1b[?1155l

The output HTML fragment may optionally begin with a special
*Graphterm directive* which looks like an HTML comment line::

  \x1b[?1155;<cookie>h<!--gterm nb_clear all=yes-->\x1b[?1155l

The above string, if output by a program, will clear output from all
cells in a notebook. The GraphTerm always begins with string
``<!--gterm`` and ends with ``-->``, like an HTML comment line. The
directive begins with an action (``nb_clear``) and optional arguments
of the form ``name=value``.

The basic actions and optional arguments are:

  ``data blob=...``   (create blob with specified random id from data URI content) 

  ``display_blob blob=... display=block|fullpage|fullwindow overwrite=yes exit_page=yes``   (display blob image) 

  ``pagelet block=overwrite``   (display arbitrary HTML page fragment
  from content)

The ``pagelet`` action allows arbitrary HTML fragments to be displayed
inline. The following python command will display inline HTML::

  print "\x1b[?1155;<cookie>h"+"<!--gterm pagelet-->"+"<b>Hello World!</b>"+"\x1b[?1155l"

The ``data`` and ``display_blob`` actions are unprivileged, i.e., they
can be executed even with a dummy cookie value of 0. This allows
"blobs" to be created from `data URIs
<http://en.wikipedia.org/wiki/Data_URI_scheme>`_ and displayed even
across SSH logins. For example, the following two python ``print``
statements will display an inline image from a data URL::

  print "\x1b[?1155;0h"+"<!--gterm data blob=75543619-->"+"image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="+"\x1b[?1155l"

  print "\x1b[?1155;0h"<!--gterm display_blob blob=75543619-->"+"\x1b[?1155l

The sample program ``hello_world.sh`` in ``$GTERM_DIR/bin`` displays
the above two strings. Executing the program across an SSH login will
still display the red dot.

A displayed inline image can be overwritten. The following two lines
will overwrite the last displayed image with a new image containing a
single white pixel::

  print "\x1b[?1155;0h"+"<!--gterm data blob=84327630-->"+"image/gif;base64,R0lGODlhAQABAIAAAP///wAAACwAAAAAAQABAAACAkQBADs="+"\x1b[?1155l"

  print "\x1b[?1155;0h"<!--gterm display_blob blob=84327630
  overwrite=yes-->"+"\x1b[?1155l


Additional actions and optional arguments are:

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
complex options and data etc.::

  \x1b[?1155;<cookie>h
  {"content_type": "text/html",
   "x_gterm_response": "pagelet"}

  <div>
  Hello World!
  </div>
  \x1b[?1155l

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
  blob_url = gterm.create_blob(content, content_type="image/png")
  gterm.display_blob(gterm.get_blob_id(blob_url), display="block")

See the toolchain programs ``gimage``, ``gframe``, etc. for examples
of this API usage.

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
