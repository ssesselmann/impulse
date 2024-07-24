# tab2.py
import dash
import plotly.graph_objs as go
import pulsecatcher as pc
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
import global_vars
import shproto.dispatcher

from dash import dcc, html, Input, Output, State, callback, Dash, callback_context
from dash.dependencies import Input, Output, State
from server import app
from dash.exceptions import PreventUpdate
from datetime import datetime

# Importing store variables from server
from server import (
    store_histogram, 
    store_histogram_2, 
    store_histogram_3d,
    store_gaussian, 
    store_sigma, 
    store_annotations,
    store_confirmation_output, 
    store_count_history
)
# Functions imported
from functions import (
    calibrate_gc, 
    clear_global_cps_list, 
    execute_serial_command, 
    find_peaks_in_gc, 
    gaussian_correl, 
    get_device_number, 
    get_isotopes, 
    get_options, 
    get_path, 
    get_spec_notes, 
    is_valid_json, 
    load_histogram, 
    load_histogram_2, 
    matching_isotopes, 
    peak_finder, 
    publish_spectrum, 
    start_recording, 
    stop_recording, 
    update_coeff, 
    update_json_notes,
    handle_modal_confirmation,
    clear_global_vars,
    save_settings_to_json,
    )

logger = logging.getLogger(__name__)

device = None
with global_vars.write_lock:
    data_directory = global_vars.data_directory

