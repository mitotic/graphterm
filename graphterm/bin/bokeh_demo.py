#!/usr/bin/env python
#

"""
bokeh_demo: Output Bokeh Lorenz example HTML to stdout for viewing in GraphTerm

Usage: bokeh_demo.py [sigma_value] | gframe -f
"""

import os, sys, tempfile

import numpy as np
from scipy.integrate import odeint
from bokeh.plotting import *

sigma = 10 if len(sys.argv) < 2 else float(sys.argv[1])
rho = 28
beta = 8.0/3
theta = 3 * np.pi / 4

def lorenz(xyz, t):
    x, y, z = xyz
    x_dot = sigma * (y - x)
    y_dot = x * rho - x * z - y
    z_dot = x * y - beta* z
    return [x_dot, y_dot, z_dot]

initial = (-10, -7, 35)
t = np.arange(0, 100, 0.006)

solution = odeint(lorenz, initial, t)

x = solution[:, 0]
y = solution[:, 1]
z = solution[:, 2]
xprime = np.cos(theta) * x - np.sin(theta) * y

colors = ["#C6DBEF", "#9ECAE1", "#6BAED6", "#4292C6", "#2171B5", "#08519C", "#08306B",]

tem_file = tempfile.NamedTemporaryFile(delete=False) if os.getenv("GTERM_COOKIE") or os.getenv("SSH_CLIENT") else None
if tem_file:
    tem_name = tem_file.name
    tem_file.close()
else:
    tem_name = "lorenz.html"

try:

    output_file(tem_name, title="lorenz.py example")

    multi_line(np.array_split(xprime, 7), np.array_split(z, 7),
               line_color=colors, line_alpha=0.8, line_width=1.5,
               tools="pan,wheel_zoom,box_zoom,reset,previewsave", title="lorenz example", name="lorenz_example")

    show(browser="none" if tem_file else None)

    if tem_file:
        # Open temporary file and write to stdout
        with open(tem_name) as f:
            sys.stdout.write(f.read())

finally:
    if tem_file:
        os.remove(tem_name)
