import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import os
import json
import numpy as np
import sqlite3 as sql
import dash_daq as daq
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app
from dash.exceptions import PreventUpdate

path = None
n_clicks = 0
global_counts = 0
global cps_list

def show_tab2():

    database = fn.get_path('data.db')
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


    html_tab2 = html.Div(id='tab2', children=[

        html.Div(id='bar_chart_div', # Histogram Chart
            children=[
                dcc.Graph(id='bar-chart', figure={},),
                dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0) # Refresh rate 1s.
            ]),

        #Start button
        html.Div(id='t2_setting_div', children=[
            html.Button('START', id='start'),
            html.Div(id='counts', children= ''),
            html.Div('Counts'),

            ]),

        html.Div(id='t2_setting_div', children=[
            html.Div(id='cps', children=''),
            html.Div(id='elapsed', children= '' ),
            html.Div('Seconds'),
            html.Div(id='stop_text', children= ''),
            ]),

        html.Div(id='t2_setting_div', children=[
            html.Div(['File name:', dcc.Input(id='filename' ,type='text' ,value=filename )]),
            html.Div(['Number of bins:', dcc.Input(id='bins'        ,type='number'  ,value=bins )]),
            html.Div(['bin size      :', dcc.Input(id='bin_size'    ,type='number'  ,value=bin_size )]),
            ]), 


        html.Div(id='t2_setting_div', children=[
            html.Div(['Stop at n counts', dcc.Input(id='max_counts', type='number', value=max_counts )]),
            html.Div(['LLD Threshold:', dcc.Input(id='threshold', type='number', value=threshold )]),
            html.Div(['Shape Tolerance:', dcc.Input(id='tolerance', type='number', value=tolerance )]),
            ]),

        html.Div(id='t2_setting_div', children=[

            html.Div(['Overlay or i/..', dcc.Input(id='filename2' ,type='text' ,value=filename2 )]),
            html.Div(['Show Comparison'      , daq.BooleanSwitch(id='compare_switch',on=False, color='purple',)]),
            html.Div(['Subtract Comparison'  , daq.BooleanSwitch(id='difference_switch',on=False, color='purple',)]),

            ]),


        html.Div(id='t2_setting_div'    , children=[
            html.Div(['Energy by bin'  , daq.BooleanSwitch(id='epb_switch',on=False, color='purple',)]),
            html.Div(['Show log(y)'     , daq.BooleanSwitch(id='log_switch',on=False, color='purple',)]),
            html.Div(['Calibration'    , daq.BooleanSwitch(id='cal_switch',on=False, color='purple',)]),
            ]),   

        html.Div(id='t2_setting_div', children=[
            html.Div('Calibration Bins'),
            html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1)),
            html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2)),
            html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3)),
            html.Div('peakfinder'),
            html.Div(dcc.Slider(id='peakfinder', min=0 ,max=1, step=0.01, value= peakfinder, marks=None,)),
            ]),

        html.Div(id='t2_setting_div', children=[
            html.Div('Energies'),
            html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1)),
            html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2)),
            html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3)),
            html.Div('Gaussian corr. (sigma)'),
            html.Div(dcc.Slider(id='sigma', min=0 ,max=3, step=0.01, value= sigma, marks=None,)),
            
            ]),

        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.png')]),
        
        html.Div(id='subfooter', children=[
            html.Div(id='start_text' , children =''),
            html.Button( 'CLEAR FILE' , id='stop'),
            html.Div(id='settings'  , children =''),
            ]),

    ]) # End of tab 2 render

    return html_tab2

#------START---------------------------------

@app.callback( Output('start_text'  ,'children'),
                [Input('start'      ,'n_clicks')])

def update_output(n_clicks):
    if n_clicks != None:
        fn.clear_global_cps_list()
        pc.pulsecatcher()
        return
#----STOP------------------------------------------------------------

@app.callback( Output('stop_text'  ,'children'),
                [Input('stop'      ,'n_clicks')])

def update_output(n_clicks):
    if n_clicks != 0:
        return 
#----------------------------------------------------------------

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
                Input('sigma'               ,'value'),
                Input('tabs'                ,'value')
                ])

