import dash
import plotly.graph_objs as go
import functions as fn
from dash import html
from dash.dependencies import Input, Output
from server import app

def show_tab3():

    html_tab3 = html.Div(id='tab3',children=[
        html.Div(id='tab3_text_div', children=[
            html.H1('The GS-PRO-V5 Spectrometer'),
            html.P('This program operates with a sound card spectrometer, this technology was invented in Australia by professor Marek Dolleiser' ),
            html.P('and the first hardware ever made was the Gammaspectacular GS-1100A back in 2010.' ),
            html.P('Since then there has been many improvements to the hardware and today we have a highly developed product'), 
            html.P('working works with a wide range of gamma scintillation detectors and geiger counters.'), 
            html.P('More information can be found at:'),
            html.P('https://www.gammaspectacular.com'),
            html.P('This software is Free open source software.'), 
            html.P(),
            html.P('Steven Sesselmann'),
            html.Div(id='add', children=[html.Img(src='assets/gs_pro_v5.png')]),
            ]),

        

        ])
    
    return html_tab3