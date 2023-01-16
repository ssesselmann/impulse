import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import csv
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app

def show_tab2():

    html_tab2 = html.Div([


        html.Div(id='start-stop', children=[

            html.Button('Start / Stop', id='start-stop', 
                style={'background-color':'pink','border-radius':'9px', 'height':'30px', 'width':'150px'}),
            html.Div(id='output', children=''),
        ],style={'width':'94%', 'margin':'20px', 'background-color':'white', 'text-align':'center', 'color':'green'}
        ),


        dcc.Graph(id='bar-chart'),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )

    ])
    return html_tab2


#------START/STOP---------------------------------

@app.callback(
    Output('output', 'children'),
    [Input('start-stop', 'n_clicks')]
)
def update_output(n_clicks):
    if n_clicks is None:
        return 'Not started yet'
    elif n_clicks % 2 == 0:

        return 'Stop'
    else:

        pc.pulsecatcher()

        return 'Start'

#----------------------------------------------------------------

@app.callback(Output('bar-chart', 'figure'),
              [Input('interval-component', 'n_intervals')])

def update_graph(n):

    path = "Sites/github/gs_plot/data/plot.csv"
    plot_data = {}
    with open(path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for x, y in reader:
            plot_data[int(x)] = int(y)

    x = list(plot_data.keys())
    y = list(plot_data.values())
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
        height=600, 
        autosize=True
        )
    return go.Figure(data=[trace], layout=layout)



