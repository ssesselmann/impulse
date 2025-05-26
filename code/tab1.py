# tab1.py
import plotly.graph_objects as go
import functions as fn
import distortionchecker as dcr
import shapecatcher as sc
import os
import dash
import threading
import queue
import logging
import requests as req
import time
import dash_daq as daq
import global_vars
import dash_bootstrap_components as dbc
import max_tempcal

from global_vars import tempcal_cancelled, data_directory
from max_tempcal import run_temperature_calibration
from dash import dcc, html, dash_table, no_update, ctx
from dash.dependencies import Input, Output, State
from server import app
from functions import (
    generate_device_settings_table, 
    allowed_command, 
    save_settings_to_json,
    start_max_pulse_check,
    stop_max_pulse_check,
    )
from shapecatcher import sc_info
from shproto.dispatcher import process_03, serial_number

with global_vars.write_lock:
    data_directory = global_vars.data_directory

logger = logging.getLogger(__name__)

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
        theme           = global_vars.theme

    device_str          = str(device)
    sample_rate_str     = str(sample_rate)
    chunk_size_str      = str(chunk_size)
    sample_length_str   = str(sample_length)
    shapecatches_str    = str(shapecatches)

    pulse_length        = 0
    filepath            = os.path.dirname(__file__)
    shape_left, shape_right = fn.load_shape()
    button_label        = ""

    logger.info(f'Tab1 stereo = {stereo}\n')

    # Generate audio and serial device lists
    try:
        adl = fn.get_device_list()  
        sdl = fn.get_serial_device_list()   
        dl = adl + sdl   
        options = [{'label': filename, 'value': index} for filename, index in dl]
        options = [{k: str(v) for k, v in option.items()} for option in options]
        options = fn.cleanup_serial_options(options)   

        valid_devices    = [option['value'] for option in options]
        default_device   = device_str if device_str in valid_devices else valid_devices[0] if valid_devices else None     
    except:
        logger.error(f"tab1 - Invalid device value: {device}")
        pass

    # Default styles and interval states
    audio_int = True
    serial_int = True
    audio_style = {'display': 'none'}
    serial_style = {'display': 'none'}

    if int(device) < 100:  # Audio device
        audio_int = False
        audio_style = {'display': 'block'}
    else:  # Serial device
        serial_int = False
        serial_style = {'display': 'block'}

    if theme == 'dark-theme':
        paper_bgcolor = 'black'
        plot_bgcolor  = 'black'
    else:
        paper_bgcolor = 'white'
        plot_bgcolor  = 'white'         

