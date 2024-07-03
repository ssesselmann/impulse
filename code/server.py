import dash
import os
import logging
import dash_bootstrap_components as dbc
import global_vars

from dash import dcc

data_directory = os.path.join(os.path.expanduser("~"), "impulse_files")

if not os.path.exists(data_directory):
    os.makedirs(data_directory)

# Set up the logger
logging.basicConfig(
    filename=f'{data_directory}/_last_run.log',
    level=logging.INFO,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s')

# Create a logger instance
logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Add a handler to print log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.info('Logging has been configured')

# Ensure settings are loaded from global_vars
global_vars.load_settings_from_json()
theme = global_vars.theme

store_device                = dcc.Store(id='store-device'             , data='')
store_filename              = dcc.Store(id='store-filename'           , data='')
store_filename_2            = dcc.Store(id='store-filename_2'         , data='')
store_bins                  = dcc.Store(id='store-bins'               , data='')
store_bins_2                = dcc.Store(id='store-bins-2'             , data='')
store_histogram             = dcc.Store(id='store-histogram'          , data=[])
store_histogram_2           = dcc.Store(id='store-histogram-2'        , data=[])
store_histogram_3d          = dcc.Store(id='store-histogram-3d'       , data={'histogram_3d': []})
store_count_history         = dcc.Store(id='store-count-history'      , data=[])
store_gaussian              = dcc.Store(id='store-gc'                 , data=[])
store_coefficients          = dcc.Store(id='store-coefficients'       , data=[1, 0, 0])
store_sigma                 = dcc.Store(id='store-sigma'              , data='')
store_annotations           = dcc.Store(id='store-annotations'        , data=[])
store_confirmation_output   = dcc.Store(id="store-confirmation-output", data='')
store_load_flag_tab3        = dcc.Store(id='store-load-flag-tab3'     , data=False)
store_load_flag_tab4        = dcc.Store(id='store-load-flag_tab4'     , data=False)

# External CSS stylesheets
external_stylesheets = [dbc.themes.BOOTSTRAP, f'https://www.gammaspectacular.com/steven/impulse/styles_{theme}.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.scripts.config.serve_locally = True

app.config['suppress_callback_exceptions'] = True

logger.info(f'Server GET: {external_stylesheets}')
logger.info('Scripts on server.py completed')

# -- End server.py
