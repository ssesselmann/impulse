import dash
import functions as fn
from dash import dcc
from dash import html
from server import app
from dash.dependencies import Input, Output, State
from tab1 import show_tab1
from tab2 import show_tab2
from tab3 import show_tab3

devices = fn.get_device_list()


#---Defines the tab buttons------------------------------------------------------------

app.layout = html.Div([
    dcc.Tabs(
        id="tabs", 
        value='tab1', 
        style={'fontWeight': 'bold'}, 
        children=[
            dcc.Tab(
                label= 'Controls', 
                value= 'tab1'),
            dcc.Tab(
                label='Histogram Chart', 
                value='tab2'),   
            dcc.Tab(
                label='Spare', 
                value='tab3'),

        ]),
    html.Div(id = 'tabs-content'),# Empty Div, where the out of render_tabs is sent to. (The page content)
    ],style={ 'background-color':'lightgray', 'margin:':'50px'})

#---Tab values call function and provide page contents

@app.callback(
    Output('tabs-content','children'),
    Input('tabs','value'))

def render_content(tab):
    if tab == 'tab1':
        html_tab1 = show_tab1()
        return html_tab1  
        
    elif tab == 'tab2':
        html_tab2 = show_tab2()
        return html_tab2

    elif tab == 'tab3':
        html_tab3 = show_tab3()
        return html_tab3    
        

   

    
