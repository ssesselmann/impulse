import dash
import functions as fn
from dash import dcc
from dash import html
from server import app
from dash.dependencies import Input, Output
from tab1 import show_tab1
from tab2 import show_tab2
from tab3 import show_tab3

devices = fn.get_device_list()

#### SET UP PATH TO THE DATA FILE !!
path = 'Sites/github/gs_plot/data/'
####################################

#---Defines the tab buttons------------------------------------------------------------

app.layout = html.Div([
    dcc.Tabs(
        id="tabs", 
        value='tab1', 
        style={'fontWeight': 'bold'}, 
        children=[
            dcc.Tab(
                label= 'Settings & Control', 
                value= 'tab1'),
            dcc.Tab(
                label='Pulse Height Histogram', 
                value='tab2'),   
            dcc.Tab(
                label='Spare', 
                value='tab3'),

        ]),
    html.Div(id = 'tabs-content'),# Empty Div, where the out of render_tabs is sent to. (The page content)
    ],style={ 'background-color':'white', 'margin:':'50px'})

#---Tab values call function and provide page contents

@app.callback(
    Output('tabs-content','children'),
    Input('tabs','value'))

def render_content(tab):
    if tab == 'tab1':
        html_tab1 = show_tab1(path)
        return html_tab1  
        
    elif tab == 'tab2':
        html_tab2 = show_tab2(path)
        return html_tab2

    elif tab == 'tab3':
        html_tab3 = show_tab3(path)
        return html_tab3    
        

   

    