def show_tab2():
    options_sorted  = get_options()

    # Load global variables
    with global_vars.write_lock:
        filename        = global_vars.filename
        filename_2      = global_vars.filename_2
        device          = global_vars.device
        sample_rate     = global_vars.sample_rate
        chunk_size      = global_vars.chunk_size
        threshold       = global_vars.threshold
        tolerance       = global_vars.tolerance
        bins            = global_vars.bins
        bin_size        = global_vars.bin_size
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
        peakfinder      = global_vars.peakfinder
        log_switch      = global_vars.log_switch
        epb_switch      = global_vars.epb_switch
        cal_switch      = global_vars.cal_switch
        coi_switch      = global_vars.coi_switch
        sigma           = global_vars.sigma
        max_seconds     = global_vars.max_seconds
        t_interval      = global_vars.t_interval
        compression     = global_vars.compression
        spec_notes      = global_vars.spec_notes
        coefficients    = global_vars.coefficients_1
        coefficients_2  = global_vars.coefficients_2

    try:
        load_histogram(filename)            # Load last histogram if it exists
    except:
        pass    

    if device <= 100 and device:        # Sound card devices
        with global_vars.write_lock:
            global_vars.bins = bins

    else:
        with global_vars.write_lock:    # Atom nano devices
            global_vars.bins = int(8192/compression)    


    millisec    = t_interval * 1000

    if device >= 100:
        serial = 'block'
        audio = 'none'
    else:
        serial = 'none'
        audio = 'block'

    counts_warning = 'red' if max_counts == 0 else 'white'
    seconds_warning = 'red' if max_seconds == 0 else 'white'

    html_tab2 = html.Div(id='tab2', children=[
        html.Div(id='main-div', children= [
            html.Div(id='polynomial', children=''),
            html.Div(id='output-roi', children=''),

            html.Div(id='bar_chart_div', children=[
                
                dcc.Interval(id='interval-component', interval=millisec, n_intervals=0),  # Refresh rate 1s.
                dcc.Graph(id='bar_chart'),
            ]),

            html.Div(id='t2_filler_div', children=''),

            html.Div(id='t2_setting_div1', children=[
                html.Button('START', id='start', n_clicks=0),
                html.Div(id='start-text', children=''),
                html.Div(id='counts-output', children=''),
                html.Div(''),
                html.Div(['Max Counts', dcc.Input(id='max_counts', type='number', step=1, readOnly=False, value=max_counts, className='input', style={'background-color': counts_warning})]),
            ]),

            html.Div(id='t2_setting_div2', children=[
                dcc.Store(id='store-device', data=device),
                html.Button('STOP', id='stop'),
                html.Div(id='stop-text', children=''),
                html.Div(id='elapsed', children=''),
                html.Div(['Max Seconds', dcc.Input(id='max_seconds', type='number', step=1, readOnly=False, value=max_seconds, className='input', style={'background-color': seconds_warning})]),
                html.Div(id='cps', children=''),
            ]),

            html.Div(id='t2_setting_div3', children=[
                html.Div(id='compression_div', children=[
                    html.Div(['Resolution:', dcc.Dropdown(id='compression', options=[
                        {'label': '512 Bins', 'value': '16'},
                        {'label': '1024 Bins', 'value': '8'},
                        {'label': '2048 Bins', 'value': '4'},
                        {'label': '4096 Bins', 'value': '2'},
                        {'label': '8192 Bins', 'value': '1'},
                    ], value=compression, className='dropdown')], style={'display': serial}),

                    html.Div(['Select existing file:', dcc.Dropdown(id='filenamelist', options=options_sorted, value=filename, className='dropdown', optionHeight=40)]),
                    
                    html.Div(['Or create new file:', dcc.Input(id='filename', type='text', value=filename, className='input', placeholder='Enter new filename')]),
                    
                    dbc.Modal([
                        dbc.ModalBody(id='modal-body'),
                        dbc.ModalFooter([
                            dbc.Button("Overwrite", id="confirm-overwrite", className="ml-auto", n_clicks=0),
                            dbc.Button("Cancel", id="cancel-overwrite", className="ml-auto", n_clicks=0),
                        ]),
                    ], id='modal-overwrite', is_open=False, centered=True, size="md", className="custom-modal"),
                    html.Div(id='start_process_flag', style={'display': 'none'}),
                    html.Div(['Number of bins:', dcc.Input(id='bins', type='number', value=bins)], className='input', style={'display': audio}),
                    html.Div(['Bin size:', dcc.Input(id='bin_size', type='number', value=bin_size)], className='input', style={'display': audio}),
                ]),
            ]),

            html.Div(id='t2_setting_div4', children=[
                html.Div(['Serial Command:', dcc.Dropdown(id='selected_cmd', options=[
                    {'label': 'Pause MCA', 'value': '-sto'},
                    {'label': 'Restart MCA', 'value': '-sta'},
                    {'label': 'Reset histogram', 'value': '-rst'},
                ], placeholder='Select command', value=None, className='dropdown')], style={'display': serial}),
                html.Div(id='cmd_text', children='', style={'display': 'none'}),
                html.Div(['LLD Threshold:', dcc.Input(id='threshold', type='number', value=threshold, className='input', style={'height': '35px'})], style={'display': audio}),
                html.Div(['Shape Tolerance:', dcc.Input(id='tolerance', type='number', value=tolerance, className='input')], style={'display': audio}),
                html.Div(['Update Interval(s)', dcc.Input(id='t_interval', type='number', step=1, readOnly=False, value=t_interval, className='input')]),
            ], style={'width': '10%'}),

            html.Div(id='t2_setting_div5', children=[
                html.Div('Comparison'),
                html.Div(dcc.Dropdown(id='filename_2', options=options_sorted, placeholder='Select comparison', value=filename_2, className='dropdown', optionHeight=40)),
                html.Div(['Show Comparison', daq.BooleanSwitch(id='compare_switch', on=False, color='purple')]),
                html.Div(['Subtract Comparison', daq.BooleanSwitch(id='difference_switch', on=False, color='purple')]),
            ]),

            html.Div(id='t2_setting_div6', children=[
                html.Div(['Energy by bin', daq.BooleanSwitch(id='epb-switch', on=epb_switch, color='purple')]),
                html.Div(['Show log(y)', daq.BooleanSwitch(id='log-switch', on=log_switch, color='purple')]),
                html.Div(['Calibration', daq.BooleanSwitch(id='cal-switch', on=cal_switch, color='purple')]),
                html.Div(['Coincidence', daq.BooleanSwitch(id='coi-switch', on=coi_switch, color='purple')], style={'display': audio}),
            ]),

            html.Div(id='t2_setting_div7', children=[
                html.Button('Sound <)', id='soundbyte', className='action_button'),
                html.Div(id='audio', children=''),
                html.Button('Update calib.', id='update_calib_button', className='action_button'),
                html.Div(id='update_calib_message', children=''),
                dbc.Button("Publish spectrum", id="publish-button", color="primary", className="action_button"),
                dbc.Modal(children=[
                    dbc.ModalBody(f"Are you sure you want to publish \"{filename}\" spectrum?"),
                    dbc.ModalFooter([
                        dbc.Button("Confirm", id="confirm-publish", className="ml-auto", color="primary"),
                        dbc.Button("Cancel", id="cancel-publish", className="mr-auto", color="secondary"),
                    ])], id="confirmation-modal", centered=True, size="md", className="custom-modal"),

                dcc.Store(id="confirmation-output", data=''),
                html.Button('isotope flags', id='toggle-annotations-button', n_clicks=0, className="action_button"),
                dcc.Store(id='store-gaussian'),
                dcc.Store(id='store-annotations', data=[]),
                html.Div('Gaussian (sigma)'),
                html.Div(dcc.Slider(id='sigma', min=0, max=3, step=0.25, value=sigma, marks={0: '0', 1: '1', 2: '2', 3: '3'})),
                dcc.Dropdown(id='flags', options=[
                    {'label': 'gamma flags', 'value': 'i/tbl/gamma.json'},
                    {'label': 'x-ray flags', 'value': 'i/tbl/xray.json'},
                    {'label': 'n-capture flags', 'value': 'i/tbl/ncapture.json'},
                ], style={'height': '15px', 'fontSize': '12px', 'borderwidth': '0px'}, value='i/tbl/gamma.json', className='dropdown', optionHeight=15),
            ]),

            html.Div(id='t2_setting_div8', children=[
                html.Div('Calibration Bins'),
                html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1, className='input')),
                html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2, className='input')),
                html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3, className='input')),
                html.Div('peakfinder'),
                html.Div(dcc.Slider(id='peakfinder', min=0, max=5, step=0.1, value=peakfinder, marks={0: '0', 1: '1',2: '2', 3: '3' , 4: '4', 5: '5'})),
            ]),

            html.Div(id='t2_setting_div9', children=[
                html.Div('Energies'),
                html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1, className='input')),
                html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2, className='input')),
                html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3, className='input')),
                html.Div(id='specNoteDiv', children=[
                    dcc.Textarea(id='spec-notes-input', value=spec_notes, placeholder='spectrum notes', cols=20, rows=6)], style={'marginTop': '15px', 'fontSize': '12px'}),
                html.Div(id='notes-warning', children=['Update notes after recording !']),
                html.Div(id='spec-notes-output', children='', style={'visibility': 'hidden'}),
            ]),
        ], style={'width':'100%', 'float':'left'}),
        html.Div(children=[html.Img(id='footer_tab2', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        html.Div(id='subfooter', children=[]),

    ])  # End of tab 2 render

    return html_tab2

@app.callback(
    Output('filename'       , 'value'),
    [Input('filenamelist'   , 'value')],
    [State('filename'       , 'value')]
)
def update_filename_from_dropdown(selected_file, current_filename):
    if selected_file:
        load_histogram(selected_file)
        return selected_file
    return current_filename

# Modal
@app.callback(
    [Output('modal-overwrite'   , 'is_open'),
     Output('modal-body'        , 'children')],
    [Input('start'              , 'n_clicks'), 
     Input('confirm-overwrite'  , 'n_clicks'), 
     Input('cancel-overwrite'   , 'n_clicks')],
    [State('filename', 'value') , 
     State('modal-overwrite'    , 'is_open')]
)
def confirm_with_user_2d(start_clicks, confirm_clicks, cancel_clicks, filename, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "start":
        file_exists = os.path.exists(f'{global_vars.data_directory}/{filename}.json')

        # Prevent overwriting files in the "i/" directory
        if filename.startswith("i/"):
            return False, f'Overwriting files in the "i/" directory is not allowed.'

        if file_exists:
            return True, f'Overwrite "{filename}.json"?'

    elif button_id in ["cancel-overwrite", "cancel-overwrite"]:
        return False, ''

    return False, ''

#start
@app.callback(
    Output('start-text'         , 'children'),
    [Input('confirm-overwrite'  , 'n_clicks'),
     Input('start'              , 'n_clicks')],
    [State('filename'           , 'value'),
     State('compression'        , 'value'),
     State('t_interval'         , 'value'),
     State('coi-switch'        , 'on'),
     State('store-device'       , 'data')]
)
def start_new_2d_spectrum(confirm_clicks, start_clicks, filename, compression, t_interval, coi_switch, dn):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    mode = 4 if coi_switch else 2

    trigger_id      = ctx.triggered[0]['prop_id'].split('.')[0]
    trigger_value   = ctx.triggered[0]['value']
    file_exists     = os.path.exists(f'{global_vars.data_directory}/{filename}.json')

    if trigger_value == 0:
        raise PreventUpdate

    if (trigger_id == 'confirm-overwrite') or (trigger_id == 'start' and not file_exists):
        if dn >= 100:
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
                shproto.dispatcher.process_01(filename, compression, "MAX", t_interval)
                logger.info(f'tab2 calls process_01(){filename}, {compression}, MAX, {t_interval}\n')

                time.sleep(0.1)

            except Exception as e:
                logger.error(f'tab 2 start_new_2d_spectrum() error {e}\n')
                return f"tab2 Error: {str(e)}"
        else:
            start_recording(mode)
            logger.info(f'tab2 start_recording(mode {mode}) passed.\n_clicks')
        return ""

    raise PreventUpdate

# Stop Button function--------------
@app.callback(
    Output('stop-text', 'children'),
    [Input('stop', 'n_clicks')],
    [State('store-device', 'data')]
)
def stop_button(n_clicks, dn):
    if n_clicks is None:
        raise PreventUpdate

    logger.info('tab2 stop button. clicked\n')


    if dn is None:
        logger.error('Device number is None\n')
        raise PreventUpdate

    if dn >= 100:
        logger.info('tab2 stop_button shproto.dispatcher\n')
        spec = threading.Thread(target=shproto.dispatcher.stop)
        spec.start()
        time.sleep(0.1)
    else:
        stop_recording()
        logger.info('tab2 stop_recording() for audio device\n')
    return


# UPDATE GRAPH ----------------------------------

@app.callback([
               Output('bar_chart'           , 'figure'), 
               Output('counts-output'       , 'children'),
               Output('elapsed'             , 'children'),
               Output('cps'                 , 'children'),
               Output('store-gaussian'      , 'data')],
              [Input('interval-component'   , 'n_intervals'),
               Input('bar_chart'            , 'relayoutData'),
               Input('store-annotations'    , 'data')], 
              [State('filename'             , 'value'),
               State('epb-switch'           , 'on'),
               State('log-switch'           , 'on'),
               State('cal-switch'           , 'on'),
               State('filename_2'            , 'value'),
               State('compare_switch'       , 'on'),
               State('difference_switch'    , 'on'),
               State('peakfinder'           , 'value'),
               State('sigma'                , 'value'),
               State('max_seconds'          , 'value'),
               State('max_counts'           , 'value'),
               State('coi-switch'          , 'on')]
               )
def update_graph(n, relayoutData, isotopes, filename, epb_switch, log_switch, cal_switch, filename_2, compare_switch, difference_switch, peakfinder, sigma, max_seconds, max_counts, coi_switch):
        
    ctx = callback_context

    # Check if the triggered input is the compare_switch
    if ctx.triggered and 'compare_switch' in ctx.triggered[0]['prop_id']:
        if compare_switch:
            try:
                load_histogram_2(filename_2)
            except Exception as e:
                logger.info(f'tab2 failed to load {filename_2}: {e}\n')    

    coincidence     = 'coincidence<br>(left if right)' if coi_switch else ""
    annotations     = []
    coefficients    = []
    prominence      = 0
    lines           = []
    gaussian        = []
    now             = datetime.now()
    date            = now.strftime('%d-%m-%Y')

    with global_vars.write_lock:
        counts          = global_vars.counts
        cps             = global_vars.cps
        elapsed         = global_vars.elapsed
        elapsed_2       = global_vars.elapsed_2
        bins            = global_vars.bins
        bins_2          = global_vars.bins_2
        histogram       = global_vars.histogram
        histogram_2     = global_vars.histogram_2
        coefficients_1  = global_vars.coefficients_1
        spec_notes      = global_vars.spec_notes


    layout = go.Layout(
        paper_bgcolor='white',
        plot_bgcolor='#f0f0f0',
        showlegend=False,
        height=460,
        margin=dict(t=20, b=0, l=0, r=0),
        autosize=True,
        yaxis=dict(range=[0, 'auto']),
        xaxis=dict(range=[0, 'auto']),
        annotations=annotations,
        shapes=lines,
        uirevision="Don't change",
    )

    fig = go.Figure(layout=layout)

    if compare_switch:
        try:
            load_histogram_2(filename_2)

        except:
            logger.info(f'tab2 failed to load {histogram_2}\n')

    if counts > 0:

        prominence = 0.5

        if sigma == 0:
            gaussian = []
        else:
            gaussian = gaussian_correl(histogram, sigma)

        x = list(range(bins))
        y = histogram

        try:
            max_value = np.max(y)
        except:
            max_value = 10    
        
        max_log_value = np.log10(max_value)

        if cal_switch:
            x = np.polyval(np.poly1d(coefficients_1), x)

        if epb_switch:
            y = [i * count for i, count in enumerate(histogram)]
            gaussian = [i * count for i, count in enumerate(gaussian)]

        trace1 = go.Bar(
            x=x, 
            y=y, 
            marker={'color': 'black', 'line': {'color': 'black', 'width': 0.5}},
            width=1.0
        )
        fig.add_trace(trace1)
    else:
        filename = 'no filename'
        y = [0]
        x = [0]
        trace1 = go.Bar(
            x=[0],
            y=[0],
            marker={'color': 'rgba(255,0,0,0.5)', 'line': {'color': 'rgba(255,0,0,0.5)', 'width': 0.5}},
            width=1.0
        )
        fig.add_trace(trace1)

    peaks, fwhm = peak_finder(y, prominence, peakfinder)

    for i in range(len(peaks)):
        peak_value  = peaks[i]
        bin_counts  = y[peaks[i]]
        x_pos       = peaks[i]
        y_pos       = y[peaks[i]]
        y_pos_ann   = int(y_pos *1.1)
        resolution  = (fwhm[i] / peaks[i]) * 100

        if y_pos_ann > (max_value * 0.9):
            y_pos_ann -= int(max_value * 0.03)

        if cal_switch:
            peak_value = np.polyval(np.poly1d(coefficients_1), peak_value)
            x_pos = peak_value

        if log_switch:
            y_pos_ann = np.log10(y_pos * 1.1)

        if peakfinder > 0:
            annotations.append(dict(
                x=x_pos,
                y=y_pos_ann,
                xref='x',
                yref='y',
                text=f'Y{bin_counts}<br>X{peak_value:.1f}<br>{resolution:.1f}%',
                align='center',
                showarrow=True,
                arrowhead=0,
                ax=0,
                ay=-40,
            ))

            lines.append(dict(
                type='line',
                x0=x_pos,
                y0=0,
                x1=x_pos,
                y1=y_pos,
                line=dict(color='red', width=1, dash='dot')
            ))

    if isotopes:
        annotations.extend(isotopes)

    fig.update_layout(
        annotations=annotations,
        title={
            'text': f'{filename}<br>{date}<br>{counts} counts<br>{elapsed} seconds<br>{coincidence}',
            'x': 0.85,
            'y': 0.9,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 14, 'color': 'black'},
        },
        shapes=lines
    )

    steps   = (elapsed / elapsed_2) if elapsed > 0 and elapsed_2 > 0 else 0.1

    x2      = list(range(bins_2))

    y2      = [int(n * steps) for n in histogram_2]

    if filename_2:

        if cal_switch:
            x2 = np.polyval(np.poly1d(global_vars.coefficients_2), x2)

        if log_switch:
            y2 = [x * 0.5 for x in y2]

        if epb_switch:
            y2 = [i * n * steps for i, n in enumerate(histogram_2)]

        trace2 = go.Scatter(
            x=x2, 
            y=y2, 
            marker={'color': 'red', 'line': {'color': 'red', 'width': 0.5}},
        )

        if compare_switch: 
            fig.add_trace(trace2)
            fig.update_layout(xaxis=dict(autorange=False))

        if difference_switch:
            y3 = [a - b for a, b in zip(y, y2)]
            trace3 = go.Bar(
                x=x,
                y=y3,
                marker={'color': 'green', 'line': {'color': 'green', 'width': 0.5}},
                width=1.0
            )
            fig = go.Figure(data=[trace3], layout=layout)
            fig.update_layout(yaxis=dict(autorange=True, range=[min(y3), max(y3)]))

        if not difference_switch:
            fig.update_layout(yaxis=dict(autorange=True))

    if sigma > 0:
        trace4 = go.Bar(
            x=x,
            y=gaussian,
            marker={'color': 'red', 'line': {'color': 'red', 'width': 0.5}},
            width=1.0
        )
        fig.add_trace(trace4)        

    if log_switch:
        fig.update_layout(yaxis=dict(autorange=False, type='log', range=[0.1, max_log_value + 0.3]))
    else:
        fig.update_layout(yaxis=dict(autorange=True, type='linear', range=[0, max(y)]))

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
            font=dict(size=16),
            align="center",
            bgcolor="white",
            bordercolor="lightgray",
            borderwidth=1
        )

    return fig, f'{counts}', f'{elapsed}', f'cps {cps}', gaussian

