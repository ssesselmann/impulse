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
    load_histogram_3d, 
    get_device_number,
    get_options_3d,
    start_recording,
    stop_recording,
    save_settings_to_json,
)

logger = logging.getLogger(__name__)

def show_tab3():

    with global_vars.write_lock:
        data_directory  = global_vars.data_directory


    files = [os.path.relpath(file, data_directory).replace("\\", "/")
             for file in glob.glob(os.path.join(data_directory, "**", "*.json"), recursive=True)]

    options_3d = get_options_3d()

    with global_vars.write_lock:
        device          = global_vars.device
        sample_rate     = global_vars.sample_rate
        chunk_size      = global_vars.chunk_size
        threshold       = global_vars.threshold
        tolerance       = global_vars.tolerance
        bins_3d         = global_vars.bins_3d
        bin_size_3d     = global_vars.bin_size_3d
        max_counts      = global_vars.max_counts
        sample_length   = global_vars.sample_length
        calib_bin_1     = global_vars.calib_bin_1
        calib_bin_2     = global_vars.calib_bin_2
        calib_bin_3     = global_vars.calib_bin_3
        calib_e_1       = global_vars.calib_e_1
        calib_e_2       = global_vars.calib_e_2
        calib_e_3       = global_vars.calib_e_3
        coeff_1         = global_vars.coeff_1
        coeff_2         = global_vars.coeff_2
        coeff_3         = global_vars.coeff_3
        max_seconds     = global_vars.max_seconds
        t_interval      = global_vars.t_interval
        compression     = global_vars.compression
        histogram_3d    = global_vars.histogram_3d
        log_switch      = global_vars.log_switch
        epb_switch      = global_vars.epb_switch
        cal_switch      = global_vars.cal_switch
        filename_3d     = global_vars.filename_3d


    load_histogram_3d(filename_3d)    

    device = int(device)

    serial = 'block' if device >= 100 else 'none'
    audio  = 'none'  if device >= 100 else 'block'

    refresh_rate = t_interval * 1000

    html_tab3 = html.Div(id='tab3', children=[
        html.Div(id='main-div', children= [
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
                html.Div(['Number of bins:', dcc.Input(id='bins', type='number', value=bins_3d)], style={'display': audio}),
                
                html.Div(['Resolution:', dcc.Dropdown(id='compression',
                                                      options=[
                                                          {'label': '512 Bins', 'value': '16'},
                                                          {'label': '1024 Bins', 'value': '8'},
                                                          {'label': '2048 Bins', 'value': '4'},
                                                          {'label': '4096 Bins', 'value': '2'},
                                                          {'label': '8192 Bins', 'value': '1'},
                                                      ],
                                                      value=1,
                                                      clearable=False,
                                                      className='dropdown')],
                         style={'display': serial}),
                html.Div(['File name:', dcc.Input(id='filename', type='text', value=filename_3d)], style={'marginTop':'5px'}),
                
            ]),
            html.Div(id='t2_setting_div4', children=[
                html.Div(['Bin size:', dcc.Input(id='bin_size', type='number', value=bin_size_3d)], style={'display': audio}),
                
                html.Div(['Select existing file:', dcc.Dropdown(
                                                            id='filename-list', 
                                                            options=options_3d, 
                                                            value=filename_3d, 
                                                            className='dropdown', 
                                                            optionHeight=40, 
                                                            style={'text-align':'left', 'fontSize':'10px'})], style={'marginTop':'5px'}),
            ]),
            html.Div(id='t2_setting_div5', children=[
                html.Div(['Time Interval Sec.', dcc.Input(id='t_interval', type='number', step=1, readOnly=False, value=t_interval)]),
                ]),
            html.Div(id='t2_setting_div6', children=[
                html.Div(['Energy by bin', daq.BooleanSwitch(id='epb-switch', on=epb_switch, color='purple')]),
                html.Div(['Show log(y)', daq.BooleanSwitch(id='log-switch', on=log_switch, color='purple')]),
                html.Div(['Calibration', daq.BooleanSwitch(id='cal-switch', on=cal_switch, color='purple')]),
            ]),
            html.Div(id='t2_setting_div7', children=[
                html.Div('Calibration Bins'),
                html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1)),
                html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2)),
                html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3)),
                html.P('Calibration shared with 2D histogram.'),
            ]),
            html.Div(id='t2_setting_div8', children=[
                html.Div('Energies'),
                html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1)),
                html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2)),
                html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3)),
            ]),
        ], style={'width':'100%', 'float':'left'}),   
        html.Div(children=[html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        html.Div(id='subfooter', children=[]),
        html.Div(id='polynomial-3d', children=''),
        
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
    [Output('modal-overwrite-tab3'  , 'is_open'),
     Output('modal-body-3d'         , 'children')],
    [Input('start_3d'               , 'n_clicks'), 
     Input('confirm-overwrite-tab3' , 'n_clicks'), 
     Input('cancel-overwrite-tab3'  , 'n_clicks')],
    [State('filename'               , 'value'), 
     State('modal-overwrite-tab3'   , 'is_open')]
)
def confirm_with_user_3d(start_clicks, confirm_clicks, cancel_clicks, filename_3d, is_open):
    ctx = callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    logging.info(f"Tab3 Modal triggered by {button_id}")

    if button_id == "start_3d":
        return True, f'Overwrite "{filename_3d}_3d.json"?'

    elif button_id in ["confirm-overwrite-tab3", "cancel-overwrite-tab3"]:
        return False, ''

    return False, ''

@app.callback(
    Output('start_text_3d'          , 'children'),
    [Input('confirm-overwrite-tab3' , 'n_clicks'),
     Input('start_3d'               , 'n_clicks')],
    [State('filename'               , 'value'),
     State('compression'            , 'value'),
     State('t_interval'             , 'value')]
)
def start_new_3d_spectrum(confirm_clicks, start_clicks, filename_3d, compression, t_interval):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    with global_vars.write_lock:
        data_directory = global_vars.data_directory
        device = global_vars.device

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_value = ctx.triggered[0]['value']
    file_exists = os.path.exists(f'{data_directory}/{filename_3d}_3d.json')

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
                logger.info(f'tab2 sends reset command -rst\n')

                time.sleep(0.1)
                shproto.dispatcher.process_03('-sta')
                logger.info(f'tab2 sends start command -sta\n')

                time.sleep(0.1)
                shproto.dispatcher.process_02(filename_3d, compression, "MAX", t_interval)
                logger.info(f'tab2 calls process_01(){filename_3d}, {compression}, MAX, {t_interval}\n')

                time.sleep(0.1)
            except Exception as e:
                logger.error(f'tab 2 start_new_or_overwrite() error {e}\n')
                return f"tab2 Error: {str(e)}"
        else:
            start_recording(3)

            logger.info(f'tab3 start_recording({3})\n')
            return ""

    raise PreventUpdate

@app.callback(Output('stop_text_3d', 'children'),
              [Input('stop_3d', 'n_clicks')])
def update_output(n_clicks):
    logger.info("update_output callback triggered\n")

    if n_clicks is None:
        raise PreventUpdate

    dn = get_device_number()

    if dn >= 100:
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()
        time.sleep(0.1)
        logger.info('Stop command sent from (tab3)\n')
    else:
        stop_recording()

    return " "

@app.callback(
    [Output('chart-3d'          , 'figure'),
     Output('counts_3d'         , 'children'),
     Output('elapsed_3d'        , 'children'),
     Output('cps_3d'            , 'children')],
    [Input('interval-component' , 'n_intervals'),
     Input('filename-list'      , 'value'),
     Input('epb-switch'         , 'on'),
     Input('log-switch'         , 'on'),
     Input('cal-switch'         , 'on'),
     Input('t_interval'         , 'value')]
)
def update_graph_3d(n_intervals, filename_list, epb_switch, log_switch, cal_switch, t_interval):
    
    with global_vars.write_lock:
        # if filename_list:
        #     global_vars.filename_3d = filename_list
        device          = global_vars.device
        counts          = global_vars.counts
        elapsed         = global_vars.elapsed
        cps             = global_vars.cps
        bins_3d         = global_vars.bins_3d
        histogram_3d    = global_vars.histogram_3d
        coefficients_1  = global_vars.coefficients_1
        filename_3d     = global_vars.filename_3d
        data_directory  = global_vars.data_directory
        threshold       = global_vars.threshold
        tolerance       = global_vars.tolerance

    axis_type   = 'log' if log_switch else 'linear'
    now         = datetime.now()
    date        = now.strftime('%d-%m-%Y')
    file_path   = os.path.join(data_directory, filename_3d)
    y_range     = [0, len(histogram_3d)]

    layout = go.Layout(
        uirevision='nochange',
        height=580,
        margin=dict(l=0, r=0, b=50, t=0),
        scene=dict(
            xaxis=dict(title='bins(x)', range=[0, bins_3d]),
            yaxis=dict(title='time intervals(y)', range=y_range),
            zaxis=dict(title='counts(z)', type=axis_type),
        )
    )
    
    try:
        z = histogram_3d
        y = list(range(len(histogram_3d)))
        x = list(range(bins_3d))

        layout.scene.yaxis.range = [0, max(y)]
      
        if epb_switch:
            z = [[num * index for index, num in enumerate(inner_list)] for inner_list in z]

        if cal_switch:
            x = np.polyval(np.poly1d(coefficients_1), x)
            layout.scene.xaxis.range = [0, max(x)]
            layout.scene.xaxis.title = "energy (x)"

        surface_trace = {
            'type': 'surface',
            'x': x,
            'y': y,
            'z': z,
            'colorscale': 'Rainbow',
            'showlegend': False
        }

        traces = [surface_trace]

        title_text = f'{filename_3d}<br>{date}<br>{counts} counts<br>{elapsed} seconds'

        layout.update(
            title={
                'text': title_text,
                'x': 0.85,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 16, 'color': 'black'}
            }
        )

        fig = go.Figure(data=traces, layout=layout)


        return fig, f'{counts}', f'{elapsed}', f'cps {cps}'

    except Exception as e:

        logger.error(f"tab3 error updating 3D chart: {e}\n")

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
    Output('polynomial-3d'  , 'children'),
    [Input('bins'           , 'value'),
     Input('bin_size'       , 'value'),
     Input('max_counts'     , 'value'),
     Input('max_seconds'    , 'value'),
     Input('t_interval'     , 'value'),
     Input('filename'       , 'value'),
     Input('calib_bin_1'    , 'value'),
     Input('calib_bin_2'    , 'value'),
     Input('calib_bin_3'    , 'value'),
     Input('calib_e_1'      , 'value'),
     Input('calib_e_2'      , 'value'),
     Input('calib_e_3'      , 'value'),
     Input('log-switch'     , 'on'),
     Input('epb-switch'     , 'on'),
     Input('cal-switch'     , 'on'),
     Input('compression'    , 'value')]
)
def save_settings(*args):
    logger.info("save_settings callback triggered\n")

    x_bins          = [args[6], args[7], args[8]]
    x_energies      = [args[9], args[10], args[11]]
    coefficients    = np.polyfit(x_bins, x_energies, 2)
    polynomial_fn   = np.poly1d(coefficients)

    with global_vars.write_lock:
        global_vars.bins_3d         = int(args[0])
        global_vars.bin_size_3d     = int(args[1])
        global_vars.max_counts      = int(args[2])
        global_vars.max_seconds     = int(args[3])
        global_vars.t_interval      = int(args[4])
        global_vars.filename_3d     = args[5]
        global_vars.calib_bin_1     = int(args[6])
        global_vars.calib_bin_2     = int(args[7])
        global_vars.calib_bin_3     = int(args[8])
        global_vars.calib_e_1       = int(args[9])
        global_vars.calib_e_2       = int(args[10])
        global_vars.calib_e_3       = int(args[11])
        global_vars.log_switch      = bool(args[12])
        global_vars.epb_switch      = bool(args[13])
        global_vars.cal_switch      = bool(args[14])
        global_vars.compression     = int(args[15])
        global_vars.coefficients_1  = list(coefficients)
        
        global_vars.coeff_1         = round(coefficients[0], 6)
        global_vars.coeff_2         = round(coefficients[1], 6)
        global_vars.coeff_3         = round(coefficients[2], 6)

        if global_vars.device >= 100:
            try:
                global_vars.bins_3d = int(8192/int(args[15]))
            except:
                global_vars.bins_3d = 8192

        save_settings_to_json()

    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'

@app.callback(
    Output('3d_update_calib_message'    , 'children'),
    [Input('update_calib_button'        , 'n_clicks')],
    [State('filename'                   , 'value')]
)
def update_current_calibration(n_clicks, filename_3d):
    logger.info("update_current_calibration callback triggered\n")

    if n_clicks is None:
        raise PreventUpdate

    with global_vars.write_lock:
        coeff_1 = round(global_vars.coeff_1, 6)
        coeff_2 = round(global_vars.coeff_2, 6)
        coeff_3 = round(global_vars.coeff_3, 6)

    update_json_3d_file(filename_3d, coeff_1, coeff_2, coeff_3)

    return f"Update {n_clicks}"

app.layout = html.Div([
    show_tab3()
])

@app.callback(
    Output('filename-list' , 'value'), 
    Input('filename-list'  , 'value'),
    )
def switch_spectrum(filename_3d):
    
    load_histogram_3d(filename_3d)

    return filename_3d

if __name__ == '__main__':
    app.run_server(debug=True)
