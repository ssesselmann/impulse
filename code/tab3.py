# tab3.py
import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import os
import json
import glob
import time
import numpy as np
import sqlite3 as sql
import dash_daq as daq
import audio_spectrum as asp

import subprocess
import serial.tools.list_ports
import threading
import logging

import shproto.dispatcher
import shproto.port as port

from dash import dcc, html
from dash.dependencies import Input, Output, State
from server import app
from dash.exceptions import PreventUpdate
from datetime import datetime

logger = logging.getLogger(__name__)

path = None
n_clicks = None
global_counts = 0

data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")

global cps_list

def show_tab3():

    # Get all filenames in data folder and its subfolders
    files = [os.path.relpath(file, data_directory).replace("\\", "/")
             for file in glob.glob(os.path.join(data_directory, "**", "*.json"), recursive=True)]
    # Add "i/" prefix to subfolder filenames for label and keep the original filename for value
    options = [{'label': "~ " + os.path.basename(file), 'value': file} if "i/" in file and file.endswith(".json") 
                else {'label': os.path.basename(file), 'value': file} for file in files]
    # Filter out filenames ending with "-cps"
    options = [opt for opt in options if not opt['value'].endswith("-cps.json")]
    # Sort options alphabetically by label
    options_sorted = sorted(options, key=lambda x: x['label'])

    for file in options_sorted:
        file['label'] = file['label'].replace('.json', '')
        file['value'] = file['value'].replace('.json', '')

    database = fn.get_path(f'{data_directory}/.data_v2.db')
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
    max_seconds     = settings[26]
    t_interval      = settings[27]
    compression     = settings[29]

    if device >= 100:
        serial          = 'block'
        audio           = 'none'
    else:
        serial          = 'none'
        audio           = 'block'

    refresh_rate = t_interval * 1000

    html_tab3 = html.Div(id='tab3', children=[
        html.Div(id='polynomial_3d', children=''),
        html.Div(id='bar_chart_div_3d', children=[
            dcc.Graph(id='chart_3d', figure={},),
            dcc.Interval(id='interval-component', interval= refresh_rate, n_intervals=0)  # Refresh rate 1s.
            ]),

        html.Div(id='t2_filler_div', children=''),
        html.Div(id='t2_setting_div1', children=[
            html.Button('START', id='start_3d'),    #Start button
            html.Div(id='counts_3d', children= ''),
            html.Div(id='start_text_3d' , children =''),
            html.Div(['Max Counts', dcc.Input(id='max_counts', type='number', step=1000, readOnly=False, value=max_counts )]),
            ]),

        html.Div(id='t2_setting_div2', children=[            
            html.Button('STOP', id='stop_3d'),
            html.Div(id='elapsed_3d', children= '' ),
            html.Div(['Max Seconds', dcc.Input(id='max_seconds', type='number', step=60,  readOnly=False, value=max_seconds )]),
            html.Div(id='cps_3d', children=''),
            html.Div(id='stop_text_3d', children= ''),
            ]),

        html.Div(id='t2_setting_div3', children=[
            html.Div(['File name:', dcc.Input(id='filename' ,type='text' ,value=filename )]),
            html.Div(['Number of bins:', dcc.Input(id='bins'        ,type='number'  ,value=bins )],
                style={'display': audio}
                ),
            html.Div(['Bin size      :', dcc.Input(id='bin_size'    ,type='number'  ,value=bin_size )],
                style={'display': audio}
                ),
            html.Div(['Resolution:', dcc.Dropdown(id='compression',
                    options=[
                        {'label': '512 Bins ', 'value': '16'},
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
            ]), 

        html.Div(id='t2_setting_div4', children=[
            
            html.Div(['LLD Threshold:', dcc.Input(id='threshold', type='number', step=10, value=threshold )],
                style={'display': audio}
                ),
            html.Div(['Shape Tolerance:', dcc.Input(id='tolerance', type='number', step=1000,  value=tolerance )],
                style={'display': audio}
                ),
            html.Div(['Time Interval Sec.', dcc.Input(id='t_interval', type='number', step=1,  readOnly=False, value=t_interval )],
                ),
            ]),

        html.Div(id='t2_setting_div5', children=[
            ]),

        html.Div(id='t2_setting_div6'    , children=[
            html.Div(['Energy by bin'  , daq.BooleanSwitch(id='epb_switch',on=False, color='purple',)]),
            html.Div(['Show log(y)'     , daq.BooleanSwitch(id='log_switch',on=False, color='purple',)]),
            html.Div(['Calibration'    , daq.BooleanSwitch(id='cal_switch',on=False, color='purple',)]),
            ]), 

        html.Div(id='t2_setting_div7', children=[
            html.Div('Calibration Bins'),
            html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1)),
            html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2)),
            html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3)),
            ]),

        html.Div(id='t2_setting_div8', children=[
            html.Div('Energies'),
            html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1)),
            html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2)),
            html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3)),            
            ]),

        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        
        html.Div(id='subfooter', children=[
            ]),

        ]) # End of tab 3 render

    return html_tab3