# SAVE SETTINGS ------------------------------------    

@app.callback(
    Output('polynomial'     , 'children'),
    [Input('bins'           , 'value'),
     Input('bin_size'       , 'value'),
     Input('max_counts'     , 'value'),
     Input('max_seconds'    , 'value'),
     Input('filename'       , 'value'),
     Input('filename_2'     , 'value'),
     Input('threshold'      , 'value'),
     Input('tolerance'      , 'value'),
     Input('calib_bin_1'    , 'value'),
     Input('calib_bin_2'    , 'value'),
     Input('calib_bin_3'    , 'value'),
     Input('calib_e_1'      , 'value'),
     Input('calib_e_2'      , 'value'),
     Input('calib_e_3'      , 'value'),
     Input('peakfinder'     , 'value'),
     Input('sigma'          , 'value'),
     Input('t_interval'     , 'value'),
     Input('compression'    , 'value'),
     Input('log-switch'     , 'on'),
     Input('epb-switch'     , 'on'),
     Input('cal-switch'     , 'on'),
     Input('coi-switch'     , 'on')]
)
def save_settings(*args):
    n_clicks = args[0]

    if n_clicks is None and not shproto.dispatcher.calibration_updated:
        raise PreventUpdate

    x_bins      = []
    x_energies  = []

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

    with global_vars.write_lock:
        global_vars.bins            = int(args[0])
        global_vars.bin_size        = int(args[1])
        global_vars.max_counts      = int(args[2])
        global_vars.max_seconds     = int(args[3])
        global_vars.filename        = args[4]
        global_vars.filename_2      = args[5]
        global_vars.threshold       = int(args[6])
        global_vars.tolerance       = int(args[7])
        global_vars.calib_bin_1     = int(args[8])
        global_vars.calib_bin_2     = int(args[9])
        global_vars.calib_bin_3     = int(args[10])
        global_vars.calib_e_1       = int(args[11])
        global_vars.calib_e_2       = int(args[12])
        global_vars.calib_e_3       = int(args[13])
        global_vars.peakfinder      = float(args[14])
        global_vars.sigma           = float(args[15])
        global_vars.t_interval      = int(args[16])
        global_vars.coeff_1         = round(coefficients[0], 6)
        global_vars.coeff_2         = round(coefficients[1], 6)
        global_vars.coeff_3         = round(coefficients[2], 6)
        global_vars.compression     = int(args[17])
        global_vars.log_switch      = args[18]
        global_vars.epb_switch      = args[19]
        global_vars.cal_switch      = args[20]
        global_vars.coi_switch      = args[21]

        global_vars.coefficients_1  = list(coefficients)
        global_vars.coeff_1         = round(coefficients[0], 6)
        global_vars.coeff_2         = round(coefficients[1], 6)
        global_vars.coeff_3         = round(coefficients[2], 6)


    save_settings_to_json()
        

    device = get_device_number()

    if device >= 100:
        global_vars.bins    = int(8192/int(args[17]))
    else:
        global_vars.bins    = args[0]
    
    logger.info(f'Settings updated from tab2\n')
    return f'Polynomial (ax^2 + bx + c) = ({polynomial_fn})'


