import dash
import os
import logging
import dash_bootstrap_components as dbc
import global_vars
import json
from dash import dcc
from functions import load_settings_from_json

data_directory = os.path.join(os.path.expanduser("~"), "impulse_data_2.0")

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
logger.info('Logging has been configured\n')

# Ensure settings are loaded from global_vars
path = os.path.join(data_directory, "_settings.json")

load_settings_from_json(path)


print(f'theme:{global_vars.theme}')        

# Now that global_vars.theme is set, initialize the external stylesheets
external_stylesheets = [dbc.themes.BOOTSTRAP, f'https://www.gammaspectacular.com/steven/impulse/styles_{global_vars.theme}.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.scripts.config.serve_locally = True

app.config['suppress_callback_exceptions'] = True

logger.info(f'Server GET: {external_stylesheets}\n')
logger.info('Scripts on server.py completed\n')

# -- End server.py
