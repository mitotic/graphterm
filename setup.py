#!/usr/bin/env python

import os, sys
from setuptools import setup
from setuptools.command.install import install as _install

class install(_install):
    def run(self):
        _install.run(self)
        dirname = os.getcwd()
        try:
             try:
                  sys.path.remove(dirname)
             except Exception:
                  dirname = None
             import graphterm.gterm_setup
             graphterm.gterm_setup.main()
        except Exception, excp:
             print >> sys.stderr, "Failed to configure executables", excp
        finally:
             if dirname:
                  sys.path.insert(0, dirname)
        
requires = ["tornado"]

setup(name="graphterm",
      cmdclass={'install': install},
      packages=["graphterm"],
            entry_points={"console_scripts":["gterm = graphterm.gterm:main",
                                             "gtermserver = graphterm.gtermserver:main",
                                             "gtermhost = graphterm.gtermhost:main",
                                             "gterm_setup = graphterm.gterm_setup:main"]},
      install_requires=requires,
      include_package_data=True,
      version="0.30.2",
      description="GraphTerm: A Graphical Terminal Interface",
      author="Ramalingam Saravanan",
      author_email="sarava@sarava.net",
      url="http://info.mindmeldr.com/code/graphterm",
      download_url="https://github.com/mitotic/graphterm/tags",
      license="BSD License",
      keywords=["console", "screen", "shell", "terminal", "terminal emulator", "vt100", "xterm"], 
      classifiers=[
      "Development Status :: 3 - Alpha",
      "Environment :: Console",
      "Intended Audience :: Developers",
      "Intended Audience :: End Users/Desktop",
      "Intended Audience :: Information Technology",
      "Intended Audience :: System Administrators",
      "License :: OSI Approved :: BSD License",
      "Operating System :: OS Independent",
      "Programming Language :: Python",
      "Topic :: System :: Shells",
      "Topic :: Terminals :: Terminal Emulators/X Terminals",
      "Topic :: Utilities",
      ],
      long_description="""\
GraphTerm: A Graphical Terminal Interface
---------------------------------------------------------------------------

*GraphTerm* is graphical command line interface, combining features
from XMLTerm and AjaxTerm.
      """
     )
