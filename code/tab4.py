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
from functions import load_cps_file, save_settings_to_json

logger      = logging.getLogger(__name__)
interval    = 1000  # 1 second interval

with global_vars.write_lock:
        filename        = global_vars.filename
        t_interval      = global_vars.t_interval
        data_directory  = global_vars.data_directory

window_size = 300    

def show_tab4():   

    with global_vars.write_lock:
        rolling         = global_vars.rolling_interval
        filename        = global_vars.filename
        theme           = global_vars.theme
    try:
        load_cps_file(filename)
    except:
        pass

    html_tab4 = html.Div(id='tab4', children=[

        dcc.Input(id='theme', type='text', value=f'{theme}', style={'display': 'none'}),

        html.Div(id='tab4-frame', children=[

        html.Div(id='count_rate_div', children=[
            dcc.Graph(id='count_rate_chart', figure={}),
            dcc.Interval(id='interval_component', interval=interval, n_intervals=0),  # Refresh rate 1s.
            html.Div(['Update Interval (s)', dcc.Input(id='t_interval', type='number', step=1, readOnly=False, value=t_interval)], style={'display': 'none'}),
            html.Div(id='saved', style={'textAlign': 'left', 'marginLeft': '20px'}),
            html.Div(children=[dcc.Slider(
                     id='rolling',
                     min=0, 
                     max= window_size,
                     step=1, 
                     value=rolling,
                     marks={i: str(i) for i in range(0, window_size, 10)}
            )]),
            html.Div(id="last-hour", children=[
                daq.ToggleSwitch(
                    id='full-monty',
                    label='Last hour | Show all',
                    color='green',
                    value=False,
                )
            ])
        ]),
        html.Div(children=[html.Img(id='footer', src='assets/footer.gif')]),

        ]), #end of tab4-frame
    ]) # end of tab4

    return html_tab4

@app.callback(
    Output('count_rate_chart'   , 'figure'),
    [Input('interval_component' , 'n_intervals'),
     Input('t_interval'         , 'value'),
     Input('full-monty'         , 'value')],
    [State('tabs'               , 'value'),
     State('rolling'            , 'value'),
     State('theme'              , 'value')]
)
def update_count_rate_chart(n_intervals, t_interval, full_monty, tab, rolling, theme):

    logger.debug(f"Updating chart with t_interval={t_interval}, full_monty={full_monty}, rolling={rolling}")
    now = datetime.now()
    time_str = now.strftime('%d/%m/%Y')

    with global_vars.write_lock:
        count_history   = list(global_vars.count_history)  # Copy to avoid modification during reading
        counts          = global_vars.counts
        cps             = global_vars.cps
        elapsed         = global_vars.elapsed
        filename        = global_vars.filename
        dropped_counts  = global_vars.dropped_counts

    if theme == 'light-theme':
        bg_color    = '#fafafa'
        paper_color = 'white'
        line_color  = 'black'
        trace_left  = '#0066ff'
        trace_right = 'red'
        trace_dots  = 'black'
    else:
        bg_color    = 'black'
        paper_color = 'black'
        line_color  = 'lightgray'  
        trace_left  = 'lightgreen'
        trace_right = 'red' 
        trace_dots  = 'white'

    if full_monty:
        x = [str(i * t_interval) for i in range(len(count_history))]
        y = count_history
    else:
        if len(count_history) < window_size:
            x = [str(i * t_interval) for i in range(len(count_history))]
            y = count_history
        else:
            x = [str(i * t_interval) for i in range(len(count_history) - window_size, len(count_history))]
            y = count_history[-window_size:]

    if not y:
        return go.Figure()

    line = go.Scatter(
        x=x, 
        y=y, 
        mode='markers+lines', 
        marker=dict(size=5, color=trace_dots), 
        line=dict(width=1, color=trace_right), 
        name='counts per sec.'
    )
    
    y_series = pd.Series(y)
    
    if rolling > 0 and len(y_series) > 0:
        rolling_series = y_series.rolling(window=max(1, rolling // t_interval), min_periods=1).sum()
        rolling_line = go.Scatter(
            x=x, 
            y=rolling_series, 
            mode='lines', 
            line=dict(width=2, color=trace_left), 
            name=f'{rolling} second average'
        )
    else:
        rolling_line = go.Scatter()

    layout = go.Layout(
        title={
            'text': f'Count Rate | {filename}',
            'x': 0.06,
            'y': 0.9,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 16, 'color': line_color}
        },
        xaxis=dict(
            title='Seconds',
            tickmode='linear',
            tick0=0,
            dtick=10,
            tickangle=90,
            tickfont=dict(family='Arial', size=14, color= line_color),
            titlefont=dict(family='Arial', size=18, color=line_color),
            type='linear',
            showline=True,
            linewidth=2,
            linecolor=line_color,
            ticks='outside'
        ),
        yaxis=dict(
            title='Counts',
            type='linear',
            tickfont=dict(family='Arial', size=14, color=line_color),
            titlefont=dict(family='Arial', size=18, color=line_color)
        ),
        annotations=[
            dict(
                text=f"{counts} Valid counts | {dropped_counts} Lost counts | {elapsed} Seconds total | {rolling} Second average",
                x=0.00,
                y=1.1,
                xref='paper',
                yref='paper',
                showarrow=False,
                font=dict(family='Arial', size=16, color=line_color)
            )
        ],
        uirevision="Don't change",
        height=500,
        margin=dict(l=80, r=50, t=100, b=50),
        paper_bgcolor=paper_color,
        plot_bgcolor=bg_color,
        showlegend=False,
    )

    fig = go.Figure(data=[line, rolling_line], layout=layout)

    return fig


# --------UPDATE SETTINGS------------------------------------------------
@app.callback(
    [Output('rolling'   , 'value'),
     Output('saved'     , 'children')],
    [Input('rolling'    , 'value')]
)
def save_settings(rolling):
    with global_vars.write_lock:
        global_vars.rolling_interval = int(rolling) 
    save_settings_to_json()
    logger.info(f'(tab4 rolling interval changed to {rolling})')
    return rolling, f'Sum Counts {rolling} seconds'
