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


    filepath = os.path.dirname(__file__)

    devices = fn.get_device_list()

    # device_channels = devices[device]['maxInputChannels']

    shape = fn.load_shape()

    tab1 = html.Div([ 


        html.Div(id='n_clicks_storage', style={'display': 'none'}),
        html.Button('Refresh Device Index ', id='get_device_button', style={'background-color':'lightgreen','border-radius':'9px', 'height':'30px', 'width':'150px'}),
        html.Div( children=[
            dash_table.DataTable( id='container_device_list',
                columns=[{"name": i, "id": i} for i in devices[0].keys()],
                data=devices),
            ],style ={'width':'94%'} ),
#  --------------- User defined settings ------------------------------

        html.H1("Settings & Pulse Shape Control", style={'text-align':'center'}),
        
        html.Div( children=[ 
            html.Div(id='input_text', children='Enter Device index'),
            html.Div(dcc.Input(id='device', type='number', value = device, style={'fontSize':18, 'width':'100px'})),
            html.Div(id='selected_device_text', children='', style={'color': 'red'}),
            ], style={'width':'16%','height':'80px','float': 'left','background-color':'lightgray', 'align':'center'}
            ),

        html.Div(id='sample_rate_div', children=[
            dcc.Dropdown(
            id="sample_rate",
            options=[
                {"label": "48 kHz", "value": "48000"},
                {"label": "96 kHz", "value": "96000"},
                {"label": "192 kHz", "value": "192000"},
                {"label": "384 kHz", "value": "384000"}
            ], 
            value=sample_rate,  # pre-selected option
            clearable=False,
            style={'width':'150px'} # style for dropdown
            ),
        html.Div(id="rate_output"),
            ],style={'width':'16%' , 'height':'60px','float': 'left', 'background-color':'lightgray', 'padding':'10px'}
            ),


        html.Div( children=[ 
            html.Div( children='Chunk Size'),
            html.Div(dcc.Input(id='chunk_size', type='number', value= chunk_size, style={'fontSize':18, 'width':'100px', 'align':'middle'})),
            html.Div(id='output_chunk_text', children='', style={'color': 'red'}),
            ], style={'width':'16%' , 'height':'80px','float': 'left', 'background-color':'lightgray', 'align':'center'}
            ),

        html.Div( children=[ 
            html.Div( children='LLD Threshold (30-100)'),
            html.Div(dcc.Input(id='threshold', type='number', value = threshold, style={'fontSize':18, 'width':'100px'})),
            html.Div(id='output_lld_text', children='', style={'color': 'red'}),
            ], style={'width':'16%' , 'height':'80px','float': 'left', 'background-color':'lightgray', 'align':'center'}
            ),

        html.Div( children=[ 
            html.Div( children='Shape Tolerance'),
            html.Div(dcc.Input(id= 'tolerance', type='number', value = tolerance, style={'fontSize':18, 'width':'100px'})),
            html.Div( children='', style={'color': 'red'}),
            ], style={'width':'10%' , 'height':'80px','float': 'left',  'background-color':'lightgray', 'align':'center'}
            ),

        html.Div( children=[ 
            html.Div( children='Name Field'),
            html.Div(dcc.Input(id='name', type='text', value =name , style={'fontSize':16, 'width':'250px'})),
            html.Div( children='', style={'color': 'red'}),
            ], style={'width':'16%' , 'height':'80px','float': 'left', 'background-color':'lightgray', 'align':'center'}
            ),

        html.Div( children=[ 
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
                            html.Div( children=[
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

        html.Div(f'Note: Path to (../data/) are relative to {filepath}', style={'color':'red', 'float':'left'}),   
                
    ]) # tab1 ends here

    ], style={'width':'100%' , 'height':'100%','background-color':'lightgray', 'float': 'left', 'padding':'30px'}),

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
        print('refresh')
        dl = fn.get_device_list()
        return dl

# Callback to save settings ---------------------------

@app.callback(
    Output('selected_device_text'   ,'children'),
    [Input('submit'                 ,'n_clicks')],
    [Input('device'                 ,'value'),
    Input('sample_rate'             ,'value'),
    Input('chunk_size'              ,'value'),
    Input('threshold'               ,'value'),
    Input( 'tolerance'              ,'value'),
    Input('name'                   ,'value'),])

def save_settings(n_clicks, value1, value2, value3, value4, value5, value6):

    if n_clicks == 0:
        device      = value1
        sample_rate = value2
        chunk_size  = value3
        threshold   = value4
        tolerance   = value5
        name        = str(value6)

        conn = sql.connect("data.db")
        c = conn.cursor()
        query = f"UPDATE settings SET device={device}, sample_rate={sample_rate}, chunk_size={chunk_size}, threshold={threshold}, tolerance={tolerance}, name='{name}' WHERE id=0;"
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
        
        marker  = dict(size = 7, color = 'purple')
        data    = [{'x': dots, 'y': shape, 'type': 'line', 'name': 'SF', 'mode': 'markers+lines', 'marker': marker}]
        layout  = {'title': 'Mean Shape Plot'}
        
        
        fig = {'data': data, 'layout': layout}

        return fig, fig
        

