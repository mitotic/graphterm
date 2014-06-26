*********************************************************************************
Using GraphTerm with R
*********************************************************************************

.. index:: R

GraphTerm supports basic inline graphics display and the notebook
interface using R. The file `$GTERM_DIR/bin/gterm.R
<https://github.com/mitotic/graphterm/blob/master/graphterm/bin/gterm.R>`_
includes helper functions for using the GraphTerm API to display
inline graphics.  The following ``R`` packages need to be installed:
``RCurl``, ``Cairo``, and ``png``.  On Linux, the following additional
libraries, or their equivalents, may need to be installed:
``libcurl4-openssl-dev libcairo2-dev libxt-dev``. Here's a plotting
example::

    $ R -q
    install.packages(c("RCurl", "Cairo", "png"))  # The first time
    gterm <- paste(Sys.getenv("GTERM_DIR"),"/bin/gterm.R", sep="")
    source(gterm)          # Load GraphTerm API helper functions
    g <- gcairo()          # Initialize Cairo device for GraphTerm output
    x <- rnorm(100,0,1)
    hist(x, col="blue")
    g$frame()              # Display plot as inline image
    hist(x, col="red")
    g$frame(TRUE)          # Overwrite previous plot
    hist(x, col="green")
    g$frame()              # New plot

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-r.png
   :align: center
   :width: 90%
   :figwidth: 85%


The notebook mode of GraphTerm will also work with ``R``, without any
additional software. GraphTerm can open Markdown files (in a format
very similar to *R-markdown*) as a notebook, and also saves notebooks
using the same format. The file ``$GTERM_DIR/notebooks/R-histogram.R.md``
contains a sample notebook displaying inline graphics (see :ref:`r_shot`).  To open the
notebook, click on it in the ``gls`` output, or use the
*notebook/open* menu option after starting ``R``.

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-r-nb.png
   :align: center
   :width: 90%
   :figwidth: 85%