# -------- HTML ------ HTML ------ HTML ------ HTML ------ HTML ------ HTML ------ HTML ---

    tab1 = html.Div(id='tab1', children=[

        html.Div(id='tab1-frame', children=[

            dcc.Interval(id='update-interval'   , interval=1000, n_intervals=0, disabled=serial_int),
            dcc.Interval(id='interval-component', interval=1000, n_intervals=0, disabled=audio_int),
            dcc.Interval(id='log-interval', interval=2000, n_intervals=0, disabled=serial_int),

            dcc.Input(id='theme', type='text', value=f'{theme}', style={'display': 'none'}),

            html.Div(id='tab1-header', children=[
                # news
                html.Div(id='tab1-heading-left', className='tab1-header-thirds', children=[
                    html.A("Latest Release", href="https://github.com/ssesselmann/impulse/releases", target="new"),
                    html.Div(id='selected_device_text', children=''),
                ]), # end news

                html.Div(id='tab1-heading-center', className='tab1-header-thirds', children=[html.H1('Device Selection and Settings')]),
                html.Div(id='tab1-heading-right', className='tab1-header-thirds', children=[""]),

                html.Div(id='sampling_time_output', className='tab1-header-thirds', children='', style=audio_style),

                ]), # end header

            html.Div(id='tab1_settings1', className='tab1-pulldown', children=[
                html.Div(children='Device selection'),
                dcc.Dropdown(
                    id='device-dropdown',
                    options=options,
                    value=default_device,  
                    clearable=False,
                    className='dropdown',
                )

            ]),

            html.Div(id='tab1_settings2', className='tab1-pulldown', children=[
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
                    value=sample_rate_str,  
                    clearable=False,
                    style=audio_style
                ),
            ], style=audio_style),

            html.Div(id='tab1_settings3', className='tab1-pulldown', children=[
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
                    value=sample_length_str,
                    clearable=False,
                    style=audio_style
                )),
            ], style=audio_style),

            html.Div(id='tab1_settings4', className='tab1-pulldown', children=[
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
                    value=shapecatches_str,
                    clearable=False,
                    style=audio_style
                )),
                html.Div(children='', style={'color': 'red'}),
            ], style=audio_style),

            html.Div(id='tab1_settings5', className='tab1-pulldown', children=[
                html.Div(children='Buffer Size'),
                html.Div(
                    dcc.Dropdown(
                        id='chunk_size',
                        className='dropdown',
                        options=[
                            {'label': '516', 'value': '516'},
                            {'label': '1024', 'value': '1024'},
                            {'label': '2048', 'value': '2048'},
                            {'label': '4096', 'value': '4096'},
                            {'label': '8192', 'value': '8192'},
                            {'label': '16184', 'value': '16184'},
                        ],
                        value=chunk_size_str,  
                        clearable=False,
                        style=audio_style
                        ),
                    ),
                html.Div(id='output_chunk_text', children=''),
            ], style=audio_style),

            html.Div(id='tab1-serial-div', children=[    

                # tab1-serial-div-1
                    html.Div(id='tab1-serial-div-1', className='tab1-serial-thirds', children=[
                        # serial-instructions div
                        html.Div(id='serial-instructions', children=[
                            dbc.Modal(
                                id='tempcal-modal',
                                is_open=False,
                                size="lg",
                                children=[
                                    dbc.ModalHeader("Temperature Calibration Progress"),
                                    dbc.ModalBody(html.Pre(id='tempcal-log-modal', style={'fontSize': '12px'})),
                                    dbc.ModalFooter([
                                    dbc.Button("Confirm", id='confirm-tempcal-btn', color='primary', className='me-2'),
                                    dbc.Button("Cancel",  id='close-tempcal-modal', color='secondary'),
                                ]),

                                ]
                            ),
                            html.H3('You have selected a GS-MAX serial device'),
                            html.Label('Input commands to device'),
                            html.Div(children=[
                                dcc.Input(id='cmd-input', type='text', value='', style={'width':'50%', 'paddingRight':'10px', 'border':'solid 1px'}),
                                dcc.Input(id='hidden-input', type='text', value=f'{device}', style={'display': 'none'}),
                                html.Button('Submit', id='submit-cmd', className='action_button', n_clicks=0, style={'marginLeft':'10px', 'width':'30%'}),
                                ]),

                            html.Div(id='command_output'),
                            html.P(''),
                            html.P('Found a bug 🐞 or have a suggestion, email me below'),
                            html.P('Steven Sesselmann'),
                            html.Div(html.A('steven@gammaspectacular.com', href='mailto:steven@gammaspectacular.com')),
                            html.Div(html.A('Gammaspectacular.com', href='https://www.gammaspectacular.com', target='_new')),
                        

                    html.Div([
                        html.Hr(),
                        html.H5("Automatic Temperature Calibration"),
                        html.P('This is an automated function for temperature compensation, see instruction in the manual on tab.6 before using.'),
                        html.P('Do Not use on factory calibrated instruments'),
                        dbc.Row([
                            dbc.Col(html.Label("Runs to sample (minimum 2):"), width=4),
                            dbc.Col(html.Label("Degrees °C between runs:"), width=4)
                        ]),

                        dbc.Row([
                            dbc.Col(dbc.Input(id='num-runs', type='number', placeholder='Number of runs', value=global_vars.tempcal_num_runs, min=2), width=4),
                            dbc.Col(dbc.Input(id='temp-step', type='number', placeholder='Δ°C between runs', value=global_vars.tempcal_delta, min=1), width=4),
                            dbc.Col(dbc.Button("Start", id='start-tempcal-btn', className='action_button', ), width=4)
                        ], className="mb-2"),

                        dcc.Loading(
                            id="tempcal-loading",
                            type="default",
                            children=html.Div(id='tempcal-output', style={'whiteSpace': 'pre-line', 'fontSize': '12px'})
                        )
                    ]),

                    ]), # end serial-instructions

                    ]), # end tab1-serial-div-1

                    # tab1-serial-div2
                    html.Div(id='tab1-serial-div-2', className='tab1-serial-thirds', children=[

                        html.Div(id='serial-device-info-table', style={'marginTop': '10px', 'width':'100%', 'height':'90%'}),
                         # Show Tco button
                        html.Button("Temperature Compensation Table", id='open-tco-modal', n_clicks=0, className='action_button', style={'marginTop': '10px', 'width':'80%', 'margin-left':'10%'}),

                        # The Modal
                        dbc.Modal(id='tco-modal', is_open=False, size="sm", children=[
                            dbc.ModalHeader("Temperature Compensation Table"),
                            dbc.ModalBody(html.Div(id='tco-modal-body'), style={'padding': '0 1rem'}),
                                dbc.ModalFooter(dbc.Button("Close", id='close-tco-modal', className='ml-auto'))
                            ])

                        ]), # end tab1-middle-div2
                    # tab1-serial-div-3
                html.Div(id='tab1-serial-div-3', className='tab1-serial-thirds', children=[
                    # max-pulse
                    html.Div(id='max-pulse', children=[
                        dcc.Graph(id='max-pulse-plot'),

                        # button div
                        html.Div(id='max-pulse-button-div', children=[
                            html.Button('Start Max Pulse', 
                                id='start-max-pulse', 
                                n_clicks=0, 
                                className='action_button', 
                                style={'marginLeft': '100px', 'marginTop': '20px', 'width':'130px'}),
                            html.Button('Stop Max Pulse', 
                                id='stop-max-pulse', 
                                n_clicks=0, 
                                className='action_button', 
                                style={'marginLeft': '10px', 'marginTop': '20px', 'width':'130px'}),
                        ]), # button div
                    ]) # end max-pulse
                ]), # end tab1-serial-div-3

                ], style=serial_style), # end tab1-serial-div


            html.Div(id='tab1-audio-div', children=[

                # Audio device instruction text box
                html.Div(id='tab1-audio-div-1', className='tab1-audio-thirds', children=[
                    html.H2('Easy step by step setup'),
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
                    html.Div(id='path_text', children=f'Files saved to:\n {data_directory}'),
                ]), # end audio device instruction

                # tab1-audio-div-2'
                    html.Div(id='tab1-audio-div-2', className='tab1-audio-thirds', children=[

                        html.Div(id='showplot', children=[
                            dcc.Graph(id='plot', figure={'data': [{}], 'layout': {}})
                        ]),

                        html.Button('Capture Pulse Shape',
                            id='get_shape_btn',
                            n_clicks=0,
                            className='action_button',
                            style={'marginLeft': '20%'}
                        ),

                        html.Div('Peak shifter', style={'marginLeft': '20px'}),
                        html.Div(dcc.Slider(
                            id='peakshifter',
                            min=-20,
                            max=20,
                            step=1,
                            value=peakshift,
                            marks={i: str(i) for i in range(-20, 21, 5)}
                        ), style={'width': '85%', 'marginLeft': 'auto', 'marginRight': '0'}),
                        
                        html.Div(id='shapecatcher-feedback',
                            children='',
                            style={'paddingLeft': '70px', 'textAlign': 'center', 'color': 'green', 'height': '20px'}
                        ),
                        html.Div(children=[
                            html.Label('Stereo off/on', style={'paddingRight': '10px'}),
                            daq.BooleanSwitch(id='stereo', on=stereo, color='green')
                        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'padding': '5px'}),
                    ]), #end tab1-audio-div-2

                    # 
                    html.Div(id='audio-distortion', className='tab1-audio-thirds', children=[
                        html.Div(id='showcurve', children=[
                            dcc.Graph(id='curve', figure={'data': [{}], 'layout': {}}),
                            
                            html.Div('', style={'height': '50px'}),
                            html.Button('Get Distortion Curve',
                                id='get_curve_btn',
                                n_clicks=0,
                                className='action_button',
                                style={'marginLeft': '20%', 'marginTop': '20px'}
                                )]
                            )]),


                ], style=audio_style),


            html.Div(id='footer-tab2', children=[
                html.Img(id='footer', src='assets/footer.gif'),
                html.Button('Save Settings', id='submit', n_clicks=0, style={'display': 'none'}),
                html.Div(id='rate_output'),
                html.Div(id='interval-audio'),
                html.Div(id='interval-serial'),
                html.Div(id='n_clicks_storage'),
            ]),

        ]), #tab1-frame ends
    ])
    
    return tab1

