import dash
import os
import logging
import dash_bootstrap_components as dbc
import global_vars
import json
from dash import dcc

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
if os.path.exists(path):
        with open(path, 'r') as f:
            settings = json.load(f)
            try:
                global_vars.filename_3d     = settings["filename_3d"]
                global_vars.bin_size_3d     = int(settings["bin_size_3d"])
                global_vars.bins_3d         = int(settings["bins_3d"])
            except: 
                pass
            global_vars.bin_size        = int(settings["bin_size"])
            global_vars.bin_size_2      = int(settings["bin_size_2"])
            global_vars.bins            = int(settings["bins"])
            global_vars.bins_2          = int(settings["bins_2"])
            global_vars.calib_bin_1     = int(settings["calib_bin_1"])
            global_vars.calib_bin_2     = int(settings["calib_bin_2"])
            global_vars.calib_bin_3     = int(settings["calib_bin_3"])
            global_vars.calib_e_1       = float(settings["calib_e_1"])
            global_vars.calib_e_2       = float(settings["calib_e_2"])
            global_vars.calib_e_3       = float(settings["calib_e_3"])
            global_vars.chunk_size      = int(settings["chunk_size"])
            global_vars.coeff_1         = float(settings["coeff_1"])
            global_vars.coeff_2         = float(settings["coeff_2"])
            global_vars.coeff_3         = float(settings["coeff_3"])
            global_vars.compression     = int(settings["compression"])
            global_vars.device          = int(settings["device"])
            global_vars.filename        = settings["filename"]
            global_vars.filename_2      = settings["filename_2"]
            global_vars.flip            = settings["flip"]
            global_vars.max_bins        = int(settings["max_bins"])
            global_vars.max_counts      = int(settings["max_counts"])
            global_vars.max_seconds     = int(settings["max_seconds"])
            global_vars.peakfinder      = float(settings["peakfinder"])
            global_vars.peakshift       = int(settings["peakshift"])
            global_vars.rolling_interval= int(settings["rolling_interval"])
            global_vars.sample_length   = int(settings["sample_length"])
            global_vars.sample_rate     = int(settings["sample_rate"])
            global_vars.shapecatches    = int(settings["shapecatches"])
            global_vars.sigma           = float(settings["sigma"])
            global_vars.stereo          = bool(settings["stereo"])
            global_vars.t_interval      = int(settings["t_interval"])
            global_vars.theme           = settings["theme"]
            global_vars.threshold       = int(settings["threshold"])
            global_vars.tolerance       = int(settings["tolerance"])

# External CSS stylesheets
external_stylesheets = [dbc.themes.BOOTSTRAP, f'https://www.gammaspectacular.com/steven/impulse/styles_{global_vars.theme}.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.scripts.config.serve_locally = True

app.config['suppress_callback_exceptions'] = True

logger.info(f'Server GET: {external_stylesheets}\n')
logger.info('Scripts on server.py completed\n')

# -- End server.py
