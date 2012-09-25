#!/usr/bin/env python

import os, sys
from setuptools import setup
from setuptools.command.install import install as _install

import graphterm.about

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
      entry_points={"console_scripts":["gterm = graphterm.bin.gterm:main",
                                       "gtermserver = graphterm.gtermserver:main",
                                       "gtermhost = graphterm.gtermhost:main",
                                       "gterm_setup = graphterm.gterm_setup:main",
                                       "gotrace = graphterm.gotrace:main",
                                       "glandslide = graphterm.bin.landslide.main:main",
                                       ]},
      install_requires=requires,
      include_package_data=True,
      version=graphterm.about.version,
      description=graphterm.about.description,
      url=graphterm.about.url,
      author="Ramalingam Saravanan",
      author_email="sarava@mindmeldr.com",
      license="BSD License",
      keywords=["command line interface", "console", "multiplexer", "remote desktop",
                "terminal", "terminal emulator", "xterm"],
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
