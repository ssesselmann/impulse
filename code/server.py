import dash
import os
import logging
import dash_bootstrap_components as dbc
import global_vars
from functions import load_settings_from_json
from dash import html
from flask import Flask, send_from_directory

# Set up the Flask server before initializing Dash
server = Flask(__name__)

# Define your data directory
data_directory = os.path.join(os.path.expanduser("~"), "impulse_data_2.0")

# Set up logging configuration
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

logging.basicConfig(
    filename=f'{data_directory}/_last_run.log',
    level=logging.INFO,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Suppress only the werkzeug request logs to WARNING to avoid repeated entries
logging.getLogger('werkzeug').setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

# Load settings and set theme from global_vars
path = os.path.join(data_directory, "_settings.json")
load_settings_from_json(path)

with global_vars.write_lock:
    theme = global_vars.theme

logger.info(f"Selected theme: {theme}")

# Flask route to serve CSS files from the `assets` directory
@server.route('/assets/<filename>')
def serve_css(filename):
    return send_from_directory('assets', filename)

# Initialize the Dash app with the external stylesheet path
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, f"/assets/styles_{theme}.css"],
    assets_ignore="^(?!styles_{theme}).*\\.css"
)

app.layout = html.Div(id="page-content")  # Main layout placeholder
app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions'] = True

logger.info("Scripts in server.py completed\n")

# -- End of server.py code
