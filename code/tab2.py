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
from datetime import datetime

path = None
n_clicks = 0

def show_tab2():

    conn            = sql.connect("data.db")
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


    html_tab2 = html.Div(id='tab2', children=[

        html.Div(id='bar_chart_div', # Histogram Chart
            children=[
                dcc.Graph(id='bar-chart', figure={},),
                dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0) # Refresh rate 1s.
            ]),

        #Start button
        html.Div(id='t2_setting_div', children=[
            html.Button( 'START' , id='start'),
            html.Div(id='counts', children= ''),
            html.Div('Counts'),
            ]),

        #Stop button
        html.Div(id='t2_setting_div', children=[
            html.Button( 'CLEAR FILE' , id='stop'),
            html.Div(id='elapsed', children= '' ),
            html.Div('Seconds'),
            html.Div(id='stop_text', children= ''),
            ]),

        html.Div(id='t2_setting_div', children=[
            html.Div(['File name     :', dcc.Input(id='filename'    ,type='text'    ,value=filename )]),
            html.Div(['Number of bins:', dcc.Input(id='bins'        ,type='number'  ,value=bins )]),
            html.Div(['bin size      :', dcc.Input(id='bin_size'    ,type='number'  ,value=bin_size )]),
            ]), 


        html.Div(id='t2_setting_div', children=[
            html.Div(['Max counts    :', dcc.Input(id='max_counts', type='number', value=max_counts )]),
            html.Div(['LLD Threshold:', dcc.Input(id='threshold', type='number', value=threshold )]),
            html.Div(['Shape Tolerance:', dcc.Input(id='tolerance', type='number', value=tolerance )]),
            ]),

        html.Div(id='t2_setting_div'    , children=[
            html.Div(['Energy per bin'  , daq.BooleanSwitch(id='epb_switch',on=False, color='purple',)]),
            html.Div(['Show log(y)'     , daq.BooleanSwitch(id='log_switch',on=False, color='purple',)]),
            html.Div(['Calibtration'    , daq.BooleanSwitch(id='cal_switch',on=False, color='purple',)]),
            ]),

        
        html.Div(id='t2_setting_div', children=[]),

        html.Div(id='t2_setting_div', children=[
            html.Div('Calibration Bins'),
            html.Div(dcc.Input(id='calib_bin_1', type='number', value=calib_bin_1)),
            html.Div(dcc.Input(id='calib_bin_2', type='number', value=calib_bin_2)),
            html.Div(dcc.Input(id='calib_bin_3', type='number', value=calib_bin_3)),
            ]),

        html.Div(id='t2_setting_div', children=[
            html.Div('Calibration Energies'),
            html.Div(dcc.Input(id='calib_e_1', type='number', value=calib_e_1)),
            html.Div(dcc.Input(id='calib_e_2', type='number', value=calib_e_2)),
            html.Div(dcc.Input(id='calib_e_3', type='number', value=calib_e_3)),
            html.Div(id='settings'  , children =''),
            ]),


        html.Div(children=[ html.Img(id='footer', src='assets/footer.jpg'),]),

        
        html.Div(id='start_text' , children =''),
        

    ]) # End of tab 2 render

    return html_tab2


#------START---------------------------------

@app.callback( Output('start_text'  ,'children'),
                [Input('start'      ,'n_clicks')])

def update_output(n_clicks):
    
    if n_clicks != None:

        mode = 1
        pc.pulsecatcher(mode)

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
                Output('elapsed'            ,'children')],
               [Input('interval-component'  ,'n_intervals'), 
                Input('filename'            ,'value'), 
                Input('epb_switch'          ,'on'),
                Input('log_switch'          ,'on'),
                Input('cal_switch'          ,'on')
                ])

