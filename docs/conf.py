# -*- coding: utf-8 -*-
#
# GraphTerm documentation build configuration file

import re
import sphinx

try:
    import about
except ImportError:
    about = None

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.todo',
              'sphinx.ext.autosummary', 'sphinx.ext.extlinks', 'rst2pdf.pdfbuilder']

master_doc = 'contents'
templates_path = ['_templates']
exclude_patterns = ['_build']

project = 'GraphTerm'
copyright = '2012-2014 R. Saravanan'
version = "0.54.2"
release = version
if about:
    version = about.version
    release = about.version

#show_authors = False

html_theme = 'sphinxdoc'
#modindex_common_prefix = ['sphinx.']
html_static_path = ['_static']
html_sidebars = {'index': ['indexsidebar.html', 'searchbox.html']}
html_additional_pages = {'index': 'index.html'}
html_use_opensearch = 'http://doc.graphterm.com'
# If false, no module index is generated.
html_domain_indices = False

htmlhelp_basename = 'GraphTermdoc'

#epub_cover = ("/_static/mmrpresentation.jpg", "")
epub_theme = 'epub'
epub_basename = 'graphterm'
epub_author = 'R. Saravanan'
epub_publisher = 'http://graphterm.com/'
epub_scheme = 'url'
epub_identifier = epub_publisher
epub_pre_files = [('index.html', 'Welcome')]
epub_exclude_files = ['_static/opensearch.xml', '_static/doctools.js',
    '_static/jquery.js', '_static/searchtools.js', '_static/underscore.js',
    '_static/basic.css', 'search.html']

# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [('contents', 'graphterm.tex', 'GraphTerm Documentation',
                    'R. Saravanan', 'manual')]
latex_elements = {
    'fontpkg': '\\usepackage{palatino}',
}

# The name of an image file (relative to this directory) to place at the top of
# the title page.
latex_logo = '_static/mmrbanner.png'

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = 'footnote'

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True

# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'graphterm', u'GraphTerm Documentation',
     [u'R. Saravanan'], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'graphterm', u'GraphTerm Documentation',
   u'R. Saravanan', 'graphterm', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'


autodoc_member_order = 'groupwise'
todo_include_todos = True
extlinks = {'duref': ('http://docutils.sourceforge.net/docs/ref/rst/'
                      'restructuredtext.html#%s', ''),
            'durole': ('http://docutils.sourceforge.net/docs/ref/rst/'
                       'roles.html#%s', ''),
            'dudir': ('http://docutils.sourceforge.net/docs/ref/rst/'
                      'directives.html#%s', '')}

# We're not using intersphinx right now, but if we did, this would be part of
# the mapping:
intersphinx_mapping = {'python': ('http://docs.python.org/dev', None)}


# -- Extension interface -------------------------------------------------------

from sphinx import addnodes


event_sig_re = re.compile(r'([a-zA-Z-]+)\s*\((.*)\)')

def parse_event(env, sig, signode):
    m = event_sig_re.match(sig)
    if not m:
        signode += addnodes.desc_name(sig, sig)
        return sig
    name, args = m.groups()
    signode += addnodes.desc_name(name, name)
    plist = addnodes.desc_parameterlist()
    for arg in args.split(','):
        arg = arg.strip()
        plist += addnodes.desc_parameter(arg, arg)
    signode += plist
    return name


def setup(app):
    from sphinx.ext.autodoc import cut_lines
    from sphinx.util.docfields import GroupedField
    app.connect('autodoc-process-docstring', cut_lines(4, what=['module']))
    app.add_object_type('confval', 'confval',
                        objname='configuration value',
                        indextemplate='pair: %s; configuration value')
    fdesc = GroupedField('parameter', label='Parameters',
                         names=['param'], can_collapse=True)
    app.add_object_type('event', 'event', 'pair: %s; event', parse_event,
                        doc_field_types=[fdesc])
