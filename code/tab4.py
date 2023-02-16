
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