Reimagining the command line in the Tablet Age
===============================================

<p>&nbsp;</p>
<p>&nbsp;</p>

R. Saravanan

Texas A&M University

**sarava@mitotic.org**

Derived from talks give at:

- *Texas Linux Festival, San Antonio, August 4, 2012*
- *PyTexas, College Station, September 16, 2012*

---

**A GUI gives you sentences you can say to express yourself.**

**A command line interface gives you words.**

*Anonymous*


---
Advantages of the CLI
==================================

- More powerful and flexible than the GUI
    - Not limited to actions that can be fitted on the screen
    - Pipe output of one command to another
        - i.e., form your own sentences using words!
    - Wild-carding, command completion, history recall

- Efficient use of screen real-estate
    - Easy to use on small screens and remotely
      (Mobile phones tend to use a menu-driven text UI, although not a CLI)

- Self-documenting
    - Useful for scripting and automation, especially on the server-side


---
Disadvantages of the Command-Line Interface (CLI)
======================================================
<p>&nbsp;</p>

- “Newbies” find a blank terminal screen confusing
    - Steep learning curve (need to learn basic commands first)
    - Abbreviated commands (efficient, but cryptic!)
    - Command have to be typed precisely (unlike natural language)
    - Poor feedback on the results of commands; difficult to undo
    - A GUI with good icons is more intuitive
        - Relies upon recognition rather than recall

- Looks dull and archaic (does not use rich monitor display)
    - Sometimes a picture is worth a thousand words

- Does not use the analog input capabilities of the mouse

---

XMLTerm (Mozilla; ca. 2000)
=========================================================

<img width="50%" height="50%" src="https://dl.dropbox.com/u/72208800/code/images/xmlterm1.jpeg">


---

AjaxTerm (Python+HTML; ca. 2006)
=========================================================

<img width="70%" height="70%" src="https://dl.dropbox.com/u/72208800/code/images/ajaxterm.png">


---

TermKit (Webkit; 2011)
=========================================================

<img width="80%" height="80%" src="https://dl.dropbox.com/u/72208800/code/images/termkit.png">


---

Terminal multiplexers
==================================================================

- GNU Screen
- tmux
- Byobu

---

GraphTerm
============

**A Graphical Terminal Interface**

- Aims to seamlessly blend the CLI and the GUI
- Fully backwards-compatible terminal emulator for xterm. 
    - Use it just like a regular terminal interface, accessing additional graphical features only as needed

- Builds upon two earlier projects, XMLTerm and AjaxTerm
- Alpha quality (dogfood status for the past 7 weeks!)

- Project Page
  **http://code.mindmeldr.com/graphterm**

- Source code (BSD License)
  **https://github.com/mitotic/graphterm**


---
GraphTerm Architecture
=======================

<img width="85%" height="85%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-architecture.png">


---

GraphTerm Implementation
=======================================================================
- Server: ~4500 lines of python
    - Tornado webserver, code from AjaxTerm
    - Websocket (2-way HTTP) connections between browser and server

- Client: ~2500 lines of HTML+JS+CSS
    - jQuery, AJAX editor (ACE)

- Adds a new xterm “escape” sequence to switch to a graphical screen mode to display HTML fragments (“pagelets”)
    - GraphTerm-aware programs can be written in any language: gls, gvi, …

- Browser connects to GraphTerm server using websockets
    - Host computers where the terminal session runs also connect to the same server (on a different port)

---

Installing and running GraphTerm
======================================================================

- Install
    - **sudo easy_install graphterm**
    - **sudo gterm_setup**
- Start server
    - **gtermserver –auth_code=none**
- Open terminal in browser (to connect to localhost)
    - **http://localhost:8900**
    - Terminal sessions have URLs of the form:
        - **http://localhost:8900/&lt;hostname&gt;/tty1**
        - **http://localhost:8900/*/tty1** (wildcard)
    - First user owns the terminal session; others can watch/steal it
- Connect additional hosts to server
    - **gtermhost --server_addr=domain &lt;hostname&gt;**

---

GraphTerm Features
================================================================

- Backwards compatible with CLI, plus incremental feature set
- Clickable (hyperlinked) text for filenames and commands
    - *Adaptive* paste behavior (depending upon the current command line)
- Optional icons for file listings etc.
- Platform-independent client (HTML+Javascript)
    - Themable using CSS
- Pure python server (should work on any Unix-ish system)
- Touch-friendly
    - Translate clicks, taps, and drops into textual commands
- Cloud and collaboration-friendly
    - Single (tabbed) browser window to connect to multiple hosts
    - Drag and drop to copy files between different hosts
    - **Screen sharing**: A terminal session can be shared by multiple users


---
GraphTerm can be embedded in a slideshow within GraphTerm
==========================================================

<p>&nbsp;</p>
<p>&nbsp;</p>

<iframe src="/local/slide/steal" width="90%" height="320"></iframe>

---

ls vs. gls
=========================================================

<img width="80%" height="80%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-ls-gls.png">


---

Checking the weather using Yahoo Weather API
=========================================================

<img width="80%" height="80%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-yweather2.png">


---

Collapse command output
=========================================================

<img width="80%" height="80%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-collapsed.png">


---

CSS-themable (3D perspective)
=========================================================

<img width="80%" height="80%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-stars3d.png">


---

Graphical editing in the “cloud” using gvi
=========================================================

<img width="80%" height="80%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-gvi.png">


---

Split-screen scrolling
=========================================================

<img width="80%" height="80%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-split.png">


---

Emacs in the browser
=========================================================

<img width="80%" height="80%" src="https://github.com/mitotic/graphterm/raw/master/doc-images/gt-screen-emacs.png">


---

Potential Applications for GraphTerm
==========================================

- A more fun (and powerful) replacement for the terminal
- A replacement for screen/tmux (detachable terminal)
- Manage a collection of computers using the browser
    - Wildcard remote access
    - Audit history of all commands
    - Debug Python programs using otrace
- For collaboration with other developers
    - Screen sharing and screen stealing
- For demonstrating or teaching CLI-based software
    - Create a virtual computer lab using the cloud
    - Receive live feedback from audience


---

The End
==========================

.qr: 450|https://github.com/mitotic/graphterm