# Callback for playing sound
@app.callback(Output('audio'     , 'children'),
              [Input('soundbyte' , 'n_clicks')],
              [State('filename'  , 'value'),
              State('sigma'      , 'value')])    

def play_sound(n_clicks, filename, sigma):
    if n_clicks is None:
        raise PreventUpdate

    if sigma == 0:
        sigma = 1    

    with global_vars.write_lock:
        gaussian = gaussian_correl(global_vars.histogram, sigma)

    asp.make_wav_file(filename, gaussian)
    logger.info('Converting gaussian correlation to wav file\n')

    asp.play_wav_file(filename)
    logger.info(f'Playing soundfile {filename}.wav\n')
    return

@app.callback(
    Output('update_calib_message', 'children'),
    [Input('update_calib_button', 'n_clicks'),
     Input('filename', 'value')]
)
def update_json_calibration(n_clicks, filename):
    if n_clicks is None:
        raise PreventUpdate

    update_coeff(filename)

    logger.info(f'tab2 Calibration updated')
    return f"Update {n_clicks}"

@app.callback(
    Output('cmd_text'       , 'children'),
    [Input('selected_cmd'   , 'value')],
    [State('tabs'           , 'value')]
)
def update_output(selected_cmd, active_tab):

    if active_tab != 'tab_2':
        raise PreventUpdate

    logger.info(f'tab2 command sent: {selected_cmd}\n')

    try:
        shproto.dispatcher.process_03(selected_cmd)

        return f'Cmd: {selected_cmd}'

    except Exception as e:

        logging.error(f"Error in update_output tab2: {e}")

        return "An error occurred."

