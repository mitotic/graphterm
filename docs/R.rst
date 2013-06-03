*********************************************************************************
Using GraphTerm with R
*********************************************************************************

.. index:: R

To display inline graphics, the following ``R`` packages need to be
installed: ``RCurl``, ``Cairo``, and ``png``.
On Linux, the following additional libraries, or their equivalents,
may need to be installed: ``libcurl4-openssl-dev libcairo2-dev
libxt-dev``
The file `$GTERM_DIR/bin/gtermapi.R
<https://github.com/mitotic/graphterm/blob/master/graphterm/bin/gtermapi.R>`_
includes helper functions for using the GraphTerm API to display
inline graphics.

The notebook mode of GraphTerm will work with ``R``, without any
additional software. GraphTerm can open Markdown files (in a format very similar
to *R-markdown*) as a notebook, and also saves notebooks using the same format.
The file 
`$GTERM_DIR/notebooks/R-histogram.R.md <https://github.com/mitotic/graphterm/blob/master/graphterm/notebooks/R-histogram.R.md>`_ contains
a sample notebook displaying inline graphics.
To open the notebook, click on it in the ``gls`` output, or use the
*notebook/open* menu option after starting ``R``.