# Callback to save settings ---------------------------

@app.callback(
    [Output('selected_device_text', 'children'),
     Output('sampling_time_output', 'children'),
     Output('stereo', 'on')],
    [Input('submit', 'n_clicks'),
     Input('device-dropdown', 'value'),
     Input('sample_rate', 'value'),
     Input('chunk_size', 'value'),
     Input('catch', 'value'),
     Input('sample_length', 'value'),
     Input('peakshifter', 'value'),
     Input('stereo', 'on')]
)
def save_settings(n_clicks, device, sample_rate, chunk_size, catch, sample_length, peakshift, stereo):
    # Only proceed if the submit button was clicked
    if n_clicks is None:
        return no_update, no_update, no_update

    # Handle the case where device is None
    try:
        device = int(device) if device is not None else None
    except (ValueError, TypeError):
        device = None

    # Update global variables
    with global_vars.write_lock:
        global_vars.device = device if device is not None else global_vars.device  # Retain the previous value if device is None
        global_vars.sample_rate = int(sample_rate) if sample_rate is not None else global_vars.sample_rate
        global_vars.chunk_size = int(chunk_size) if chunk_size is not None else global_vars.chunk_size
        global_vars.shapecatches = int(catch) if catch is not None else global_vars.shapecatches
        global_vars.sample_length = int(sample_length) if sample_length is not None else global_vars.sample_length
        global_vars.peakshift = int(peakshift) if peakshift is not None else global_vars.peakshift
        global_vars.stereo = bool(stereo) if stereo is not None else global_vars.stereo

    # Save settings to JSON
    save_settings_to_json()

    # Calculate pulse length and warning message
    if sample_rate is not None and sample_length is not None:
        pulse_length = int(1000000 * int(sample_length) / int(sample_rate))
        warning = 'WARNING LONG' if pulse_length >= 334 else ''
    else:
        pulse_length = 0
        warning = ''

    logger.debug(f'Settings saved to JSON file\n')

    # Return the updated UI elements
    return (
        f'Device: {device}' if device is not None else 'No device selected',
        f'{warning} Dead time ~ {pulse_length} µs' if sample_rate and sample_length else 'No sample rate or length set',
        stereo
    )

