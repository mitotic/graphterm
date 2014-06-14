<!--gterm notebook command=python-->
## Leaflet Map

Demo of embedding a pannable, zoomable
[Leaflet map](http://leafletjs.com) within GraphTerm

Requires python modules [mplleaflet](https://github.com/jwass/mplleaflet)
and [mplexporter](https://github.com/mpld3/mplexporter)


```python
import numpy as np
lon = np.arange(240, 360.0, 10.0)
lat = 40 + 10*np.sin(lon/10)
plot(lon,lat)

import mplleaflet
html = mplleaflet.fig_to_html()

import gterm
iframe_html = gterm.iframe_html(html=html, width="80%")
gterm.nb_clear()
gterm.write_pagelet(iframe_html)
```