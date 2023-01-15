import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import csv
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app

def show_tab3():

    html_tab3 = html.Div([
        
        html.Div(id='tab3', children =html.H3("Hello, I am tab 3"))


        ], style={'background-color':'green', 'padding':'50px'})

    return html_tab3