# Callback to capture and save mean pulse shape ----------

@app.callback(
    [Output('plot'          , 'figure'),
     Output('showplot'      , 'figure')],
    [Input('get_shape_btn'  , 'n_clicks')],
    [State('stereo'         , 'on'),
    State('theme'           , 'value')]
)
def capture_pulse_shape(n_clicks, stereo, theme):
    if theme == 'light-theme':
        bg_color    = 'white'
        line_color  = 'black'
        trace_left  = '#0066ff'
        trace_right = 'red'
        trace_dots  = 'black'
    else:
        bg_color    = 'black'
        line_color  = 'white'  
        trace_left  = 'lightgreen'
        trace_right = 'pink' 
        trace_dots  = 'white'

    layout = {
        'title': {
            'text': f'Mean Pulse Captured (always positive)',
            'font': {'size': 16, 'color': line_color},
            'x': 0.5,
            'y': 0.95
        },
        'margin': {'l': 40, 'r': 10, 't': 40, 'b': 40},
        'height': 350,
        'paper_bgcolor': bg_color,
        'plot_bgcolor': bg_color,
        'xaxis': {
            'showgrid': True,
            'gridcolor': 'lightgray',
            'zeroline': True,
            'zerolinecolor': line_color,
            'zerolinewidth': 1,
            'tickfont': {'color': line_color, 'size': 10}
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': 'lightgray',
            'zeroline': True,
            'zerolinecolor': line_color,
            'zerolinewidth': 1,
            'tickfont': {'color': line_color, 'size': 10}
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
        marker={'color': trace_dots, 'size': 4},
        line={'color': trace_left, 'width': 2},
        name='Left Channel'
    )

    trace_right = go.Scatter(
        x=dots,
        y=shape_right,
        mode='lines+markers',
        marker={'color': trace_dots, 'size': 4},
        line={'color': trace_right, 'width': 2},
        name='Right Channel'
    )

    fig = go.Figure(data=[trace_left, trace_right] if stereo else [trace_left], layout=layout)
    
    return fig, fig


# Callback for plotting distortion curve ------------------------

@app.callback(
    [Output('curve'         , 'figure'),
     Output('showcurve'     , 'figure')],
    [Input('get_curve_btn'  , 'n_clicks')],
    [State('stereo'         , 'on'),
    State('theme'           , 'value')]
)
def distortion_curve(n_clicks, stereo, theme):
    if theme == 'light-theme':
        bg_color    = 'white'
        line_color  = 'black'
        trace_left  = '#0066ff'
        trace_right = 'red' 

    else:
        bg_color    = 'black'
        line_color  = 'white'  
        trace_left  = 'lightgreen'
        trace_right = 'pink' 

    layout = {
        'title': {
            'text': 'Pulses Sorted by Distortion', 
            'font': {
                'size': 16, 
                'color': line_color
                }, 
        'x': 0.5, 
        'y': 0.95},
        'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
        'height': 300,
        'showlegend': False,
        'paper_bgcolor': bg_color,
        'plot_bgcolor': bg_color,
        'xaxis': {
            'showgrid': True,
            'gridcolor': 'lightgray',
            'zeroline': True,
            'zerolinecolor': line_color,
            'zerolinewidth': 1,
            'tickfont': {'color': line_color, 'size': 10}
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': 'lightgray',
            'zeroline': True,
            'zerolinecolor': line_color,
            'zerolinewidth': 1,
            'tickfont': {'color': line_color, 'size': 10}
        },
    }

    if n_clicks == 0:
        return {'data': [{}], 'layout': layout}, {'data': [{}], 'layout': layout}
    else:
        line_style_left = dict(size=2, color='blue')
        line_style_right = dict(size=2, color='red')

        distortion_list_left, distortion_list_right = dcr.distortion_finder(stereo)

        x_left = list(range(len(distortion_list_left)))
        x_right = list(range(len(distortion_list_right)))

        # Left Channel Trace
        trace_left = go.Scatter(
            x=x_left,
            y=distortion_list_left,
            mode='lines',  # Equivalent to 'line' type and 'mode: lines'
            name='Left Channel',
            line=dict(color=trace_left, width=2),  # Line style: specify color and width
            marker=line_style_left  # Marker style for the left channel
        )

        # Right Channel Trace
        trace_right = go.Scatter(
            x=x_right,
            y=distortion_list_right,
            mode='lines',
            name='Right Channel',
            line=dict(color=trace_right, width=2),  # Line style: specify color and width
            marker=line_style_right  # Marker style for the right channel
        )

        fig = {'data': [trace_left, trace_right] if stereo else [trace_left], 'layout': layout}
        return fig, fig

# ------- Send serial device commands -------------------

@app.callback(
    [
        Output('command_output', 'children'),
        Output('serial-device-info-table', 'children'),
        Output('cmd-input', 'value')
    ],
    [
        Input('submit-cmd', 'n_clicks'),
        Input('cmd-input', 'n_submit'),
        Input('device-dropdown', 'value'),
    ],
    [
        State('cmd-input', 'value'),
    ]
)
def update_serial_table(n_clicks, n_submit, device, cmd):
    trigger = ctx.triggered_id
    logger.debug(f"🔔 update_serial_table triggered by {trigger}")

    # Default fallback values
    command_output  = no_update
    cmd_input_value = no_update

    try:
        dev = int(device)
    except (ValueError, TypeError):
        return "Invalid device", html.Div("No device selected"), ""

    if dev < 100:
        return "Audio device selected", html.Div("Audio device has no firmware table"), ""

    # When just selecting the device → show table
    if trigger == 'device-dropdown':
        table = fn.generate_device_settings_table()
        return no_update, table, no_update

    # If Submit or Enter was pressed
    if trigger in ('submit-cmd', 'cmd-input'):

        if not cmd or not isinstance(cmd, str) or cmd.strip() == "":

            table = fn.generate_device_settings_table()

            return "Click [submit] to refresh table", table, ""
        
        allowed = allowed_command(cmd)

        if cmd.startswith("+"):
            cmd = cmd[1:]

        if allowed:
            # Carry out command
            process_03(cmd)
            time.sleep(0.5)

            table = fn.generate_device_settings_table()

            return f"Command sent: {cmd}", table, ""
        else:
            table = fn.generate_device_settings_table()
            return "Command not allowed", table, ""

    return no_update, no_update, no_update

# Callback for updating shapecatcher feedback ---------
@app.callback(
    Output('shapecatcher-feedback'  , 'children'),
    [Input('interval-component'     , 'n_intervals')]
)
def update_log_output(n_intervals):
    return html.Pre('\n'.join(sc_info[-1:]))  

@app.callback(
    Output('update-interval'    , 'disabled'),
    Input('start-max-pulse'     , 'n_clicks'),
    Input('stop-max-pulse'      , 'n_clicks'),
    prevent_initial_call=True
)
def control_interval(start_clicks, stop_clicks):
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'start-max-pulse':
        start_max_pulse_check()

    elif button_id == 'stop-max-pulse':
        stop_max_pulse_check()
    return

@app.callback(
    Output('max-pulse-plot' , 'figure'),
    Input('update-interval' , 'n_intervals'),
    State('theme'           , 'value')
)
def update_graph(n_intervals, theme):
    if theme == 'light-theme':
        bg_color    = 'white'
        line_color  = 'black'
        trace_left  = 'lightblue'
        trace_right = 'red' 

    else:
        bg_color    = 'black'
        line_color  = 'white'  
        trace_left  = 'lightgreen'
        trace_right = 'pink' 
    # Retrieve the max pulse shape from global_vars
    with global_vars.write_lock:
        pulse_data  = global_vars.max_pulse_shape
        max_pulse_x = global_vars.max_pulse_length
        max_pulse_y = global_vars.max_pulse_height

    # Check if there's no data available
    if not pulse_data:  # No data available
        return {
            'data': [
                go.Scatter(
                    x=[0],  # Placeholder X
                    y=[0],  # Placeholder Y
                    mode='lines+markers',
                    line=dict(color=trace_left, width=2),
                    marker=dict(size=6, color=line_color),
                    name='No Data'
                )
            ],
            'layout': {
                'title': {
                    'text': 'Max Pulse Plot (No Data)',
                    'font': {'color': line_color}
                },
                'paper_bgcolor': bg_color,
                'plot_bgcolor': bg_color,
                'xaxis': {
                    'showgrid': True,
                    'gridcolor': 'lightgray',
                    'zeroline': True,
                    'zerolinecolor': line_color,
                    'zerolinewidth': 1,
                    'tickfont': {'color': line_color, 'size': 10},
                    'range': [0, max_pulse_x],
                },
                'yaxis': {
                    'showgrid': True,
                    'gridcolor': 'lightgray',
                    'zeroline': True,
                    'zerolinecolor': line_color,
                    'zerolinewidth': 1,
                    'tickfont': {'color': line_color, 'size': 10},
                    'range': [0, max_pulse_y],
                },
            }
        }

    # Limit to the last 20 points
    pulse_data = pulse_data[-20:]

    # Prepare the graph
    x_values = list(range(len(pulse_data)))  # X-axis: indices of the last 20 points
    y_values = pulse_data  # Y-axis: pulse amplitudes

    figure = {
        'data': [
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',  
                line=dict(color=trace_left, width=2),  
                marker=dict(size=6, color=line_color), 
                name='Pulse Data'
            )
        ],
        'layout': {
            'title': {
                'text': 'Max Pulse Pulse',
                'font': {'color': line_color}
                },
            'paper_bgcolor': bg_color,
            'plot_bgcolor': bg_color,
            'xaxis': {
                'showgrid': True,
                'gridcolor': 'lightgray',
                'zeroline': True,
                'zerolinecolor': line_color,
                'zerolinewidth': 1,
                'tickfont': {'color': line_color, 'size': 10},
                'range': [0, max_pulse_x],
            },
            'yaxis': {
                'showgrid': True,
                'gridcolor': 'lightgray',
                'zeroline': True,
                'zerolinecolor': line_color,
                'zerolinewidth': 1,
                'tickfont': {'color': line_color, 'size': 10},
                'range': [0, max_pulse_y],
            },
        }
    }
    return figure

