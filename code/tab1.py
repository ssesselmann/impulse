# tab1.py
import plotly.graph_objects as go
import functions as fn
import distortionchecker as dcr
import shapecatcher as sc
import os
import logging
import requests as req
import shproto.dispatcher
import time
import dash_daq as daq
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from server import app
from functions import (
    execute_serial_command, 
    generate_device_settings_table, 
    allowed_command, 
    get_path, 
    save_settings_to_json 
    )
from shapecatcher import sc_info
import global_vars

logger = logging.getLogger(__name__)

with global_vars.write_lock:
    data_directory = global_vars.data_directory

# ----------- Audio input selection ---------------------------------

def show_tab1():

    with global_vars.write_lock:
        filename        = global_vars.filename
        device          = int(global_vars.device)
        sample_rate     = global_vars.sample_rate
        chunk_size      = global_vars.chunk_size
        threshold       = global_vars.threshold
        tolerance       = global_vars.tolerance
        bins            = global_vars.bins
        bin_size        = global_vars.bin_size
        max_counts      = global_vars.max_counts
        shapecatches    = global_vars.shapecatches
        sample_length   = global_vars.sample_length
        peakshift       = global_vars.peakshift
        stereo          = global_vars.stereo
        
    pulse_length    = 0
    filepath        = os.path.dirname(__file__)
    shape_left, shape_right = fn.load_shape()

    logger.info(f'stereo retrieved from settings as {stereo}\n')

    try:
        response = req.get('https://www.gammaspectacular.com/steven/impulse/news.html', verify=False)
        news = response.text
    except:
        news = "No internet connection, version information temporarily unavailable."

    try:
        adl = fn.get_device_list()          # audio device list
        sdl = fn.get_serial_device_list()   # serial device list
        dl = adl + sdl                      # combined device list
    except:
        pass

    options = [{'label': filename, 'value': index} for filename, index in dl]
    options = [{k: str(v) for k, v in option.items()} for option in options]
    options = fn.cleanup_serial_options(options)
        
    if device < 100 and device:        # Sound card devices
        serial = 'none'
        audio = 'block'

    if device >= 100 and device:
        serial = 'block'
        audio = 'none' 

    tab1 = html.Div(id='tab1', children=[
        dcc.Interval(id='interval-component', interval=500, n_intervals=0),
        html.Div(id='news', children=[dcc.Markdown(news)]),
        html.Div(id='sampling_time_output', children='', style={'display': audio}),
        html.Div(id='heading', children=[html.H1('Device Selection and Settings')]),
        html.Div(id='tab1_settings1', children=[
            html.Div(id='selected_device_text', children=''),
            dcc.Dropdown(
                id='device_dropdown',
                options=options,
                value=device,  
                clearable=False,
                className='dropdown',
            ),
        ]),
        html.Div(id='tab1_settings2', children=[
            html.Div(children='Sample rate'),
            dcc.Dropdown(
                id='sample_rate',
                className='dropdown',
                options=[
                    {'label': '44.1 kHz', 'value': '44100'},
                    {'label': '48 kHz', 'value': '48000'},
                    {'label': '96 kHz', 'value': '96000'},
                    {'label': '192 kHz', 'value': '192000'},
                    {'label': '384 kHz', 'value': '384000'},
                    {'label': 'not used', 'value': 'not used'}
                ],
                value=sample_rate,
                clearable=False,
                style={'display': audio}
            ),
        ], style={'display': audio}),
        html.Div(id='tab1_settings3', children=[
            html.Div(children='Sample size', style={'textAlign': 'left'}),
            html.Div(dcc.Dropdown(
                id='sample_length',
                className='dropdown',
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
                style={'display': audio}
            )),
        ], style={'display': audio}),
        html.Div(id='tab1_settings4', children=[
            html.Div(children='Pulses to sample'),
            html.Div(dcc.Dropdown(
                id='catch',
                className='dropdown',
                options=[
                    {'label': '10', 'value': '10'},
                    {'label': '50', 'value': '50'},
                    {'label': '100', 'value': '100'},
                    {'label': '500', 'value': '500'},
                    {'label': '1000', 'value': '1000'}
                ],
                value=shapecatches,
                clearable=False,
                style={'display': audio}
            )),
            html.Div(children='', style={'color': 'red'}),
        ], style={'display': audio}),
        html.Div(id='tab1_settings5', children=[
            html.Div(children='Buffer Size'),
            html.Div(dcc.Dropdown(
                id='chunk_size',
                className='dropdown',
                options=[
                    {'label': '516', 'value': '516'},
                    {'label': '1024', 'value': '1024'},
                    {'label': '2048', 'value': '2048'},
                    {'label': '4096', 'value': '4096'}
                ],
                value=chunk_size,
                clearable=False,
                style={'display': audio}
            )),
            html.Div(id='output_chunk_text', children=''),
        ], style={'display': audio}),
        html.Div(id='n_clicks_storage', ),
        html.Button('Save Settings', id='submit', n_clicks=0, style={'display': 'none'}),
        html.Div(children=[
            html.Div(id='button', children=[
                html.Div(id='output_div'),
                html.Div(id='canvas', children=[
                    html.Div(id='instructions', children=[
                        html.H3('You have selected a GS-MAX serial device'),
                        html.Label('Input commands to device'),
                        html.Div(children=[
                            dcc.Input(id='cmd_input', type='text', value='', style={'marginRight': '10px', 'width': '50%'}),
                            dcc.Input(id='hidden-input', type='text', value=f'{device}', style={'display': 'none'}),
                            html.Button('Submit', id='submit_cmd', n_clicks=0),
                        ]),
                        html.Div(id='command_output', style={'width': '100%', 'marginTop': '20px'}),
                        html.P(''),
                        html.P('Found a bug 🐞 or have a suggestion, email me below'),
                        html.P('Steven Sesselmann'),
                        html.Div(html.A('steven@gammaspectacular.com', href='mailto:steven@gammaspectacular.com')),
                        html.Div(html.A('Gammaspectacular.com', href='https://www.gammaspectacular.com', target='_new')),
                    ], style={'display': serial}),
                    html.Div(id='instruction_div', children=[
                        html.H2('Easy step by step setup and run'),
                        html.P('You have selected an GS-PRO Audio device'),
                        html.P('1) Select preferred sample rate, higher is better'),
                        html.P('2) Select sample length - dead time < 200 µs'),
                        html.P('3) Sample up to 1000 pulses for a good mean'),
                        html.P('4) Capture pulse shape (about 3000 for Cs-137)'),
                        html.P('5) Optionally check distortion curve, this will help you set correct tolerance on tab2'),
                        html.P('6) Once pulse shape shows on plot go to tab2'),
                        html.P('Found a bug 🐞 or have a suggestion, email me below'),
                        html.P('Steven Sesselmann'),
                        html.Div(html.A('steven@gammaspectacular.com', href='mailto:steven@gammaspectacular.com')),
                        html.Div(html.A('Gammaspectacular.com', href='https://www.gammaspectacular.com', target='_new')),
                        html.Hr(),
                        html.Div(id='path_text', children=f'Note: {data_directory}'),
                    ], style={'display': audio, 'width': '100%', 'height': '100%', 'padding': 10}),
                ], style={'width': 400, 'height': '100%', 'backgroundColor': 'lightgray', 'float': 'left', 'padding': 10}),
                html.Div(id='canvas2', children=[
                    html.Div(id='information_upd'),
                ], style={'width': 400, 'backgroundColor': 'lightgray', 'float': 'left', 'marginTop': 20, 'marginLeft': 20, 'display': serial}),
                html.Div(id='pulse_shape_div', children=[
                    html.Div(id='showplot', children=[
                        dcc.Graph(id='plot', figure={'data': [{}], 'layout': {}})
                    ]),
                    html.Div('Peak shifter', style={'marginLeft': '20px'}),
                    html.Div(dcc.Slider(
                        id='peakshifter',
                        min=-20,
                        max=20,
                        step=1,
                        value=peakshift,
                        marks={i: str(i) for i in range(-20, 21, 5)}
                    ), style={'width': '85%', 'marginLeft': 'auto', 'marginRight': '0'}),
                    html.Button('Capture Pulse Shape',
                        id='get_shape_btn',
                        n_clicks=0,
                        className='action_button',
                        style={'marginLeft': '20%'}
                    ),
                    html.Div(id='shapecatcher-feedback',
                        children='',
                        style={'paddingLeft': '70px', 'textAlign': 'center', 'color': 'green', 'height': '20px'}
                    ),
                    html.Div(children=[
                        html.Label('Stereo off/on', style={'paddingRight': '10px'}),
                        daq.BooleanSwitch(id='stereo', on=stereo, color='purple')
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'padding': '5px'}),
                ], style={'display': audio}),
                html.Div(id='distortion_div', children=[
                    html.Div(id='showcurve', children=[
                        dcc.Graph(id='curve', figure={'data': [{}], 'layout': {}}),
                        html.Div('', style={'height': '50px'}),
                        html.Button('Get Distortion Curve',
                            id='get_curve_btn',
                            n_clicks=0,
                            className='action_button',
                            style={'marginLeft': '20%', 'marginTop': '20px'}
                        ),
                    ]),
                ], style={'display': audio}),
            ], style={'backgroundColor': 'white', 'width': '100%', 'height': '600px', 'float': 'left'}),
        ]),
        html.Div(id='footer', children=[
            html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif'),
            html.Div(id="rate_output"),
        ]),
    ])
    
    return tab1

