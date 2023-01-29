
import dash
import dash_daq as daq
import sys
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app
from flask import request

def show_tab4():

    html_tab4 = html.Div([ 
        html.H1(children='Thanks for using impulse, see you back soon!'),
        html.Button(id='exit-button', children='Click to terminate process'),
        html.P(children='Always exit the program by clicking the red button, this prevents processes running after browser window is closed.'),
        ],style={'textAlign':'center'}),

    return html_tab4

@app.callback(Output(component_id='exit-button', component_property='children'), 
            Input(component_id='exit-button', component_property='n_clicks'
        ))
def prog_exit(n):

    if (n != None): 
        shutdown()
        return 'Program closed'
    else:
        return 'Click to terminate process'

def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

    