
# coding: utf-8

# Bokeh example
# =============
# This example demonstrates the use of bokeh in the sphinx-nbgallery.
# 
# The example is taken from the bokeh-notebook gallery to demonstrate the use
# bokeh. For the sphinx-nbgallery, you have to do 3 additional modifications
# in the `example_gallery_config` of your `conf.py`:
# 
# 1. You have to set the `insert_bokeh` configuration value because we need
#    additional style sheets and javascript files
# 2. Note, that, since the  `output_notebook` function needs some time, we 
#   recommend to use the `dont_preprocess` configuration value for this 
#   notebook. 
# 3. We cannot estimate a thumbnail figure for a notebook not using matplotlib.
#    So you should provide it using the `thumbnail_figure` metadata key (as it
#    has been done for this notebook)

# In[ ]:


import logging
logging.captureWarnings(True)
logging.getLogger('py.warnings').setLevel(logging.ERROR)


# In[ ]:

from bokeh.models import HoverTool, ColumnDataSource
from bokeh.palettes import Viridis6
from bokeh.plotting import figure, show, output_notebook
from bokeh.sampledata.us_counties import data as counties
from bokeh.sampledata.unemployment import data as unemployment


# In[ ]:

counties = {
    code: county for code, county in counties.items() if county["state"] == "tx"
}

county_xs = [county["lons"] for county in counties.values()]
county_ys = [county["lats"] for county in counties.values()]


# In[ ]:

county_names = [county['name'] for county in counties.values()]
county_rates = [unemployment[county_id] for county_id in counties]
county_colors = [Viridis6[int(rate/3)] for rate in county_rates]

source = ColumnDataSource(data=dict(
    x=county_xs,
    y=county_ys,
    color=county_colors,
    name=county_names,
    rate=county_rates,
))


# In[ ]:

output_notebook()


# In[ ]:

TOOLS="pan,wheel_zoom,box_zoom,reset,hover,save"

p = figure(title="Texas Unemployment 2009", tools=TOOLS,
           x_axis_location=None, y_axis_location=None)
p.grid.grid_line_color = None

p.patches('x', 'y', source=source,
          fill_color='color', fill_alpha=0.7,
          line_color="white", line_width=0.5)

hover = p.select_one(HoverTool)
hover.point_policy = "follow_mouse"
hover.tooltips = [
    ("Name", "@name"),
    ("Unemployment rate)", "@rate%"),
    ("(Long, Lat)", "($x, $y)"),
]


# In[ ]:

show(p)


# In[ ]:




# In[ ]:



