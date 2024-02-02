# tab1.py
import plotly.graph_objects as go
import functions as fn
import distortionchecker as dcr
import sqlite3 as sql
import shapecatcher as sc
import os
import logging
import requests as req

from dash import dcc, html
from dash.dependencies import Input, Output
from server import app

logger = logging.getLogger(__name__)

data_directory = os.path.join(os.path.expanduser("~"), "impulse_data")

# ----------- Audio input selection ---------------------------------

def show_tab1():
    
    database = fn.get_path(f'{data_directory}/.data_v2.db')

    conn = sql.connect(database)
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
    shapecatches    = settings[10]
    sample_length   = settings[11]
    peakshift       = settings[28]
    response        = req.get('https://www.gammaspectacular.com/steven/impulse/news.html', verify=False)
    news            = response.text
    pulse_length    = 0
    filepath        = os.path.dirname(__file__)
    shape           = fn.load_shape()

    try:
        adl         = fn.get_device_list()          # audio device list
        sdl         = fn.get_serial_device_list()   # serial device list
        dl          = adl + sdl                     # combined device list
    except:
        pass

    options   = [{'label': name, 'value': index} for name, index in dl]
    options   = [{k: str(v) for k, v in option.items()} for option in options]
    options   = fn.cleanup_serial_options(options)
        
    if device >= 100:
        serial = 'block'
        audio  = 'none'
    else:
        serial = 'none'
        audio  = 'block'

    tab1 = html.Div(id='tab1', children=[
        html.Div(id='firstrow'),
        html.Div(id='news', children=[dcc.Markdown(news)]),
        html.Div(id='sampling_time_output', children=''),
        html.Div(id='heading', children=[html.H1('Device Selection and Settings')]),
        html.Div(id='tab1_settings1', children=[
            
        html.Div(id='selected_device_text', children=''),
        dcc.Dropdown(
            id='device_dropdown',
            options=options,
            value=device,  # pre-selected option
            clearable=False,
        ),
        ]),
        html.Div(id='tab1_settings2', children=[
            html.Div(children='Sample rate'),
            dcc.Dropdown(
                id='sample_rate',
                options=[

                    {'label': '44.1 kHz', 'value': '44100'},
                    {'label': '48 kHz', 'value': '48000'},
                    {'label': '96 kHz', 'value': '96000'},
                    {'label': '192 kHz', 'value': '192000'},
                    {'label': '384 kHz', 'value': '384000'},
                    {'label': 'not used', 'value': 'not used'}
                 ],
                value=sample_rate,  # pre-selected option
                clearable=False,
                style={'display':audio}
                ),
        ],
        style={'display':audio}
        ),

        html.Div(id='tab1_settings3', children=[
            html.Div(children='Sample size', style={'textAlign': 'left'}),
            html.Div(dcc.Dropdown(id='sample_length',
                options=[
                    {'label': '11 dots', 'value': '11'},
                    {'label': '16 dots', 'value': '16'},
                    {'label': '21 dots', 'value': '21'},
                    {'label': '31 dots', 'value': '31'},
                    {'label': '41 dots', 'value': '41'},
                    {'label': '51 dots', 'value': '51'},
                    {'label': '61 dots', 'value': '61'}
                    ],
                value=sample_length,
                clearable=False,
                style={'display':audio}
                )),

            
            ],style={'display':audio}),

        html.Div(id='tab1_settings4', children=[
            html.Div(children='Pulses to sample'),
            html.Div(dcc.Dropdown(
                id='catch',
                options=[
                    {'label': '10', 'value': '10'},
                    {'label': '50', 'value': '50'},
                    {'label': '100', 'value': '100'},
                    {'label': '500', 'value': '500'},
                    {'label': '1000', 'value': '1000'}
                    ],
                value=shapecatches,
                clearable=False,
                style={'display':audio}
                )),

        html.Div(
            children='', 
            style={'color': 'red'}),
            ],style={'display':audio}),

        html.Div(id='tab1_settings5', children=[
            html.Div(children='Buffer Size'),
            html.Div(dcc.Dropdown(id='chunk_size',
                                  options=[
                                      {'label': '516', 'value': '516'},
                                      {'label': '1024', 'value': '1024'},
                                      {'label': '2048', 'value': '2048'},
                                      {'label': '4096', 'value': '4096'}
                                  ],
                                  value=chunk_size,
                                  clearable=False,
                                  style={'display':audio}
                                  )),
            html.Div(id='output_chunk_text', children=''),
        ], style={'display':audio}),

        html.Div(id='n_clicks_storage', ),
        html.Button('Save Settings', id='submit', n_clicks=0, style={'display':'none'}),
        html.Div(children=[
            html.Div(id='button', children=[
                html.Div(id='output_div'),

                # -------------------------------------------

                html.Div(id='canvas', children=[

                    html.Div(id='instruction_div', children=[
                        html.Div(id='instructions', children=[
                            html.H2('Easy step by step setup and run'),
                            html.P('You have selected a GS-MAX serial device',      style={'display': serial}), 
                            html.P('Nothing to do here ... Go to tab 2 -->'  ,      style={'display': serial}),

                            html.P('You have selected an GS-PRO Audio device',      style={'display': audio}),
                            html.P('1) Select preferred sample rate, higher is better', style={'display': audio}),
                            html.P('2) Select sample length - dead time < 200 µs',    style={'display': audio}),
                            html.P('3) Sample up to 1000 pulses for a good mean',      style={'display': audio}),
                            html.P('4) Capture pulse shape (about 3000 for Cs-137)',    style={'display': audio}),
                            html.P('5) Optionally check distortion curve, this will help you set correct tolerance on tab2',    style={'display': audio}),
                            html.P('6) Once pulse shape shows on plot go to tab2',    style={'display': audio}),
                            html.P('Found a bug 🐞 or have a suggestion, email me below'),
                            html.P('Steven Sesselmann'),
                            html.Div(html.A('steven@gammaspectacular.com', href='mailto:steven@gammaspectacular.com')),
                            html.Div(html.A('Gammaspectacular.com', href='https://www.gammaspectacular.com', target='_new')),
                            html.Hr(),
                            html.Div(id='path_text', children=f'Note: {data_directory}'),
                        ]),
                    ]),

                    html.Div(id='pulse_shape_div', children=[
                        html.Div(id='showplot', children=[
                            dcc.Graph(id='plot', figure={'data': [{}], 'layout': {}})]),

                            html.Div('Peak shifter', style= { 'marginLeft':'20px'}),
                            html.Div(dcc.Slider(
                                id  ='peakshifter', 
                                min   = -20 ,
                                max   = 20, 
                                step  = 1, 
                                value = peakshift, 
                                marks = {-20:'-20', -15:'-15', -10:'-10', -5:'-5', 0:'0', 5:'5', 10:'10', 15:'15',20:'20'}
                                ),
                                style = {'width': '85%', 'marginLeft': 'auto', 'marginRight': '0'}
                                ),

                        html.Button('Capture Pulse Shape', id='get_shape_btn', n_clicks=0, style={'backgroundColor':'purple','borderRadius':'6px','color':'white','fontWeight':'bold','marginTop':'10px'}),
                    ], style={  'display':audio }),

                    html.Div(id='distortion_div', children=[
                        html.Div(id='showcurve', children=[
                            dcc.Graph(id='curve', figure={'data': [{}], 'layout': {}}),
                            html.Div('', style= { 'height':'50px'}),
                            html.Button('Get Distortion Curve', id='get_curve_btn', n_clicks=0, style={'backgroundColor':'purple','borderRadius':'6px','color':'white','fontWeight':'bold','marginTop':'10px'}),
                        ]),
                    ], style={'display':audio}),

                ],style={'backgroundColor':'white', 'width':'100%', 'height': '500px', 'float':'left'}),


            ]),
            html.Div(id='footer', children=[
                html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif'),
                html.Div(id="rate_output")]),
        ]),  # tab1 ends here
    ]),
    
    return tab1

