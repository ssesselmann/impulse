# tab2.py
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

from dash import dcc, html, Input, Output, State, callback, Dash
from dash.dependencies import Input, Output, State
from server import app
from dash.exceptions import PreventUpdate
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

path            = None
n_clicks        = None
commands        = None
cmd             = None
schemaVersion   = None
device          = None
global_counts   = 0
global_cps      = 0
stop_event      = threading.Event()
data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")
sdl             = fn.get_serial_device_list()

def show_tab2():
    global global_counts
    global global_cps
    global cps_list
    global device

    # Get all filenames in data folder and its subfolders
    files = [os.path.relpath(file, data_directory).replace("\\", "/")
             for file in glob.glob(os.path.join(data_directory, "**", "*.json"), recursive=True)]
    # Add "i/" prefix to subfolder filenames for label and keep the original filename for value
    options = [{'label': "~ " + os.path.basename(file), 'value': file} if "i/" in file and file.endswith(".json") 
                else {'label': os.path.basename(file), 'value': file} for file in files]
    # Filter out filenames ending with "-cps"
    options = [opt for opt in options if not opt['value'].endswith("-cps.json")]
    # Filter out filenames ending with "-3d"
    options = [opt for opt in options if not opt['value'].endswith("_3d.json")]
    # Sort options alphabetically by label
    options_sorted = sorted(options, key=lambda x: x['label'])

    for file in options_sorted:
        file['label'] = file['label'].replace('.json', '')
        file['value'] = file['value'].replace('.json', '')

    database = fn.get_path(f'{data_directory}/.data.db')
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
        html.Div(id='bar_chart_div', # Histogram Chart
            children=[
                dcc.Graph(id='bar-chart', figure={},),
                dcc.Interval(id='interval-component', interval=bins, n_intervals=0) # Refresh rate 1s.
            ]),

        html.Div(id='t2_filler_div', children=''),
        #Start button
        html.Div(id='t2_setting_div1', children=[
            html.Button('START', id='start'),
            html.Div(id='start_text', children=''),
            html.Div(id='counts', children= ''),
            html.Div(''),
            html.Div(['Max Counts', dcc.Input(id='max_counts', type='number', step=bins,  readOnly=False, value=max_counts, className='input',style={'background-color': counts_warning} )]),
            ]),

        html.Div(id='t2_setting_div2', children=[            
            html.Button('STOP', id='stop'), 
            html.Div(id='stop_text', children=''),
            html.Div(id='elapsed', children= '' ),
            html.Div(['Max Seconds', dcc.Input(id='max_seconds', type='number', step=60,  readOnly=False, value=max_seconds, className='input', style={'background-color': seconds_warning} )]),
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

                html.Div(['File name:', dcc.Input(id='filename', type='text', value=filename, className='input')]),
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
                    {'label': '----Gain--------'  , 'value': ''},
                    {'label': 'Approx 580 Volts'  , 'value': '-U040'},
                    {'label': 'Approx 596 Volts'  , 'value': '-U048'},
                    {'label': 'Approx 612 Volts'  , 'value': '-U056'},
                    {'label': 'Approx 628 Volts'  , 'value': '-U064'},
                    {'label': 'Approx 644 Volts'  , 'value': '-U072'},
                    {'label': 'Approx 660 Volts'  , 'value': '-U080'},
                    {'label': 'Approx 676 Volts'  , 'value': '-U088'},
                    {'label': 'Approx 692 Volts'  , 'value': '-U096'},
                    {'label': 'Approx 708 Volts'  , 'value': '-U104'},
                    {'label': 'Approx 724 Volts'  , 'value': '-U112'},
                    {'label': 'Approx 740 Volts'  , 'value': '-U120'},
                    {'label': 'Approx 756 Volts'  , 'value': '-U128'},
                    {'label': 'Approx 772 Volts'  , 'value': '-U136'},
                    {'label': 'Approx 788 Volts'  , 'value': '-U144'},
                    {'label': 'Approx 804 Volts'  , 'value': '-U152'},
                    {'label': 'Approx 820 Volts'  , 'value': '-U160'},
                    {'label': 'Approx 836 Volts'  , 'value': '-U168'},
                    {'label': 'Approx 852 Volts'  , 'value': '-U176'},
                    {'label': 'Approx 868 Volts'  , 'value': '-U184'},
                    {'label': 'Approx 884 Volts'  , 'value': '-U192'},
                    {'label': 'Approx 900 Volts'  , 'value': '-U200'},
                    {'label': 'Approx 916 Volts'  , 'value': '-U208'},
                    {'label': 'Approx 932 Volts'  , 'value': '-U216'},
                    {'label': 'Approx 948 Volts'  , 'value': '-U224'},
                    {'label': 'Approx 964 Volts'  , 'value': '-U232'},
                    {'label': 'Approx 980 Volts'  , 'value': '-U240'},
                    {'label': 'Approx 996 Volts'  , 'value': '-U248'},
                    {'label': 'Approx 1012 Volts' , 'value': '-U256'}

                ],
                placeholder='Select command',
                value=commands[0] if commands else None, # Check if commands is not None before accessing its elements
                className='dropdown',
            )], style={'display':serial}),  

            html.Div(id='cmd_text', children='', style={'display': 'none'}),
            html.Div(['LLD Threshold:'      , dcc.Input(id='threshold'  , type='number', value=threshold, className='input')], style={'display':audio}),
            html.Div(['Shape Tolerance:'    , dcc.Input(id='tolerance'  , type='number', value=tolerance, className='input' )], style={'display':audio}),
            html.Div(['Update Interval(s)'  , dcc.Input(id='t_interval' , type='number', step=1,  readOnly=False, value=t_interval, className='input' )], style={'display':audio}),

        ],style={'width':'10%', } 
        ),

        # ------------------------------------------------------
        
        html.Div(id='t2_setting_div5', children=[
            html.Div('Select Comparison'),
            html.Div(dcc.Dropdown(
                    id='filename2',
                    options=options_sorted,
                    placeholder='Select comparison',
                    value=filename2,
                    className='dropdown',
                    )),

            html.Div(['Show Comparison'      , daq.BooleanSwitch(id='compare_switch',on=False, color='purple',)]),
            html.Div(['Subtract Comparison'  , daq.BooleanSwitch(id='difference_switch',on=False, color='purple',)]),

            ]),

        html.Div(id='t2_setting_div6'   , children=[
            html.Div(['Energy by bin'   , daq.BooleanSwitch(id='epb_switch',on=False, color='purple',)]),
            html.Div(['Show log(y)'     , daq.BooleanSwitch(id='log_switch',on=False, color='purple',)]),
            html.Div(['Calibration'     , daq.BooleanSwitch(id='cal_switch',on=False, color='purple',)]),
            ]), 

        html.Div(id='t2_setting_div7', children=[
            html.Button('Gaussian sound <)' , id='soundbyte'),
            html.Div(id='audio', children=''),
            html.Button('Update calibration', id='update_calib_button'),
            html.Div(id='update_calib_message', children='')
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
            
            ]),

        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        
        html.Div(id='subfooter', children=[
            ]),

    ]) # End of tab 2 render

    return html_tab2

