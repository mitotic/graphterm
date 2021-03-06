
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
    newfig()
    plot([2,3])
    resize_newfig()
    plot([4, 5])

Example 2:
    import numpy as np
    fig = pylab.figure()  # a new figure window
    ax = fig.add_subplot(1, 1, 1)  # specify (nrows, ncols, axnum)
    x = np.linspace(0, 10, 1000)
    y = np.sin(x)

    ax.plot(x, y)
    display(fig)

Notes: Use figure(...) to clear current figure
       Use newfig(...) to setup new figure (with same arguments as figure())
       Use resize_newfig(...) to setup new resized figure
       Use show() to update image
       Use show(False) to display new image (same as show(overwrite=False))
       Use display(fig) to display figure
       Use resize_win() to resize next figure
       Use ioff() to disable interactive mode
       Use gterm.nbmode(False) to re-enable default expression printing behaviour
"""

import sys

try:
    try:
        import gmatplot as gm
    except ImportError:
        import graphterm.bin.gmatplot as gm

    gm.setup()    # Sets up gmatplot and patches pylab
    from pylab import *

    try:
        import gterm
    except ImportError:
        import graphterm.bin.gterm as gterm

    try:
        from gmatplot import display, newfig, resize_newfig, resize_win, _gterm_cell_start_hook, _gterm_cell_end_hook
    except ImportError:
        from graphterm.bin.gmatplot import display, newfig, resize_newfig, resize_win, _gterm_cell_start_hook, _gterm_cell_end_hook

    import matplotlib
    matplotlib.rcParams.update({'font.size': 8})

    def _gpylab_display_hook(expr):
        if isinstance(expr, matplotlib.figure.Figure):
            display(expr, overwrite=True)
            return None
        obj = expr[0] if isinstance(expr, list) and expr else expr
        if hasattr(obj, "get_figure"):
            fig = getattr(obj, "get_figure")()
            if isinstance(fig, matplotlib.figure.Figure):
                display(fig, overwrite=True)
                return None
        return expr

    gterm.display_hook = _gpylab_display_hook

    ion()

    sys.stderr.write("NOTE: Enabled interactive plotting mode, ion()\n")
    sys.stderr.write("      To disable, use ioff()\n")
except ImportError:
    sys.stderr.write("NOTE: Plotting modules not loaded\n")

if __name__ == "__main__" and sys.flags.interactive:
    try:
        import gterm
    except ImportError:
        import graphterm.bin.gterm as gterm

    gterm.nb_setup()
