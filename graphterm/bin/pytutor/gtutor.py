#!/usr/bin/env python
#

""" gtutor.py: command-line version of OnlinePythonTutor for inline use within GraphTerm (http://code.mindmeldr.com/graphterm)

Modified from the CGI script web_exec.py.
Original version of OPT: pgbovine-OnlinePythonTutor-v-Aug8-for-DeNero-389-gd1cb398.tar

Place this script in the directory containing pg_logger.py and pg_encoder.py (or run it from that directory)

Typical interactive usage:
   gtutor.py [options] example.py | giframe -f

For delayed "tracing", save the command output to a file and load it later using giframe:
   gtutor.py example.py > example_trace.html
   giframe -f example_trace.html
"""

import cgi
import json
import os
import sys

from optparse import OptionParser

try:
  import pg_logger
except ImportError:
    sys.path.append(".")
    try:
      import pg_logger
    except ImportError:
      print >> sys.stderr, "Module pg_logger not found; please cd to directory where it is located"
      sys.exit(1)

# set to true if you want to log queries in DB_FILE 
LOG_QUERIES = False

if LOG_QUERIES:
  import os, datetime, create_log_db, sqlite3

HEADERFMT = """This is a command-line version of the Online Python Tutorial. See <a href="http://pythontutor.com" target="_blank">pythontutor.com</a> for more info.  To exit, click on the red X above.
  <hr>
  For command options, type <code>gtutor -h</code>.<br>
  Note: The <em>Edit code</em> link does not work in the command-line version at this time.<br>
  File: <em>%(filepath)s</em>.
"""

IFRAMEFMT = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">

<head>
  <title>Online Python Tutor embedding demo</title>

<!-- dependencies for pytutor.js -->
<script type="text/javascript" src="%(staticURL)s/js/d3.v2.min.js"></script>
<script type="text/javascript" src="%(staticURL)s/js/jquery-1.6.min.js"></script>
<script type="text/javascript" src="%(staticURL)s/js/jquery.ba-bbq.min.js"></script> <!-- for handling back button and URL hashes -->
<script type="text/javascript" src="%(staticURL)s/js/jquery.jsPlumb-1.3.10-all-min.js "></script> <!-- for rendering SVG connectors -->
<script type="text/javascript" src="%(staticURL)s/js/jquery-ui-1.8.21.custom.min.js"></script> <!-- for sliders and other UI elements -->
<link type="text/css" href="%(staticURL)s/css/ui-lightness/jquery-ui-1.8.21.custom.css" rel="stylesheet" />


<!-- Python Tutor frontend code and styles -->
<script type="text/javascript" src="%(staticURL)s/js/pytutor.js"></script>
<link rel="stylesheet" href="%(staticURL)s/css/pytutor.css"/>


<!-- This JavaScript file contains the demo code - READ IT!!!
     (Include this file AFTER all of its dependencies.)
-->
<script>
var traceOutput=%(traceOutput)s;

// 2. When the HTML document finishes loading, populate the div
//    (traceDiv) with the visualization
//    corresponding to the trace.
$(document).ready(function() {

  // 3. Create a new ExecutionVisualizer object for each visualization.
  //    (See %(staticURL)s/js/pytutor.js for the full specs of ExecutionVisualizer.)
  //
  //    The basic idea is that the parent div name is passed as the first argument,
  //    and the trace object is passed as the second argument.
  //
  //    The third argument contains optional parameters.

  // Note that "embeddedMode: true" makes the visualizer appear more compact on-screen.
  // editCodeBaseURL is the base URL to prepend onto the 'Edit code' link.

  // Render listSumTrace inside of listSumDiv
  var traceVisualizer = new ExecutionVisualizer('traceDiv', traceOutput,
                                                {embeddedMode: %(embeddedMode)s,
                                                 startingInstruction: %(startingInstruction)d,
                                                 jumpToEnd: %(jumpToEnd)s,
                                                 editCodeBaseURL: "%(editCodeBaseURL)s"});

  // The redrawConnectors() method needs to be called whenever
  // HTML elements move around on-screen. This is because the SVG
  // arrows rendered by jsPlumb don't automatically get redrawn
  // in their new positions unless redrawConnectors() is called.

  // Call redrawConnectors() whenever the window is resized,
  // since HTML elements might have moved during a resize.
  $(window).resize(function() {
    traceVisualizer.redrawConnectors();
  });


  // A more subtle point is that when some div in your HTML webpage
  // (such as a visualizer div) expands in height, it will "push down"
  // all divs below it, but the SVG arrows rendered by jsPlumb
  // WILL NOT MOVE. Thus, they will be in the incorrect location,
  // unless you call redrawConnectors(). Here is one jQuery plugin
  // that you can use to detect div height changes:
  //
  // http://benalman.com/projects/jquery-resize-plugin/
  //
  // As a concrete example, drag around the execution slider in
  // "Towers of Hanoi" and notice how the arrows in "Happy Birthday"
  // end up not properly aligned with the other elements.
  //
  // A related trick you can implement is to make a div never shrink
  // in height once it's grown; that way, you can avoid lots of jarring
  // jumps and redraws.
  //
  // Please email me if you want me to add more official support
  // for this behavior.
});
</script>
</head>

