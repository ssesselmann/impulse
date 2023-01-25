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



    html_tab3 = html.Div(id='tab3',children=[
        html.Div(id='tab3_text_div', children=[
            html.H1('The GS-PRO-V5 Spectrometer'),
            html.P('This program operates with a sound card spectrometer, sound card spectrometry was invented in Australia by professor Marek Dolleiser and the first hardware ever made was the Gammaspectacular GS-1100A back in 2010.' ),
            html.P('Since then there has been many improvements to the hardware and today we have an excellent product that works with a wide range of gamma scintillation detectors and geiger counters.'), 
            html.P('More information can be found at:'),
            html.P('https://www.gammaspectacular.com'),
            html.P('This software is Free open source software.'), 
            html.P(),
            html.P('Steven Sesselmann'),
            html.Div(id='add', children=[html.Img(src='assets/gs_pro_v5.png')]),
            ]),

        

        ])

    

    return html_tab3