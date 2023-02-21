import dash

# external CSS stylesheets
external_stylesheets = ['https://www.gammaspectacular.com/steven/impulse/styles2.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server
#app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions']=True
#app.run_server(threaded=True, debug=True, processes=1)