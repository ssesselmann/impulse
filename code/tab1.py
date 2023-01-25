import dash
import plotly.graph_objects as go
import pyaudio
import functions as fn
import sqlite3 as sql
import shapecatcher as sc
import os
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app

n_clicks = None

# ----------- Audio input selection ---------------------------------

def show_tab1():

    conn = sql.connect("data.db")
    c = conn.cursor()
    query = "SELECT * FROM settings "
    c.execute(query) 
    settings = c.fetchall()[0]

    name            = settings[1]
    device          = settings[2]             
    sample_rate     = settings[3]
    chunk_size      = settings[4]                        
    threshold       = settings[5]
    tolerance       = settings[6]
    bins            = settings[7]
    bin_size        = settings[8]
    max_counts      = settings[9]
    shapes          = settings[10]
    sample_length   = settings[11]


    filepath = os.path.dirname(__file__)

    devices = fn.get_device_list()

    # device_channels = devices[device]['maxInputChannels']

    shape = fn.load_shape()

    tab1 = html.Div(id='tab1', children=[ 


        html.Div(id='n_clicks_storage', style={'display': 'none'}),

        html.Button('Refresh Device Index ', id='get_device_button'),

        html.Div( children=[
            dash_table.DataTable( id='container_device_list',
                columns=[{"name": i, "id": i} for i in devices[0].keys()],
                data=devices),
            ]),
#  --------------- User defined settings ------------------------------

        html.Div(id='heading', children=[html.H1('Pulse Shape Capture and Settings')]),
        
        html.Div(id='tab1_settings', children=[ 
            html.Div(id='input_text', children='Enter Device index'),
            html.Div(dcc.Input(id='device', type='number', value = device, style={'fontSize':18, 'width':'100px'})),
            html.Div(id='selected_device_text', children='', style={'color': 'red'}),
            ]),

        html.Div(id='tab1_settings',children=[
            html.Div( children='Sample rate'),
            dcc.Dropdown(id="sample_rate",
                options=[
                    {"label": "48 kHz", "value": "48000"},
                    {"label": "96 kHz", "value": "96000"},
                    {"label": "192 kHz", "value": "192000"},
                    {"label": "384 kHz", "value": "384000"}
                ], 
                value=sample_rate,  # pre-selected option
                clearable=False,
                style={'width':'130px'} # style for dropdown
                ),
            ]),


        html.Div(id='tab1_settings', children=[ 
            html.Div( children='Chunk Size'),
            html.Div(dcc.Dropdown(id='chunk_size', 
                options=[
                    {'label': '516', 'value':  '516'},
                    {'label':'1024', 'value': '1024'},
                    {'label':'2048', 'value': '2048'},
                    {'label':'4096', 'value': '4096'}
                    ],
                value= chunk_size, 
                clearable=False,
                style={'fontSize':16, 'width':'130px', 'align':'middle'})),
            html.Div(id='output_chunk_text', children='', style={'color': 'red'}),
            ]),


        html.Div(id='tab1_settings', children=[ 
            html.Div( children='Pulses to sample'),
            html.Div(dcc.Dropdown(id='catch', 
                options=[
                    {'label': '10', 'value':  '10'},
                    {'label': '50', 'value':  '50'},
                    {'label':'100', 'value': '100'},
                    {'label':'500', 'value': '500'},
                    {'label':'1000', 'value': '1000'}
                    ],
                value =shapes ,
                clearable=False, 
                style={'fontSize':16, 'width':'130px'})),
            html.Div( children='', style={'color': 'red'}),
            ]),

            html.Div(id='tab1_settings', children=[ 
            html.Div( children='Sample length'),
            html.Div(dcc.Dropdown(id='sample_length', 
                options=[
                    {'label':'21 dots', 'value': '21'},
                    {'label':'31 dots', 'value': '31'},
                    {'label':'41 dots', 'value': '41'},
                    {'label':'51 dots', 'value': '51'},
                    {'label':'61 dots', 'value': '61'}
                    ],
                value =sample_length ,
                clearable=False, 
                style={'fontSize':16, 'width':'130px'}))
            ]),

            html.Div(id='tab1_settings', children=''),

            html.Div(id='tab1_settings', children=''),

            html.Div(id='tab1_settings', children=''),

            html.Div(id='tab1_settings', children=''),

            html.Div(id='tab1_settings', children=''),

            html.Button('Save Settings', id='submit', n_clicks=0, style={'visibility':'hidden'}),
                
            
            html.Div(children=[ 
                html.Div(id='button', children=[ 
                    html.Div(id='output_div'),
#------------------------------------------------------------------------------------------------------------
                       html.Div(id='ps_button_box', children=[
                                html.Button('Capture Pulse Shape',  id='get_shape', n_clicks=0), 
                            ]),
                    
#-----------------------------------------------------------------------------------------------------------
                            html.Div(id='pulse_shape_div', children=[
                                    html.Div(id='showplot', children=[
                                    dcc.Graph(id='plot', figure={'data': [{}], 'layout': {}})
                                    ]),
                                ]),
                            
                            html.Div(id='instruction_div', children=[ 
                                html.Div(id='instructions', children=[
                                    html.H1('Operating Instructions'),
                                    html.P('1) Click the green button to get a list of audio devices connected to your computer', style={'text-align':'left'}),
                                    html.P('2) Look up the index number of the input device you want to use', style={'text-align':'left'}),
                                    html.P('3) Enter your preferred audio settings, your choice is automatically saved in settings.db', style={'text-align':'left'}),
                                    html.P('4) Click the black pulse capture button to start pulse shape training', style={'text-align':'left'}),
                                    html.P('This function records the sum avarage pulse shape from 100 pulses and saves it as shape.csv',style={'text-align':'left'}),
                                    html.P('This open source software is being developed by Bee Research Pty for use with sound card gamma spectrometers.', style={'text-align':'left'}),
                                    html.H3('www.gammaspectacular.com'),
                                    html.Div(f'Note: Path to (../data/) are relative to {filepath}', style={'color':'red', 'float':'left'}),   

                                    ]), 
                                ]),
                ]),

       
        html.Div(id='footer', children=[
            html.Img(id='footer', src='assets/footer.jpg'),
            html.Div(id="rate_output"),

            ]),

    ]) # tab1 ends here



    ]),

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
        fn.refresh_audio_devices()
        dl = fn.get_device_list()
        return dl

