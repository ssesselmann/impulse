import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import os
import json
import glob
import numpy as np
import sqlite3 as sql
import dash_daq as daq
import audio_spectrum as asp
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app
from dash.exceptions import PreventUpdate
from datetime import datetime

path = None
n_clicks = None
global_counts = 0
global_cps = 0
grand_cps = 0

data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")

def show_tab2():

    global global_counts
    global global_cps
    global cps_list
    global grand_cps

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

    if max_counts == 0:
        counts_warning = 'red'
    else: 
        counts_warning = 'white'    

    if max_seconds == 0:
        seconds_warning = 'red'
    else: 
        seconds_warning = 'white' 

    html_tab2 = html.Div(id='tab2', children=[
        html.Div(id='polynomial', children=''),
        html.Div(id='bar_chart_div', # Histogram Chart
            children=[
                dcc.Graph(id='bar-chart', figure={},),
                dcc.Interval(id='interval-component', interval=1000, n_intervals=0) # Refresh rate 1s.
            ]),

        html.Div(id='t2_filler_div', children=''),
        #Start button
        html.Div(id='t2_setting_div1', children=[
            html.Button('START', id='start'),
            html.Div(id='start_text', children=''),
            html.Div(id='counts', children= ''),
            html.Div(''),
            html.Div(['Max Counts', dcc.Input(id='max_counts', type='number', step=1000,  readOnly=False, value=max_counts, style={'background-color': counts_warning} )]),
            html.Div(id='grand_cps', children=''),
            ]),

        html.Div(id='t2_setting_div2', children=[            
            html.Button('STOP', id='stop'), 
            html.Div(id='stop_text', children=''),
            html.Div(id='elapsed', children= '' ),
            html.Div(['Max Seconds', dcc.Input(id='max_seconds', type='number', step=60,  readOnly=False, value=max_seconds, style={'background-color': seconds_warning} )]),
            html.Div(id='cps', children=''),
            ]),

        html.Div(id='t2_setting_div3', children=[
            html.Div(['File name:', dcc.Input(id='filename' ,type='text' ,value=filename )]),
            html.Div(['Number of bins:', dcc.Input(id='bins'        ,type='number'  ,value=bins )]),
            html.Div(['bin size      :', dcc.Input(id='bin_size'    ,type='number'  ,value=bin_size )]),
            ]), 


        html.Div(id='t2_setting_div4', children=[
            html.Div(['LLD Threshold:', dcc.Input(id='threshold', type='number', value=threshold )]),
            html.Div(['Shape Tolerance:', dcc.Input(id='tolerance', type='number', value=tolerance )]),
            html.Div(['Update Interval(s)', dcc.Input(id='t_interval', type='number', step=1,  readOnly=False, value=t_interval )]),
            ]),

        html.Div(id='t2_setting_div5', children=[
            html.Div('Select Comparison'),
            html.Div(dcc.Dropdown(
                    id='filename2',
                    options=options_sorted,
                    placeholder='Select acomparison',
                    value=filename2,
                    style={'font-family':'Arial', 'height':'32px', 'margin':'0px', 'padding':'0px','border':'None', 'text-align':'left'}
                    )),

            html.Div(['Show Comparison'      , daq.BooleanSwitch(id='compare_switch',on=False, color='purple',)]),
            html.Div(['Subtract Comparison'  , daq.BooleanSwitch(id='difference_switch',on=False, color='purple',)]),

            ]),

        html.Div(id='t2_setting_div6'    , children=[
            html.Div(['Energy by bin'  , daq.BooleanSwitch(id='epb_switch',on=False, color='purple',)]),
            html.Div(['Show log(y)'     , daq.BooleanSwitch(id='log_switch',on=False, color='purple',)]),
            html.Div(['Calibration'    , daq.BooleanSwitch(id='cal_switch',on=False, color='purple',)]),
            ]), 

        html.Div(id='t2_setting_div7', children=[
            html.Button('Gaussian sound <)' , id='soundbyte'),
            html.Div(id='audio', children=''),
            html.Button('Update calibration', id='update_calib_button'),
            html.Div(id='update_calib_message', children='')
        ]),

        html.Div(id='t2_setting_div8', children=[
            html.Div('Calibration Bins'),
            html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1)),
            html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2)),
            html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3)),
            html.Div('peakfinder'),
            html.Div(dcc.Slider(id='peakfinder', min=0 ,max=1, step=0.1, value= peakfinder, marks={0:'0', 1:'1'})),
            ]),

        html.Div(id='t2_setting_div9', children=[
            html.Div('Energies'),
            html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1)),
            html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2)),
            html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3)),
            html.Div('Gaussian corr. (sigma)'),
            html.Div(dcc.Slider(id='sigma', min=0 ,max=3, step=0.25, value= sigma, marks={0: '0', 1: '1', 2: '2', 3: '3'})),
            
            ]),

        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        
        html.Div(id='subfooter', children=[
            ]),

    ]) # End of tab 2 render

    return html_tab2

