import gmatplot as gm
gm.setup()    # Sets up gmatplot and patches pylab
from pylab import *

import sys
Saved_displayhook = sys.displayhook

def autoprint(enable=True):
    global Saved_displayhook
    if enable:
        sys.displayhook = Saved_displayhook
    else:
        # Suppress automatic printing of expressions
        Saved_displayhook = sys.displayhook
        sys.displayhook = lambda x: None

autoprint(False)