def update_graph(n, filename, epb_switch, log_switch, cal_switch, filename2, compare_switch, difference_switch, peakfinder, sigma, active_tab):
    
    if active_tab != 'tab2':  # only update the chart when "tab3" is active
        raise PreventUpdate

    global global_counts
    histogram1 = fn.get_path(f'data/{filename}.json')
    histogram2 = fn.get_path(f'data/{filename2}.json')

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

            mu = 0
            #sigma = 0.5
            lin_log = 'linear'
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
     
            x = list(range(numberOfChannels))
            y = spectrum

            if cal_switch == True:
                x = np.polyval(np.poly1d(coefficients), x)

            if epb_switch == True:
                y = [i * count for i, count in enumerate(spectrum)]
                gc= [i * count for i, count in enumerate(gc)]

            if log_switch == True:
                lin_log = 'log'

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
                resolution  = (fwhm[i]/peaks[i])*100

                if cal_switch == True:
                    peak_value  = np.polyval(np.poly1d(coefficients), peak_value)
                    x_pos       = peak_value

                if log_switch == True:
                    y_pos = y_pos    

                if peakfinder != 0:
                    annotations.append(
                        dict(
                            x= x_pos,
                            y= y_pos + 10,
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

            if log_switch == True: # This is a botch due to a bug in plotly
                layout = go.Layout(
                    paper_bgcolor = 'white', 
                    plot_bgcolor = 'white',
                    title={
                    'text': filename,
                    'x': 0.5,
                    'y': 0.9,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'family': 'Arial', 'size': 24, 'color': 'black'},
                    },
                    height  =450, 
                    margin_t=0,
                    margin_b=0,
                    margin_l=0,
                    margin_r=0,
                    autosize=True,
                    xaxis=dict(dtick=50, tickangle = 90, range =[0, max(x)]),
                    yaxis=dict(type=lin_log),
                    uirevision="Don't change",
                    )
            else:
                layout = go.Layout(
                    paper_bgcolor = 'white', 
                    plot_bgcolor = 'white',
                    title={
                    'text': filename,
                    'x': 0.5,
                    'y': 0.9,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'family': 'Arial', 'size': 24, 'color': 'black'},
                    },
                    height  =450, 
                    margin_t=0,
                    margin_b=0,
                    margin_l=0,
                    margin_r=0,
                    autosize=True,
                    xaxis=dict(dtick=50, tickangle = 90, range =[0, max(x)]),
                    yaxis=dict(type=lin_log),
                    annotations=annotations,
                    shapes=lines,
                    uirevision="Don't change",
                    )
#-------Comparison spectrum ---------------------------------------------------------------------------

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

                    if log_switch == True:
                        lin_log = 'log'

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

#----------------------------------------------------------------------------------------------------------------                   
            
            if compare_switch == False:
                fig = go.Figure(data=[trace1, trace4], layout=layout), validPulseCount, elapsed, f'cps {cps}'

            if compare_switch == True: 
                fig = go.Figure(data=[trace1, trace2], layout=layout), validPulseCount, elapsed, f'cps {cps}'

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

                fig = go.Figure(data=[trace3], layout=layout), validPulseCount, elapsed, f'cps {cps}'

            return fig

    else:
        layout = go.Layout(
                paper_bgcolor = 'white', 
                plot_bgcolor = 'white',
                title={
                'text': filename,
                'x': 0.5,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
                },
                height  =450, 
                autosize=True,
                xaxis=dict(dtick=50, tickangle = 90, range =[0, max(x)]),
                yaxis=dict(type=lin_log),
                uirevision="Don't change",
                )
        return go.Figure(data=[], layout=layout), 0, 0, 0

#--------UPDATE SETTINGS------------------------------------------------------------------------------------------
@app.callback( Output('settings'        ,'children'),
                [Input('bins'           ,'value'),
                Input('bin_size'        ,'value'),
                Input('max_counts'      ,'value'),
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
                Input('sigma'           ,'value')
                ])  

def save_settings(bins, bin_size, max_counts, filename, filename2, threshold, tolerance, calib_bin_1, calib_bin_2, calib_bin_3, calib_e_1, calib_e_2, calib_e_3, peakfinder, sigma):
    
    database = fn.get_path('data.db')

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
                    sigma={sigma}
                    WHERE id=0;"""

    c.execute(query)
    conn.commit()

    calibration_input = [
        {'bin':-1*calib_bin_3, 'energy':-1*calib_e_3}, 
        {'bin':-1*calib_bin_2, 'energy':-1*calib_e_2}, 
        {'bin':-1*calib_bin_1, 'energy':-1*calib_e_1},
        {'bin':   calib_bin_1, 'energy':   calib_e_1}, 
        {'bin':   calib_bin_2, 'energy':   calib_e_2}, 
        {'bin':   calib_bin_3, 'energy':   calib_e_3}
        ]

    x_data = [item['bin'] for item in calibration_input]
    y_data = [item['energy'] for item in calibration_input]

    coefficients = np.polyfit(x_data, y_data, 2)

    polynomial_fn = np.poly1d(coefficients)

    conn = sql.connect(database)
    c = conn.cursor()

    query = f"""UPDATE settings SET 
                    coeff_1={float(coefficients[0])},
                    coeff_2={float(coefficients[1])},
                    coeff_3={float(coefficients[2])}
                    WHERE id=0;"""
    
    c.execute(query)
    conn.commit()

    return f'Polynomial (a + bx + cx^2) = ({polynomial_fn})'
