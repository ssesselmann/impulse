
import dash
import dash_daq as daq
import sys
import functions as fn
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app
from flask import request

def show_tab4():

    html_tab4 = html.Div([ 
        html.H1(children='Thanks for using impulse, see you back soon!'),
        html.Button(id='exit-button', children=''),
        html.P(children='Always exit the program by clicking the red button, this prevents processes running after browser window is closed.'),
        html.Div(id='tab3_text_div', children=[
            html.H1('The GS-PRO-V5 Spectrometer'),
            html.P('This program operates with a sound card spectrometer, this technology was invented in Australia by professor Marek Dolleiser' ),
            html.P('and the first hardware ever made was the Gammaspectacular GS-1100A back in 2010.' ),
            html.P('Since then there has been many improvements to the hardware and today we have a highly developed product'), 
            html.P('working with a wide range of gamma scintillation detectors and geiger counters.'), 
            html.P('More information can be found at:'),
            html.P('https://www.gammaspectacular.com'),
            html.P('This software is Free open source software and everyone is invoted to contribute.'), 
            html.P(),
            html.P('Steven Sesselmann'),
            html.Div(id='add', children=[html.Img(src='https://www.gammaspectacular.com/steven/impulse/gs_pro_v5.png')]),]),
        ],style={'textAlign':'center'}),

    return html_tab4

@app.callback(Output('exit-button', 'children'),
              [Input('exit-button', 'n_clicks')])

def shutdown_server(n_clicks):
    if n_clicks is not None:
        fn.shutdown()
        return 'Port Closed'
    else:
        return 'Click to Exit'