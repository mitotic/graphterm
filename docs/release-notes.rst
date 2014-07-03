Release Notes
******************************************************************************************
.. contents::


0.56.1 (July 3, 2014)
---------------------------------------------------------------------------------

 - Toolchain now works both Python2 and Python3; many fixes


0.55.0 (June 26, 2014)
---------------------------------------------------------------------------------

 - Progressively fillable notebooks for scaffolding

 - MathJax implemented for TeX formulas

 - ``gncplot`` for 2-D visualization of netCDF data

 - Login authentication type implemented

 - Tooltips for forms

 - Leaflet zoomable demo

0.54.3 (May 8, 2014)
---------------------------------------------------------------------------------

 - Major docs update

 - Image display from unauthenticated (cookie-less) terminals

 - Introduced shortcut commands: ``gpython`` and ``gipython``

 - Cleaned up inline plotting

 - Cleaned up gterm_setup


0.53.0 (May 5, 2014)
---------------------------------------------------------------------------------

 - Improved remote machine access

 - Implemented gdownload

 - Added colors to terminal

 - Enabled multiuser mode with existing users (user_setup=manual)

 - Renames --auto_users to --user_setup=auto

 - Renamed auth_type=local to auth_type=singleuser


0.52.0 (April 28, 2014)
---------------------------------------------------------------------------------

 - Fixes for user permissions; indentation handling in notebook cells; autosave; killing terminals

0.51.1 (April 22, 2014)
---------------------------------------------------------------------------------

 - Bug fix release


0.51.0 (April 21, 2014)
---------------------------------------------------------------------------------

 - Added support for Google Authentication

 - Added support for dark theme and saving prefs

 - Improved terminal resizing

0.50.1 (April 17, 2014)
---------------------------------------------------------------------------------

 - Fix to better handle blank lines in notebook code cells


0.50.0 (April 15, 2014)
---------------------------------------------------------------------------------

 - Cosmetic changes (notebook CSS margins, font size)


0.49.0 (April 14, 2014)
---------------------------------------------------------------------------------

  - Full implementation of ``multiuser`` authentication type to create
    virtual computer lab, with automatic creation of new users

  - Implemented ``gadmin`` command to monitor and administer multiple
    users

  - Implemented user groups for collaboration

  - Implemented notebook cell modification tracking

  - Improved chat capability, with terminal alert option

  - Implemented ``gnbserver`` command to run public IPython notebook
    servers on a per-user basis

  - Implemented notebook autosave

  - Implemented ``gls --download`` option

  - Tested ``https`` options with self-signed certificate

  - Improved support for iOS and Android touch devices (tablets and
    phones)

  - Introduced ``command`` menu for useful actions

  - Improved browser support (especially Windows browsers)

  - Cleaned up authentication types

  - Improved ``gterm`` command to launch terminals

  - Fixed cross-domain embedding

  - Fixed wildcard access to ``osh`` terminals

  - Improved EC2 instance launching

  - Improved logging

0.40.2 (February 3, 2014)
---------------------------------------------------------------------------------

  - Updated EC2 launching


0.40.1 (June 26, 2013)
---------------------------------------------------------------------------------

  - Fix for XSS vulnerability (Issue#5)

  - Added mypres1.md for reveal.js demo


0.40.0 (June 25, 2013)
---------------------------------------------------------------------------------

  - Implemented config file to specify default options for gtermserver

  - ``auth_type=user`` changed to ``auth_type=multiuser``


0.39.0 (June 21, 2013)
---------------------------------------------------------------------------------

  - Support for auto user creation

  - Support for inline HTML display for pandas.DataFrame objects

  - Support for server and user authentication via the gterm command

  - Added ``ystock`` command

  - Renamed ``auth_code`` option to ``auth_type``

  - Renamed ``gtermapi.py`` to ``gterm.py``


0.38.1 (June 3, 2013)
---------------------------------------------------------------------------------

  - Fix for symlinks being ignored in the egg file

0.38.0 (June 2, 2013)
---------------------------------------------------------------------------------

  - Follow-up release to 0.37.0

  - Mostly bug fixes; menu and documentation updates


0.37.0 (May 29, 2013)
---------------------------------------------------------------------------------

  - Follow-up release to 0.36.0

  - Mostly bug fixes and cleanup of notebook mode

  - *gload* to load new terminal in current window


0.36.0 (May 26, 2013)
---------------------------------------------------------------------------------

  - Follow-up release to 0.35.0

  - Many fixes to notebook mode

  - Now notebooks/graphics work with R

  - Introduced *metro.sh* to demo/test multiple terminals simultaneously

  - Introduced *gsh* to execute commands remotely on any accessible terminal

  - Renamed environment variables GRAPHTERM_* to GTERM_*


0.35.0 (May 20, 2013)
---------------------------------------------------------------------------------

  - New generic notebook mode with code/markdown cell and paging/slide
    options, interoperable with IPython notebook

  - New menu bar that can float or be anchored; with Ctrl-J for
    keyboard shortcuts

  - Improved access control options for session sharing

  - Scrollable pagelets to work with session sharing

  - Improved platform compatibility (Android, IE10)

  - Locale export hack to work across SSH logins

  - Form authentication to disallow CSRF

  - Further streamlined copy/paste to work seamlessly on
    Chrome/Firefix on Mac/Linux

  - New logo and fancier splash screen

  - **Toolchain updates:**

  - Introduced *d3cloud* command for inline word clouds using *d3.js*

  - Renamed *giframe* command to *gframe*, with expanded capabilities
    for creating split frames and embedded terminals.

  - Updated *gls* from bash to Python for opening notebooks etc.

  - Introduced *gjs* to execute Javscript in client browser

  - Introduced *gmenu* for command-line access to the new menu bar

  - Introduced *gprofile* for appending to the user's ``.bash_profile``

  - Introduced *gpylab.py* for the monkey-patched ``pylab`` mode

  - Introduced *gqrcode* for inline display of QR codes

  - Introduced *greveal* command for inline presentations of Markdown
    files using *reveal.js*

  - Example script *gshow.ncl* for inline graphics with NCL

  - Example script *gshow.pro* for inline graphics with IDL

  - Updated *gtermapi.py* for scrollable pagelets and stderr output option

  - Introduced *gupload* for drag-and-drop file upload


0.34.0 (Jan. 6, 2013)
---------------------------------------------------------------------------------

  - Added *gtutor* command,  command line version of the pythontutor.com

  - Added *gsnowflake.py*, inline SVG demo

  - Added *helloworld.sh* demo program

  - Streamlined copy/paste

  - Bug fixes: UTF-8 paste handling (for Japanese etc.)

  - Moved documentation from Google sites (info.mindmeldr.com) to
    Github Pages (code.mindmeldr.com)


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

