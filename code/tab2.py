import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import os
import json
import sqlite3 as sql
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app
from datetime import datetime

path = None
n_intervals = 0

def show_tab2():

    conn            = sql.connect("data.db")
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 
    settings        = c.fetchall()[0]

    name            = settings[1]
    device          = settings[2]             
    sample_rate     = settings[3]
    chunk_size      = settings[4]
    threshold       = settings[5]
    tolerance       = settings[6]
    bins            = settings[7]
    bin_size        = settings[8]
    max_counts      = settings[9]


    html_tab2 = html.Div([

        html.Div( children=[
            dcc.Graph(id='bar-chart', figure={},),
            dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0)
        ],style={'width':'96%', 'height':'90%', 'background-color':'lightgray'}),

        #Start button
        html.Div( children=[
            html.Button( 'START' , id='start', style={'background-color':'lightgreen','border-radius':'9px', 'height':'30px', 'width':'150px'}),
            html.Div(id='counts', children= '' , style={'fontSize':'50px','color':'blue', 'text-align':'center', 'fontFamily':'Arial', 'fontWeight' : 'bold'}),

            ],style={'width':'10%', 'height':'150px', 'padding':'20px', 'background-color':'orange', 'text-align':'center', 'color':'green', 'float':'left'}
        ),

        #Stop button
        html.Div( children=[
            html.Button( 'CLEAR FILE' , id='stop', style={'background-color':'red','border-radius':'9px', 'height':'30px', 'width':'150px'}),
            html.Div(id='elapsed', children= '' , style={'fontSize':'50px','color':'blue', 'text-align':'center', 'fontFamily':'Arial', 'fontWeight' : 'bold'}),
            html.Div(id='stop_text', children= '' , style={'fontSize':'10px','color':'blue', 'text-align':'center', 'fontFamily':'Arial', 'fontWeight' : 'bold'}),
            ],style={'width':'10%', 'height':'150px','padding':'20px', 'background-color':'orange', 'text-align':'center', 'color':'green', 'float':'left'}
        ),

        html.Div(children=[
            html.Div(['File name     :', dcc.Input(id='filename', type='text', value=name, style={'text-align':'right'})]),
            html.Div(['Number of bins:', dcc.Input(id='bin_qty', type='number', value=bins, style={'text-align':'right'})]),
            html.Div(['Bin Size      :', dcc.Input(id='bin_size', type='number', value=bin_size, style={'text-align':'right'})]),
            html.Div(['Max counts    :', dcc.Input(id='max_counts', type='number', value=max_counts, style={'text-align':'right'})]),
        ],style={'width':'10%', 'height':'150px','padding':'20px', 'background-color':'orange', 'text-align':'right', 'color':'blue', 'float':'left', 'fontFamily':'Arial'}
        ),


        html.Div(children=[
            html.Div(['LLD Threshold:', dcc.Input(id='threshold', type='number', value=threshold, style={'text-align':'right'})]),
            html.Div(['Shape Tolerance:', dcc.Input(id='tolerance', type='number', value=tolerance, style={'text-align':'right'})]),
        ],style={'width':'10%', 'height':'150px','padding':'20px', 'background-color':'orange', 'text-align':'right', 'color':'blue', 'float':'left', 'fontFamily':'Arial'}
        ),

        html.Div(
            
            ),

        
        html.Div(id='start_text' , children =''),
        html.Div(id='settings'  , children =''),
        

    ],style={'width':'100%' , 'height':'100%','background-color':'orange', 'float': 'left', 'padding':'30px'}) # End of tab 2 render

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

    if n_clicks % 2 == 0:

        return "not working"

#----------------------------------------------------------------

@app.callback([ Output('bar-chart'  ,'figure'), Output('counts'     ,'children'),Output('elapsed'    ,'children')],
              [ Input('interval-component'   ,'n_intervals'), Input('filename'    ,'value')])

def update_graph(n, filename):

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
                #title='GS Pulse Height Histogram', 
                height  =700, 
                autosize=True,

                )
            return go.Figure(data=[trace], layout=layout), validPulseCount, elapsed[:-7]

    else:
        layout = go.Layout(title={
            'text': 'Pulse Height Histogram',
            'x': 0.5,
            'y': 0.9,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
        },
            #title='GS Pulse Height Histogram', 
            height=700, 
            autosize=True
            )
        return go.Figure(data=[], layout=layout), 0

#--------UPDATE SETTINGS-------------------
@app.callback( Output('settings'        ,'children'),
                [Input('bin_qty'        ,'value'),
                Input('bin_size'        ,'value'),
                Input('max_counts'      ,'value'),
                Input('filename'        ,'value'),
                Input('threshold'       ,'value'),
                Input('tolerance'       ,'value'),
                ])


def save_settings(bin_qty, bin_size, max_counts, filename, threshold, tolerance):

    conn = sql.connect("data.db")
    c = conn.cursor()

    query = f"UPDATE settings SET bins={bin_qty}, bin_size={bin_size}, max_counts={max_counts}, name='{filename}', threshold={threshold}, tolerance={tolerance} WHERE id=0;"
    c.execute(query)
    conn.commit()


    return 