# Dynamically switch between audio and serial devices
@app.callback(
    [
        Output('tab1-audio-div', 'style'),
        Output('tab1-serial-div', 'style'),
    ],
    Input('device-dropdown', 'value')
)
def toggle_frames(device):
    hidden_style = {'display': 'none'}
    visible_style = {'display': 'block'}

    try:
        device = int(device) if device is not None else None
    except (ValueError, TypeError):
        device = None

    if device is None or device < 100:  # Audio device or invalid
        return visible_style, hidden_style  # Show audio, hide serial
    else:  # Serial device
        return hidden_style, visible_style  # Hide audio, show serial


@app.callback(
    [
      Output('tempcal-modal',        'is_open'),
      Output('tempcal-log-modal',    'children'),
      Output('close-tempcal-modal',  'children'),
    ],
    [
      Input('start-tempcal-btn',     'n_clicks'),
      Input('confirm-tempcal-btn',   'n_clicks'),
      Input('log-interval',          'n_intervals'),
      Input('close-tempcal-modal',   'n_clicks'),
    ],
    [
      State('tempcal-modal',        'is_open'),
      State('device-dropdown',      'value'),
      State('num-runs',             'value'),
      State('temp-step',            'value'),
    ],
    prevent_initial_call=True
)
def handle_tempcal_modal(start_clicks, confirm_clicks, interval, close_clicks,
                         is_open, device, num_runs, temp_delta):

    trigger = ctx.triggered_id

    with global_vars.write_lock:
        global_vars.tempcal_num_runs     = num_runs
        global_vars.tempcal_delta        = temp_delta

    # If user just hit “Start”, pop open the modal for confirmation
    if trigger == 'start-tempcal-btn':
        from global_vars import (
            tempcal_stability_tolerance,
            tempcal_stability_window_sec,
            tempcal_poll_interval_sec,
            tempcal_spectrum_duration_sec,
            tempcal_smoothing_sigma,
            tempcal_peak_search_range,
            tempcal_base_value,
            tempcal_num_runs,
            tempcal_delta
        )

        settings_summary = "\n".join([
            "❗ Please confirm you want to run temperature calibration.",
            "----------------------------------------------------------",
            f"🔧 Calibration Settings used (edit in _settings.json).",
            "----------------------------------------------------------",
            f"• Stability tolerance: {tempcal_stability_tolerance} °C",
            f"• Stability window: {tempcal_stability_window_sec} sec",
            f"• Poll interval: {tempcal_poll_interval_sec} sec",
            f"• Spectrum duration: {tempcal_spectrum_duration_sec} sec",
            f"• Smoothing sigma: {tempcal_smoothing_sigma} σ",
            f"• Expected Peak search range: {tempcal_peak_search_range}",
            f"• Base value: {tempcal_base_value}",
            f"• Number of calibration runs: {tempcal_num_runs}",
            f"• Temperature ∆ between runs: {tempcal_delta} C˚",
            "----------------------------------------------------------",
            "Click Confirm to begin..."
        ])

        return True, settings_summary, "Cancel"

    # If they hit “Confirm”, do some basic checks then actually start the run
    elif trigger == 'confirm-tempcal-btn':
        try:
            dev = int(device)
        except:
            return True, "❌ Invalid device selected.", "Close"

        if dev < 100 or dev > 999:

            return True, f"❌ Device {dev} out of allowed range (100–999).", "Close"

        if not num_runs or not temp_delta:
            
            return True, "❗ Please fill in both ‘Number of runs’ and ‘Δ°C between runs’.", "Cancel"

        tempcal_cancelled = False

        def run():
            try:
                with global_vars.write_lock:
                    num     = global_vars.tempcal_num_runs
                    delta   = global_vars.tempcal_delta
                    base    = global_vars.tempcal_base_value

                    tdelta  = [delta] * (num - 1)

                run_temperature_calibration(temp_delta=tdelta , base_value=base)

            except Exception as e:
                print(e)

        threading.Thread(target=run, daemon=True).start()

        return True, "⚙️ Calibration started. Check _tempcal.log for progress.", "Close"

    # Regular log refresh from file
    elif trigger == 'log-interval':
        log_path = os.path.join(data_directory, '_tempcal.log')

        if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
            # Skip update if log hasn't started
            return is_open, no_update, no_update
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
            recent_lines = lines[-10:]
            log_text = ''.join(recent_lines)
        except Exception as e:
            log_text = f"❌ Could not read log: {str(e)}"

        # Auto-close modal if calibration completed
        if "✅ Temperature calibration complete" in log_text:
            return False, log_text, "Close"

        # label = "Close" if "✅ Temperature calibration complete" in log_text else "Cancel"

        return is_open, log_text, "Cancel"

    # User hit “Cancel” or “Close”
    elif trigger == 'close-tempcal-modal':
        tempcal_cancelled = True
        return False, "Calibration cancelled.", "Cancel"

    return is_open, no_update, no_update


@app.callback(
    Output('start-tempcal-btn', 'disabled'),
    Input('serial-device-info-table', 'children')
)
def disable_tempcal(_):

    serial = global_vars.serial_number

    try:
        s = int(serial)
    except (ValueError, TypeError):
        # no valid serial yet → disable
        return True
    # only enable if 200 ≤ serial ≤ 999
    return not (200 <= s <= 999)


# 3a) Toggle open/close
@app.callback(
    Output('tco-modal', 'is_open'),
    [ Input('open-tco-modal', 'n_clicks'), Input('close-tco-modal', 'n_clicks') ],
    [ State('tco-modal', 'is_open') ]
)
def toggle_tco_modal(open_clicks, close_clicks, is_open):
    # if either button clicked, flip the open state
    if open_clicks or close_clicks:
        return not is_open
    return is_open

# 3b) Populate the modal body when first opened
@app.callback(
    Output('tco-modal-body', 'children'),
    [ Input('open-tco-modal', 'n_clicks') ]
)
def render_tco_modal(n_clicks):
    if not n_clicks:
        return no_update  # don't render until user asks
    # call the helper we just added
    return fn.generate_temperature_comp_table()


# -- End of tab1.py ---