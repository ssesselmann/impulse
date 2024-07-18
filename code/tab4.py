import dash
import json
import os
import time
import logging
import plotly.graph_objs as go
import dash_daq as daq
import pandas as pd
import global_vars

from datetime import datetime
from dash import html, dcc
from dash.dependencies import Input, Output, State
from server import app

from functions import (
    get_path, 
    load_cps_file, 
    reset_stores, 
    save_settings_to_json,
    )

# Importing store variables from server
from server import store_load_flag_tab4

logger = logging.getLogger(__name__)

data_directory = global_vars.data_directory

def show_tab4():

    with global_vars.write_lock:
        global_vars.count_hostory = []      
        filename    = global_vars.filename
        t_interval  = global_vars.t_interval
        rolling     = global_vars.rolling_interval

    interval    = 1000  # 1 second interval

    #load_cps_file(filename)

    html_tab4 = html.Div(id='tab4', children=[
        html.Div(dcc.Input(id='filename', type='text', value=filename, style={'display': 'none'})),
        html.Div(id='count_rate_div',  # Histogram Chart
            children=[
                dcc.Store(id='store_load_flag_tab4', data=False),
                dcc.Graph(id='count_rate_chart', figure={}),
                dcc.Interval(id='interval_component', interval=interval, n_intervals=0),  # Refresh rate 1s.
                html.Div(['Update Interval (s)', dcc.Input(id='t_interval', type='number', step=1, readOnly=False, value=t_interval)], style={'display': 'none'}),
                html.Div(id='saved', style={'textAlign': 'left', 'marginLeft': '20px'}),
                html.Div(children=[dcc.Slider(
                         id='rolling',
                         min=0, max=3600,
                         step=1, value=rolling,
                         marks={i: str(i) for i in range(0, 3601, 300)}
                )]),
                html.Div(id="last-hour", children=[
                daq.ToggleSwitch(
                        id='full-monty',
                        label='Last hour | Show all',
                        value=False,
                        color='purple'
                    )
                    ])
                ]),
        html.Div(html.H5('Start and Stop from 2D tab.'), style={'textAlign': 'left', 'marginTop': '10px', 'marginLeft': '5%'}),
        html.Div(children=[html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),
        #html.Div(id='saved', children=''),
    ])

    return html_tab4

# -----------------END of Page---------------------------------------------------

@app.callback(
    [Output('count_rate_chart', 'figure'),
     Output('store_load_flag_tab4', 'data')],
    [Input('interval_component', 'n_intervals'),
     Input('filename', 'value'),
     Input('t_interval', 'value'),
     Input('full-monty', 'value')],
    [State('store_load_flag_tab4', 'data'),
     State('tabs', 'value'),
     State('rolling', 'value')]
)
def update_count_rate_chart(n_intervals, filename, t_interval, full_monty, store_load_flag_tab4, tab, rolling):
    logger.debug(f"Updating chart with filename={filename}, t_interval={t_interval}, full_monty={full_monty}, rolling={rolling}")

    now         = datetime.now()
    time_str    = now.strftime('%d/%m/%Y')

    if os.path.exists(os.path.join(data_directory, f"{filename}_cps.json")) and not global_vars.run_flag:
        load_cps_file(filename)

    with global_vars.write_lock:
        count_history   = global_vars.count_history
        sum_counts      = sum(count_history)
        counts          = global_vars.counts
        cps             = global_vars.cps
        elapsed         = global_vars.elapsed

    if not full_monty:
        start_index = max(0, len(count_history) - 3600 // t_interval)
        count_history = count_history[start_index:]
        x = [str(i * t_interval) for i in range(start_index, start_index + len(count_history))]
    else:
        x = [str(i * t_interval) for i in range(len(count_history))]

    y = count_history  # Use the already validated list of integers

    if not y:
        return go.Figure(), store_load_flag_tab4

    logger.debug(f"X values: {x}")
    logger.debug(f"Y values: {y}")

    line = go.Scatter(x=x, y=y, mode='markers+lines', marker=dict(size=4, color='black'), line=dict(width=1, color='purple'), name='counts per sec.')
    
    y_series = pd.Series(y)
    
    if rolling > 0 and len(y_series) > 0:
        rolling_series = y_series.rolling(window=max(1, rolling // t_interval), min_periods=1).sum()
        rolling_line = go.Scatter(x=x, y=rolling_series, mode='lines', line=dict(width=2, color='green'), name=f'{rolling} second average')
    else:
        rolling_line = go.Scatter()

    layout = go.Layout(
        title={
            'text': f'{filename} | Counts | {time_str}',
            'x': 0.5,
            'y': 0.9,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 16, 'color': 'black'}
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
                text=f"{rolling} Second average<br>{counts} Total counts<br>{sum_counts} Sum counts<br>{elapsed} Seconds total",
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

    return fig, store_load_flag_tab4


# --------UPDATE SETTINGS------------------------------------------------
@app.callback(
    [Output('rolling', 'value'),
     Output('saved', 'children')],
    [Input('rolling', 'value')]
)
def save_settings(rolling):

    with global_vars.write_lock:
        global_vars.rolling_interval = int(rolling)
        
    save_settings_to_json()

    logger.info(f'(tab4 rolling interval changed to {rolling})')

    return rolling, f'Sum Counts {rolling} seconds'