@app.callback(
    Output("confirmation-modal", "is_open"),
    [Input("publish-button", "n_clicks"),
     Input("confirm-publish", "n_clicks"),
     Input("cancel-publish", "n_clicks")],
    [State("confirmation-modal", "is_open")]
)
def toggle_modal(open_button_clicks, confirm_button_clicks, cancel_publish_clicks, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "publish-button" and open_button_clicks:
        return not is_open
    elif button_id in ["confirm-publish", "cancel-publish"]:
        return not is_open
    return is_open


@app.callback(
    Output("store-confirmation-output", "data"),
    [Input("confirm-publish", "n_clicks"),
     Input("cancel-publish", "n_clicks")],
    [State("filename", "value")]
)
def display_confirmation_result(confirm_publish_clicks, cancel_publish_clicks, filename):

    ctx = dash.callback_context

    if not ctx.triggered:
        return ""

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    

    if button_id == "confirm-publish" and confirm_publish_clicks:

        logger.info(f'tab2 user confirmed publishing of {filename}\n')

        response_message = publish_spectrum(filename)

        logger.info(f'{filename} published successfully')

        return f'{filename} \nPublished'

    elif button_id == "cancel-publish" and cancel_publish_clicks:

        logger.info(f'Publish cancelled')

        return "You canceled!"
    return ""

@app.callback(
    Output('spec-notes-output'  , 'children'),
    [Input('spec-notes-input'   , 'value'),
     Input('filename'           , 'value')],
)
def update_spectrum_notes(spec_notes, filename):

    with global_vars.write_lock:
        global_vars.spec_notes = spec_notes

    if not global_vars.run_flag.is_set():
                
        update_json_notes(filename, spec_notes)

        logger.info(f'tab2 spectrum notes updated {spec_notes}\n')

    return spec_notes

app.layout = show_tab2()

@app.callback(
    Output('store-annotations'          , 'data'),
    Output('toggle-annotations-button'  , 'children'),
    Output('flags'                      , 'value'),
    Input('toggle-annotations-button'   , 'n_clicks'),
    Input('flags'                       , 'value'),
    State('store-gaussian'              , 'data'),
    State('sigma'                       , 'value'),
    State('cal-switch'                  , 'on')
)
def toggle_annotations(n_clicks, flags, gaussian, sigma, cal_switch):
    if n_clicks is None:
        raise PreventUpdate

    n_clicks += 1
    with global_vars.write_lock:
        coefficients = global_vars.coefficients_1

    if n_clicks % 2 == 0:
        if gaussian is not None and coefficients is not None:

            path_isotopes   = os.path.join(data_directory, flags)
            gc_calibrated   = calibrate_gc(gaussian, coefficients)
            peaks           = find_peaks_in_gc(gaussian, sigma=sigma)
            isotopes_data   = get_isotopes(path_isotopes)
            matches         = matching_isotopes(gc_calibrated, peaks, isotopes_data, sigma)
            annotations     = []


            for idx, (x, y, isotopes) in matches.items():
                isotope_names = ', '.join([isotope['isotope'] for isotope in isotopes])
                y_pos = 0.85 - ((idx % 16) * 0.03)

                annotations.append(
                    dict(
                        x=x,
                        y=y_pos,
                        xref='x',
                        yref='paper',
                        text=isotope_names,
                        showarrow=True,
                        arrowhead=None,
                        ax=0,
                        ay=-40,
                        font=dict(size=10, color='blue'),
                        xanchor='left',
                        yanchor='bottom',
                        align='right',
                        bgcolor='white'
                    )
                )

            if not cal_switch or sigma == 0:
                return [], '! Turn on calib first', flags

            return annotations, 'Isotope Flags On', flags

        return [], '', flags

    return [], 'Isotopes Flags off', flags

if __name__ == '__main__':
    app.run_server(debug=True)

# -- End of tab2.py --
