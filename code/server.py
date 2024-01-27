# server.py
import dash
import os
import sqlite3 as sql
import functions as fn
import logging

# Set up the logger
logging.basicConfig(
	filename='impulse_last_run.log', 
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
logger.info(f'Logging has been configured')

data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")

try:
	database 	= fn.get_path(f'{data_directory}/.data_v2.db')
	conn 		= sql.connect(database)
	c 			= conn.cursor()
	query 		= "SELECT theme FROM settings "

	c.execute(query) 
	
	theme 		= c.fetchall()[0][0]
	
except:
	theme = 'lightgray'	

# external CSS stylesheets
external_stylesheets = [f'https://www.gammaspectacular.com/steven/impulse/styles_{theme}.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.scripts.config.serve_locally = True

app.config['suppress_callback_exceptions']=True

logger.info(f'Server GET: {external_stylesheets}')
logger.info(f'Scripts on server.py completed')