#----START---------------------------------

@app.callback(Output('start_text'   , 'children'),
              [Input('start'        , 'n_clicks')], 
              [State('filename'     , 'value'),
                State('compression' , 'value')
                ])

def update_output(n_clicks, filename, compression):

    if n_clicks == None:
        raise PreventUpdate

    logger.debug('Start on tab2 clicked')

    sdl = fn.get_serial_device_list()

    if sdl:
        try:
            logger.debug('Serial ports discovered')

            shproto.dispatcher.spec_stopflag = 0
            dispatcher = threading.Thread(target=shproto.dispatcher.start)
            dispatcher.start()

            time.sleep(1)

            # Reset spectrum
            command = '-rst'
            shproto.dispatcher.process_03(command)
            logger.debug(f'tab2 sends command {command}')

            time.sleep(1)

            # Start multichannel analyser
            command = '-sta'
            shproto.dispatcher.process_03(command)
            logger.debug(f'tab2 sends command {command}')

            time.sleep(1)

            shproto.dispatcher.process_01(filename, compression, "GS-MAX or ATOM-NANO")
            logger.debug(f'dispatcher.process_01 Started')

            time.sleep(1)

        except Exception as e:
            return f"Error: {str(e)}"
    else:
        
        fn.start_recording(2)

        logger.debug('Audio Codec Recording Started')

        return 
