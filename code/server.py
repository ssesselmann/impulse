import dash
import sqlite3 as sql
import functions as fn

try:
	database = fn.get_path('data.db')
	datafolder = fn.get_path('data')
	conn = sql.connect(database)
	c = conn.cursor()
	query = "SELECT theme FROM settings "
	c.execute(query) 
	theme = c.fetchall()[0][0]
	
except:
	theme = 'lightgray'	

# external CSS stylesheets
external_stylesheets = [f'https://www.gammaspectacular.com/steven/impulse/styles_{theme}.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server
#app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions']=True
#app.run_server(threaded=True, debug=True, processes=1)
