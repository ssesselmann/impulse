import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pulsecatcher as pc
import csv

path = "Sites/github/gs_plot/data/plot.csv"
app = dash.Dash()
plot_data = {}

app.layout = html.Div([
    dcc.Graph(id='bar-chart'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000, # in milliseconds
        n_intervals=0
    )
])



@app.callback(Output('bar-chart', 'figure'),
              [Input('interval-component', 'n_intervals')])

def update_graph(n):
   
    plot_data = {}
    with open(path, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for x, y in reader:
            plot_data[int(x)] = int(y)

    x = list(plot_data.keys())
    y = list(plot_data.values())
    trace = go.Bar(x=x, y=y, width=1, marker={'color': 'black'})
    layout = go.Layout(title='Histogram', height=800, width=1200)
    return go.Figure(data=[trace], layout=layout)


if __name__ == '__main__':
    app.run_server(debug=False)