# Callback to save settings ---------------------------

@app.callback(
    [Output('selected_device_text'  , 'children'),
     Output('sampling_time_output'  , 'children'),
     Output('stereo'                , 'on')],
    [Input('submit'                 , 'n_clicks'),
     Input('device_dropdown'        , 'value'),
     Input('sample_rate'            , 'value'),
     Input('chunk_size'             , 'value'),
     Input('catch'                  , 'value'),
     Input('sample_length'          , 'value'),
     Input('peakshifter'            , 'value'),
     Input('stereo'                 , 'on')
     ])
def save_settings(n_clicks, device, sample_rate, chunk_size, catch, sample_length, peakshift, stereo):
    if n_clicks is not None:
        with global_vars.write_lock:
            global_vars.device          = int(device)
            global_vars.sample_rate     = int(sample_rate)
            global_vars.chunk_size      = int(chunk_size)
            global_vars.shapecatches    = int(catch)
            global_vars.sample_length   = int(sample_length)
            global_vars.peakshift       = int(peakshift)
            global_vars.stereo          = bool(stereo)

        save_settings_to_json()

        pulse_length = int(1000000 * int(sample_length) / int(sample_rate))
        warning = 'WARNING LONG' if pulse_length >= 334 else ''

        logger.debug(f'Settings saved to JSON file\n')

        return f'Device: {device} (Refresh)', f'{warning} Dead time ~ {pulse_length} µs', stereo

