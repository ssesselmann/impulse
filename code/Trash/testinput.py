import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

app = dash.Dash()

app.layout = html.Div([
    html.H1("My Dash App"),
    dcc.Input(id="input1", type="text", value="initial value"),
    dcc.Input(id="input2", type="text", value="initial value"),
    dcc.Input(id="input3", type="text", value="initial value"),
    html.Button("Submit", id="submit"),
    dcc.Graph(id="output")
])

@app.callback(
    Output("output", "figure"),
    [Input("submit", "n_clicks")],
    [State("input1", "value"), State("input2", "value"), State("input3", "value")])

def update_output(n_clicks, input1, input2, input3):
    return {"data": [{"x": [1, 2, 3], "y": [input1, input2, input3]}]}

if __name__ == '__main__':
    app.run_server(debug=True)