#----START---------------------------------

@app.callback(Output('start_text_3d'   , 'children'),
              [Input('start_3d'        , 'n_clicks')], 
              [State('filename'        , 'value'),
              State('compression'      , 'value'),
              State('t_interval'       , 'value')])

def update_output(n_clicks, filename, compression, t_interval):

    if n_clicks == None:
        raise PreventUpdate

    sdl = fn.get_serial_device_list()

    if sdl:
        try:

            shproto.dispatcher.spec_stopflag = 0
            dispatcher = threading.Thread(target=shproto.dispatcher.start)
            dispatcher.start()

            time.sleep(1)

            # Reset spectrum
            command = '-rst'
            shproto.dispatcher.process_03(command)
            logger.info(f'tab2 sends command {command}')

            time.sleep(1)

            # Start multichannel analyser
            command = '-sta'
            shproto.dispatcher.process_03(command)
            logger.info(f'tab2 sends command {command}')

            time.sleep(1)

            shproto.dispatcher.process_02(filename, compression, t_interval)
            logger.info(f'dispatcher.process_01 Started')

            time.sleep(1)

        except Exception as e:

            logger.error(f'update_output() on tab3 failed: {e}')
            return f"Error: {str(e)}"
    else:
        
        fn.start_recording(3)

        logger.info('Audio Codec Recording Started')

        return 
#----STOP------------------------------------------------------------

@app.callback( Output('stop_text_3d'  ,'children'),
                [Input('stop_3d'      ,'n_clicks')])

def update_output(n_clicks):

    if n_clicks is None:
        raise PreventUpdate

    sdl = fn.get_serial_device_list()

    if sdl:
        # Stop Spectrum 
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()

        time.sleep(0.1)

        logger.info('Stop command sent from (tab2)')

    else:
        fn.stop_recording()
        return " "

#----RENDER CHART-----------------------------------------------------------

@app.callback([ Output('chart_3d'           ,'figure'), 
                Output('counts_3d'          ,'children'),
                Output('elapsed_3d'         ,'children'),
                Output('cps_3d'             ,'children')],
               [Input('interval-component'  ,'n_intervals'), 
                Input('filename'            ,'value'), 
                Input('epb_switch'          ,'on'),
                Input('log_switch'          ,'on'),
                Input('cal_switch'          ,'on'),
                Input('t_interval'          ,'value')], prevent_initial_call=True
                )


def update_graph(n, filename, epb_switch, log_switch, cal_switch, t_interval):
    
    if n is None:
        raise PreventUpdate

    if log_switch == True:
        axis_type = 'log'

    else:
        axis_type = 'linear'        
    
    global global_counts
    
    histogram3 = fn.get_path(f'{data_directory}/{filename}_3d.json')

    now = datetime.now()
    time = now.strftime("%A %d %B %Y")

    title_text = "<b>{}</b><br><span style='fontSize: 12px'>{}</span>".format(filename, time)

    layout = go.Layout(
            uirevision='nochange',
            height=550,
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis=dict(title='Energy(x)'),
                yaxis=dict(title='Seconds(y)'),
                zaxis=dict(title='Counts(z)', type= axis_type),
            ),
            title={
                'text': title_text,
                'x': 0.9,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'},
                }
        )

    if os.path.exists(histogram3):
        with open(histogram3, "r") as f:
            data = json.load(f)

            numberOfChannels = data["resultData"]["energySpectrum"]["numberOfChannels"]
            validPulseCount = data["resultData"]["energySpectrum"]["validPulseCount"]
            elapsed = data["resultData"]["energySpectrum"]["measurementTime"]
            polynomialOrder = data["resultData"]["energySpectrum"]["energyCalibration"]["polynomialOrder"]
            coefficients = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
            spectra = data["resultData"]["energySpectrum"]["spectrum"]
            coefficients = coefficients[::-1]  # Reverse order

        if elapsed == 0:
            global_cps = 0  

        else:
            global_cps = int((validPulseCount - global_counts)/t_interval)
            global_counts = validPulseCount 

        x = list(range(numberOfChannels))
        y = spectra

        if epb_switch == True:
            # Multiply each number by its index
            y = [[num * index for index, num in enumerate(inner_list)] for inner_list in spectra]

        if cal_switch == True:
                x = np.polyval(np.poly1d(coefficients), x)


        traces = []

        for i in range(len(y)):
            z = [i] * len(y)

            trace = {
                'type': 'scatter3d',
                'showlegend': False  # Hide the trace index in legend
            }

            traces.append(trace)

        surface_trace = {
            'type': 'surface',
            'x': x,
            'y': list(range(len(y))),
            'z': y,
            'colorscale': 'Rainbow',
            'showlegend': False  # Hide the trace index in legend
        }

        traces.append(surface_trace)

        fig = go.Figure(data=traces, layout=layout)

        return fig, f'{validPulseCount}', f'{elapsed}', f'cps {global_cps}'

    else:
        
        data = [
            go.Scatter3d(
                x=[0],  # x-coordinate of the data point
                y=[0],  # y-coordinate of the data point
                z=[0],  # z-coordinate of the data point
                mode='markers',
                marker=dict(
                    size=5,
                    color='blue'
                )
            )
        ]

        fig = go.Figure(data=data, layout=layout)  

        return fig, 0, 0, 0

