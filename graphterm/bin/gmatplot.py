#!/usr/bin/env python

"""
gmatplot: Convenience functions of gterm-aware matplotlib usage
"""

import time
import gtermapi

def display_blockimg(url, overwrite=False):
    """Display block image in a sequence.
    New image display causes previous images to be hidden.
    Display of hidden images can be toggled by clicking.
    """
    IMGFORMAT = '<span class="gterm-blockseqlink"><em>&lt;image&gt;</em></span><img class="gterm-blockimg gterm-blockseqlink" src="%s"></img><br>'
    add_headers={"classes": "gterm-blockseq"}
    if overwrite:
        add_headers["block"] = "overwrite"
    gtermapi.write_html(IMGFORMAT % url, add_headers=add_headers)

def gplot_setup():
    import matplotlib
    matplotlib.use("Agg")

def gplot_savefig(format="png", overwrite=False):
    """Save figure as a blob and display as block image
    """
    import matplotlib.pyplot as plt

    content_type = "application/pdf" if format=="pdf" else "image/"+format
    outbuf = gtermapi.BlobStringIO(content_type)
    plt.savefig(outbuf, format=format)
    blob_url = outbuf.close()
    display_blockimg(blob_url, overwrite=overwrite)
    
def demo():
    """gterm-aware matplotlib demo"""
    gplot_setup()

    import matplotlib.pyplot as plt

    fmt = "png" # or "pdf"

    plt.plot([1,2,3,2,3,0])
    gplot_savefig(format=fmt)

    time.sleep(2)

    plt.plot([1,2,3,2,3,1])
    gplot_savefig(format=fmt)

    n = 20
    dx = 5.0/n
    for j in range(1,n):
        time.sleep(0.5)
        plt.plot([1,2,3,2,3,1+j*dx])
        gplot_savefig(format=fmt, overwrite=True)

if __name__ == "__main__":
    demo()
