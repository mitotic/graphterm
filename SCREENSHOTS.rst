GraphTerm Screenshots
*********************************************************************************
.. sectnum::
.. contents::

ls vs. gls
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-ls-gls.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Comparing plain vanilla ``ls`` command and the graphterm-aware ``gls``.
   The icons and the blue filenames are clickable. (The icon display
   is optional, and may be disabled.)

   ..

.. raw:: html

   <hr style="margin-bottom: 3em;">


stars3d theme, with icons enabled
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-stars3d.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing output of the ``cat episode4.txt`` command below the
   output of the ``gls`` command, using the 3D  perspective theme. 
   This is actually a working theme, although it is meant for
   primarily for "show". Scrolling through a large text file using the
   ``vi`` editor in this theme gives a nice *roller coaster* effect!
   (This screenshot was captured with Google Chrome running on
   Mac OS X Lion, which supports hidden scrollbars. On other
   software platforms, the scrollbar will be visible.)

   ..

.. raw:: html

   <hr style="margin-bottom: 3em;">

Graphical weather forecast (using Yahoo Weather API)
=========================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-yweather1.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the screen for the command ``yweather`` to
   illustrate inline HTML form display. Since the location argument
   is omitted, the  form is displayed to enter the location
   name. 

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-yweather2.png
   :align: center
   :width: 90%
   :figwidth: 85%

   The submitted location information is used to generate a new
   command, ``yweather -f  "new york"``, and execute it for inline
   weather display.

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Inline HTML document display
=========================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-giframe1.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the screen for the command ``rs2html README.rst | giframe`` to
   illustrate inline HTML document display. The ``rs2html README.rst``
   command converts a *ReStructured Text* doument to HTML, writing the output
   to ``stdout``. The ``giframe`` command wraps the HTML in an *iframe*
   and displays it inline.

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Inline data visualization (plotting using matplotlib)
=========================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gmatplot1.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the screen for the demo program ``gmatplot.py`` which
   generates ``matplotlib`` plots as PNG files and displays them inline.

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Text editing (emacs)
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-emacs.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the screen for the command ``emacs gtermserver.py`` to
   illustrate backwards compatibility with the traditional terminal interface.

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Graphical code editing using a "cloud" editor
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gvi.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the screen for the command ``gvi gtermserver.py`` to
   illustrate graphical editing using the Ajax.org Cloud9 editor (ACE).

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Collapsed mode
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-collapsed.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the screen when all command output is collapsed. Clicking
   on any of the underlined prompts will display the command output.
   Also note  the *Bottom menubar*, which is enabled by clicking on
   the last prompt. Clicking on *Control* and then any of the prompts
   will cause the corresponding command to be pasted.

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Split scrolling
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-split.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the split-screen scrolling mode, where the command
   line is anchored at the bottom of the screen. Clicking on ``gls``
   output will paste filenames into the command line.

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

On the Raspberry Pi
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-raspberrypi1.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing GraphTerm running on a credit-card sized
   computer, `Raspberry Pi <http://www.raspberrypi.org/faqs>`_,
   remotely  accessed using a laptop. It runs rather slowly, but is usable.

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Web slideshows using `Landslide <https://github.com/adamzap/landslide>`_
=============================================================================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-embedded.png
   :align: center
   :width: 90%
   :figwidth: 85%

   Showing the output of ``glandslide -o graphterm-talk1.md | giframe``
   command, which displays a HTML5-based slideshow using
   `Markdown <http://daringfireball.net/projects/markdown/>`_.
   The displayed slide has an ``iframe`` with another
   GraphTerm session which is also displaying a slideshow...

   ..


.. raw:: html

   <hr style="margin-bottom: 3em;">

Miscellaneous screenshots
==================================================

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-ec2launch1.png
   :align: center
   :width: 90%
   :figwidth: 85%

.. figure:: https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gtweet1.png
   :align: center
   :width: 90%
   :figwidth: 85%

   ..

.. raw:: html

   <hr style="margin-bottom: 3em;">