#----STOP------------------------------------------------------------

@app.callback( Output('stop_text'  ,'children'),
                [Input('stop'      ,'n_clicks'),
                Input('filename'   , 'value'),
                ])

def update_output(n_clicks, filename):

    if n_clicks is None:
        raise PreventUpdate

    sdl = fn.get_serial_device_list()

    if sdl:
        # Stop Spectrum 
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()

        time.sleep(0.1)

        logger.debug('Stop command sent from (tab2)')

    else:

        fn.stop_recording()

        logger.debug('Audio Codec Recording Stopped')

        return 

#-------UPDATE GRAPH---------------------------------------------------------

@app.callback([ Output('bar-chart'          ,'figure'), 
                Output('counts'             ,'children'),
                Output('elapsed'            ,'children'),
                Output('cps'                ,'children')],
               [Input('interval-component'  ,'n_intervals'), 
                Input('filename'            ,'value'), 
                Input('epb_switch'          ,'on'),
                Input('log_switch'          ,'on'),
                Input('cal_switch'          ,'on'),
                Input('filename2'           ,'value'),
                Input('compare_switch'      ,'on'),
                Input('difference_switch'   ,'on'),
                Input('peakfinder'          ,'value'),
                Input('sigma'               ,'value')
                ])

def update_graph(n, filename, epb_switch, log_switch, cal_switch, filename2, compare_switch, difference_switch, peakfinder, sigma):

    global global_counts
    histogram1 = fn.get_path(f'{data_directory}/{filename}.json')
    histogram2 = fn.get_path(f'{data_directory}/{filename2}.json')

    if os.path.exists(histogram1):
        with open(histogram1, "r") as f:

            data = json.load(f)

            schemaVersion       = data["schemaVersion"]

            if schemaVersion  == "NPESv2":

                data = data["data"][0] # This makes it backwards compatible

            numberOfChannels    = data["resultData"]["energySpectrum"]["numberOfChannels"]
            validPulseCount     = data["resultData"]["energySpectrum"]["validPulseCount"]
            elapsed             = data["resultData"]["energySpectrum"]["measurementTime"]
            polynomialOrder     = data["resultData"]["energySpectrum"]["energyCalibration"]["polynomialOrder"]
            coefficients        = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
            spectrum            = data["resultData"]["energySpectrum"]["spectrum"]
            coefficients        = coefficients[::-1] # Revese order   

            now = datetime.now()
            time = now.strftime("%A %d %B %Y")

            mu = 0
            prominence = 0.5

            if sigma == 0:
                gc = []
            else:    
                gc = fn.gaussian_correl(spectrum, sigma)
            

            if elapsed == 0:
                cps = 0  
            else:
                cps = validPulseCount - global_counts
                global_counts = validPulseCount  
     
            x               = list(range(numberOfChannels))
            y               = spectrum
            max_value       = np.max(y)
            if max_value    == 0:
                max_value   = 10
            
            max_log_value   = np.log10(max_value)

            if cal_switch == True:
                x = np.polyval(np.poly1d(coefficients), x)

            if epb_switch == True:
                y = [i * count for i, count in enumerate(spectrum)]
                gc= [i * count for i, count in enumerate(gc)]

            trace1 = go.Scatter(
                x=x, 
                y=y, 
                mode='lines+markers', 
                fill='tozeroy' ,  
                marker={'color': 'darkblue', 'size':3}, 
                line={'width':1})

  #-------------------annotations-----------------------------------------------          
            peaks, fwhm = fn.peakfinder(y, prominence, peakfinder)
            num_peaks   = len(peaks)
            annotations = []
            lines       = []

            for i in range(num_peaks):
                peak_value  = peaks[i]
                counts      = y[peaks[i]]
                x_pos       = peaks[i]
                y_pos       = y[peaks[i]]
                y_pos_ann   = y_pos + 10
                resolution  = (fwhm[i]/peaks[i])*100

                if y_pos_ann > (max_value * 0.9):
                    y_pos_ann = int(y_pos_ann - max_value * 0.03)

                if cal_switch == True:
                    peak_value  = np.polyval(np.poly1d(coefficients), peak_value)
                    x_pos       = peak_value

                if log_switch == True:
                    y_pos = np.log10(y_pos)
                    y_pos_ann = y_pos + 0.02

                if peakfinder != 0:
                    annotations.append(
                        dict(
                            x= x_pos,
                            y= y_pos_ann,
                            xref='x',
                            yref='y',
                            text=f'cts: {counts}<br>bin: {peak_value:.1f}<br>{resolution:.1f}%',
                            showarrow=True,
                            arrowhead=1,
                            ax=0,
                            ay=-40
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
                            color='white',
                            width=1,
                            dash='dot'
                        )
                    )
                )

            title_text = "<b>{}</b><br><span style='font-size: 12px'>{}</span>".format(filename, time)

            layout = go.Layout(
                paper_bgcolor = 'white', 
                plot_bgcolor = 'white',
                title={
                'text': title_text,
                'x': 0.9,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'},
                },
                height  =450, 
                margin_t=40,
                margin_b=0,
                margin_l=0,
                margin_r=0,
                autosize=True,
                #xaxis=dict(dtick=50, tickangle = 90, range =[0, max(x)]),
                yaxis=dict(autorange=True),
                annotations=annotations,
                shapes=lines,
                uirevision="Don't change",
                )
