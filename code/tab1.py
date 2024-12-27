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
import shproto.dispatcher
import time
import dash_daq as daq
import global_vars
from dash import dcc, html, dash_table, no_update
from dash.dependencies import Input, Output, State
from server import app
from functions import (
    execute_serial_command, 
    generate_device_settings_table, 
    allowed_command, 
    save_settings_to_json,
    start_max_pulse_check,
    stop_max_pulse_check
    )
from shapecatcher import sc_info

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
        theme           = global_vars.theme

    pulse_length    = 0
    filepath        = os.path.dirname(__file__)
    shape_left, shape_right = fn.load_shape()

    logger.info(f'Tab1 stereo = {stereo}\n')

    # Generate audio and serial device lists
    try:
        adl = fn.get_device_list()  
        sdl = fn.get_serial_device_list()   
        dl = adl + sdl   
        options = [{'label': filename, 'value': index} for filename, index in dl]
        options = [{k: str(v) for k, v in option.items()} for option in options]
        options = fn.cleanup_serial_options(options)                   
    except:
        logger.info("Tab1 - Something went wrong retrieving device list")
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
                    value=device,  
                    clearable=False,
                    className='dropdown',
                ),
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
                    value=sample_rate,
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
                    value=sample_length,
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
                    value=shapecatches,
                    clearable=False,
                    style=audio_style
                )),
                html.Div(children='', style={'color': 'red'}),
            ], style=audio_style),

            html.Div(id='tab1_settings5', className='tab1-pulldown', children=[
                html.Div(children='Buffer Size'),
                html.Div(dcc.Dropdown(
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
                    value=chunk_size,
                    clearable=False,
                    style=audio_style
                )),
                html.Div(id='output_chunk_text', children=''),
            ], style=audio_style),

            html.Div(id='tab1-serial-div', children=[    

                # tab1-serial-div-1
                    html.Div(id='tab1-serial-div-1', className='tab1-serial-thirds', children=[
                        # serial-instructions div
                        html.Div(id='serial-instructions', children=[
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
                        ]), # end serial-instructions
                    ]), # end tab1-serial-div-1

                    # tab1-serial-div2
                    html.Div(id='tab1-serial-div-2', className='tab1-serial-thirds', children=[
                        html.Div(id='serial-device-info-table'),
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
    [Output('selected_device_text'  , 'children'),
     Output('sampling_time_output'  , 'children'),
     Output('stereo'                , 'on')],
    [Input('submit'                 , 'n_clicks'),
     Input('device-dropdown'        , 'value'),
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

        return f'Device: {device}', f'{warning} Dead time ~ {pulse_length} µs', stereo

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
    Output('command_output'             , 'children'),
    Output('serial-device-info-table'   , 'children'),
    Output('cmd-input'                  , 'value')
    ],
    [
    Input('submit-cmd'                  , 'n_clicks'), 
    Input('cmd-input'                   , 'n_submit'),
    ],
    [
    State('cmd-input'                   , 'value'), 
    State('device-dropdown'             , 'value'),
    ]
)
def update_output(n_clicks, n_submit, cmd, device):
    # Check if the device is a valid serial device
    if not device or int(device) < 100:  # If no device or not a serial device
        return "No device found", no_update, no_update

    if cmd is None or not isinstance(cmd, str):
        table = generate_device_settings_table()
        return 'No command sent', table, ''

    allowed = allowed_command(cmd)

    if cmd.startswith("+"):
        cmd = cmd[1:]

    if allowed:
        execute_serial_command(cmd)
        table = generate_device_settings_table()
        return f'Command sent: {cmd}', table, ''

    else:
        table = generate_device_settings_table()
        return "Click Submit for device data", table, ''

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
    """
    Toggle between audio and serial frames based on device selection.
    - Audio devices: device < 100
    - Serial devices: device >= 100
    """
    hidden_style = {'display': 'none'}
    visible_style = {'display': 'block'}

    # Check if the device is audio or serial
    if int(device) < 100:  # Audio device
        return visible_style, hidden_style  # Show audio, hide serial
    else:  # Serial device
        return hidden_style, visible_style  # Hide audio, show serial


# -- End of tab1.py ---