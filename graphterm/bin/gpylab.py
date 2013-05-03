
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

Example 2:
    fig = plt.figure()  # a new figure window
    ax = fig.add_subplot(1, 1, 1)  # specify (nrows, ncols, axnum)
    x = np.linspace(0, 10, 1000)
    y = np.sin(x)

    ax.plot(x, y)
    display(fig)

Notes: Use ioff() to disable interactive mode
       Use show() to update image
       Use show(False) to display new image
       Use display(fig) to display figure
       Use autoprint(True) to re-enable default expression printing behaviour
"""

import gmatplot as gm
gm.setup()    # Sets up gmatplot and patches pylab
from pylab import *
from gmatplot import display
import matplotlib

import sys
Saved_displayhook = sys.displayhook

def gpylab_display_hook(expr):
    if isinstance(expr, matplotlib.figure.Figure):
        display(expr, overwrite=True)

def autoprint(enable=True):
    global Saved_displayhook
    if enable:
        sys.displayhook = Saved_displayhook
    else:
        # Suppress automatic printing of expressions
        Saved_displayhook = sys.displayhook
        sys.displayhook = gpylab_display_hook

autoprint(False)
ion()

if __name__ == "__main__":
    import sys
    import gtermapi
    if len(sys.argv) > 1 and (sys.argv[1].endswith(".gnb.md") or sys.argv[1].endswith(".ipynb.json")):
        # Switch to notebook mode (after prompt is displayed)
        gtermapi.open_notebook(sys.argv[1])
