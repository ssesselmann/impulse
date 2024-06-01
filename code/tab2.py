import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import os
import json
import time
import numpy as np
import sqlite3 as sql
import dash_daq as daq
import dash_bootstrap_components as dbc
import audio_spectrum as asp

import subprocess
import serial.tools.list_ports
import threading
import logging

import shproto.dispatcher

from dash import dcc, html, Input, Output, State, callback, Dash
from dash.dependencies import Input, Output, State
from server import app
from dash.exceptions import PreventUpdate
from datetime import datetime
from functions import is_valid_json
from functions import execute_serial_command
from functions import get_options

logger = logging.getLogger(__name__)

path            = None
n_clicks        = None
commands        = None
cmd             = None
schemaVersion   = None
device          = None
global_counts   = 0
global_cps      = 0
cps             = 0
stop_event      = threading.Event()
data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")
spec_notes      = ''
write_lock      = threading.Lock()

def show_tab2():
    global global_counts
    global cps_list
    global device

    options_sorted = get_options()

    database        = fn.get_path(f'{data_directory}/.data_v2.db')

    conn            = sql.connect(database)
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 

    settings        = c.fetchall()[0]
    filename        = settings[1]
    device          = settings[2]             
    sample_rate     = settings[3]
    chunk_size      = settings[4]
    threshold       = settings[5]
    tolerance       = settings[6]
    bins            = settings[7]
    bin_size        = settings[8]
    max_counts      = settings[9]
    shapestring     = settings[10]
    sample_length   = settings[11]
    calib_bin_1     = settings[12]
    calib_bin_2     = settings[13]
    calib_bin_3     = settings[14]
    calib_e_1       = settings[15]
    calib_e_2       = settings[16]
    calib_e_3       = settings[17]
    coeff_1         = settings[18]
    coeff_2         = settings[19]
    coeff_3         = settings[20]
    filename2       = settings[21]
    peakfinder      = settings[23]
    sigma           = settings[25]
    max_seconds     = settings[26]
    t_interval      = settings[27]
    compression     = settings[29]

    millisec        = t_interval*1000

    spec_notes      = fn.get_spec_notes(filename)

    if device >= 100:
        serial          = 'block'
        audio           = 'none'
    else:
        serial          = 'none'
        audio           = 'block'

    if max_counts == 0:
        counts_warning  = 'red'
    else: 
        counts_warning  = 'white'    

    if max_seconds == 0:
        seconds_warning = 'red'
    else: 
        seconds_warning = 'white'  

    html_tab2 = html.Div(id='tab2', children=[
        html.Div(id='polynomial', children=''),
        html.Div(id='output-roi', children=''),
        html.Div(id='bar_chart_div', # Histogram Chart
            children=[
                dcc.Graph(id='bar-chart', figure={},),
                dcc.Interval(id='interval-component', interval=millisec, n_intervals=0) # Refresh rate 1s.
            ]),

        html.Div(id='t2_filler_div', children=''),
        #Start button
        html.Div(id='t2_setting_div1', children=[
            html.Button('START', id='start'),
            html.Div(id='start_text', children=''),
            html.Div(id='counts', children= ''),
            html.Div(''),
            html.Div(['Max Counts', dcc.Input(id='max_counts', type='number', step=1,  readOnly=False, value=max_counts, className='input',style={'background-color': counts_warning} )]),
            ]),

        html.Div(id='t2_setting_div2', children=[            
            html.Button('STOP', id='stop'), 
            html.Div(id='stop_text', children=''),
            html.Div(id='elapsed', children= '' ),
            html.Div(['Max Seconds', dcc.Input(id='max_seconds', type='number', step=1,  readOnly=False, value=max_seconds, className='input', style={'background-color': seconds_warning} )]),
            html.Div(id='cps', children=''),
            ]),

        html.Div(id='t2_setting_div3', children=[
            html.Div(id='compression_div', children=[
                html.Div(['Resolution:', dcc.Dropdown(id='compression',
                    options=[
                        {'label': '512 Bins', 'value': '16'},
                        {'label': '1024 Bins', 'value': '8'},
                        {'label': '2048 Bins', 'value': '4'},
                        {'label': '4096 Bins', 'value': '2'},
                        {'label': '8192 Bins', 'value': '1'},
                    ],
                    value=compression,
                    className='dropdown')
                    ],
                     style={'display': serial}
                     ),

                html.Div(['Select existing file:', 
                    dcc.Dropdown(id='filenamelist', options=options_sorted, value=filename, className='dropdown', optionHeight=40)
                ]),
                
                html.Div(['Or create new file:', 
                    dcc.Input(id='filename', type='text', value=filename, className='input', placeholder='Enter new filename')
                ]),
                
                # Overwrite confirmation modal
                dbc.Modal([
                    dbc.ModalBody(id='modal-body'),
                    dbc.ModalFooter([
                        dbc.Button("Overwrite", id="confirm-overwrite", className="ml-auto", n_clicks=0),
                        dbc.Button("Cancel", id="cancel-overwrite", className="ml-auto", n_clicks=0),
                    ]),
                    ], 
                    id='modal-overwrite', 
                    is_open=False,
                    centered=True,
                    size="md",
                    className="custom-modal",
                    ),
                html.Div(id='start_process_flag', style={'display': 'none'}),
                html.Div(['Number of bins:', dcc.Input(id='bins', type='number', value=bins)], className='input', style={'display': audio}),
                html.Div(['Bin size:', dcc.Input(id='bin_size', type='number', value=bin_size)], className='input', style={'display': audio}),
            ]),
        ]),

        # this part switches depending which device is connected ---------------

        html.Div(id='t2_setting_div4', children=[
            html.Div(['Serial Command:', dcc.Dropdown(
                id='selected_cmd', 
                options=[
                    {'label': 'Pause MCA'         , 'value': '-sto'},
                    {'label': 'Restart MCA'       , 'value': '-sta'},
                    {'label': 'Reset histogram  ' , 'value': '-rst'},
                ],
                placeholder='Select command',
                value=commands[0] if commands else None, # Check if commands is not None before accessing its elements
                className='dropdown',
            )], style={'display':serial}),  

            html.Div(id='cmd_text', children='', style={'display': 'none'}),
            html.Div(['LLD Threshold:'      , dcc.Input(id='threshold'  , type='number', value=threshold, className='input')], style={'display':audio}),
            html.Div(['Shape Tolerance:'    , dcc.Input(id='tolerance'  , type='number', value=tolerance, className='input' )], style={'display':audio}),
            html.Div(['Update Interval(s)'  , dcc.Input(id='t_interval' , type='number', step=1,  readOnly=False, value=t_interval, className='input' )]),

        ],style={'width':'10%', } 
        ),

        # ------------------------------------------------------
        
        html.Div(id='t2_setting_div5', children=[
            html.Div('Comparison'),
            html.Div(dcc.Dropdown(
                    id='filename2',
                    options=options_sorted,
                    placeholder='Select comparison',
                    value=filename2,
                    className='dropdown',
                    optionHeight=40
                    )),

            html.Div(['Show Comparison'      , daq.BooleanSwitch(id='compare_switch',on=False, color='purple',)]),
            html.Div(['Subtract Comparison'  , daq.BooleanSwitch(id='difference_switch',on=False, color='purple',)]),

            ]),

        html.Div(id='t2_setting_div6'   , children=[
            html.Div(['Energy by bin'   , daq.BooleanSwitch(id='epb_switch',on=False, color='purple',)]),
            html.Div(['Show log(y)'     , daq.BooleanSwitch(id='log_switch',on=False, color='purple',)]),
            html.Div(['Calibration'     , daq.BooleanSwitch(id='cal_switch',on=False, color='purple',)]),
            html.Div(['Coincidence'     , daq.BooleanSwitch(id='mode-switch',on=False, color='purple',)]),
            ]), 

        html.Div(id='t2_setting_div7', children=[
            html.Button('Sound <)' , id='soundbyte', className='action_button'),
            html.Div(id='audio', children=''),
            html.Button('Update calib.', id='update_calib_button', className='action_button'),
            html.Div(id='update_calib_message', children=''),
            dbc.Button("Publish Spectrum", id="publish-button", color="primary", className="action_button"),
            
            dbc.Modal(
                children=[
                    dbc.ModalBody(f"Are you sure you want to publish \"{filename}\" spectrum?"),
                    dbc.ModalFooter([
                        dbc.Button("Confirm", id="confirm-publish", className="ml-auto", color="primary"),
                        dbc.Button("Cancel", id="cancel-publish", className="mr-auto", color="secondary"),
                        ],
                    ),
                ],
                id="confirmation-modal",
                centered=True,
                size="md",
                className="custom-modal", 
            ),

            html.Div(id="confirmation-output", children= ''),

        ]),

        html.Div(id='t2_setting_div8', children=[
            html.Div('Calibration Bins'),
            html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1, className='input')),
            html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2, className='input')),
            html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3, className='input')),
            html.Div('peakfinder'),
            html.Div(dcc.Slider(id='peakfinder', min=0 ,max=1, step=0.1, value= peakfinder, marks={0:'0', 1:'1'})),
            ]),

        html.Div(id='t2_setting_div9', children=[
            html.Div('Energies'),
            html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1, className='input')),
            html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2, className='input')),
            html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3, className='input')),
            html.Div('Gaussian corr. (sigma)'),
            html.Div(dcc.Slider(id='sigma', min=0 ,max=3, step=0.25, value= sigma, marks={0: '0', 1: '1', 2: '2', 3: '3'})),
            html.Div(id='specNoteDiv', children=[
                dcc.Textarea(id='spec-notes-input', value=spec_notes, placeholder='Spectrum notes', cols=20, rows=6)]),
                html.Div(id='notes-warning', children=['! Stop recording before writing notes !']),
                html.Div(id='spec-notes-output', children='', style={'visibility':'hidden'}),
            
            ]),

        html.Div(children=[ html.Img(id='footer_tab2', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        
        html.Div(id='subfooter', children=[
            ]),

    ]) # End of tab 2 render

    return html_tab2

# This callback just inserts the filename into the input field
@app.callback(
    Output('filename', 'value'),
    [Input('filenamelist', 'value')],
    [State('filename', 'value')]
)
def update_filename_from_dropdown(selected_file, current_filename):
    if selected_file:
        return selected_file
    return current_filename

# START BUTTON callback - pop up warning
@app.callback(
    Output('modal-overwrite', 'is_open'),
    Output('modal-body', 'children'),
    [Input('start', 'n_clicks'), 
     Input('confirm-overwrite', 'n_clicks'), 
     Input('cancel-overwrite', 'n_clicks')],
    [State('filename', 'value'),
     State('modal-overwrite', 'is_open')]
)
def confirm_with_user(start_clicks, confirm_clicks, cancel_clicks, filename, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "start":
        file_exists = os.path.exists(f'{data_directory}/{filename}.json')
        # Open the modal only if the file exists
        if file_exists:
            return True, f'Overwrite "{filename}"?'

    # Close the modal if either "confirm-overwrite" or "cancel-overwrite" is clicked
    elif button_id in ["confirm-overwrite", "cancel-overwrite"]:
        return False, ''

    return False, ''  # Default case to ensure modal is closed if no conditions above are met

# Conditional Start function
@app.callback(
    Output('start_text', 'children'),
    [Input('confirm-overwrite', 'n_clicks'),
     Input('start', 'n_clicks')], 
    [State('filename', 'value'),
     State('compression', 'value'),
     State('t_interval', 'value'),
     State('mode-switch', 'on')]  
)
def start_new_or_overwrite(confirm_clicks, start_clicks, filename, compression, t_interval, mode_switch):
    fn.clear_global_cps_list()

    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    if mode_switch:
        mode = 4
    else:
        mode = 2        

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_value = ctx.triggered[0]['value']
    file_exists = os.path.exists(f'{data_directory}/{filename}.json')

    if trigger_value == 0:
        raise PreventUpdate

    if (trigger_id == 'confirm-overwrite') or (trigger_id == 'start' and not file_exists):

        dn = fn.get_device_number()

        if dn >= 100:
            try:
                shproto.dispatcher.spec_stopflag = 0
                dispatcher = threading.Thread(target=shproto.dispatcher.start)
                dispatcher.start()

                time.sleep(0.1)

                # Reset spectrum
                command = '-rst'
                shproto.dispatcher.process_03(command)
                logger.info(f'tab2 sends command {command}')

                time.sleep(0.1)

                # Start multichannel analyser
                command = '-sta'
                shproto.dispatcher.process_03(command)
                logger.info(f'tab2 sends command {command}')

                time.sleep(0.1)

                shproto.dispatcher.process_01(filename, compression, "GS-MAX or ATOM-NANO", t_interval)
                logger.info(f'Serial recording started')

                time.sleep(0.1)

            except Exception as e:
                logger.error(f'tab 2 update_output() error {e}')
                return f"Error: {str(e)}"
        else:
            fn.start_recording(mode)
            logger.info(f'Tab2 fn.start_recording(mode {mode}) passed.') 

        return

    raise PreventUpdate

# STOP BUTTON callback
@app.callback(Output('stop_text'  ,'children'),
              [Input('stop'      ,'n_clicks')],
              [State('filename'   , 'value')])
def stop_button(n_clicks, filename):

    if n_clicks is None:
        raise PreventUpdate

    dn = fn.get_device_number()

    if dn >= 100:
        # Stop Spectrum 
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()
        time.sleep(0.1)
        logger.info('Stop button clicked (tab2) serial device')
        return

    else:
        fn.stop_recording()
        logger.info('Stop button clicked (tab2) audio device')
        return

# UPDATE GRAPH callback
@app.callback([ Output('bar-chart'          ,'figure'), 
                Output('counts'             ,'children'),
                Output('elapsed'            ,'children'),
                Output('cps'                ,'children')],
               [Input('interval-component'  ,'n_intervals'),
                Input('bar-chart', 'relayoutData')], 
                [State('filename'           ,'value'),
                State('epb_switch'          ,'on'),
                State('log_switch'          ,'on'),
                State('cal_switch'          ,'on'),
                State('filename2'           ,'value'),
                State('compare_switch'      ,'on'),
                State('difference_switch'   ,'on'),
                State('peakfinder'          ,'value'),
                State('sigma'               ,'value'),
                State('max_seconds'         ,'value'),
                State('max_counts'          ,'value'),
                State('mode-switch'         , 'on')])
def update_graph(n, relayoutData, filename, epb_switch, log_switch, cal_switch, filename2, compare_switch, difference_switch, peakfinder, sigma, max_seconds, max_counts, mode_switch):

    if device is not None and isinstance(device, int):

        if device > 100:
            from shproto.dispatcher import cps

        elif device < 100:
            from pulsecatcher import mean_cps
            cps = mean_cps

        else:
            cps = 0    
    else:
        cps = 0        

    if mode_switch:
        coincidence = 'coincidence<br>(left if right)'
    else:
        coincidence = ""        

    annotations = []
    lines       = []
    title_text  = ''
    now         = datetime.now()
    time        = now.strftime('%d/%m/%Y')
    histogram1  = fn.get_path(f'{data_directory}/{filename}.json')

    if not os.path.exists(histogram1):
        filename = ''

    layout = go.Layout(
        paper_bgcolor = 'white', 
        plot_bgcolor = '#f0f0f0',
        showlegend=False,
        
        height  =460, 
        margin_t=20,
        margin_b=0,
        margin_l=0,
        margin_r=0,
        autosize=True,
        yaxis=dict(range=[0, 'auto']),
        xaxis=dict(range=[0, 'auto']),
        annotations=annotations,
        shapes=lines,
        uirevision="Don't change",
        )

    fig = go.Figure(layout=layout)

    if os.path.exists(histogram1) and is_valid_json(histogram1):

        with open(histogram1, "r") as f:

            with write_lock:
                data = json.load(f)

        if data["schemaVersion"]  == "NPESv2":
            data = data["data"][0] # This makes it backwards compatible

        numberOfChannels    = data["resultData"]["energySpectrum"]["numberOfChannels"]
        validPulseCount     = data["resultData"]["energySpectrum"]["validPulseCount"]
        elapsed             = data["resultData"]["energySpectrum"]["measurementTime"]
        polynomialOrder     = data["resultData"]["energySpectrum"]["energyCalibration"]["polynomialOrder"]
        coefficients        = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
        spectrum            = data["resultData"]["energySpectrum"]["spectrum"]
        coefficients        = coefficients[::-1] # Revese order   
        mu                  = 0
        prominence          = 0.5

        if sigma == 0:
            gc = []
        else:  
            gc = fn.gaussian_correl(spectrum, sigma)

        x           = list(range(numberOfChannels))
        y           = spectrum
        max_value   = np.max(y)

        if max_value    == 0:
            max_value   = 10
        
        max_log_value   = np.log10(max_value)

        if cal_switch:
            x = np.polyval(np.poly1d(coefficients), x)

        if epb_switch:
            y = [i * count for i, count in enumerate(spectrum)]
            gc= [i * count for i, count in enumerate(gc)]

        trace1 = go.Bar(
            x=x, 
            y=y, 
            marker={
                'color': 'black',
                'line': {
                    'color': 'black',  # Customize the border color here
                    'width': 0.5          # Customize the border width here
                }
            },
            width=1.0  # Set the width of the bars
        )  

        fig.add_trace(trace1)      

    else:
        filename    = 'no filename'
        prominence  = 0
        elapsed     = 0
        validPulseCount = 0

        y = [0]
        x = [0]

        trace1 = go.Bar(
            x=[0],  # Minimal data for the dummy trace
            y=[0],
            marker={
                'color': 'rgba(255,0,0,0.5)',  # Semi-transparent red marker
                'line': {
                    'color': 'rgba(255,0,0,0.5)',  # Customize the border color here
                    'width': 0.5                  # Customize the border width here
                }
            },
            width=1.0  # Set the width of the bars
        )  

    # Annotations
    peaks, fwhm = fn.peakfinder(y, prominence, peakfinder)
    num_peaks   = len(peaks)
    annotations = []
    lines       = []

    for i in range(num_peaks):
        peak_value  = peaks[i]
        counts      = y[peaks[i]]
        x_pos       = peaks[i]
        y_pos       = y[peaks[i]]
        y_pos_ann   = y_pos + int(y_pos/10)
        resolution  = (fwhm[i]/peaks[i])*100

        if y_pos_ann > (max_value * 0.9):
            y_pos_ann = int(y_pos_ann - max_value * 0.03)

        if cal_switch:
            peak_value  = np.polyval(np.poly1d(coefficients), peak_value)
            x_pos       = peak_value

        if log_switch:
            y_pos_ann = np.log10(y_pos) #if y_pos > 0 else 0
            #y_pos_ann = y_pos + 0.1

        if peakfinder > 0:
            annotations.append(
                dict(
                    x= x_pos,
                    y= y_pos_ann,
                    xref='x',
                    yref='y',
                    text=f'Y{counts}<br>X{peak_value:.1f}<br>{resolution:.1f}%',
                    align='center',
                    showarrow=True,
                    arrowhead=0,
                    ax=0,
                    ay=-40,
                )
            )

            lines.append(
                dict(
                    type='line',
                    x0=x_pos,
                    y0=0,
                    x1=x_pos,
                    y1=y_pos,
                    line=dict(
                        color='red',
                        width=1,
                        dash='dot'
                    )
                )
            )
                
    # Add annotations to the figure
    fig.update_layout(
        annotations=annotations,
        title={
            'text': f'{filename}<br>{time}<br>{validPulseCount} counts<br>{elapsed} seconds<br>{coincidence}',
            'x': 0.85,
            'y': 0.9,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 18, 'color': 'black'},
            },
        )

    # Add lines (shapes) to the figure
    fig.update_layout(shapes=lines)     

    # Histogram 2
    histogram2 = fn.get_path(f'{data_directory}/{filename2}.json')

    if os.path.exists(histogram2) and is_valid_json(histogram1):
        with open(histogram2, "r") as f:
            data_2 = json.load(f)

            schema_version = data_2["schemaVersion"]

            if schema_version  == "NPESv2":
                data_2 = data_2["data"][0] # This makes it backwards compatible

            numberOfChannels_2    = data_2["resultData"]["energySpectrum"]["numberOfChannels"]
            elapsed_2             = data_2["resultData"]["energySpectrum"]["measurementTime"]
            spectrum_2            = data_2["resultData"]["energySpectrum"]["spectrum"]
            coefficients_2        = data_2["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]

            if elapsed > 0 and elapsed_2 > 0:
                steps = (elapsed/elapsed_2)
            else:
                steps = 0.1    

            x2 = list(range(numberOfChannels_2))
            y2 = [int(n * steps) for n in spectrum_2]

            if cal_switch:
                x2 = np.polyval(np.poly1d(coefficients_2), x2)

            if log_switch:
                y2 = [x * 0.5 for x in y2]    

            if epb_switch:
                y2 = [i * n * steps for i, n in enumerate(spectrum_2)]

            trace2 = go.Scatter(
                x=x2, 
                y=y2, 
                marker={
                    'color': 'red',  # Semi-transparent red marker
                    'line': {
                        'color': 'red',  # Customize the border color here
                        'width': 0.5                  # Customize the border width here
                    }
                },
            )

    if sigma == 0:
        trace4 = {}
    else:    
        trace4 = go.Bar(
            x=x, 
            y=gc, 
            marker={
                'color': 'red',
                'line': {
                    'color': 'red',  # Customize the border color here
                    'width': 0.5        # Customize the border width here
                }
            },
            width=1.0  # Set the width of the bars
        )
        fig.add_trace(trace4)

    if compare_switch and os.path.exists(histogram2): 
        fig.add_trace(trace2)
        fig.update_layout(xaxis=dict(autorange=False))

    if difference_switch:
        y3 = [a - b for a, b in zip(y, y2)]
        trace3 = go.Bar(
            x=x, 
            y=y3, 
            marker={
                'color': 'green',
                'line': {
                    'color': 'green',  # Customize the border color here
                    'width': 0.5       # Customize the border width here
                }
            },
            width=1.0  # Set the width of the bars
        )
        fig = go.Figure(data=[trace3], layout=layout)
        fig.update_layout(yaxis=dict(autorange=True, range=[min(y3),max(y3)]))

    if not difference_switch:
        fig.update_layout(yaxis=dict(autorange=True))

    if log_switch:
        fig.update_layout(yaxis=dict(autorange=False, type='log', range=[0.1, max_log_value+0.3])) 
    else:
        fig.update_layout(yaxis=dict(autorange=True, type='linear', range=[0, max(y)]))

    # Check if user has selected a region of interest and calculate visible counts
    if relayoutData and 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
        x0, x1 = relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']
        visible_counts = sum(count for count, bin in zip(y, x) if x0 <= bin <= x1)
        if difference_switch:
            visible_counts = sum(count for count, bin in zip(y3, x) if x0 <= bin <= x1)
        fig.add_annotation(
            x=0.95, xref="paper",
            y=0.8, yref="paper",
            text=f"Selected counts {visible_counts}",
            showarrow=False,
            font=dict(size=14),
            align="center",
            bgcolor="white",
            bordercolor="lightgray",
            borderwidth=1
        )   
    return fig, f'{validPulseCount}', f'{elapsed}', f'cps {cps}'

# UPDATE SETTINGS callback
@app.callback(
    Output('polynomial', 'children'),
    [Input('bins', 'value'),
     Input('bin_size', 'value'),
     Input('max_counts', 'value'),
     Input('max_seconds', 'value'),
     Input('filename', 'value'),
     Input('filename2', 'value'),
     Input('threshold', 'value'),
     Input('tolerance', 'value'),
     Input('calib_bin_1', 'value'),
     Input('calib_bin_2', 'value'),
     Input('calib_bin_3', 'value'),
     Input('calib_e_1', 'value'),
     Input('calib_e_2', 'value'),
     Input('calib_e_3', 'value'),
     Input('peakfinder', 'value'),
     Input('sigma', 'value'),
     Input('t_interval', 'value'),
     Input('compression', 'value')]
)
def save_settings(*args):
    n_clicks = args[0]

    if n_clicks is None and not shproto.dispatcher.calibration_updated:
        raise PreventUpdate

    if shproto.dispatcher.calibration_updated:
        with shproto.dispatcher.calibration_lock:
            shproto.dispatcher.calibration_updated = 0
            x_bins_default = [512, 1024, 2048, 4096, 8192]
            x_bins = [value / args[17] for value in x_bins_default]
            polynomial_fn = np.poly1d(shproto.dispatcher.calibration[::-1])
            x_energies = [polynomial_fn(x_bins_default[0]), polynomial_fn(x_bins_default[1]), polynomial_fn(x_bins_default[2])]
    else:
        x_bins = [args[8], args[9], args[10]]
        x_energies = [args[11], args[12], args[13]]

    coefficients = np.polyfit(x_bins, x_energies, 2)
    polynomial_fn = np.poly1d(coefficients)
    database = fn.get_path(f'{data_directory}/.data_v2.db')
    conn = sql.connect(database)
    c = conn.cursor()

    query = f"""UPDATE settings SET 
                bins={args[0]}, 
                bin_size={args[1]}, 
                max_counts={args[2]}, 
                max_seconds={args[3]},
                name='{args[4]}', 
                comparison='{args[5]}',
                threshold={args[6]}, 
                tolerance={args[7]}, 
                calib_bin_1={x_bins[0]},
                calib_bin_2={x_bins[1]},
                calib_bin_3={x_bins[2]},
                calib_e_1={x_energies[0]},
                calib_e_2={x_energies[1]},
                calib_e_3={x_energies[2]},
                peakfinder={args[14]},
                sigma={args[15]},
                t_interval={args[16]},
                coeff_1={float(coefficients[0])},
                coeff_2={float(coefficients[1])},
                coeff_3={float(coefficients[2])},
                compression={args[17]}
                WHERE id=0;"""
    
    c.execute(query)
    conn.commit()

    logger.info(f'(Settings updated from tab2)')
    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'

# PLAY SOUND callback
@app.callback( Output('audio'       ,'children'),
                [Input('soundbyte'  ,'n_clicks')],
                [State('filename'   ,'value')])    
def play_sound(n_clicks, filename):
    if n_clicks is None:
        raise PreventUpdate

    if os.path.exists( f'{data_directory}/{filename}.wav'):
        asp.play_wav_file(filename)
        logger.info(f'Playing existing wav file: {filename}.wav')
        return
    else:
        spectrum = []
        histogram = fn.get_path(f'{data_directory}/{filename}.json')

        if os.path.exists(histogram):
                with open(histogram, "r") as f:
                    data     = json.load(f)
                    spectrum = data["data"][0]["resultData"]["energySpectrum"]["spectrum"]

        gc = fn.gaussian_correl(spectrum, 1)
        logger.info('calculating gaussian correlation')

        asp.make_wav_file(filename, gc)
        logger.info('Converting gaussian correlation to wav file')

        asp.play_wav_file(filename)
        logger.info(f'Playing soundfile {filename}.wav')
        return

# UPDATE CALIBRATION OF EXISTING SPECTRUM callback
@app.callback(
    Output('update_calib_message'   ,'children'),
    [Input('update_calib_button'    ,'n_clicks'),
    Input('filename'                ,'value')]
)
def update_current_calibration(n_clicks, filename):
    if n_clicks is None:
        raise PreventUpdate
    else:
        settings = fn.load_settings()
        coeff_1 = round(settings[18], 6)
        coeff_2 = round(settings[19], 6)
        coeff_3 = round(settings[20], 6)

        with write_lock:
            fn.update_coeff(filename, coeff_1, coeff_2, coeff_3)

        logger.info(f'Calibration updated tab2: {filename, coeff_1, coeff_2, coeff_3}')
        return f"Update {n_clicks}"

# MAX Dropdown callback
@app.callback(
    Output('cmd_text'       , 'children'),
    [Input('selected_cmd'   , 'value')],
    [State('tabs'            ,'value')]
)
def update_output(selected_cmd, active_tab):
    if active_tab != 'tab_2':  # only update the chart when "tab4" is active
        raise PreventUpdate

    logger.info(f'Command selected tab2: {selected_cmd}')
    try:
        shproto.dispatcher.process_03(selected_cmd)
        return f'Cmd: {selected_cmd}'
    except Exception as e:
        logging.error(f"Error in update_output tab2: {e}")
        return "An error occurred."

# Callback to publish spectrum to web with confirm message
@app.callback(
    Output("confirmation-modal", "is_open"),
    [Input("publish-button", "n_clicks"),
     Input("confirm-publish", "n_clicks"),
     Input("cancel-publish", "n_clicks")],
    [State("confirmation-modal", "is_open")]
)
def toggle_modal(open_button_clicks, confirm_button_clicks, cancel_publish_clicks, is_open):
    ctx = dash.callback_context

    if not ctx.triggered_id:
        button_id = None
    else:
        button_id = ctx.triggered_id.split(".")[0]

    if button_id == "publish-button" and open_button_clicks:
        return not is_open
    elif button_id in ["confirm-publish", "cancel-publish"]:
        return not is_open
    else:
        return is_open

@app.callback(
    Output("confirmation-output", "children"),
    [Input("confirm-publish", "n_clicks"),
     Input("cancel-publish", "n_clicks"),
     State("filename", "value")]
)
def display_confirmation_result(confirm_publish_clicks, cancel_publish_clicks, filename):
    ctx = dash.callback_context

    if not ctx.triggered_id:
        button_id = None
    else:
        button_id = ctx.triggered_id.split(".")[0]

    if button_id == "confirm-publish" and confirm_publish_clicks:
        logger.info(f'Confirm publish for: {filename}')
        response_message = fn.publish_spectrum(filename)
        logger.info(f'{filename} published')
        return f'{filename} \nPublished'
    elif button_id == "cancel-button" and cancel_publish_clicks:
        logger.info(f'Publish cancelled')
        return "You canceled!"
    else:
        return ""

# Update Spectrum Notes callback
@app.callback(
    Output('spec-notes-output', 'children'),
    [Input('spec-notes-input', 'value'),
     Input('filename', 'value')],
)
def update_spectrum_notes(spec_notes, filename):
    with write_lock:
        fn.update_json_notes(filename, spec_notes)
    logger.info(f'Spectrum notes updated {spec_notes}')
    return spec_notes

app.layout = show_tab2()

if __name__ == '__main__':
    app.run_server(debug=True)
