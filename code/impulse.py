# impulse.py

# This is the main script 

import functions as fn
import webbrowser
import warnings
import launcher
import time

from server import app
from threading import Timer

from tab0 import show_tab0
from tab1 import show_tab1
from tab2 import show_tab2
from tab3 import show_tab3
from tab4 import show_tab4
from tab5 import show_tab5
from tab6 import show_tab6

from dash import dcc, html, Input, Output, State, callback, callback_context

warnings.filterwarnings('ignore')

#---Defines the browser tabs------------------------------------------------------------

app.layout = html.Div([
    dcc.Tabs(id='tabs', value='tab_1', children=[
        dcc.Tab(label='My Details', value='tab_0'),
        dcc.Tab(label='Device', value='tab_1'),
        dcc.Tab(label='2D Histogram', value='tab_2'), 
        dcc.Tab(label='3D Histogram', value='tab_3'), 
        dcc.Tab(label='Count Rate', value='tab_4'), 
        dcc.Tab(label='Repository', value='tab_5'),
        dcc.Tab(label='Manual & Exit', value='tab_6'),
    ]),
    html.Div(id='tab-content')  # Empty Div for tab content
])

#---Tab values call function and provide page contents

@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    if tab == 'tab_0':
        return show_tab0()
    elif tab == 'tab_1':
        return show_tab1()
    elif tab == 'tab_2':
        return show_tab2()
    elif tab == 'tab_3':
        return show_tab3()
    elif tab == 'tab_4':
        return show_tab4()
    elif tab == 'tab_5':
        return show_tab5()
    elif tab == 'tab_6':
        return show_tab6()
    else:
        return html.Div('Tab not found')

#---------------------------------------------
port = 8050

# Application must be started from (__main__)
if __name__ == '__main__':
    Timer(1, lambda: fn.open_browser(port)).start()
    app.run_server(host='0.0.0.0', debug=False, threaded=True, port=port)