# Callback to capture and save mean pulse shape ----------

@app.callback(
    [Output('plot', 'figure'),
     Output('showplot', 'figure')],
    [Input('get_shape_btn', 'n_clicks')],
    [State('stereo', 'on')]
)
def capture_pulse_shape(n_clicks, stereo):
    layout = {
        'title': {
            'text': 'Pulse Shape (16 bit)',
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
        },
        'legend': {
            'x': 0.6,
            'y': 0.1,
            'xanchor': 'center',
            'yanchor': 'top',
            'orientation': 'h'
        }
    }

    if n_clicks == 0:
        # Load existing shape data on initial page load
        shape_left, shape_right = fn.load_shape()
    else:
        # Capture a new pulse shape when the button is clicked
        result = sc.shapecatcher()

        if result is None or len(result) < 2:
            shape_left = []
            shape_right = []
        else:
            shape_left, shape_right = result

    dots = list(range(len(shape_left)))

    trace_left = go.Scatter(
        x=dots,
        y=shape_left,
        mode='lines+markers',
        marker={'color': 'blue', 'size': 4},
        line={'color': 'blue', 'width': 2},
        name='Left Channel'
    )

    trace_right = go.Scatter(
        x=dots,
        y=shape_right,
        mode='lines+markers',
        marker={'color': 'red', 'size': 4},
        line={'color': 'red', 'width': 2},
        name='Right Channel'
    )

    fig = go.Figure(data=[trace_left, trace_right] if stereo else [trace_left], layout=layout)
    
    return fig, fig


# Callback for plotting distortion curve ------------------------

@app.callback(
    [Output('curve', 'figure'),
     Output('showcurve', 'figure')],
    [Input('get_curve_btn', 'n_clicks')],
    [State('stereo', 'on')]
)
def distortion_curve(n_clicks, stereo):
    layout = {
        'title': {'text': 'Distortion curve', 'font': {'size': 16}, 'x': 0.5, 'y': 0.9},
        'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
        'height': 350,
        'showlegend': False
    }

    if n_clicks == 0:
        return {'data': [{}], 'layout': layout}, {'data': [{}], 'layout': layout}
    else:
        line_style_left = dict(size=2, color='blue')
        line_style_right = dict(size=2, color='red')

        distortion_list_left, distortion_list_right = dcr.distortion_finder(stereo)

        x_left = list(range(len(distortion_list_left)))
        x_right = list(range(len(distortion_list_right)))

        trace_left = {'x': x_left, 'y': distortion_list_left, 'type': 'line', 'name': 'Left Channel', 'mode': 'lines', 'marker': line_style_left}
        trace_right = {'x': x_right, 'y': distortion_list_right, 'type': 'line', 'name': 'Right Channel', 'mode': 'lines', 'marker': line_style_right}

        fig = {'data': [trace_left, trace_right] if stereo else [trace_left], 'layout': layout}
        return fig, fig

# ------- Send serial device commands -------------------

from dash import no_update

@app.callback(
    [Output('command_output', 'children'),
     Output('information_upd', 'children'),
     Output('cmd_input', 'value')],
    [Input('submit_cmd', 'n_clicks')],
    [State('cmd_input', 'value')]
)
def update_output(n_clicks, cmd):
    if n_clicks is None:
        return no_update, no_update, no_update

    if cmd is None or not isinstance(cmd, str):
        table = generate_device_settings_table()
        return 'No command sent', table, ''

    allowed = allowed_command(cmd)

    if cmd.startswith("+"):
        cmd = cmd[1:]

    if allowed:
        execute_serial_command(cmd)
        time.sleep(0.1)
        table = generate_device_settings_table()
        return f'Command sent: {cmd}', table, ''

    else:
        table = generate_device_settings_table()
        return "!! Command disallowed !!", table, '' 

# Callback for updating shapecatcher feedback ---------
@app.callback(
    Output('shapecatcher-feedback', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_log_output(n_intervals):
    return html.Pre('\n'.join(sc_info[-1:]))  



# -- End of tab1.py ---