# Callback to save settings ---------------------------

@app.callback(
    [Output('selected_device_text'      ,'children'),
    Output('sampling_time_output'       ,'children')],
    [Input('submit'                     ,'n_clicks')],
    [Input('device_dropdown'            ,'value'),
    Input('sample_rate'                 ,'value'),
    Input('chunk_size'                  ,'value'),
    Input('catch'                       ,'value'),
    Input('sample_length'               ,'value'),
    Input('peakshifter'                 ,'value'),
    ])

def save_settings(n_clicks, value1, value2, value3, value4, value5, value6):

    if n_clicks == 0:
        device      = value1
        sample_rate = value2
        chunk_size  = value3
        catch       = value4
        length      = value5
        peakshift   = value6

        database    = fn.get_path(f'{data_directory}/.data_v2.db')
        conn        = sql.connect(database)
        c           = conn.cursor()
        query       = f'''
                    UPDATE settings SET device={device}, 
                    sample_rate={sample_rate},
                    chunk_size={chunk_size}, 
                    shapecatches={catch}, 
                    sample_length={length}, 
                    peakshift={peakshift} 
                    WHERE id=0;'''
        
        c.execute(query)
        conn.commit()

        pulse_length = int(1000000 * int(length)/int(sample_rate))

        warning = ''

        if pulse_length >= 334:
            warning = 'WARNING LONG'

        logger.info(f'Settings saved to database tab1')

        return f'Device: {device} (Refresh)', f'{warning} Dead time ~ {pulse_length} µs'