#---------------Histrogram2 ---------------------------------------------------------------------------

            if os.path.exists(histogram2):
                with open(histogram2, "r") as f:

                    data_2 = json.load(f)

                    schema_version = data_2["schemaVersion"]

                    if schema_version  == "NPESv2":

                        data_2 = data_2["data"][0] # This makes it backwards compatible

                    numberOfChannels_2    = data_2["resultData"]["energySpectrum"]["numberOfChannels"]
                    elapsed_2             = data_2["resultData"]["energySpectrum"]["measurementTime"]
                    spectrum_2            = data_2["resultData"]["energySpectrum"]["spectrum"]
 
                    if elapsed > 0:
                        steps = (elapsed/elapsed_2)
                    else:
                        steps = 0.1    

                    x2 = list(range(numberOfChannels_2))
                    y2 = [int(n * steps) for n in spectrum_2]

                    if cal_switch == True:
                        x2 = np.polyval(np.poly1d(coefficients), x2)

                    if epb_switch == True:
                        y2 = [i * n * steps for i, n in enumerate(spectrum_2)]

                    trace2 = go.Scatter(
                        x=x2, 
                        y=y2, 
                        mode='lines+markers',  
                        marker={'color': 'red', 'size':1}, 
                        line={'width':2})

        if sigma == 0:
            trace4 = {}
        else:    
            trace4 = go.Scatter(
                x=x, 
                y=gc, 
                mode='lines+markers',  
                marker={'color': 'yellow', 'size':1}, 
                line={'width':2})
    
        if compare_switch == False:
            fig = go.Figure(data=[trace1, trace4], layout=layout)

        if compare_switch == True: 
            fig = go.Figure(data=[trace1, trace2], layout=layout) 

        if difference_switch == True:
            y3 = [a - b for a, b in zip(y, y2)]
            trace3 = go.Scatter(
                            x=x, 
                            y=y3, 
                            mode='lines+markers', 
                            fill='tozeroy',  
                            marker={'color': 'green', 'size':3}, 
                            line={'width':1}
                            )

            fig = go.Figure(data=[trace3], layout=layout)

            fig.update_layout(yaxis=dict(autorange=True, range=[min(y3),max(y3)]))

        if difference_switch == False:
            fig.update_layout(yaxis=dict(autorange=True))

        if log_switch == True:
            fig.update_layout(yaxis=dict(autorange=False, type='log', range=[0, max_log_value+0.3])) 

        return fig, f'{validPulseCount}', f'{elapsed}', f'cps {cps}'

    else:
        layout = go.Layout(
                paper_bgcolor = 'white', 
                plot_bgcolor = 'white',
                title={
                'text': filename,
                'x': 0.9,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
                },
                height  =450, 
                autosize=True,
                #xaxis=dict(dtick=50, tickangle = 90, range =[0, 100]),
                xaxis=dict(autorange=True),
                yaxis=dict(autorange=True),
                uirevision="Don't change",
                )
        return go.Figure(data=[], layout=layout), 0, 0, 0

