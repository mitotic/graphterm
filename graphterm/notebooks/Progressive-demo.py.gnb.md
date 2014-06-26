# Progressively fillable notebook demo

This notebook demonstrates the progressively fillable notebook
features of GraphTerm. Code lines ending with comment ``## ANSWER``
will be hidden when this notebook is renamed as
``name-fill.py.gnb.md`` or ``name-share.py.gnb.md`` or
``name-assign.py.gnb.md``. The ``-share`` suffix enables the super
user to share the notebook with other users for viewing and filling
synchronously. The ``-assign`` suffix enables asynchronous sharing. If
a subdirectory SUBMIT is present in the same directory as a shared
notebook file, other users can *submit* a filled shared notebook to
this directory using the *notebook/submit* menu option.

Use *Control-Enter* to execute filled code without saving it. This can
be repeated as needed, until the filled code yields the correct
results. (As a special case, deleting the entire code cell and typing
*Control-Enter* will restore the originally displayed content.)  Use
*Shift-Enter* to save filled code and advance to the next code
cell. The previous code cell will display the correct (ANSWER) code
after this operation, and the filled code cannot be modified. Cells
further down are hidden until your reach them after successive
*Shift-Enter* operations, but if the first line of a Markdown cell
following a page break (*triple-dash*) starts with "#", then the first
line alone is displayed (as a section heading). The
*notebook/page/slide* menu option can be used to enable page view.

To access a shared notebook, other users should start ``gpython`` and
select the *notebook/open* menu option, typing in the name of the
terminal path (``/user/session_name``). For synchronous sharing, other
users can only execute code using *Control-Enter* and cannot advance
to the next code cell until the super user has executed *Shift-Enter*
on the current cell. New users can start accessing the shared notebook
any time and should execute cells sequentially using *Control-Enter*.

To create a progressively fillable notebook that displays *expected
output*, open a regular notebook, append the comment ``## ANSWER`` to
code lines that need to be hidden, execute the code sequentially and
save it with the suffix ``-fill`` (or ``-share`` or ``-assign``)
appended to the base name of the file. This will automatically convert
the code output to *expected output*. (Note: The ``## ANSWER`` suffix
may also be used in the ``expect`` block of fillable notebook to hide
test results.)

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
