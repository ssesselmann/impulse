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

path = None

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
        ],style={'width':'100%', 'height':'90%'}),

        #Start button
        html.Div( children=[
            html.Button( 'START' , id='start', style={'background-color':'lightgreen','border-radius':'9px', 'height':'30px', 'width':'150px'}),
            html.Div(id='counts', children= '' , style={'fontSize':'50px','color':'blue', 'text-align':'center', 'fontFamily':'Arial', 'fontWeight' : 'bold'}),

            ],style={'width':'10%', 'height':'150px', 'padding':'20px', 'background-color':'orange', 'text-align':'center', 'color':'green', 'float':'left'}
        ),

        #Stop button
        html.Div( children=[
            html.Button( 'CLEAR FILE' , id='stop', style={'background-color':'red','border-radius':'9px', 'height':'30px', 'width':'150px'}),
            html.Div(id='stop_text', children= '' , style={'fontSize':'10px','color':'blue', 'text-align':'center', 'fontFamily':'Arial', 'fontWeight' : 'bold'}),
            ],style={'width':'10%', 'height':'150px','padding':'20px', 'background-color':'orange', 'text-align':'center', 'color':'green', 'float':'left'}
        ),

        html.Div(children=[
            html.Div(['File name     :', dcc.Input(id='filename', type='text', value=name)]),
            html.Div(['Number of bins:', dcc.Input(id='bin_qty', type='number', value=bins)]),
            html.Div(['Bin Size      :', dcc.Input(id='bin_size', type='number', value=bin_size)]),
            html.Div(['Max counts    :', dcc.Input(id='max_counts', type='number', value=max_counts)]),
        ],style={'width':'74%', 'height':'150px','padding':'20px', 'background-color':'orange', 'text-align':'left', 'color':'blue', 'float':'left', 'fontFamily':'Arial'}
        ),

        html.Div(
            
            ),

        
        html.Div(id='start_text' , children =''),
        html.Div(id='settings'  , children =''),
        

    ],style={'width':'100%' , 'height':'100%','background-color':'lightgray', 'float': 'left', 'padding':'30px'}) # End of tab 2 render

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

@app.callback([Output('bar-chart'            ,'figure'),(Output('counts', 'children'))],
              [Input('interval-component'   ,'n_intervals'), Input('filename', 'value')])

def update_graph(n, filename):

    if os.path.exists(f'../data/{filename}.json'):
        with open(f"../data/{filename}.json", "r") as f:
            data = json.load(f)
            schemaVersion       = data["schemaVersion"]
            startTime           = data["startTime"]
            endTime             = data["endTime"]
            numberOfChannels    = data["resultData"]["energySpectrum"]["numberOfChannels"]
            validPulseCount     = data["resultData"]["energySpectrum"]["validPulseCount"]
            measurementTime     = data["resultData"]["energySpectrum"]["measurementTime"]
            polynomialOrder     = data["resultData"]["energySpectrum"]["energyCalibration"]["polynomialOrder"]
            coefficients        = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
            spectrum            = data["resultData"]["energySpectrum"]["spectrum"]

            x = list(range(numberOfChannels))
            y = spectrum

            trace = go.Bar(x=x, y=y, width=1, marker={'color': 'darkblue'})
            layout = go.Layout(title={
                'text': 'Pulse Height Histogram',
                'x': 0.5,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
            },
                #title='GS Pulse Height Histogram', 
                height  =700, 
                autosize=True
                )
            return go.Figure(data=[trace], layout=layout), validPulseCount

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
                Input('filename'        ,'value'),])


def save_settings(bin_qty, bin_size, max_counts, filename):

    conn = sql.connect("data.db")
    c = conn.cursor()

    query = f"UPDATE settings SET bins={bin_qty}, bin_size={bin_size}, max_counts={max_counts}, name='{filename}' WHERE id=0;"
    c.execute(query)
    conn.commit()


    return 
