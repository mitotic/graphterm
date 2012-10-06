Release Notes
*********************************************************************************
.. contents::


0.33.0 (Sep. 30, 2012)
---------------------------------------------------------------------------------
  - Added references to GraphTerm mailing list/Twitter account
  - Added Troubleshooting FAQ
  - Added sample slideshows using ``glandslide``
  - Implemented ``glandslide``, GraphTerm-aware version of ``landslide``
    slideshow presenter.
  - Factored out ace/ckeditor, to be loaded on demand. This
    significantly speeds up initial load, and allows any editor to be
    easily embedded using the editor API. Also implemented presenter API
    using inter-frame communication.
  - Implemented ``/osh/web/user`` JS console for GraphTerm
  - ``gvi`` can explicitly choose between ace/ckeditor (for WYSIWYG
    HTML editing)
  - Improved ``gls`` column handling
  - Implemented ``gscript`` for saving/running scripted commands
  - Added ``ec2launch`` option to copy and install source tarball

0.32.0 (Sep. 15, 2012)
---------------------------------------------------------------------------------
  - Now works on Raspberry Pi out-of-the-box!
  - Added CKEditor (doubled size of package)
  - Much improved iPad experience (bottom menu on by default; CKEditor for
    ``gvi`` editing; **bold** theme)
  - Updated screenshots
  - Revamped ``ec2launch`` and ``ec2list`` for EC2 cluster management
  - Clicking on image in ``gls`` output now displays image inline
  - Popup help display for forms
  - ``--key_secret`` option for HMAC digest server-host authentication

0.31.0 (Sep. 9, 2012)
---------------------------------------------------------------------------------
  - Updated screenshots and documentation
  - Replaced broken ``gweather`` with ``yweather`` (for inline forecasts)
  - Better popups/alerts
  - Added ``Control A-E-K`` to Bottom menu
  - Improved Unicode output
  - Version checks for API
  - Improved ``ec2launch`` to autostart ``gtermserver`` and install *PyLab*


0.30.9 (Aug 26, 2012):
---------------------------------------------------------------------------------
  - Updated documentation
  - Syntax for ``gtermhost`` command has changed slightly
  - *Action->Export* Environment to use GraphTerm across SSH logins
  - ``gmatplot.py`` to demo inline plotting using matplotlib
  - Wildcard session names for multiplexed stdin and stdout (oshell-only)
  - ``gotrace`` command to use *otrace* with any python program (including those reading from stdin)
  - Clear terminal option
  - ``giframe`` command to display files, URLs and HTML from stdin
  - Transient blob storage for images and inline *matplotlib* output
  - Capture interactive feedback using ``GRAPHTERM_SOCKET``
  - Modified command recall handling
  - Fixed invisible widget overlay bug


0.30.8 (Aug 15, 2012):
---------------------------------------------------------------------------------
  First public release + many quick fixes

