import dash
import json
import os
import time
import logging
import plotly.graph_objs as go
import functions as fn
import dash_daq as daq
import sqlite3 as sql
import pandas as pd

from datetime import datetime
from dash import html, dcc
from dash.dependencies import Input, Output, State
from server import app

logger = logging.getLogger(__name__)

data_directory = os.path.join(os.path.expanduser("~"), "impulse_data")

t_interval = 1

def show_tab4():

    # Get some settings from database----------
    database = fn.get_path(f'{data_directory}/.data_v2.db')
    conn = sql.connect(database)
    c = conn.cursor()
    c.execute("SELECT * FROM settings") 

    settings = c.fetchall()[0]
    filename = settings[1]
    t_interval = settings[27]
    rolling = settings[31]
    t_interval = int(t_interval)
    interval = 1000

    html_tab4 = html.Div(id='tab4', children=[
        html.Div(dcc.Input(id='filename', type='text', value=settings[1], style={'display': 'none'})),
        html.Div(id='count_rate_div', # Histogram Chart
            children=[
                dcc.Graph(id='count_rate_chart', figure={}),
                dcc.Interval(id='interval_component', interval=interval), # Refresh rate 1s.
                html.Div(['Update Interval (s)', dcc.Input(id='t_interval', type='number', step=1, readOnly=False, value=t_interval)], style={'display':'none'}),
                html.Div('Sum Counts ', style={'textAlign':'left', 'marginLeft':'20px'}),
                html.Div(children=[dcc.Slider(
                    id='rolling', 
                    min=0, max=3600, 
                    step=1, value=rolling, 
                    marks={0:'0', 300:'300', 600:'600', 900:'900', 1200:'1200', 1500:'1500', 1800:'1800', 2100:'2100', 2400:'2400', 2700:'2700', 3000:'3000', 3300:'3300', 3600:'3600'}
                )]),
            

        html.Div(children=[
                    daq.ToggleSwitch(
                        id='full-monty',
                        label='Last hour | Show all',
                        value=False,
                        color='purple'
                    )
                ], style={'width': '200px', 'float':'right', 'marginTop':'40px'})
            ]),

        html.Div(html.H5('Start and Stop from 2D tab.'), style={'textAlign':'left', 'marginTop':'10px', 'marginLeft':'5%'}),
        html.Div(children=[html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        html.Div(id='saved', children=''),
    ])

    conn.close()

    return html_tab4

#-----------------END of Page---------------------------------------------------

@app.callback(
    Output('count_rate_chart', 'figure'),
    [Input('interval_component', 'n_intervals'),
     Input('filename', 'value'),
     Input('t_interval', 'value'),
     Input('full-monty', 'value')],
    [State('tabs', 'value'), 
     State('rolling', 'value')]
)
def update_count_rate_chart(n_intervals, filename, t_interval, full_monty, tab, rolling):
    cps_file = fn.get_path(f'{data_directory}/{filename}-cps.json')

    if os.path.exists(cps_file):
        try:
            with open(cps_file, "r") as f:
                count_data = json.load(f)
                
            countrate = count_data.get("cps", [])
            total_counts = sum(countrate)
            now = datetime.now()
            time_str = now.strftime('%d/%m/%Y')
            
            try:
                elapsed = int(count_data.get("elapsed", 0))
            except ValueError:
                elapsed = 0

            if not full_monty:
                start_index = max(0, len(countrate) - 3600 // t_interval)
                countrate = countrate[start_index:]
                x = [str(i * t_interval) for i in range(start_index, start_index + len(countrate))]
            else:
                x = [str(i * t_interval) for i in range(len(countrate))]
            
            y = list(map(int, countrate))  # convert y values from string to integer

            line = go.Scatter(x=x, y=y, mode='markers+lines', marker=dict(size=4, color='black'), line=dict(width=1, color='purple'), name='counts per sec.')
            # create pandas series for y data
            y_series = pd.Series(y)
            # create counts per t_interval
            rolling_series = y_series.rolling(window=rolling // t_interval, min_periods=rolling // t_interval).sum()
            # create scatter trace for rolling average line
            rolling_line = go.Scatter(x=x, y=rolling_series, mode='lines', line=dict(width=2, color='green'), name=f'{rolling} second countrate')

            layout = go.Layout(
                title={
                    'text': f'{filename} | Counts | {time_str}',
                    'x': 0.5,
                    'y': 0.9,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'family': 'Arial', 'size': 20, 'color': 'black'}
                },
                xaxis=dict(
                    title='Seconds',
                    tickmode='auto',
                    tickangle=90,
                    tickfont=dict(family='Arial', size=14, color='black'),
                    titlefont=dict(family='Arial', size=18, color='black'),
                    type='linear',
                    showline=True,
                    linewidth=2,
                    linecolor='black',
                    ticks='outside'
                ),
                yaxis=dict(
                    title='Counts',
                    type='linear',
                    tickfont=dict(family='Arial', size=14, color='black'),
                    titlefont=dict(family='Arial', size=18, color='black')
                ),
                annotations=[
                    dict(
                        text=f"{rolling} Second average<br>{total_counts} Total counts<br>{elapsed} Seconds total",
                        x=0.95,
                        y=0.95,
                        xref='paper',
                        yref='paper',
                        showarrow=False,
                        font=dict(family='Arial', size=16, color='black')
                    )
                ],
                uirevision="Don't change",
                height=600,
                margin=dict(l=80, r=50, t=100, b=50),
                paper_bgcolor='white',
                plot_bgcolor='#efefef',
                showlegend=False,   
            )

            fig = go.Figure(data=[line, rolling_line], layout=layout)
        
        except json.JSONDecodeError:
            logger.error(f"JSONDecodeError: Could not decode {cps_file}")
            fig = {
                'data': [{'type': 'scatter', 'mode': 'markers+lines', 'x': [], 'y': []}], 
                'layout': {'title': 'Invalid JSON data', 
                           'xaxis': {'title': 'X-axis title'}, 
                           'yaxis': {'title': 'Y-axis title'}}
            }

    else:
        fig = {
            'data': [{'type': 'scatter', 'mode': 'markers+lines', 'x': [], 'y': []}], 
            'layout': {'title': 'No data available', 
                       'xaxis': {'title': 'X-axis title'}, 
                       'yaxis': {'title': 'Y-axis title'}}
        }

    return fig






#--------UPDATE SETTINGS------------------------------------------------
@app.callback(
    [Output('rolling', 'value'),
     Output('saved', 'children')],
    [Input('rolling', 'value')]
)  
def save_settings(rolling):
    database = fn.get_path(f'{data_directory}/.data_v2.db')
    conn = sql.connect(database)
    c = conn.cursor()

    query = f"""UPDATE settings SET rolling_interval={rolling} WHERE id=0;"""
    
    c.execute(query)
    conn.commit()
    conn.close()

    logger.info(f'(tab4 rolling interval changed to {rolling})')

    return rolling, ''

#-----------------------The End --------------------
