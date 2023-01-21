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
        max_counts      INTEGER DEFAULT 1000);"""

query2  = f'''CREATE TABLE IF NOT EXISTS histogram (id INTEGER PRIMARY KEY, '0' INTEGER,
            '1' INTEGER, '2' INTEGER, '3' INTEGER, '4' INTEGER, '5' INTEGER,
            '6' INTEGER, '7' INTEGER, '8' INTEGER, '9' INTEGER, '10' INTEGER,
            '11' INTEGER, '12' INTEGER, '13' INTEGER, '14' INTEGER, '15' INTEGER,
            '16' INTEGER, '17' INTEGER, '18' INTEGER, '19' INTEGER, '20' INTEGER,
            '21' INTEGER, '22' INTEGER, '23' INTEGER, '24' INTEGER, '25' INTEGER,
            '26' INTEGER, '27' INTEGER, '28' INTEGER, '29' INTEGER, '30' INTEGER,
            '31' INTEGER, '32' INTEGER, '33' INTEGER, '34' INTEGER, '35' INTEGER,
            '36' INTEGER, '37' INTEGER, '38' INTEGER, '39' INTEGER, '40' INTEGER,
            '41' INTEGER, '42' INTEGER, '43' INTEGER, '44' INTEGER, '45' INTEGER,
            '46' INTEGER, '47' INTEGER, '48' INTEGER, '49' INTEGER, '50' INTEGER,
            '99' INTEGER);'''

with conn:
    c.execute(query).execute(query2)
    conn.commit()





   # c.execute("INSERT OR IGNORE INTO settings VALUES (0, 'My Settings', 1, 48000, 1025, 100, 10000, 1000, 30, 1000);") 
   # conn.commit()

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
        

   

    