<body>

  <!-- This demo shows one visualization, embedded within a div ... -->
%(header)s
  <p>
  <div id="traceDiv"></div>

</body>
</html>
"""

ONLINE_STATIC_URL = "http://pythontutor.com"
OFFLINE_STATIC_URL = "/static/pytutor"

def main():
  usage = "usage: %prog [options] python_file"
  parser = OptionParser(usage=usage)

  parser.add_option("", "--bare", action="store_true", dest="bare", default=False,
                    help="Bare display (for embedding)")

  parser.add_option("", "--end", action="store_true", dest="end", default=False,
                    help="Skip to end")

  parser.add_option("", "--offline", action="store_true", dest="offline", default=False,
                    help="Generate output for offline use")

  parser.add_option("", "--output", action="store_true", dest="output", default=False,
                    help="Show program output")

  parser.add_option("", "--step", dest="step", default=0,
                    help="Starting step (default: 0)")

  (options, args) = parser.parse_args()
  if not args:
    print >> sys.stderr, parser.get_usage()
    sys.exit(1)

  filepath = args[0]

  def cgi_finalizer(input_code, output_trace):
    """Write JSON output for js/pytutor.js as a CGI result."""
    ret = dict(code=input_code, trace=output_trace)
    json_output = json.dumps(ret, indent=None) # use indent=None for most compact repr

    if LOG_QUERIES:
      # just to be paranoid, don't croak the whole program just
      # because there's some error in logging it to the database
      try:
        # log queries into sqlite database.
        # make sure that your web server's account has write permissions
        # in the current directory, for logging to work properly
        con = sqlite3.connect(create_log_db.DB_FILE)
        cur = con.cursor()

        cur.execute("INSERT INTO query_log VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                    (datetime.datetime.now(),
                     os.environ.get("REMOTE_ADDR", "N/A"),
                     os.environ.get("HTTP_USER_AGENT", "N/A"),
                     os.environ.get("HTTP_REFERER", "N/A"),
                     user_script,
                     int(cumulative_mode)))
        con.commit()
        cur.close()
      except Exception as err:
        # this is bad form, but silently fail on error ...
        print(err)

    header = "" if options.bare else HEADERFMT % {"filepath": filepath}
    print IFRAMEFMT % {"traceOutput": json_output,
                       "embeddedMode": "false" if options.output else "true",
                       "startingInstruction": options.step,
                       "jumpToEnd": "true" if options.end else "false",
                       "staticURL": OFFLINE_STATIC_URL if options.offline else ONLINE_STATIC_URL,
                       "editCodeBaseURL": "",
                       "header": header}

  cumulative_mode = False

  if not os.path.exists(filepath) and not os.path.isabs(filepath):
    def_filepath = os.path.normpath(os.path.join(os.path.dirname(__file__), "example-code", filepath))
    if not def_filepath.endswith(".py") and not def_filepath.endswith(".txt"):
      def_filepath += ".txt"
    if os.path.exists(def_filepath):
      filepath = def_filepath
    else:
      print >> sys.stderr, "File %s not found" % filepath
      
  # Process script from file ...
  user_script = open(filepath).read()

  # Ensure that the file compiles
  compile(user_script, filepath, "exec")

  pg_logger.exec_script_str(user_script, cumulative_mode, cgi_finalizer)

if __name__ == "__main__":
    main()
