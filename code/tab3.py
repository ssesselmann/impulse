import os
import json
import glob
import time
import numpy as np
import sqlite3 as sql
import threading
import logging
import global_vars
import audio_spectrum as asp
import subprocess
import serial.tools.list_ports
import dash_bootstrap_components as dbc
import shproto.dispatcher
import shproto.port as port
import dash
import dash_daq as daq
import plotly.graph_objs as go

from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from server import app
from datetime import datetime
from functions import (
    update_json_3d_file, 
    load_3d_json, 
    get_device_number,
    start_recording,
    stop_recording,
)

logger = logging.getLogger(__name__)

with global_vars.write_lock:
    data_directory = global_vars.data_directory
    device = global_vars.device
    filename = global_vars.filename

def show_tab3():

    global_vars.load_settings_from_json()
    logger.info("Loading settings from JSON")

    with global_vars.write_lock:
        filename = global_vars.filename
        data_directory = global_vars.data_directory

    load_3d_json(filename)

    files = [os.path.relpath(file, data_directory).replace("\\", "/")
             for file in glob.glob(os.path.join(data_directory, "**", "*.json"), recursive=True)]

    options = [{'label': "~ " + os.path.basename(file), 'value': file} if "i/" in file and file.endswith(".json")
               else {'label': os.path.basename(file), 'value': file} for file in files]

    options = [opt for opt in options if not opt['value'].endswith("-cps.json")]

    options_sorted = sorted(options, key=lambda x: x['label'])

    for file in options_sorted:
        file['label'] = file['label'].replace('.json', '')
        file['value'] = file['value'].replace('.json', '')

    with global_vars.write_lock:
        device = global_vars.device
        sample_rate = global_vars.sample_rate
        chunk_size = global_vars.chunk_size
        threshold = global_vars.threshold
        tolerance = global_vars.tolerance
        bins = global_vars.bins
        bin_size = global_vars.bin_size
        max_counts = global_vars.max_counts
        sample_length = global_vars.sample_length
        calib_bin_1 = global_vars.calib_bin_1
        calib_bin_2 = global_vars.calib_bin_2
        calib_bin_3 = global_vars.calib_bin_3
        calib_e_1 = global_vars.calib_e_1
        calib_e_2 = global_vars.calib_e_2
        calib_e_3 = global_vars.calib_e_3
        coeff_1 = global_vars.coeff_1
        coeff_2 = global_vars.coeff_2
        coeff_3 = global_vars.coeff_3
        max_seconds = global_vars.max_seconds
        t_interval = global_vars.t_interval
        compression = global_vars.compression
        histogram_3d = global_vars.histogram_3d


    serial = 'block' if device >= 100 else 'none'
    audio = 'none' if device >= 100 else 'block'
    refresh_rate = t_interval * 1000

    html_tab3 = html.Div(id='tab3', children=[
        html.Div(id='plolynomial-3d', children=''),
        html.Div(id='bar-chart-div-3d', children=[
            dcc.Graph(id='chart-3d', figure={}),
            dcc.Interval(id='interval-component', interval=refresh_rate, n_intervals=0)
        ]),
        html.Div(id='last-filename', children=''),
        html.Div(id='t2_filler_div', children=''),
        html.Div(id='t2_setting_div1', children=[
            html.Button('START', id='start_3d', n_clicks=0),
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
            dbc.ModalBody(id='modal-body-3d'),
            dbc.ModalBody(children=[
                html.P('Avoid huge arrays.'),
                html.P('Try 500 bins and 10 second intervals'),
                ], style={'color': 'red', 'align':'center', 'fontWeight':'bold', 'textAlign':'center'}),
            dbc.ModalFooter([
                dbc.Button("Overwrite", id="confirm-overwrite-tab3", className="ml-auto", n_clicks=0),
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

@app.callback(
    [Output('modal-overwrite-tab3', 'is_open'),
     Output('modal-body-3d', 'children')],
    [Input('start_3d', 'n_clicks'), 
     Input('confirm-overwrite-tab3', 'n_clicks'), 
     Input('cancel-overwrite-tab3', 'n_clicks')],
    [State('filename', 'value'), 
     State('modal-overwrite-tab3', 'is_open')]
)
def confirm_with_user_3d(start_clicks, confirm_clicks, cancel_clicks, filename, is_open):
    ctx = callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    logging.info(f"Tab3 Modal triggered by {button_id}")

    if button_id == "start_3d":
        return True, f'Overwrite "{filename}_3d.json"?'

    elif button_id in ["confirm-overwrite-tab3", "cancel-overwrite-tab3"]:
        return False, ''

    return False, ''

@app.callback(
    Output('start_text_3d', 'children'),
    [Input('confirm-overwrite-tab3', 'n_clicks'),
     Input('start_3d', 'n_clicks')],
    [State('filename', 'value'),
     State('compression', 'value'),
     State('t_interval', 'value')]
)
def start_new_3d_spectrum(confirm_clicks, start_clicks, filename, compression, t_interval):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    with global_vars.write_lock:
        data_directory = global_vars.data_directory
        device = global_vars.device

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_value = ctx.triggered[0]['value']
    file_exists = os.path.exists(f'{data_directory}/{filename}_3d.json')

    if trigger_value == 0:
        raise PreventUpdate

    if (trigger_id == 'confirm-overwrite-tab3') or (trigger_id == 'start_3d' and not file_exists):
        if device >= 100:
            try:
                shproto.dispatcher.spec_stopflag = 0
                dispatcher = threading.Thread(target=shproto.dispatcher.start)
                dispatcher.start()

                time.sleep(0.1)
                shproto.dispatcher.process_03('-rst')
                logger.info(f'tab2 sends reset command -rst')

                time.sleep(0.1)
                shproto.dispatcher.process_03('-sta')
                logger.info(f'tab2 sends start command -sta')

                time.sleep(0.1)
                shproto.dispatcher.process_02(filename, compression, "MAX", t_interval)
                logger.info(f'tab2 calls process_01(){filename}, {compression}, MAX, {t_interval}')

                time.sleep(0.1)
            except Exception as e:
                logger.error(f'tab 2 start_new_or_overwrite() error {e}')
                return f"tab2 Error: {str(e)}"
        else:
            start_recording(3)

            logger.info(f'tab3 start_recording({3})')
            return ""

    raise PreventUpdate

@app.callback(Output('stop_text_3d', 'children'),
              [Input('stop_3d', 'n_clicks')])
def update_output(n_clicks):
    logger.info("update_output callback triggered")

    if n_clicks is None:
        raise PreventUpdate

    dn = get_device_number()

    if dn >= 100:
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()
        time.sleep(0.1)
        logger.info('Stop command sent from (tab3)')
    else:
        stop_recording()

    return " "

@app.callback(
    [Output('chart-3d', 'figure'),
     Output('counts_3d', 'children'),
     Output('elapsed_3d', 'children'),
     Output('cps_3d', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('filename', 'value'),
     Input('epb_switch', 'on'),
     Input('log_switch', 'on'),
     Input('cal_switch', 'on'),
     Input('t_interval', 'value')]
)
def update_graph_3d(n_intervals, filename, epb_switch, log_switch, cal_switch, t_interval):
    with global_vars.write_lock:
        device          = global_vars.device
        counts          = global_vars.counts
        elapsed         = global_vars.elapsed
        cps             = global_vars.cps
        bins            = global_vars.bins
        histogram_3d    = global_vars.histogram_3d
        coefficients_1  = [global_vars.coeff_1, global_vars.coeff_2, global_vars.coeff_3]
        filename        = global_vars.filename
        data_directory  = global_vars.data_directory



    axis_type   = 'log' if log_switch else 'linear'
    now         = datetime.now()
    date        = now.strftime('%d/%m/%Y')
    filename_3d = f'{filename}_3d.json'
    file_path   = os.path.join(data_directory, filename_3d)
    y_range     = [0, len(histogram_3d)]

    layout = go.Layout(
        uirevision='nochange',
        height=580,
        margin=dict(l=0, r=0, b=50, t=0),
        scene=dict(
            xaxis=dict(title='Energy(x)', range=[0, bins]),
            yaxis=dict(title='Time intervals(y)', range=y_range),
            zaxis=dict(title='Counts(z)', type=axis_type),
        )
    )
    
    try:
        z = histogram_3d
        y = list(range(len(histogram_3d)))
        x = list(range(bins))

        layout.scene.yaxis.range = [0, max(y)]
      
        if epb_switch:
            z = [[num * index for index, num in enumerate(inner_list)] for inner_list in z]

        if cal_switch:
            x = np.polyval(np.poly1d(coefficients_1), x)

        surface_trace = {
            'type': 'surface',
            'x': x,
            'y': y,
            'z': z,
            'colorscale': 'Rainbow',
            'showlegend': False
        }

        traces = [surface_trace]

        title_text = f'{filename}<br>{date}<br>{counts} counts<br>{elapsed} seconds'

        layout.update(
            title={
                'text': title_text,
                'x': 0.85,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
            }
        )

        fig = go.Figure(data=traces, layout=layout)


        return fig, f'{counts}', f'{elapsed}', f'cps {cps}'

    except Exception as e:

        logger.error(f"tab3 error updating 3D chart: {e}")

        data = [go.Scatter3d(
            x=[0],
            y=[0],
            z=[0],
            mode='markers',
            marker=dict(size=5, color='blue')
        )]

        fig = go.Figure(data=data, layout=layout)

        return fig, "0", "0", f'cps {cps}'

@app.callback(
    Output('plolynomial-3d', 'children'),
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
     Input('calib_e_3', 'value')]
)
def save_settings(bins, bin_size, max_counts, max_seconds, t_interval, filename, threshold, tolerance, calib_bin_1, calib_bin_2, calib_bin_3, calib_e_1, calib_e_2, calib_e_3):
    logger.info("save_settings callback triggered")

    x_bins = [calib_bin_1, calib_bin_2, calib_bin_3]
    x_energies = [calib_e_1, calib_e_2, calib_e_3]
    coefficients = np.polyfit(x_bins, x_energies, 2)
    polynomial_fn = np.poly1d(coefficients)

    with global_vars.write_lock:
        global_vars.bins = bins
        global_vars.bin_size = bin_size
        global_vars.max_counts = max_counts
        global_vars.max_seconds = max_seconds
        global_vars.filename = filename
        global_vars.threshold = threshold
        global_vars.tolerance = tolerance
        global_vars.calib_bin_1 = calib_bin_1
        global_vars.calib_bin_2 = calib_bin_2
        global_vars.calib_bin_3 = calib_bin_3
        global_vars.calib_e_1 = calib_e_1
        global_vars.calib_e_2 = calib_e_2
        global_vars.calib_e_3 = calib_e_3
        global_vars.t_interval = t_interval
        global_vars.coeff_1 = coefficients[0]
        global_vars.coeff_2 = coefficients[1]
        global_vars.coeff_3 = coefficients[2]

        global_vars.save_settings_to_json()

    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'

@app.callback(
    Output('3d_update_calib_message', 'children'),
    [Input('update_calib_button', 'n_clicks')],
    [State('filename', 'value')]
)
def update_current_calibration(n_clicks, filename):
    logger.info("update_current_calibration callback triggered")

    if n_clicks is None:
        raise PreventUpdate

    with global_vars.write_lock:
        coeff_1 = round(global_vars.coeff_1, 6)
        coeff_2 = round(global_vars.coeff_2, 6)
        coeff_3 = round(global_vars.coeff_3, 6)

    update_json_3d_file(filename, coeff_1, coeff_2, coeff_3)

    return f"Update {n_clicks}"

app.layout = html.Div([
    show_tab3()
])

if __name__ == '__main__':
    app.run_server(debug=True)
