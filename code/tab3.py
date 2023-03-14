import dash
import json
import os
import plotly.graph_objs as go
import functions as fn
import dash_daq as daq
import sqlite3 as sql
import pandas as pd
from dash import html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from server import app
from dash import dcc

def show_tab3():
    # Get some settings from database----------
    database = fn.get_path('data.db')
    conn            = sql.connect(database)
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 
    settings        = c.fetchall()[0]
    filename        = settings[1]
    interval        = 1000
    #------------------------------------------

    html_tab3 = html.Div(id='tab3', children=[

        html.Div(dcc.Input(id='filename', type='text', value=settings[1], style={'display': 'none'})),
        

        html.Div(id='count_rate_div', # Histogram Chart
            children=[
                dcc.Graph(id='count_rate_chart', figure= {}),
                dcc.Interval(id='interval_component', interval= interval) # Refresh rate 1s.
            ]),

        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif'),]),

    ])

    return html_tab3

#-----------------END of Page---------------------------------------------------

@app.callback(Output('count_rate_chart', 'figure'),
              [Input('interval_component', 'n_intervals'),
               Input('filename', 'value'),
               Input('tabs', 'value')])  # pass the current figure as a state


def update_count_rate_chart(n_intervals, filename, active_tab):


    if active_tab != 'tab3':  # only update the chart when "tab3" is active
        raise PreventUpdate

    cps_file = fn.get_path(f'data/{filename}-cps.json')

    if os.path.exists(cps_file):
        with open(cps_file, "r") as f:
            count_data = json.load(f)
            countrate = count_data["cps"]
            
            x = [str(i) for i in range(len(countrate))]
            y = list(map(int, countrate))  # convert y values from string to integer

            line = go.Scatter(x=x, y=y, mode='markers+lines', marker=dict(size=4, color='black'), line=dict(width=1, color='purple'), name='counts per sec.')

            # create pandas series for y data
            y_series = pd.Series(y)

            # create rolling average series
            rolling_series = y_series.rolling(window=11, center=True).mean()

            # create scatter trace for rolling average line
            rolling_line = go.Scatter(x=x[10:], y=rolling_series[10:], mode='lines', line=dict(width=2, color='green'), name='10 sec rolling ave')

            layout = go.Layout(
                title={
                    'text': filename,
                    'x': 0.5,
                    'y': 0.9,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'family': 'Arial', 'size': 24, 'color': 'black'}
                },
                xaxis=dict(
                    title='Seconds',
                    dtick=10,
                    tickangle=90,
                    range=[0, 300],
                    tickfont=dict(family='Arial', size=14, color='black'),
                    titlefont=dict(family='Arial', size=18, color='black'),
                    type='linear',
                    rangeslider=dict(visible=True),
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
                uirevision="Don't change",
                height=500,
                margin=dict(l=80, r=50, t=100, b=80),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

            fig = go.Figure(data=[line, rolling_line], layout=layout)
    else:
        
        fig = {'data': [{'type': 'scatter', 'mode': 'markers+lines', 'x': [], 'y': []}], 
                    'layout': {'title': 'No data available', 
                    'xaxis': {'title': 'X-axis title'}, 
                    'yaxis': {'title': 'Y-axis title'}}}

    return fig




