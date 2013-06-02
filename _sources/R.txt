*********************************************************************************
Using GraphTerm with R
*********************************************************************************

.. index:: R

The notebook mode of GraphTerm will work with ``R``, without any
additional software. GraphTerm can open Markdown files (in a format very similar
to *R-markdown*)
as a notebook, and also saves notebooks using the same format.
To display inline graphics, the following ``R`` packages need to be
installed: ``RCurl``, ``Cairo``, and ``png``.
(On Linux, the following additional libraries, or their equivalents,
may need to be installed: ``libcurl4-openssl-dev libcairo2-dev
libxt-dev``)

The file `$GTERM_DIR/bin/gtermapi.R
<https://github.com/mitotic/graphterm/blob/master/graphterm/bin/gtermapi.R>`_
includes convenience functions for using the GraphTerm API to display
inline graphics.
The R-markdown file 
`$GTERM_DIR/notebooks/R-histogram.R.md <https://github.com/mitotic/graphterm/blob/master/graphterm/notebooks/R-histogram.R.md>`_ contains
a sample notebook that can be opened by clicking on it in the ``gls`` output.
