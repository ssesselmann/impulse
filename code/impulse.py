import webbrowser
import warnings
import global_vars
import launcher
import time

from functions import open_browser, clear_global_vars
from server import app, version
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

device = global_vars.device

app.layout = html.Div(children=[
    dcc.Tabs(id='tabs', value='tab_1'     , children=[
        dcc.Tab(label='My Details'        , value='tab_0', className='custom-tabs'),
        dcc.Tab(label=f'impulse {version}', value='tab_1', className='custom-tabs'),
        dcc.Tab(label='2D Histogram'      , value='tab_2', className='custom-tabs'), 
        dcc.Tab(label='3D Histogram'      , value='tab_3', className='custom-tabs'), 
        dcc.Tab(label='Count Rate'        , value='tab_4', className='custom-tabs'), 
        dcc.Tab(label='Repository'        , value='tab_5', className='custom-tabs'),
        dcc.Tab(label='Manual & Exit'     , value='tab_6', className='custom-tabs'),
    ]),
    html.Div(id='tab-content'),

])

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

port = 8050

if __name__ == '__main__':
    Timer(1, lambda: open_browser(port)).start()
    app.run_server(host='0.0.0.0', debug=False, threaded=True, port=port)