#-------- Callback to capture and save mean pulse shape ----------

@app.callback(
    [Output('plot'        ,'figure'),
    Output('showplot'         ,'figure')],
    [Input('get_shape_btn'    ,'n_clicks')
    ])

def capture_pulse_shape(n_clicks):

    layout = {
                'title': {
                'text': 'Pulse Shape',
                'font': {'size': 16},
                'x': 0.5,
                'y': 0.9
            },
            'margin': {'l': 40, 'r': 10, 't': 40, 'b': 40},
            'height': 350,
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'xaxis': {
                'showgrid': True,
                'gridcolor': 'lightgray',
                'zeroline': True,
                'zerolinecolor': 'black',
                'zerolinewidth': 1
            },
            'yaxis': {
                'showgrid': True,
                'gridcolor': 'lightgray',
                'zeroline': True,
                'zerolinecolor': 'black',
                'zerolinewidth': 1
            }
        }

    #prevent click on page load
    if n_clicks == 0:
        fig = {'data': [{}], 'layout': layout}
        feedback = ''
    else:   
        shape = sc.shapecatcher()
        dots = list(range(len(shape[0])))

        data = go.Scatter(
            x = dots, 
            y = shape[0], 
            mode = 'lines+markers',  
            marker = {'color': 'black', 'size':4}, 
            line = {'color':'blue', 'width':2},
            showlegend = False)
        
        threshold = go.Scatter(
            x = dots, 
            y = shape[1], 
            mode = 'lines',  
            line = {'color':'red', 'width':1},
            showlegend = False)

        fig = go.Figure(data=[data, threshold], layout=layout)

    return fig, fig

#------- Distortion curve -----------------------------------

@app.callback(
            [Output('curve'         ,'figure'),
            Output('showcurve'      ,'figure')],
            [Input('get_curve_btn'  ,'n_clicks'),
            ])

def distortion_curve(n_clicks):

    layout  = {'title': {'text': 'Distortion curve','font': {'size': 16},'x': 0.5,'y': 0.9}, 'margin':{'l':'40', 'r':'40', 't':'40', 'b':'40'}, 'height': '350'}

    #prevent click on page load
    if n_clicks == 0: 
        fig = {'data': [{}], 'layout': layout}

    else: 
        lines   = dict(size = 2, color = 'blue')
        y       = dcr.distortion_finder()
        x       = list(range(len(y)))
        data    = [{'x': x, 'y': y, 'type': 'line', 'name': 'SF', 'mode': 'lines', 'marker':lines}]
        fig     = {'data': data, 'layout': layout}

    return fig, fig
        