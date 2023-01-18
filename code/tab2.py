import dash
import plotly.graph_objs as go
import pulsecatcher as pc
import functions as fn
import csv
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from server import app

path = None


def show_tab2(path):


    data = fn.load_settings(path)
    values = [row[1] for row in data[1:]]
    input_index     = int(values[0])
    input_rate      = int(values[1])
    input_chunk     = int(values[2])
    input_lld       = int(values[3])
    input_tolerance = int(values[4])

    html_tab2 = html.Div([

        html.Div( children=[
            dcc.Graph(id='bar-chart', figure={},),
            dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0)
        ],style={'width':'100%', 'height':'90%'}),

        

        #Start button
        html.Div( children=[
            html.Button( 'START' , id='start', style={'background-color':'lightgreen','border-radius':'9px', 'height':'30px', 'width':'150px'}),
            ],style={'width':'48%', 'margin':'20px', 'background-color':'white', 'text-align':'center', 'color':'green', 'float':'left'}
        ),

        #Stop button
        html.Div( children=[
            html.Button( 'STOP' , id='stop', style={'background-color':'red','border-radius':'9px', 'height':'30px', 'width':'150px'}),
            ],style={'width':'48%', 'margin':'20px', 'background-color':'white', 'text-align':'center', 'color':'green', 'float':'left'}
        ),

        html.Div(id='start_text', children =''),
        html.Div(id='stop_text', children =''),
        html.Div(dcc.Input(id='path1', value= path),style={'visibility':'hidden'}),
        html.Div(dcc.Input(id='path2', value= path),style={'visibility':'hidden'}),
        html.Div(dcc.Input(id='path3', value= path),style={'visibility':'hidden'}),

    ])

    return html_tab2


#------START---------------------------------

@app.callback( Output('start_text'  , 'children'),
                [Input('start'       , 'n_clicks')],
                [State('path1'        , 'value')]
)
def update_output(n_clicks, value):
    
    if n_clicks != None:
        mode = 1
        pc.pulsecatcher(mode, value)

        return 'Run !!'

#----STOP------------------------------------------------------------

@app.callback( Output('stop_text'  , 'children'),
                [Input('stop'       , 'n_clicks')],
                [State('path2'        , 'value')])



def update_output(n_clicks, value):
    

    if n_clicks != None:

        mode = 0
        pc.pulsecatcher(mode, value)

        return 'Break !!!', 'Screech'

#----------------------------------------------------------------

@app.callback(Output('bar-chart', 'figure'),
              [Input('interval-component', 'n_intervals')],
              [State('path3'        , 'value')])

def update_graph(n, value):

    plot_data = {}
    path = value

    with open(f'{path}plot.csv', "r") as f:

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



