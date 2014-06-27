*********************************************************************************
 API for writing GraphTerm-aware programs
*********************************************************************************

.. contents::

.. index:: API, hello_gterm.sh, graphterm-aware commands


A `graphterm-aware program <https://github.com/mitotic/graphterm/tree/master/graphterm/bin>`_ can
be written in any language, much like a
`CGI <http://en.wikipedia.org/wiki/Common_Gateway_Interface>`_ script.
The program `hello_gterm.sh <https://github.com/mitotic/graphterm/blob/master/graphterm/bin/hello_gterm.sh>`_
is a simple example.  See also the programs ``gls``, ``gimage``,
``gframe``, ``gvi``, ``gfeed``, ``yweather``, ``ec2launch`` and
``ec2list`` for examples of GraphTerm API usage. You can use the
``which gls`` command to figure out where these programs are located.
The file ``gterm.py`` contains many helper functions for accessing the
GraphTerm API. See also the `gcowsay
<https://github.com/mitotic/gcowsay>`_ program for an example of a
stand-alone GraphTerm-aware command.

*Note:* This API is poorly documented, primarily because it
is in a state of flux. If you would like to develop a non-trivial
application using this API, please be aware that the syntax may change
without notice.

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
"blobs" to be created from
`<http://en.wikipedia.org/wiki/Data_URI_scheme>_data URIs and displayed even across SSH
logins. For example, the following two python ``print`` statements
will display an inline image from a data URL::

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


Python API module
-----------------------------------------------------------------------

The Python module ``gterm.py`` contains many convenience functions for
accessing the textual GraphTerm API. The following Python code will display
some raw HTML followed by an image::

  import gterm

  gterm.write_html("<b>Hello Wordl!</b>")

  with open("sample.png") as f:
      content = f.read()
  blob_url = gterm.create_blob(content, content_type="image/png")
  gterm.display_blob(gterm.get_blob_id(blob_url), display="block")

See the toolchain programs ``gimage``, ``gframe``, etc. for examples
of this API usage.


.. index:: notebook format

Notebook format
----------------------------------------------------

Although GraphTerm can read and write notebooks in the IPython
(``.ipynb``) format, it natively saves notebooks using basic `Markdown
<http://daringfireball.net/projects/markdown>`_ syntax, with support
for the GitHub-style fenced code extension. The notebook filenames have
the extension ``.py.gnb.md`` for Python, ``.R.gnb.md`` for R and so
on. The Markdown sequential text format has some advantages over the
JSON format used for ``.ipynb`` files:

- Notebooks may be easily viewed using standard Markup rendering
  software (e.g. on GitHub)

- Notebooks can be easily modified using standard text editors,
  moving around blocks of code and markup.

- Notebooks can be split and concatenated at block boundaries, like
  text files

Markup cells are simply saved as Markdown text in the notebook file.
This can include raw HTML, figures, or program statements. Program
statements occurring within a markup cell must be indented by at
least four spaces. The data URIs for all figures are saved at the end
of the file, making it easier to view the notebook cell content.

Code cells are saved as fenced code blocks in the notebook file, e.g.::

    ```python
    print "Hello World"
    ```

Output text resulting from running the code is saved in fenced code
blocks of type ``output``::


    ```output
    Hello
    ```

Figures resulting from code execution are distinguished by the prefix ``output-``
in their name, e.g.::

  ![image][output-fig1-test.py]

Multiple ``output`` text blocks and output figures, separated by blank
lines, are considered as representing the cumulative output from
executing the previous code block. To create a progressively fillable
notebook, ``output`` blocks and figures are converted to ``expect``
blocks and figures.