#------START---------------------------------

@app.callback( Output('start_text'  ,'children'),
                [Input('start'      ,'n_clicks')])

def update_output(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        mode = 2      
        fn.clear_global_cps_list()
        pc.pulsecatcher(mode)
        return ''
#----STOP------------------------------------------------------------

@app.callback( Output('stop_text'  ,'children'),
                [Input('stop'      ,'n_clicks')])

def update_output(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        fn.stop_recording()
        return " "
#-------UPDATE GRAPH---------------------------------------------------------

@app.callback([ Output('bar-chart'          ,'figure'), 
                Output('counts'             ,'children'),
                Output('grand_cps'          ,'children'),
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
                Input('sigma'               ,'value'),
                Input('tabs'                ,'value')
                ])

def update_graph(n, filename, epb_switch, log_switch, cal_switch, filename2, compare_switch, difference_switch, peakfinder, sigma, active_tab):

    if active_tab != 'tab2':  # only update the chart when "tab2" is active
        raise PreventUpdate

    global global_counts
    global grand_cps
    histogram1 = fn.get_path(f'{data_directory}/{filename}.json')
    histogram2 = fn.get_path(f'{data_directory}/{filename2}.json')

    if os.path.exists(histogram1):
        with open(histogram1, "r") as f:

            data = json.load(f)
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
                grand_cps = 0  
            else:
                cps = validPulseCount - global_counts
                global_counts = validPulseCount  
                grand_cps = validPulseCount / elapsed
     
            x = list(range(numberOfChannels))
            y = spectrum
            max_value = np.max(y)
            max_log_value = np.log10(max_value)

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
                xaxis=dict(dtick=50, tickangle = 90, range =[0, max(x)]),
                yaxis=dict(autorange=True),
                annotations=annotations,
                shapes=lines,
                uirevision="Don't change",
                )
#---------------Histrogram2 ---------------------------------------------------------------------------

            if os.path.exists(histogram2):
                with open(histogram2, "r") as f:
                    data_2 = json.load(f)
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

        return fig, f'{validPulseCount}', f'CPS {grand_cps:.2f}', f'{elapsed}', f'cps {cps}'

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
                xaxis=dict(dtick=50, tickangle = 90, range =[0, 100]),
                yaxis=dict(autorange=True),
                uirevision="Don't change",
                )
        return go.Figure(data=[], layout=layout), 0, 0, 0, 0

#--------UPDATE SETTINGS------------------------------------------------------------------------------------------
@app.callback( Output('polynomial'      ,'children'),
                [Input('bins'           ,'value'),
                Input('bin_size'        ,'value'),
                Input('max_counts'      ,'value'),
                Input('max_seconds'     ,'value'),
                Input('filename'        ,'value'),
                Input('filename2'       ,'value'),
                Input('threshold'       ,'value'),
                Input('tolerance'       ,'value'),
                Input('calib_bin_1'     ,'value'),
                Input('calib_bin_2'     ,'value'),
                Input('calib_bin_3'     ,'value'),
                Input('calib_e_1'       ,'value'),
                Input('calib_e_2'       ,'value'),
                Input('calib_e_3'       ,'value'),
                Input('peakfinder'      ,'value'),
                Input('sigma'           ,'value'),
                Input('t_interval'      ,'value')
                ])  

def save_settings(bins, bin_size, max_counts, max_seconds, filename, filename2, threshold, tolerance, calib_bin_1, calib_bin_2, calib_bin_3, calib_e_1, calib_e_2, calib_e_3, peakfinder, sigma, t_interval):
    
    database = fn.get_path(f'{data_directory}/.data.db')

    conn = sql.connect(database)
    c = conn.cursor()

    query = f"""UPDATE settings SET 
                    bins={bins}, 
                    bin_size={bin_size}, 
                    max_counts={max_counts}, 
                    name='{filename}', 
                    comparison='{filename2}',
                    threshold={threshold}, 
                    tolerance={tolerance}, 
                    calib_bin_1={calib_bin_1},
                    calib_bin_2={calib_bin_2},
                    calib_bin_3={calib_bin_3},
                    calib_e_1={calib_e_1},
                    calib_e_2={calib_e_2},
                    calib_e_3={calib_e_3},
                    peakfinder={peakfinder},
                    sigma={sigma},
                    t_interval={t_interval},
                    max_seconds={max_seconds}
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
    return

#------UPDATE CALIBRATION OF EXISTING SPECTRUM-------------------

@app.callback(
    Output('update_calib_message','children'),
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
