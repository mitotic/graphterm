#!/usr/bin/env python

"""
gmatplot: Convenience functions of gterm-aware matplotlib usage
"""

import time
import gtermapi

def setup(patch_show=False, figsize="4.0, 3.0"):
    """Setup gterm-aware matplotlib.
    Note: Must be called before importing matplotlib
    If patch_show, patch the show function of pyplot/pylab.
    """
    import matplotlib
    matplotlib.use("Agg")
    if figsize:
        matplotlib.rcParams["figure.figsize"] = figsize
    if patch_show:
        import matplotlib.pyplot
        import pylab
        matplotlib.pyplot.show = show
        pylab.show = show

def show(overwrite=False, format="png", title=""):
    """Save current figure as a blob and display as block image
    """
    import matplotlib.pyplot as plt
    display(plt, overwrite=overwrite, format=format, title=title)

def display(fig, overwrite=False, format="png", title=""):
    """Save figure as a blob and display as block image
    """
    content_type = "application/pdf" if format=="pdf" else "image/"+format
    outbuf = gtermapi.BlobStringIO(content_type)
    fig.savefig(outbuf, format=format)
    blob_url = outbuf.close()
    ##gtermapi.display_blockimg(blob_url, overwrite=overwrite, alt=title)
    gtermapi.display_blockhtml(blob_url, overwrite=overwrite, alt=title)

def demo():
    """gterm-aware matplotlib demo"""
    setup()

    import matplotlib.pyplot as plt

    fmt = "png" # or "pdf"

    plt.plot([1,2,3,2,3,0])
    show(format=fmt, title="Simple plot")

    time.sleep(2)

    plt.plot([1,2,3,2,3,1])
    show(format=fmt, title="Simple animation")

    n = 20
    dx = 5.0/n
    for j in range(1,n):
        time.sleep(0.5)
        plt.plot([1,2,3,2,3,1+j*dx])
        show(overwrite=True, format=fmt)

if __name__ == "__main__":
    demo()
