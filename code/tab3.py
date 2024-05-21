import os
import json
import glob
import time
import numpy as np
import sqlite3 as sql
import threading
import logging
from datetime import datetime

import dash
import dash_daq as daq
import plotly.graph_objs as go
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from server import app

import functions as fn
import pulsecatcher as pc
import audio_spectrum as asp
import subprocess
import serial.tools.list_ports
import dash_bootstrap_components as dbc
import shproto.dispatcher
import shproto.port as port

logger = logging.getLogger(__name__)

device = None
mean_cps = None
cps = None

data_directory = os.path.join(os.path.expanduser("~"), "impulse_data")

def show_tab3():
    global device

    # Load available JSON files
    files = [os.path.relpath(file, data_directory).replace("\\", "/")
             for file in glob.glob(os.path.join(data_directory, "**", "*.json"), recursive=True)]
    options = [{'label': "~ " + os.path.basename(file), 'value': file} if "i/" in file and file.endswith(".json")
               else {'label': os.path.basename(file), 'value': file} for file in files]
    options = [opt for opt in options if not opt['value'].endswith("-cps.json")]
    options_sorted = sorted(options, key=lambda x: x['label'])

    for file in options_sorted:
        file['label'] = file['label'].replace('.json', '')
        file['value'] = file['value'].replace('.json', '')

    # Load settings from database
    database = fn.get_path(f'{data_directory}/.data_v2.db')
    conn = sql.connect(database)
    c = conn.cursor()
    query = "SELECT * FROM settings"
    c.execute(query)
    settings = c.fetchall()[0]

    filename = settings[1]
    device = settings[2]
    sample_rate = settings[3]
    chunk_size = settings[4]
    threshold = settings[5]
    tolerance = settings[6]
    bins = settings[7]
    bin_size = settings[8]
    max_counts = settings[9]
    shapestring = settings[10]
    sample_length = settings[11]
    calib_bin_1 = settings[12]
    calib_bin_2 = settings[13]
    calib_bin_3 = settings[14]
    calib_e_1 = settings[15]
    calib_e_2 = settings[16]
    calib_e_3 = settings[17]
    coeff_1 = settings[18]
    coeff_2 = settings[19]
    coeff_3 = settings[20]
    max_seconds = settings[26]
    t_interval = settings[27]
    compression = settings[29]

    if device >= 100:
        serial = 'block'
        audio = 'none'
    else:
        serial = 'none'
        audio = 'block'

    refresh_rate = t_interval * 1000

    # Render tab layout
    html_tab3 = html.Div(id='tab3', children=[
        html.Div(id='polynomial_3d', children=''),
        html.Div(id='bar_chart_div_3d', children=[
            dcc.Graph(id='chart_3d', figure={}),
            dcc.Interval(id='interval-component', interval=refresh_rate, n_intervals=0)
        ]),
        html.Div(id='t2_filler_div', children=''),
        html.Div(id='t2_setting_div1', children=[
            html.Button('START', id='start_3d'),
            html.Div(id='counts_3d', children=''),
            html.Div(id='start_text_3d', children=''),
            html.Div(['Max Counts', dcc.Input(id='max_counts', type='number', step=1000, readOnly=False, value=max_counts)]),
        ]),
        html.Div(id='t2_setting_div2', children=[
            html.Button('STOP', id='stop_3d'),
            html.Div(id='elapsed_3d', children=''),
            html.Div(['Max Seconds', dcc.Input(id='max_seconds', type='number', step=60, readOnly=False, value=max_seconds)]),
            html.Div(id='cps_3d', children=''),
            html.Div(id='stop_text_3d', children=''),
        ]),
        html.Div(id='t2_setting_div3', children=[
            html.Div(['Number of bins:', dcc.Input(id='bins', type='number', value=bins)], style={'display': audio}),
            html.Div(['Bin size:', dcc.Input(id='bin_size', type='number', value=bin_size)], style={'display': audio}),
            html.Div(['Resolution:', dcc.Dropdown(id='compression',
                                                  options=[
                                                      {'label': '512 Bins', 'value': '16'},
                                                      {'label': '1024 Bins', 'value': '8'},
                                                      {'label': '2048 Bins', 'value': '4'},
                                                      {'label': '4096 Bins', 'value': '2'},
                                                      {'label': '8192 Bins', 'value': '1'},
                                                  ],
                                                  value=compression,
                                                  className='dropdown')],
                     style={'display': serial}),
            html.Div(['File name:', dcc.Input(id='filename', type='text', value=filename)])
        ]),
        html.Div(id='t2_setting_div4', children=[
            html.Div(['LLD Threshold:', dcc.Input(id='threshold', type='number', step=10, value=threshold)], style={'display': audio}),
            html.Div(['Shape Tolerance:', dcc.Input(id='tolerance', type='number', step=1000, value=tolerance)], style={'display': audio}),
            html.Div(['Time Interval Sec.', dcc.Input(id='t_interval', type='number', step=1, readOnly=False, value=t_interval)]),
        ]),
        html.Div(id='t2_setting_div5', children=[]),
        html.Div(id='t2_setting_div6', children=[
            html.Div(['Energy by bin', daq.BooleanSwitch(id='epb_switch', on=False, color='purple')]),
            html.Div(['Show log(y)', daq.BooleanSwitch(id='log_switch', on=False, color='purple')]),
            html.Div(['Calibration', daq.BooleanSwitch(id='cal_switch', on=False, color='purple')]),
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
        html.Div(children=[html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        html.Div(id='subfooter', children=[]),
        
        dbc.Modal([
            dbc.ModalBody(f'Overwrite \"{filename}\" ?'),
            dbc.ModalFooter([
                dbc.Button("Append", id="confirm-overwrite-tab3", className="ml-auto", n_clicks=0),
                dbc.Button("Cancel", id="cancel-overwrite-tab3", className="ml-auto", n_clicks=0),
            ]),
            ], 
            id='modal-overwrite-tab3', 
            is_open=False,
            centered=True,
            size="md",
            className="custom-modal",
        ),
    ])
    return html_tab3

# --------- CALLBACK FOR START MODAL FUNCTION ------------------------
@app.callback(
    [Output('modal-overwrite-tab3', 'is_open'),
     Output('start_text_3d', 'children')],
    [Input('start_3d', 'n_clicks'), 
     Input('confirm-overwrite-tab3', 'n_clicks'), 
     Input('cancel-overwrite-tab3', 'n_clicks')],
    [State('filename', 'value'),
     State('modal-overwrite-tab3', 'is_open'),
     State('compression', 'value'),
     State('t_interval', 'value')]
)
def handle_start_and_modal(start_clicks, confirm_clicks, cancel_clicks, filename, is_open, compression, t_interval):
    logger.info("Entering handle_start_and_modal")
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    logger.info(f"Triggered by {button_id}")
    logger.info(f"Current is_open state: {is_open}")

    try:
        if button_id == "start_3d":
            file_exists = os.path.exists(f'{data_directory}/{filename}_3d.json')
            logger.info(f"Checked and file exists: {file_exists}")
            if file_exists:
                logger.info("Modal should open")
                return True, ""
            else:
                thread = threading.Thread(target=start_recording, args=(filename, compression, t_interval))
                thread.start()
                return False, " "

        elif button_id == "confirm-overwrite-tab3":
            logger.info("Confirm overwrite button clicked")
            thread = threading.Thread(target=start_recording, args=(filename, compression, t_interval))
            thread.start()
            logger.info("Modal should close")
            return False, " "

        elif button_id == "cancel-overwrite-tab3":
            logger.info("Cancel overwrite button clicked")
            logger.info("Modal should close")
            return False, ""  # Ensure modal is closed

    except Exception as e:
        logger.error(f"Error in handle_start_and_modal: {e}")
        return is_open, f"Error: {str(e)}"

    return False, ""

def start_recording(filename, compression, t_interval):
    """
    Starts the recording process depending on the device type.
    """
    logger.info(f"Starting recording with filename: {filename}, compression: {compression}, t_interval: {t_interval}")
    dn = fn.get_device_number()
    logger.info(f"Device number: {dn}")

    if dn >= 100:
        try:
            shproto.dispatcher.spec_stopflag = 0
            dispatcher = threading.Thread(target=shproto.dispatcher.start)
            dispatcher.start()

            time.sleep(0.1)
            shproto.dispatcher.process_03('-rst')
            logger.info('tab3 sends command -rst')
            time.sleep(0.1)
            shproto.dispatcher.process_03('-sta')
            logger.info('tab3 sends command -sta')
            time.sleep(0.1)
            shproto.dispatcher.process_02(filename, compression, t_interval)
            logger.info('dispatcher.process_02 Started')
            time.sleep(0.1)
        except serial.SerialException as e:
            logger.error(f'SerialException: {e}')
        except KeyError as e:
            logger.error(f'KeyError: {e}')
        except Exception as e:
            logger.error(f'Unexpected error in start_recording: {e}')
    else:
        fn.start_recording(3)
        logger.info('Audio Codec Recording Started')

#-------- STOP FUNCTION ---------------------
@app.callback(Output('stop_text_3d', 'children'),
              [Input('stop_3d', 'n_clicks')])
def update_output(n_clicks):
    """
    Stops the recording process.
    """
    if n_clicks is None:
        raise PreventUpdate

    dn = fn.get_device_number()
    if dn >= 100:
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()
        time.sleep(0.1)
        logger.info('Stop command sent from (tab3)')
    else:
        fn.stop_recording()
        return " "

# ------- RENDER CHART FUNCTION ------------------------
@app.callback([Output('chart_3d', 'figure'),
               Output('counts_3d', 'children'),
               Output('elapsed_3d', 'children'),
               Output('cps_3d', 'children')],
              [Input('interval-component', 'n_intervals'),
               Input('filename', 'value'),
               Input('epb_switch', 'on'),
               Input('log_switch', 'on'),
               Input('cal_switch', 'on'),
               Input('t_interval', 'value')], prevent_initial_call=True)
def update_graph(n, filename, epb_switch, log_switch, cal_switch, t_interval):
    """
    Updates the 3D graph with the current data.
    """
    global mean_cps
    global global_counts
    global device

    if n is None:
        raise PreventUpdate

    if device is not None and isinstance(device, int):
        if device > 100:
            from shproto.dispatcher import cps
        elif device < 100:
            from pulsecatcher import mean_cps
            cps = mean_cps 

    axis_type   = 'log' if log_switch else 'linear'
    histogram3  = fn.get_path(f'{data_directory}/{filename}_3d.json')
    now         = datetime.now()
    layout = go.Layout(
            uirevision='nochange',
            height=480,
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis=dict(title='Energy(x)'),
                yaxis=dict(title='Seconds(y)'),
                zaxis=dict(title='Counts(z)', 
                type=axis_type),
            ))

    if os.path.exists(histogram3):
        with open(histogram3, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                return go.Figure(data=[], layout=layout), 0, 0, 0

            numberOfChannels = data["resultData"]["energySpectrum"]["numberOfChannels"]
            validPulseCount = data["resultData"]["energySpectrum"]["validPulseCount"]
            elapsed = data["resultData"]["energySpectrum"]["measurementTime"]
            coefficients = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"][::-1]
            spectra = data["resultData"]["energySpectrum"]["spectrum"]

        global_counts = validPulseCount
        x = list(range(numberOfChannels))
        y = spectra

        if epb_switch:
            y = [[num * index for index, num in enumerate(inner_list)] for inner_list in spectra]

        if cal_switch:
            x = np.polyval(np.poly1d(coefficients), x)

        traces = []
        for i in range(len(y)):
            trace = {
                'type': 'scatter3d',
                'showlegend': False
            }
            traces.append(trace)

        surface_trace = {
            'type': 'surface',
            'x': x,
            'y': list(range(len(y))),
            'z': y,
            'colorscale': 'Rainbow',
            'showlegend': False
        }
        traces.append(surface_trace)

        date        =now.strftime('%d/%m/%Y')
        title_text  = f'{filename}<br>{date}<br>{global_counts} counts<br>{elapsed} seconds'

        layout = go.Layout(
            title={
                'text': title_text,
                'x': 0.85,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'}},
            uirevision='nochange',
            height=480,
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis=dict(title='Energy(x)'),
                yaxis=dict(title='Seconds(y)'),
                zaxis=dict(title='Counts(z)', 
                type=axis_type),
            )
        )

        fig = go.Figure(data=traces, layout=layout)

        return fig, f'{validPulseCount}', f'{elapsed}', f'cps {cps}'
    else:
        data = [go.Scatter3d(
            x=[0],
            y=[0],
            z=[0],
            mode='markers',
            marker=dict(size=5, color='blue')
        )]

        fig = go.Figure(data=data, layout=layout)

        return fig, 0, 0, 0

# Update Settings
@app.callback(Output('polynomial_3d', 'children'),
              [Input('bins', 'value'),
               Input('bin_size', 'value'),
               Input('max_counts', 'value'),
               Input('max_seconds', 'value'),
               Input('t_interval', 'value'),
               Input('filename', 'value'),
               Input('threshold', 'value'),
               Input('tolerance', 'value'),
               Input('calib_bin_1', 'value'),
               Input('calib_bin_2', 'value'),
               Input('calib_bin_3', 'value'),
               Input('calib_e_1', 'value'),
               Input('calib_e_2', 'value'),
               Input('calib_e_3', 'value')])
def save_settings(bins, bin_size, max_counts, max_seconds, t_interval, filename, threshold, tolerance, calib_bin_1, calib_bin_2, calib_bin_3, calib_e_1, calib_e_2, calib_e_3):
    """
    Saves settings to the database.
    """
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

    x_bins = [calib_bin_1, calib_bin_2, calib_bin_3]
    x_energies = [calib_e_1, calib_e_2, calib_e_3]
    coefficients = np.polyfit(x_bins, x_energies, 2)
    polynomial_fn = np.poly1d(coefficients)

    query = f"""UPDATE settings SET 
                coeff_1={float(coefficients[0])},
                coeff_2={float(coefficients[1])},
                coeff_3={float(coefficients[2])}
                WHERE id=0;"""
    c.execute(query)
    conn.commit()

    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'

# Update Calibration of Existing Spectrum
@app.callback(Output('3d_update_calib_message', 'children'),
              [Input('update_calib_button', 'n_clicks'),
               Input('filename', 'value')])
def update_current_calibration(n_clicks, filename):
    """
    Updates the calibration of the existing spectrum.
    """
    if n_clicks is None:
        raise PreventUpdate

    settings = fn.load_settings()
    coeff_1 = round(settings[18], 6)
    coeff_2 = round(settings[19], 6)
    coeff_3 = round(settings[20], 6)

    fn.update_coeff(filename, coeff_1, coeff_2, coeff_3)
    return f"Update {n_clicks}"
