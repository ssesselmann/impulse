import dash
import time
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
from tab4 import show_tab4
from server import app

data_directory = fn.get_path('data')
database = fn.get_path('data.db')
shapecsv = fn.get_path('data/shape.csv')

try:
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
except:
    pass

try:
    if not os.path.exists(filename):
        fn.create_dummy_csv(shapecsv)
except:
    pass

# Connects to database
conn    = sql.connect(database)
c       = conn.cursor()

# This query creates a table in the database when used for the first time
query   = """CREATE TABLE IF NOT EXISTS settings (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,  
        name            TEXT    DEFAULT 'my_spectrum',      
        device          INTEGER DEFAULT 1,                           
        sample_rate     INTEGER DEFAULT 44100,             
        chunk_size      INTEGER DEFAULT 1024,               
        threshold       INTEGER DEFAULT 100,                
        tolerance       INTEGER DEFAULT 50000,              
        bins            INTEGER DEFAULT 1000,               
        bin_size        INTEGER DEFAULT 30,                 
        max_counts      INTEGER DEFAULT 10000,              
        shapecatches    INTEGER DEFAULT 10,                 
        sample_length   INTEGER DEFAULT 51,                 
        calib_bin_1     INTEGER DEFAULT 0,                  
        calib_bin_2     INTEGER DEFAULT 500,                
        calib_bin_3     INTEGER DEFAULT 1000,               
        calib_e_1       REAL    DEFAULT 0,                  
        calib_e_2       REAL    DEFAULT 1500,               
        calib_e_3       REAL    DEFAULT 3000,               
        coeff_1         REAL    DEFAULT 1,                  
        coeff_2         REAL    DEFAULT 1,                  
        coeff_3         REAL    DEFAULT 0,                  
        comparison      TEXT    DEFAULT '',                 
        flip            INTEGER DEFAULT 1,                  
        peakfinder      REAL    DEFAULT 0.5                  
        );"""

# This query inserts the first record in settings with defaults
query2  =  f'INSERT INTO settings (id, name) SELECT 0, "myspectrum" WHERE NOT EXISTS (SELECT 1 FROM settings WHERE id = 0);'

# This excecutes the sqli query
with conn:
    c.execute(query).execute(query2)
    conn.commit()


#---Defines the browser tabs------------------------------------------------------------

app.layout = html.Div([
    
    dcc.Tabs(
        id='tabs', 
        value='tab1', 
        #style={'fontWeight': 'bold'}, 
        children=[
            dcc.Tab(
                label= 'Settings & Control', 
                value= 'tab1'),
            dcc.Tab(
                label='Pulse Height Histogram', 
                value='tab2'),   
            dcc.Tab(
                label='Count Rate Histogram', 
                value='tab3'),
            dcc.Tab(
                label='Important! Exit Here', 
                value='tab4'),
        ]),
    html.Div(id = 'tabs-content'),# Empty Div, where the out of render_tabs is sent to. (The page content)
    ],className='app-styles')

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
        
    elif tab == 'tab4':
        html_tab4 = show_tab4()
        return html_tab4   
   

    