#--------UPDATE SETTINGS------------------------------------------------------------------------------------------
@app.callback( Output('polynomial_3d'   ,'children'),
               [Input('bins'            ,'value'),
                Input('bin_size'        ,'value'),
                Input('max_counts'      ,'value'),
                Input('max_seconds'     ,'value'),
                Input('t_interval'      ,'value'),
                Input('filename'        ,'value'),
                Input('threshold'       ,'value'),
                Input('tolerance'       ,'value'),
                Input('calib_bin_1'     ,'value'),
                Input('calib_bin_2'     ,'value'),
                Input('calib_bin_3'     ,'value'),
                Input('calib_e_1'       ,'value'),
                Input('calib_e_2'       ,'value'),
                Input('calib_e_3'       ,'value'),
                ])  

def save_settings(bins, bin_size, max_counts, max_seconds, t_interval, filename, threshold, tolerance, calib_bin_1, calib_bin_2, calib_bin_3, calib_e_1, calib_e_2, calib_e_3):
    
    database = fn.get_path(f'{data_directory}/.data_v2.db')

    conn = sql.connect(database)
    c = conn.cursor()

    query = f"""UPDATE settings SET 
                    bins={bins}, 
                    bin_size={bin_size}, 
                    max_counts={max_counts},
                    max_seconds={max_seconds}, 
                    name='{filename}', 
                    threshold={threshold}, 
                    tolerance={tolerance}, 
                    calib_bin_1={calib_bin_1},
                    calib_bin_2={calib_bin_2},
                    calib_bin_3={calib_bin_3},
                    calib_e_1={calib_e_1},
                    calib_e_2={calib_e_2},
                    calib_e_3={calib_e_3},
                    t_interval={t_interval}
                    WHERE id=0;"""

    c.execute(query)
    conn.commit()

    x_bins        = [calib_bin_1, calib_bin_2, calib_bin_3]
    x_energies    = [calib_e_1, calib_e_2, calib_e_3]

    coefficients  = np.polyfit(x_bins, x_energies, 2)
    polynomial_fn = np.poly1d(coefficients)


    conn  = sql.connect(database)
    c     = conn.cursor()

    query = f"""UPDATE settings SET 
                    coeff_1={float(coefficients[0])},
                    coeff_2={float(coefficients[1])},
                    coeff_3={float(coefficients[2])}
                    WHERE id=0;"""
    
    c.execute(query)
    conn.commit()

    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'

#------UPDATE CALIBRATION OF EXISTING SPECTRUM-------------------

@app.callback(
    Output('3d_update_calib_message','children'),
    [Input('update_calib_button' ,'n_clicks'),
    Input('filename'         ,'value')
    ])

def update_current_calibration(n_clicks, filename):
    if n_clicks is None:
        raise PreventUpdate
    else:
        settings        = fn.load_settings()
        coeff_1         = round(settings[18],6)
        coeff_2         = round(settings[19],6)
        coeff_3         = round(settings[20],6)

        # Update the calibration coefficients using the specified values
        fn.update_coeff(filename, coeff_1, coeff_2, coeff_3)
        # Return a message indicating that the update was successful
        return f"Update {n_clicks}"