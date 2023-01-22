import dash
import os
import functions as fn
import sqlite3 as sql
from dash import dcc
from dash import html
from server import app
from dash.dependencies import Input, Output
from tab1 import show_tab1
from tab2 import show_tab2
from tab3 import show_tab3

#devices = fn.get_device_list()

conn    = sql.connect("data.db")
c       = conn.cursor()

query   = """CREATE TABLE IF NOT EXISTS settings (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT    DEFAULT '',
        device          INTEGER DEFAULT 1,              
        sample_rate     INTEGER DEFAULT 48000,
        chunk_size      INTEGER DEFAULT 1025,                        
        threshold       INTEGER DEFAULT 100,
        tolerance       INTEGER DEFAULT 10000,
        bins            INTEGER DEFAULT 1000,
        bin_size        INTEGER DEFAULT 30,
        max_counts      INTEGER DEFAULT 1000,
        shapecatches    INTEGER DEFAULT 100 );"""

query2  =  f'INSERT INTO settings (id, name) SELECT 0, 0 WHERE NOT EXISTS (SELECT 1 FROM settings WHERE id = 0);'


with conn:
    c.execute(query).execute(query2)
    conn.commit()


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
        html_tab1 = show_tab1()
        return html_tab1  
        
    elif tab == 'tab2':
        html_tab2 = show_tab2()
        return html_tab2

    elif tab == 'tab3':
        html_tab3 = show_tab3()
        return html_tab3    
        

   

    
