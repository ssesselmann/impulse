import os
import glob
import time
import logging
import threading
import numpy as np
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objs as go
import shproto.dispatcher
import global_vars

from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from server import app
from datetime import datetime
from functions import (
    load_histogram_3d,
    get_options_3d,
    start_recording,
    stop_recording,
    save_settings_to_json,
    format_date,
    get_device_number,
)

logger = logging.getLogger(__name__)

def show_tab3():
    with global_vars.write_lock:
        data_directory = global_vars.data_directory

    files = [os.path.relpath(file, data_directory).replace("\\", "/")
             for file in glob.glob(os.path.join(data_directory, "**", "*.json"), recursive=True)]

    with global_vars.write_lock:
        device      = global_vars.device
        bin_size_3d = global_vars.bin_size_3d
        max_counts  = global_vars.max_counts
        max_seconds = global_vars.max_seconds
        t_interval  = global_vars.t_interval
        filename_3d = global_vars.filename_3d
        log_switch  = global_vars.log_switch
        epb_switch  = global_vars.epb_switch
        cal_switch  = global_vars.cal_switch
        calib_bin_1 = global_vars.calib_bin_1
        calib_bin_2 = global_vars.calib_bin_2
        calib_bin_3 = global_vars.calib_bin_3
        calib_e_1   = global_vars.calib_e_1
        calib_e_2   = global_vars.calib_e_2
        calib_e_3   = global_vars.calib_e_3

    device          = int(device)
    serial          = 'block'   if device >= 100 else 'none'
    audio           = 'none'    if device >= 100 else 'block'
    refresh_rate    = t_interval * 1000
    options_3d      = get_options_3d()
    compression     = 8
    bins_3d         = 512

    return html.Div(id='tab3', children=[
        # vertical screen divider
        html.Div(className='tab3-split-div', children=[
            # 3x3 grid 
            html.Div(className='grid-container', children=[

                html.Div(className='t3subdiv', children=[
                    html.Button('START', id='start_3d', n_clicks=0),
                    html.Div(id='counts_3d', children=''),
                    html.Div(id='start_text_3d', children=''),
                    html.Div(['Max Counts', dcc.Input(id='max_counts', type='number', step=1000, readOnly=False, value=max_counts)]),
                ]),

                html.Div(className='t3subdiv', children=[
                    html.Button('STOP', id='stop_3d'),
                    html.Div(id='elapsed_3d', children=''),
                    html.Div(['Max Seconds', dcc.Input(id='max_seconds', type='number', step=60, readOnly=False, value=max_seconds)]),
                    html.Div(id='cps_3d', children=''),
                    html.Div(id='stop_text_3d', children=''),
                ]),

                html.Div(className='t3subdiv', children=[
                    html.Div(['Select existing file:', dcc.Dropdown(
                        id='filename-list',
                        options=options_3d,
                        value="",
                        className='dropdown',
                        optionHeight=40,
                        style={'text-align': 'left', 'fontSize': '10px'})]),
                    html.Div(['Or enter new file name:', dcc.Input(id='filename_3d', type='text', value=filename_3d)], style={'marginTop': '5px'}),
                ]),

                html.Div(className='t3subdiv', children=[
                    html.Div(['3D Bin size:', dcc.Input(id='bin_size_3d', type='number', value=bin_size_3d)], style={'display': audio}),
                    html.Div(['Number of bins:', dcc.Input(id='bins', type='number', value=bins_3d)], style={'visibility': 'hidden'}),
                    html.Div(['Resolution:', dcc.Dropdown(id='compression',
                                                          options=[
                                                              {'label': '512 Bins', 'value': '16'},
                                                              {'label': '1024 Bins', 'value': '8'},
                                                              {'label': '2048 Bins', 'value': '4'},
                                                              {'label': '4096 Bins', 'value': '2'},
                                                              {'label': '8192 Bins', 'value': '1'},
                                                          ],
                                                          value=compression,
                                                          clearable=False,
                                                          className='dropdown')],
                             style={'visibility': 'hidden'}),
                ]),

                html.Div(className='t3subdiv', children=[
                    html.Div(['Time Interval Sec.', dcc.Input(id='t_interval', type='number', step=1, readOnly=False, value=t_interval)]),
                ]),

                html.Div(className='t3subdiv', children=[
                    html.Div(['Energy by bin', daq.BooleanSwitch(id='epb-switch', on=epb_switch, color='purple')]),
                    html.Div(['Show log(y)', daq.BooleanSwitch(id='log-switch', on=log_switch, color='purple')]),
                    html.Div(['Calibration', daq.BooleanSwitch(id='cal-switch', on=cal_switch, color='purple')]),
                ]),

                html.Div(className='t3subdiv', children=[
                    html.Div('Calibration Bins'),
                    html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1)),
                    html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2)),
                    html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3)),
                    
                ]),

                html.Div(className='t3subdiv', children=[
                    html.Div('Energies'),
                    html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1)),
                    html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2)),
                    html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3)),
                ]),

                html.Div(className='t3subdiv', children=[
                    html.P('Calibration setting are shared with 2D histogram,', style={'textAlign':'center'}),
                    html.P('large arrays take time,', style={'textAlign':'center'}),
                    html.P('patience is a virtue.', style={'textAlign':'center'}),
                    html.P('🙄', style={'textAlign':'center'}),
                    ]),

            ]),

            html.Div(children=[html.Img(id='t3footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
            html.Div(id='polynomial-3d' , children=''),

            ]),
            
        html.Div(className='tab3-split-div', children=[
            html.Div(id='chartbox', children=[
                dcc.Graph(id='chart-3d', figure={}),
                dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
                ]),
            ]),

        # pop up start confirmation
        dbc.Modal([
            dbc.ModalBody(id='modal-body-3d'),
            dbc.ModalBody(children=[
                html.P('To avoid huge arrays.'),
                html.P('This histogram is hard coded for 512 channels'),
                html.P('Longer intervals will further reduce file size.')
            ], style={'color': 'red', 'align': 'center', 'fontWeight': 'bold', 'textAlign': 'center'}),
            dbc.ModalFooter([
                dbc.Button(f"Overwrite {filename_3d}", id="confirm-overwrite-tab3", className="ml-auto", n_clicks=0),
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

app.layout = html.Div([show_tab3()])

# Pull down file selection loads histogram
@app.callback(
    Output('filename_3d'    , 'value'),
    Input('filename-list'   , 'value'),
    State('filename_3d'     , 'value')
)
def switch_spectrum(selected_filename, current_filename):
    if selected_filename:
        load_histogram_3d(selected_filename)
        return selected_filename
    return current_filename

# Pop up window asking user to confirm overwrite if file exists
@app.callback(
    [Output('modal-overwrite-tab3'  , 'is_open'),
     Output('modal-body-3d'         , 'children')],
    [Input('start_3d'               , 'n_clicks'),
     Input('confirm-overwrite-tab3' , 'n_clicks'),
     Input('cancel-overwrite-tab3'  , 'n_clicks')],
    [State('filename_3d'            , 'value')  ,
     State('modal-overwrite-tab3'   , 'is_open')]
)
def confirm_with_user_3d(start_clicks, confirm_clicks, cancel_clicks, filename_3d, is_open):
    ctx = callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    logging.info(f"tab3 Modal triggered by {button_id}")

    if button_id == "start_3d":
        with global_vars.write_lock:
            data_directory = global_vars.data_directory

        file_exists = os.path.exists(f'{data_directory}/{filename_3d}_3d.json')

        if file_exists:
            return True, f'Continue {filename_3d}_3d.json ?'
        else:
            return False, ''

    elif button_id in ["tab-3 confirm-overwrite", "tab3-cancel-overwrite"]:
        return False, ''

    return False, ''


# Function to start spectrum 
@app.callback(
    Output('start_text_3d'          , 'children'),
    [Input('confirm-overwrite-tab3' , 'n_clicks'),
     Input('start_3d'               , 'n_clicks')],
    [State('filename_3d'            , 'value'),
     State('t_interval'             , 'value')]
)
def start_new_3d_spectrum(confirm_clicks, start_clicks, filename_3d, t_interval):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    with global_vars.write_lock:
        data_directory = global_vars.data_directory
        device = global_vars.device

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_value = ctx.triggered[0]['value']

    compression = 8

    file_exists = os.path.exists(f'{data_directory}/{filename_3d}_3d.json')

    if file_exists:
        load_histogram_3d(filename_3d)

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
                logger.info(f'tab3 sends reset command -rst\n')

                time.sleep(0.1)
                shproto.dispatcher.process_03('-sta')
                logger.info(f'tab3 sends start command -sta\n')

                time.sleep(0.1)
                shproto.dispatcher.process_02(filename_3d, compression, "MAX", t_interval)
                logger.info(f'tab3 process_01(){filename_3d}, {compression}, MAX, {t_interval}\n')

                time.sleep(0.1)
            except Exception as e:
                logger.error(f'tab 2 start_new_or_overwrite() error {e}\n')
                return f"tab2 Error: {str(e)}"
        else:
            start_recording(3)
            logger.info(f'tab3 start_recording({3})\n')
            return ""

    raise PreventUpdate

# Function to stop recording
@app.callback(
    Output('stop_text_3d'   , 'children'),
    [Input('stop_3d'        , 'n_clicks')]
)
def update_output(n_clicks):
    logger.info("update_output callback triggered\n")

    if n_clicks is None:
        raise PreventUpdate

    dn = get_device_number()

    if dn >= 100:
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()
        time.sleep(0.1)
        logger.info('tab3 Stop command sent\n')
    else:
        stop_recording()

    return " "

# Main function which updates the graph on the page
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
        device          = global_vars.device
        counts          = global_vars.counts
        elapsed         = global_vars.elapsed
        cps             = global_vars.cps
        bins_3d         = global_vars.bins_3d
        histogram_3d    = global_vars.histogram_3d
        coefficients_1  = global_vars.coefficients_1
        filename_3d     = global_vars.filename_3d
        data_directory  = global_vars.data_directory
        cps             = int(cps/t_interval)

        try:
            start_time  = global_vars.startTime3d
            start_time  = format_date(start_time)
        except:
            start_time  = ""
            pass

    axis_type   = 'log' if log_switch else 'linear'
    now         = datetime.now()
    date        = now.strftime('%d-%m-%Y')
    file_path   = os.path.join(data_directory, filename_3d)
    y_range     = [0, len(histogram_3d)]

    layout = go.Layout(
            uirevision='nochange',
            margin=dict(l=10, r=10, b=10, t=10),
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

        traces      = [surface_trace]
        
        title_text  = f'{filename_3d}_3d.json<br>{start_time}<br>{counts} counts<br>{elapsed} seconds'

        layout.update(
            title={
                'text': title_text,
                'x': 0.05,
                'y': 0.9,
                'xanchor': 'left',
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

        layout.scene.yaxis.range = [0, 0]

        fig = go.Figure(data=data, layout=layout)

        return fig, "0", "0", f'cps {cps}'

# Function to save settings when one of the inputs change
@app.callback(
    Output('polynomial-3d'  , 'children'),
    [Input('bins'           , 'value'),
     Input('bin_size_3d'       , 'value'),
     Input('max_counts'     , 'value'),
     Input('max_seconds'    , 'value'),
     Input('t_interval'     , 'value'),
     Input('filename_3d'    , 'value'),
     Input('calib_bin_1'    , 'value'),
     Input('calib_bin_2'    , 'value'),
     Input('calib_bin_3'    , 'value'),
     Input('calib_e_1'      , 'value'),
     Input('calib_e_2'      , 'value'),
     Input('calib_e_3'      , 'value'),
     Input('log-switch'     , 'on'),
     Input('epb-switch'     , 'on'),
     Input('cal-switch'     , 'on'),
]
)
def save_settings(*args):
    if not args:
        raise PreventUpdate

    logger.info("save_settings callback triggered\n")

    x_bins = [args[6], args[7], args[8]]
    x_energies = [args[9], args[10], args[11]]
    coefficients = np.polyfit(x_bins, x_energies, 2)
    polynomial_fn = np.poly1d(coefficients)

    with global_vars.write_lock:
        global_vars.bins_3d         = 512 # hard coded
        global_vars.bin_size_3d        = int(args[1])
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
        global_vars.compression     = 8 # Hard coded 
        global_vars.coefficients_1  = list(coefficients)
        global_vars.coeff_1         = round(coefficients[0], 6)
        global_vars.coeff_2         = round(coefficients[1], 6)
        global_vars.coeff_3         = round(coefficients[2], 6)

        save_settings_to_json()

    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'


