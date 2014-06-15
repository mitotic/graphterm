<!--gterm notebook command=python-->

# Fillable shared notebook demo

This notebook demonstrates the fillable and shareable notebook
features of GraphTerm.  Code lines ending with comment ``## ANSWER``
will be hidden when this notebook is renamed as
``name-fill.py.gnb.md`` or ``name-share.py.gnb.md``. The latter name
will also allow the super user to share the notebook with other users
for viewing and filling. If a subdirectory SUBMIT is present in the
same directory as a shared notebook file, other users can *submit* a
filled notebook to this directory.

Use *Control-Enter* to execute filled code without saving it. This can
be repeated as needed, until the filled code yields the correct
results. Use *Shift-Enter* to save filled code and advance to the next
code cell. The previous code cell will display the correct (ANSWER)
code after this operation, and the filled code cannot be
modified. Cells further down are hidden until your reach them after
successive *Shift-Enter* operations, but if the first line of a
Markdown cell following a page break (*triple-dash*) starts with "#",
then the first line alone is displayed (as a section heading). The
*notebook/page/slide* menu option can be used to enable page view.

To view a shared notebook, other users should use the *notebook/open*
menu option and type in the name of the terminal path, e.g.,
``/user/session_name`` Other users cannot advance to the next code
cell until the super user has executed *Shift-Enter* on the current
cell. (New users can start viewing the shared notebook any time but
cannot advance beyond the last executed cell.)  For non-interactive
assignments, the super user should execute *Shift-Enter* for all code
cells and leave the terminal in the notebook mode.

To create a fillable notebook that displayes *expected output*, create
a regular notebook and append ``-fill`` (or ``-share``) to name of the
saved file (before the extension). Append the comment ``## ANSWER`` to
lines that need to be hidden.

---

## Part I

Write a function ``abs_add`` that returns the sum of the absolute values of two numbers and another
function ``abs_sub`` that computes the difference of absolute values. Test the two functions.

```python
# Part 1a: Define the function abs_add
def abs_add(a, b):          ## ANSWER
    return abs(a) + abs(b)  ## ANSWER

# Testing function abs_add
print abs_add(3, -4)

# Part 1b: Define the function abs_sub
def abs_sub(a, b):          ## ANSWER
    return abs(a) - abs(b)  ## ANSWER

# Testing function abs_sub
print abs_sub(3, -4)
```

---

## Part II

Write some code to create a simple line plot with a title using the ``pylab`` module.

```python
x = [1, 2, 3, 4]
y = [1, 4, 9, 16]
title = "Plot of y = x-squared"

import pylab
# Part 2: Plotting code
pylab.plot(x, y)     ## ANSWER
pylab.title(title)   ## ANSWER

```