def update_graph(n, filename, epb_switch, log_switch, cal_switch):

    if os.path.exists(f'../data/{filename}.json'):
        with open(f"../data/{filename}.json", "r") as f:

            data = json.load(f)
            numberOfChannels    = data["resultData"]["energySpectrum"]["numberOfChannels"]
            validPulseCount     = data["resultData"]["energySpectrum"]["validPulseCount"]
            elapsed             = data["resultData"]["energySpectrum"]["measurementTime"]
            polynomialOrder     = data["resultData"]["energySpectrum"]["energyCalibration"]["polynomialOrder"]
            coefficients        = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
            spectrum            = data["resultData"]["energySpectrum"]["spectrum"]


            x = list(range(numberOfChannels))

            if cal_switch == True:
                polynomial_function = np.poly1d(coefficients)
                x = np.polyval(polynomial_function, x)


            if epb_switch == True:
                y = [i * count for i, count in enumerate(spectrum)]

            elif log_switch == True:
                y = [i * np.log10(count) for i, count in enumerate(spectrum)]
            else: 
                y = spectrum

            trace = go.Bar(x=x, y=y, width=1, marker={'color': 'darkblue'})
            layout = go.Layout(
                paper_bgcolor = 'white', 
                plot_bgcolor = 'white',
                title={
                'text': 'Pulse Height Histogram',
                'x': 0.5,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
            },
                height  =600, 
                autosize=True,
                xaxis=dict(dtick=50, tickangle = 90),

                )
            return go.Figure(data=[trace], layout=layout), validPulseCount, elapsed

    else:
        layout = go.Layout(title={
            'text': 'Pulse Height Histogram',
            'x': 0.5,
            'y': 0.9,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
        },
            height=600, 
            autosize=True,
            xaxis=dict(dtick=50),

            )
        return go.Figure(data=[], layout=layout), 0, 0

#--------UPDATE SETTINGS-------------------
@app.callback( Output('settings'        ,'children'),
                [Input('bins'           ,'value'),
                Input('bin_size'        ,'value'),
                Input('max_counts'      ,'value'),
                Input('filename'        ,'value'),
                Input('threshold'       ,'value'),
                Input('tolerance'       ,'value'),
                Input('calib_bin_1'     ,'value'),
                Input('calib_bin_2'     ,'value'),
                Input('calib_bin_3'     ,'value'),
                Input('calib_e_1'       ,'value'),
                Input('calib_e_2'       ,'value'),
                Input('calib_e_3'       ,'value')
                ])  


def save_settings(bins, bin_size, max_counts, filename, threshold, tolerance, calib_bin_1, calib_bin_2, calib_bin_3, calib_e_1, calib_e_2, calib_e_3):

    conn = sql.connect("data.db")
    c = conn.cursor()

    query = f"""UPDATE settings SET 
                    bins={bins}, 
                    bin_size={bin_size}, 
                    max_counts={max_counts}, 
                    name='{filename}', 
                    threshold={threshold}, 
                    tolerance={tolerance}, 
                    calib_bin_1={calib_bin_1},
                    calib_bin_2={calib_bin_2},
                    calib_bin_3={calib_bin_3},
                    calib_e_1={calib_e_1},
                    calib_e_2={calib_e_2},
                    calib_e_3={calib_e_3}
                    WHERE id=0;"""
    
    c.execute(query)
    conn.commit()

    calibration_input = [{'bin':-1*calib_e_1, 'energy':-1*calib_e_1}, {'bin':-1*calib_bin_2, 'energy':-1*calib_e_2}, {'bin':-1*calib_bin_3, 'energy':-1*calib_e_3}, {'bin':calib_e_1, 'energy':calib_e_1}, {'bin':calib_bin_2, 'energy':calib_e_2}, {'bin':calib_bin_3, 'energy':calib_e_3}]

    x_data = [item['bin'] for item in calibration_input]
    y_data = [item['energy'] for item in calibration_input]

    coefficients = np.polyfit(x_data, y_data, 2)

    polynomial_fn = np.poly1d(coefficients)

    conn = sql.connect("data.db")
    c = conn.cursor()

    query = f"""UPDATE settings SET 
                    coeff_1={float(coefficients[0])},
                    coeff_2={float(coefficients[1])},
                    coeff_3={float(coefficients[2])}
                    WHERE id=0;"""
    
    c.execute(query)
    conn.commit()

    return str(polynomial_fn)
