import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app
#app = dash.Dash()

app.layout = html.Div([
    #dcc.Input(id='input', value='Enter a value here', type='text'),
    html.Div(id='output'),
    dcc.Graph(id='graph')
])

# @app.callback(
#     Output(component_id='output', component_property='children'),
#     [Input(component_id='input', component_property='value')]
# )
# def update_value(input_data):
#     return 'You\'ve entered "{}"'.format(input_data)

@app.callback(
    Output(component_id='graph', component_property='figure'),
    [Input(component_id='input', component_property='value')]
)
def update_graph(input_data):
    # x = [1, 2, 3]
    # y = [4, 1, 2]
    # data = [{'x': x, 'y': y, 'type': 'line', 'name': 'SF'}]
    # layout = {'title': 'Line Graph'}
    # return {'data': data, 'layout': layout}


    fig = {'data': [{'x': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50], 'y': [-332.72058823529414, -285.84058823529415, -281.2805882352941, -310.9405882352941, -305.86058823529413, -263.2705882352941, -264.42058823529413, -332.09058823529415, -369.1405882352941, -310.41058823529414, -250.8505882352941, -303.73058823529414, -396.5005882352941, -365.23058823529414, -240.9505882352941, -238.19058823529411, -397.4105882352941, -457.5605882352941, -260.05058823529413, -97.43058823529412, -325.59058823529415, -660.6605882352942, -266.0605882352941, 1218.629411764706, 2984.4094117647055, 3738.2494117647057, 3050.549411764706, 1724.0194117647059, 801.5494117647058, 520.379411764706, 409.2794117647059, 125.21941176470585, -178.21058823529413, -261.48058823529414, -200.43058823529412, -221.71058823529413, -347.9505882352941, -420.2405882352941, -383.0005882352941, -352.7505882352941, -406.59058823529415, -467.61058823529413, -450.7005882352941, -400.60058823529414, -406.9305882352941, -460.1405882352941, -480.42058823529413, -449.97058823529414, -430.2405882352941, -454.9105882352941, -482.2005882352941], 'type': 'line', 'name': 'SF',}], 'layout': {'title': 'Normalised Shape', }}

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
