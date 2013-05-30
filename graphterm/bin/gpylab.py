
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
       Use show(False) to display new image (same as show(overwrite=False))
       Use display(fig) to display figure
       Use gtermapi.nbmode(False) to re-enable default expression printing behaviour
"""

try:
    import gmatplot as gm
    gm.setup()    # Sets up gmatplot and patches pylab
    from pylab import *
    import gtermapi
    from gmatplot import display
    import matplotlib

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

    gtermapi.display_hook = _gpylab_display_hook

    ion()

    print >> sys.stderr, "NOTE: Enabled interactive plotting mode, ion()"
    print >> sys.stderr, "      To disable, use ioff()"
except ImportError:
    pass

if __name__ == "__main__":
    gtermapi.nbmode()
    gtermapi.process_args()