#--------UPDATE SETTINGS------------------------------------------------------------------------------------------
@app.callback( Output('polynomial'      ,'children'),
                [
                Input('bins'            ,'value'), # [0]
                Input('bin_size'        ,'value'), # [1]
                Input('max_counts'      ,'value'), # [2]
                Input('max_seconds'     ,'value'), # [3]
                Input('filename'        ,'value'), # [4]
                Input('filename2'       ,'value'), # [5]
                Input('threshold'       ,'value'), # [6]
                Input('tolerance'       ,'value'), # [7]
                Input('calib_bin_1'     ,'value'), # [8]
                Input('calib_bin_2'     ,'value'), # [9]
                Input('calib_bin_3'     ,'value'), # [10]
                Input('calib_e_1'       ,'value'), # [11]
                Input('calib_e_2'       ,'value'), # [12]
                Input('calib_e_3'       ,'value'), # [13]
                Input('peakfinder'      ,'value'), # [14]
                Input('sigma'           ,'value'), # [15]
                Input('t_interval'      ,'value'), # [16]
                Input('compression'     ,'value')  # [17]
                ])  

def save_settings(*args):

    n_clicks = args[0]
    if n_clicks is None:
        raise PreventUpdate

    x_bins          = [args[8], args[9], args[10]]
    x_energies      = [args[11], args[12], args[13]]
    coefficients    = np.polyfit(x_bins, x_energies, 2)
    polynomial_fn   = np.poly1d(coefficients)
    
    database        = fn.get_path(f'{data_directory}/.data.db')
    conn            = sql.connect(database)
    c               = conn.cursor()

    query = f"""UPDATE settings SET 
                    bins={args[0]}, 
                    bin_size={args[1]}, 
                    max_counts={args[2]}, 
                    max_seconds={args[3]},
                    name='{args[4]}', 
                    comparison='{args[5]}',
                    threshold={args[6]}, 
                    tolerance={args[7]}, 
                    calib_bin_1={args[8]},
                    calib_bin_2={args[9]},
                    calib_bin_3={args[10]},
                    calib_e_1={args[11]},
                    calib_e_2={args[12]},
                    calib_e_3={args[13]},
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

    logger.debug(f'Settings Saved (tab2) {query}')

    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'

#-------PLAY SOUND ---------------------------------------------

@app.callback( Output('audio'       ,'children'),
                [Input('soundbyte'  ,'n_clicks'),
                Input('filename2'   ,'value')])    


def play_sound(n_clicks, filename2):

    if n_clicks is None:
        raise PreventUpdate
    else:
        spectrum_2 = []
        histogram2 = fn.get_path(f'{data_directory}/{filename2}.json')

        if os.path.exists(histogram2):
                with open(histogram2, "r") as f:
                    data_2     = json.load(f)
                    spectrum_2 = data_2["resultData"]["energySpectrum"]["spectrum"]

        gc = fn.gaussian_correl(spectrum_2, 1)

        asp.make_wav_file(filename2, gc)

        asp.play_wav_file(filename2)

    logger.debug(f'Play Gaussian Sound: {filename2}')
        
    return

#------UPDATE CALIBRATION OF EXISTING SPECTRUM-------------------

@app.callback(
    Output('update_calib_message'   ,'children'),
    [Input('update_calib_button'    ,'n_clicks'),
    Input('filename'                ,'value')
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

        logger.debug(f'Calibration updated (tab2): {filename, coeff_1, coeff_2, coeff_3}')

        # Return a message indicating that the update was successful
        return f"Update {n_clicks}"

# ------MAX Dropdown callback ---------------------------

@app.callback(
    Output('cmd_text'       , 'children'),
    [Input('selected_cmd'   , 'value')],
    [State('tabs'            ,'value')]
    )

def update_output(selected_cmd, active_tab):

    if active_tab != 'tab2':  # only update the chart when "tab4" is active
        raise PreventUpdate

    logger.debug(f'Command selected (tab2): {selected_cmd}')

    try:
        shproto.dispatcher.process_03(selected_cmd)

        return f'Command: {selected_cmd}'

    except Exception as e:

        logging.exception(f"Error in update_output: {e}")

        return "An error occurred."
