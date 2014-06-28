.. _format:

*********************************************************************************
 Markdown notebook format
*********************************************************************************

.. contents::

.. index:: notebook format, markdown


Although GraphTerm can read and write notebooks in the IPython
(``.ipynb``) format, it natively saves notebooks using basic `Markdown
<http://daringfireball.net/projects/markdown>`_ syntax, with support
for the GitHub-style `fenced code extension
<https://help.github.com/articles/github-flavored-markdown>`_. The
notebook filenames have the extension ``.py.gnb.md`` for Python,
``.R.gnb.md`` for R and so on. The Markdown sequential text format has
some advantages over the JSON format used for ``.ipynb`` files:

- Notebooks may be easily viewed using standard Markup rendering
  software and will automatically render on GitHub
  (`example <https://github.com/mitotic/graphterm/blob/master/graphterm/notebooks/Progressive-demo.py.gnb.md>`_).

- Notebooks can be easily modified using standard text editors,
  moving around blocks of code and markup.

- Notebooks can be split and concatenated at block boundaries, like
  text files (e.g. ``cat a.py.gnb.md b.py.gnb.md > c.py.gnb.md``)

Markup cells are simply saved as Markdown text in the notebook file.
This can include raw HTML, figures, or program statements. Triple
dashes (``---``) can be used as page breaks to denote section/slide
boundaries. Program statements occurring within a markup cell must be
indented by at least four spaces. The data URIs for all figures are
saved at the end of the file, making it easier to view the notebook
cell content.

Code cells are saved as fenced code blocks in the notebook file, e.g.::

    ```python
    print "Hello World"
    ```

Output text resulting from running the code is saved in fenced code
blocks of type ``output``::


    ```output
    Hello
    ```

Figures resulting from code execution are distinguished by the prefix ``output-``
in their name, e.g.::

  ![image][output-fig1-test.py]

Multiple ``output`` text blocks and output figures, separated by blank
lines, are considered as representing the cumulative output from
executing the previous code block. To create a progressively fillable
notebook, ``output`` blocks and figures are converted to ``expect``
blocks and figures.
