# Makefile for GraphTerm documentation
#

PKGNAME       = $(shell basename $(shell dirname $(PWD)))

# You can set these variables from the command line.
SPHINXOPTS   =
SPHINXBUILD  = python ./sphinx-build.py
PAPER        =
BUILDDIR      = ../$(PKGNAME)/www/docs
PAGESDIR      = ../../ghp-$(PKGNAME)

PAPEROPT_a4      = -D latex_paper_size=a4
PAPEROPT_letter  = -D latex_paper_size=letter
ALLSPHINXOPTS    = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) \
                   $(SPHINXOPTS) $(O) .
I18NSPHINXOPTS   = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) $(O) .

.PHONY: help clean cleanpages pages git_pages html dirhtml singlehtml text man pickle json htmlhelp \
	qthelp devhelp epub latex latexpdf changes linkcheck doctest

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  pages      to export standalone HTML files to project pages repository"
	@echo "  git_pages  to export pages and sync local project pages with Github"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files called index.html in directories"
	@echo "  singlehtml to make one big HTML file"
	@echo "  text       to make text files"
	@echo "  man        to make manual pages"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make json files"
	@echo "  htmlhelp   to make HTML files and a HTML help project"
	@echo "  qthelp     to make Qt help files and project"
	@echo "  devhelp    to make Devhelp files and project"
	@echo "  epub       to make an epub file"
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX files and run pdflatex"
	@echo "  texinfo    to make Texinfo files"
	@echo "  info       to make Texinfo files and run them through makeinfo"
	@echo "  gettext    to make PO message catalogs"
	@echo "  changes    to make an overview over all changed/added/deprecated items"
	@echo "  linkcheck  to check all external links for integrity"

clean:
	-rm -rf $(BUILDDIR)/*

cleanpages:
	-rm -rf $(PAGESDIR)/*

pages:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(PAGESDIR)
	@echo
	@echo "Build finished. The HTML pages are in $(PAGESDIR)."

git_pages: pages
	cd $(PAGESDIR) && git add -A && git commit -a -m "Publishing $(PKGNAME) at `date`" && git push origin gh-pages
	@echo
	@echo "Published package $(PKGNAME) at `date`"

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

dirhtml:
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) $(BUILDDIR)/dirhtml
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/dirhtml."

singlehtml:
	$(SPHINXBUILD) -b singlehtml $(ALLSPHINXOPTS) $(BUILDDIR)/singlehtml
	@echo
	@echo "Build finished. The HTML page is in $(BUILDDIR)/singlehtml."

text:
	$(SPHINXBUILD) -b text $(ALLSPHINXOPTS) $(BUILDDIR)/text
	@echo
	@echo "Build finished."

man:
	$(SPHINXBUILD) -b man $(ALLSPHINXOPTS) $(BUILDDIR)/man
	@echo
	@echo "Build finished."

pickle:
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) $(BUILDDIR)/pickle
	@echo
	@echo "Build finished."

json:
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) $(BUILDDIR)/json
	@echo
	@echo "Build finished."

htmlhelp:
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) $(BUILDDIR)/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in $(BUILDDIR)/htmlhelp."

qthelp:
	$(SPHINXBUILD) -b qthelp $(ALLSPHINXOPTS) $(BUILDDIR)/qthelp
	@echo
	@echo "Build finished; now you can run qcollectiongenerator with the" \
	      ".qhcp project file in build/qthelp."
	@echo "# qcollectiongenerator $(BUILDDIR)/qthelp/GraphTerm.qhcp"
	@echo "To view the help collection:"
	@echo "# assistant -collectionFile $(BUILDDIR)/qthelp/GraphTerm.qhc"

devhelp:
	$(SPHINXBUILD) -b devhelp $(ALLSPHINXOPTS) $(BUILDDIR)/devhelp
	@echo
	@echo "Build finished."
	@echo "To view the help file:"
	@echo "# mkdir -p $$HOME/.local/share/devhelp/graphterm"
	@echo "# ln -s $(BUILDDIR)/devhelp $$HOME/.local/share/devhelp/graphterm"
	@echo "# devhelp"

epub:
	$(SPHINXBUILD) -b epub $(ALLSPHINXOPTS) $(BUILDDIR)/epub
	@echo
	@echo "Build finished. The epub file is in $(BUILDDIR)/epub."

pdf:
	$(SPHINXBUILD) -b pdf $(ALLSPHINXOPTS) $(BUILDDIR)/pdf
	@mv $(BUILDDIR)/pdf/Python.pdf $(BUILDDIR)/pdf/GraphTerm.pdf
	@echo
	@echo "Build finished. The pdf file is in $(BUILDDIR)/pdf."

latex:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo
	@echo "Build finished; the LaTeX files are in $(BUILDDIR)/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

latexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through pdflatex..."
	make -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

gettext:
	$(SPHINXBUILD) -b gettext $(I18NSPHINXOPTS) $(BUILDDIR)/locale
	@echo
	@echo "Build finished. The message catalogs are in $(BUILDDIR)/locale."

changes:
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) $(BUILDDIR)/changes
	@echo
	@echo "The overview file is in $(BUILDDIR)/changes."

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) $(BUILDDIR)/doctest

texinfo:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	@echo
	@echo "Build finished. The Texinfo files are in $(BUILDDIR)/texinfo."
	@echo "Run \`make' in that directory to run these through makeinfo" \
	      "(use \`make info' here to do that automatically)."

info:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	@echo "Running Texinfo files through makeinfo..."
	make -C $(BUILDDIR)/texinfo info
	@echo "makeinfo finished; the Info files are in $(BUILDDIR)/texinfo."
