import dash
import plotly.graph_objs as go
import numpy as np
import pyaudio
import functions as fn
import shapecatcher as sc
import csv

from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash import Dash, dcc, html, Input, Output, State
from server import app

# ----------- Audio input selection ---------------------------------

def show_tab1():

    fig = {}
    audio_format = pyaudio.paInt16
    p = pyaudio.PyAudio()
    data = fn.load_settings()
    values = [row[1] for row in data[1:]]

    input_index     = values[0]
    input_rate      = values[1]
    input_chunk     = values[2]
    input_lld       = values[3]
    input_tolerance = values[4]
    input_path      = values[5]

    devices = fn.get_device_list()

    device_channels = devices[int(values[0])]['maxInputChannels']



    tab1 = html.Div([ 


        html.Div(id='n_clicks_storage', style={'display': 'none'}),
        html.Button('Refresh Device Index ', id='get_device_button', style={'background-color':'lightgreen','border-radius':'9px', 'height':'30px', 'width':'150px'}),
        html.Div(id='datatable', children=[
            dash_table.DataTable(
                id='container_device_list',
                columns=[{"name": i, "id": i} for i in devices[0].keys()],
                data=devices),
            ],style ={'width':'94%'} ),
#  --------------- User defined settings ------------------------------

        html.H1("Settings & Pulse Shape Control", style={'text-align':'center'}),
        
        html.Div(id='input_text_div', children=[ 
            html.Div(id='input_text', children='Enter Device index'),
            html.Div(dcc.Input(id='input_index', type='number', value = input_index, style={'fontSize':18, 'width':'100px'})),
            html.Div(id='output_index_text', children='', style={'color': 'red'}),
            ], style={'width':'16%','height':'80px','float': 'left','background-color':'lightgray', 'align':'center'}
            ),

        html.Div(id='input_rate_div', children=[
            dcc.Dropdown(
            id="input_rate",
            options=[
                {"label": "48 kHz", "value": "48000"},
                {"label": "96 kHz", "value": "96000"},
                {"label": "192 kHz", "value": "192000"},
                {"label": "384 kHz", "value": "384000"}
            ], 
            value=input_rate,  # pre-selected option
            clearable=False,
            style={'width':'150px'} # style for dropdown
            ),
        html.Div(id="rate_output"),
            ],style={'width':'16%' , 'height':'60px','float': 'left', 'background-color':'lightgray', 'padding':'10px'}
            ),


        html.Div(id='input_chunk_div', children=[ 
            html.Div(id='input_text', children='Chunk Size'),
            html.Div(dcc.Input(id='input_chunk', type='number', value= input_chunk, style={'fontSize':18, 'width':'100px', 'align':'middle'})),
            html.Div(id='output_chunk_text', children='', style={'color': 'red'}),
            ], style={'width':'16%' , 'height':'80px','float': 'left', 'background-color':'lightgray', 'align':'center'}
            ),

        html.Div(id='input_lld_div', children=[ 
            html.Div(id='input_text', children='LLD Threshold (30-100)'),
            html.Div(dcc.Input(id='input_lld', type='number', value = input_lld, style={'fontSize':18, 'width':'100px'})),
            html.Div(id='output_lld_text', children='', style={'color': 'red'}),
            ], style={'width':'16%' , 'height':'80px','float': 'left', 'background-color':'lightgray', 'align':'center'}
            ),

        html.Div(id='input_tolerance_div', children=[ 
            html.Div(id='input_text', children='Shape Tolerance'),
            html.Div(dcc.Input(id='input_tolerance', type='number', value = input_tolerance, style={'fontSize':18, 'width':'100px'})),
            html.Div(id='output_tolerance_text', children='', style={'color': 'red'}),
            ], style={'width':'10%' , 'height':'80px','float': 'left',  'background-color':'lightgray', 'align':'center'}
            ),

        html.Div(id='input_path_div', children=[ 
            html.Div(id='input_text', children='Path to folder'),
            html.Div(dcc.Input(id='input_path', type='text', value = input_path, style={'fontSize':16, 'width':'250px'})),
            html.Div(id='output_path_text', children='', style={'color': 'red'}),
            ], style={'width':'16%' , 'height':'80px','float': 'left', 'background-color':'lightgray', 'align':'center'}
            ),

        html.Div(id='submit_div', children=[ 
            html.Button('Save Settings', 
                id='submit', 
                n_clicks=0, 
                style={'visibility':'hidden'}
                ),
                
                html.Div(id='button', children=[ 
                    html.Div(id='output_div'),
#------------------------------------------------------------------------------------------------------------
                       html.Div(id='graybox', children=[
                        
                            html.Div(id='output_div_2', children=[ 

                                html.Button('Capture Pulse Shape',  id='get_shape', n_clicks=0, style={'background-color':'black','fontSize':18, 'color':'white'}), 

                            ]),
                            ],style={'height':'40px', 'width':'97%', 'background-color':'lightgray', 'float':'left', 'padding':'10px'}
                        ),
#-----------------------------------------------------------------------------------------------------------
                        
                            html.Div(id='showplot',style={'width':'48%', 'float':'left'}), 
                            dcc.Graph(id='plot', figure={}, style={'width':'48%', 'float':'left', 'border': '2px solid black'} ),
                            html.Div(id='textbox', children=[
                            html.H1('Operating Instructions'),
                            html.P('1) Click the green button to get a list of audio devices connected to your computer', style={'text-align':'left'}),
                            html.P('2) Look up the index number of the input device you want to use', style={'text-align':'left'}),
                            html.P('3) Enter your preferred audio settings, your choice is automatically saved in settings.csv', style={'text-align':'left'}),
                            html.P('4) Click the black pulse capture button to start pulse shape training', style={'text-align':'left'}),
                            html.P('This function records the sum avarage pulse shape from 100 pulses and saves it as shape.csv',style={'text-align':'left'}),
                            html.P('This open source software is being developed by Bee Research Pty for use with sound card gamma spectrometers.', style={'text-align':'left'}),
                            html.H3('www.gammaspectacular.com'),
                            ], style={ 'width':'40%', 'height':'380px','background-color':'white', 'float':'left', 'text-align':'center', 'border': '2px solid black', 'padding':'35px'}
                            ),


                ]),
                
    ]) # tab1 ends here

    ], style={'width':'100%' , 'height':'100%','background-color':'lightgray', 'float': 'left', 'padding':'30px'}),
    
    # dcc.Graph(id='plot')

    return tab1

