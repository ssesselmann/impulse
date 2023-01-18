import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import csv
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app

def show_tab3(path):

    data = fn.load_settings(path)
    values = [row[1] for row in data[1:]]
    input_index     = int(values[0])
    input_rate      = int(values[1])
    input_chunk     = int(values[2])
    input_lld       = int(values[3])
    input_tolerance = int(values[4])


    html_tab3 = html.Div([
        
        html.Div(children =html.H3("Hello, I am tab 3", '\n', 
                                                values, '\n',
                                                input_index, '\n',
                                                input_rate, '\n',
                                                input_chunk,'\n'))


        ], style={'background-color':'lightgreen', 'padding':'50px'})

    return html_tab3