# Callback to save settings ---------------------------

@app.callback(
    Output('selected_device_text'   ,'children'),
    [Input('submit'                 ,'n_clicks')],
    [Input('device'                 ,'value'),
    Input('sample_rate'             ,'value'),
    Input('chunk_size'              ,'value'),
    Input('catch'                   ,'value'),
    Input('sample_length'           ,'value')
    ])

def save_settings(n_clicks, value1, value2, value3, value4, value5):

    if n_clicks == 0:
        device      = value1
        sample_rate = value2
        chunk_size  = value3
        catch       = value4
        length      = value5

        conn = sql.connect("data.db")
        c = conn.cursor()
        query = f"UPDATE settings SET device={device}, sample_rate={sample_rate}, chunk_size={chunk_size}, shapecatches={catch}, sample_length={length} WHERE id=0;"
        c.execute(query)
        conn.commit()

        return f'Device ({device}) selected'

#-------- Callback to capture and save mean pulse shape ----------


@app.callback(
    [Output('plot'      ,'figure'),
    Output('showplot'   ,'figure')],
    [Input('get_shape'  ,'n_clicks')])

def capture_pulse_shape(n_clicks):

    #prevent click on page load
    if n_clicks is None:

        fig = {'data': [{}], 'layout': {}}
        
    else:    

        shape = sc.shapecatcher()

        dots = list(range(len(shape)))

        # print('len shape', len(shape))
        
        marker  = dict(size = 7, color = 'purple')
        data    = [{'x': dots, 'y': shape, 'type': 'line', 'name': 'SF', 'mode': 'markers+lines', 'marker': marker}]
        layout  = {'title': 'Mean Shape Plot'}
        
        
        fig = {'data': data, 'layout': layout}

        return fig, fig
        

