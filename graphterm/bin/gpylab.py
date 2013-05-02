
"""
gpylab: Convenience functions for gterm-aware pylab usage
(See also gmatplot.py)

Usage:

$ python -i gpylab.py
>>> ion()
  OR
$ ipython -i gpylab.py
>>> ion()

Example: 
    figure()
    plot([1,3])
    plot([2,4])
    plot([2,3])
    show(False)

Note: If not using ion(),
     use show() to update image
     and show(False) to display new image
"""

import gmatplot as gm
gm.setup()    # Sets up gmatplot and patches pylab
from pylab import *

import sys
Saved_displayhook = sys.displayhook

def autoprint(enable=True):
    global Saved_displayhook
    if enable:
        sys.displayhook = Saved_displayhook
    else:
        # Suppress automatic printing of expressions
        Saved_displayhook = sys.displayhook
        sys.displayhook = lambda x: None

autoprint(False)

if __name__ == "__main__":
    import sys
    import gtermapi
    if len(sys.argv) > 1 and (sys.argv[1].endswith(".gnb.md") or sys.argv[1].endswith(".ipynb.json")):
        # Switch to notebook mode (after prompt is displayed)
        gtermapi.open_notebook(sys.argv[1])
