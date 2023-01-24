import dash

app = dash.Dash(__name__)
server = app.server
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config['suppress_callback_exceptions']=True
#app.run_server(threaded=True, debug=True, processes=1)