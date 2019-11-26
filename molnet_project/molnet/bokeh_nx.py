import sys

import networkx as nx
import pandas as pd
#import numpy as np
#import pickle
#import matplotlib.pyplot as plt

#from molnet.mnet import Cluster

#from bokeh.plotting import figure
from bokeh.io import show, output_file
#from bokeh.layouts import layout

from bokeh.embed import components
from bokeh.resources import INLINE, CDN

from bokeh.models import ColumnDataSource, Range1d, Plot, Circle, MultiLine, HoverTool, BoxZoomTool, ResetTool, WheelZoomTool, BoxSelectTool, PanTool, TapTool
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
from bokeh.palettes import Spectral6


    
    
def mn_display(edges_df, analysis_id):
    # create networkx object
    G = nx.from_pandas_edgelist(edges_df, source='cluster1', target='cluster2', edge_attr=True)
    
    
    
    # convert node attributes
    node_dict = dict()
    node_dict['index'] = list(G.nodes())
    
    node_attr_keys = [attr_key for node in list(G.nodes(data=True)) for attr_key in node[1].keys()]
    node_attr_keys = list(set(node_attr_keys))
    
    
    for attr_key in node_attr_keys:
        node_dict[attr_key] = [node_attr[attr_key] if attr_key in node_attr.keys() else None
                  for node_key, node_attr in list(G.nodes(data=True))]
    
    
    # convert edge attributes
    edge_dict = dict()
    edge_dict['start'] = [x[0] for x in G.edges(data=True)]
    edge_dict['end'] = [x[1] for x in G.edges(data=True)]
    
    edge_attr_keys = [attr_key for edge in list(G.edges(data=True)) for attr_key in edge[2].keys()]
    edge_attr_keys = list(set(edge_attr_keys))
    
    for attr_key in edge_attr_keys:
        edge_dict[attr_key] = [edge_attr[attr_key] if attr_key in edge_attr.keys() else None
                  for _, _, edge_attr in list(G.edges(data=True))]

    node_source = ColumnDataSource(data=node_dict)
    edge_source = ColumnDataSource(data=edge_dict)
    
                
            
    
    
    TOOLTIPS = [
            ("cluster1", "@start"),
            ("score", "@similarity_score"),
            ("cluster2", "@end")
    ]
    
    
    plot = Plot(x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))
    
    
    plot.add_tools(HoverTool(tooltips=TOOLTIPS), 
                   WheelZoomTool(), 
                   TapTool(), 
                   BoxSelectTool(), 
                   ResetTool(), 
                   PanTool(), 
                   BoxZoomTool())
    
    
    # networkx object >> bokeh
    graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0,0))

    graph_renderer.node_renderer.data_source.data = node_source.data
    graph_renderer.edge_renderer.data_source.data = edge_source.data


    # glyphs for nodes
    graph_renderer.node_renderer.glyph = Circle(size=15, fill_color=Spectral6[0])
    graph_renderer.node_renderer.selection_glyph = Circle(size=15, fill_color=Spectral6[2])
    graph_renderer.node_renderer.hover_glyph = Circle(size=15, fill_color=Spectral6[1])
    
    
    # glyphs for edges
    graph_renderer.edge_renderer.glyph = MultiLine(line_color="#cccccc", line_alpha=0.8, line_width=3)
    graph_renderer.edge_renderer.selection_glyph = MultiLine(line_color=Spectral6[2], line_width=3)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color=Spectral6[1], line_width=5)                                                 
    
    
    graph_renderer.selection_policy = NodesAndLinkedEdges()
    graph_renderer.inspection_policy = EdgesAndLinkedNodes()
    
    plot.renderers.append(graph_renderer)
    
    output_file("output.html", title="Analysis {}".format(analysis_id))
    show(plot)
    
    resources = INLINE.render()
    script, div = components(plot)
    
    return plot, script, div, resources
    
    