# Callback for getting device index -----------------------
@app.callback(Output('n_clicks_storage', 'children'),
              [Input('get_device_button', 'n_clicks')])

def update_n_clicks(n_clicks):
    return n_clicks

@app.callback(Output('container_device_list',   'data'),
              [Input('n_clicks_storage',        'children')])

def on_button_click(n_clicks):
    if n_clicks is not None:
        initialise = fn.refresh_audio_devices()
        dl = fn.get_device_list()
        return dl

# Callback to save settings ---------------------------

@app.callback(
    Output('output_index_text', 'children'),
    [Input('submit',            'n_clicks')],
    [Input('input_index',       'value'),
    Input('input_rate',         'value'),
    Input('input_chunk',        'value'),
    Input('input_lld',          'value'),
    Input('input_tolerance',    'value'),
    Input('input_path',         'value'),])

def save_settings(n_clicks, value1, value2, value3, value4, value5, value6):

    if n_clicks == 0:
        input_index     = value1
        input_rate      = value2
        input_chunk     = value3
        input_lld       = value4
        input_tolerance = value5
        input_path      = value6


        #path = "../data/settings.csv"
        path = "Sites/github/gs_plot/data/settings.csv"
        data = {'device index':value1, 'sample rate':value2, 'chunk size':value3, 'LLD':value4, 'Shape tolerance':value5, 'File path':value6}

        fn.write_settings_csv(path,data)

        return f'Device ({input_index}) selected'

#-------- Callback to capture and save mean pulse shape ----------


@app.callback(
    [Output('plot',      'figure'),
    Output('showplot',  'figure')],
    [Input('get_shape', 'n_clicks')])

def plot_callback(n_clicks):
    # if n_clicks is None:
        #prevent click on page load
        # raise PreventUpdate
    #if n_clicks > 0:

    if n_clicks is None:

        fig = {'data': [], 'layout': {}}
    else:    

        shape = sc.shapecatcher()
        dots = list(range(len(shape)))
        
        marker = dict(size = 7, color = 'black')
        data = [{'x': dots, 'y': shape, 'type': 'line', 'name': 'SF', 'mode': 'markers+lines', 'marker': marker}]
        layout = {'title': 'Mean Shape Plot'}
        fig = {'data': data, 'layout': layout}
        return fig, fig
        






