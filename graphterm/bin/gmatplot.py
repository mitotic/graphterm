#!/usr/bin/env python

"""
gmatplot: Convenience and demo functions for gterm-aware matplotlib usage
(See also gpylab.py)

Usage:

$ python
>>> import gmatplot as gm
>>> gm.setup()    # Sets up gmatplot and patches pylab/pyplot
>>> import pylab

...
pylab.plot(...)

pylab.ion()           # For interactive plotting

pylab.figure(...)     # Clear figure for plotting
pylab.newfig(...)     # Display new figure for plotting (same args as figure())
pylab.resize_newfig() # To resize default figure to fit window

pylab.show()          # To update previously displayed image
pylab.show(False)     # To display as new image

gm.display(fig)       # To display figure
gm.resize_win()       # To resize default image to fit window

Note: If setting up using gm.setup(nopatch=True),
 use gm.show(), gm.figure(), gm.draw() instead of pylab functions

"""

import time
import gterm

pyplot_dict = {}

def setup(nopatch=False, figsize="4.0, 3.0"):
    """Setup gterm-aware matplotlib.
    Note: Must be called before importing matplotlib
    If nopatch, do not patch the draw/figure/show functions of pyplot/pylab.
    """
    import matplotlib
    matplotlib.use("Agg")
    if figsize:
        matplotlib.rcParams["figure.figsize"] = figsize

    import matplotlib.pyplot
    import pylab
    pyplot_dict["new_cell"] = False
    pyplot_dict["new_plot"] = True
    pyplot_dict["drawing"] = False
    pyplot_dict["draw"] = matplotlib.pyplot.draw
    pyplot_dict["figure"] = matplotlib.pyplot.figure
    pyplot_dict["show"] = matplotlib.pyplot.show
    if not nopatch:
        matplotlib.pyplot.draw_if_interactive = draw_if_interactive
        pylab.draw_if_interactive = draw_if_interactive
        matplotlib.pyplot.draw = draw
        matplotlib.pyplot.figure = figure
        matplotlib.pyplot.show = show
        pylab.draw = draw
        pylab.figure = figure
        pylab.show = show

def _gterm_cell_start_hook():
    pyplot_dict["new_cell"] = True
    figure()

def _gterm_cell_end_hook():
    pass

def draw_if_interactive():
    try:
        import matplotlib
        from matplotlib._pylab_helpers import Gcf
        if matplotlib.is_interactive():
            figManager = Gcf.get_active()
            if figManager is not None and figManager.canvas and figManager.canvas.figure:
                retval = display(figManager.canvas.figure, overwrite=(not pyplot_dict["new_plot"]))
                pyplot_dict["new_plot"] = False
                return retval
    except Exception:
        pass

def draw(*args, **kwargs):
    """Wrapper for pyplot.draw
    """
    if not pyplot_dict:
        raise Exception("gmatplot.setup not invoked")
    import matplotlib.pyplot as plt
    retval = display(plt, overwrite=(not pyplot_dict["new_plot"]))
    pyplot_dict["new_plot"] = False
    return retval

def figure(*args, **kwargs):
    """Wrapper for pyplot.figure
    """
    if not pyplot_dict:
        raise Exception("gmatplot.setup not invoked")
    pyplot_dict["new_plot"] = True
    return pyplot_dict["figure"](*args, **kwargs)

def show(*args, **kwargs):
    """Save current figure as a blob and display as block image
    """
    if not pyplot_dict:
        raise Exception("gmatplot.setup not invoked")

    if args:
        overwrite = args[0]
    else:
        overwrite = kwargs.pop("overwrite", not pyplot_dict["new_plot"])
    format = kwargs.pop("format", "png")
    outfile = kwargs.pop("outfile", "")
    title = kwargs.pop("title", "")
    fullscreen = kwargs.pop("fullscreen", False)

    import matplotlib.pyplot as plt
    retval = display(plt, overwrite=overwrite, format=format, outfile=outfile, title=title, fullscreen=fullscreen)
    pyplot_dict["new_plot"] = False
    return retval

def display(fig, overwrite=False, format="png", outfile="", title="", fullscreen=False, max_bytes=25000000):
    """Save figure as a blob and display as block image
    """
    if not pyplot_dict:
        raise Exception("gmatplot.setup not invoked")

    if outfile:
        fig.savefig(outfile, format=format)
        return

    content_type = "application/pdf" if format=="pdf" else "image/"+format
    outbuf = gterm.BlobStringIO(content_type, host=(gterm.Host or "*"), max_bytes=max_bytes)
    pyplot_dict["drawing"] = True
    try:
        fig.savefig(outbuf, format=format)
    finally:
        pyplot_dict["drawing"] = False

    blob_url = outbuf.close()
    ##gterm.display_blockimg_old(blob_url, overwrite=overwrite, alt=title)
    if pyplot_dict["new_cell"]:
        pyplot_dict["new_cell"] = False
        pyplot_dict["new_plot"] = True
    else:
        #gterm.display_blockimg(blob_url, overwrite=overwrite, alt=title, toggle=True)
        gterm.display_blob(gterm.get_blob_id(blob_url), overwrite=overwrite, toggle=True,
                           display="fullscreen" if fullscreen else "block")

def resize_win(dimensions=""):
    """Resize matplotlib default window for terminal"""
    if not pyplot_dict:
        raise Exception("gmatplot.setup not invoked")
    if not dimensions:
        dimensions = gterm.Dimensions
    if not dimensions:
        return

    try:
        char_dims, sep, pixel_dims = dimensions.partition(";")
        if not pixel_dims:
            return
        width, height = pixel_dims.lower().split("x")
        import matplotlib
        dpi = float(matplotlib.rcParams["figure.dpi"])
        figsize = "%.2f, %.2f" % (0.8*float(width)/dpi, 0.7*float(height)/dpi)
        matplotlib.rcParams["figure.figsize"] = figsize
    except Exception, excp:
        raise Exception("Error in resizing: "+str(excp))

def newfig(*args, **kwargs):
    """New figure
    """
    retval = figure(*args, **kwargs)
    print ""  # Hack: This is needed to make it work. Otherwise previous figure is repeated
    show()
    return retval

def resize_newfig(*args, **kwargs):
    """Resize matplotlib default window for terminal (for new figure)
    """
    resize_win()
    return newfig(*args, **kwargs)
    
def main():
    """gterm-aware matplotlib demo"""
    setup()

    import matplotlib.pyplot as plt
    from optparse import OptionParser

    usage = "usage: %prog [--animate]"
    parser = OptionParser(usage=usage)
    parser.add_option("", "--animate",
                      action="store_true", dest="animate", default=False,
                      help="Simple animation demo")

    (options, args) = parser.parse_args()

    fmt = "png"

    if options.animate:
        plt.plot([1,2,3,2,3,1])
        show(overwrite=False, format=fmt, title="Simple animation")

        n = 10
        dx = 5.0/n
        for j in range(1,n):
            time.sleep(0.5)
            plt.plot([1,2,3,2,3,1+j*dx])
            show(overwrite=True, format=fmt)
    else:
        plt.plot([1,2,3,2,3,0])
        show(overwrite=False, format=fmt, title="Simple plot")
        ##time.sleep(2)

if __name__ == "__main__":
    gterm.nbmode()
    main()
