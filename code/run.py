import functions as fn
import webbrowser
from threading import Timer
from App import app

# The following three lines limit output to errors
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Define default `8050` port
port = 8050 

# Function to open browser
fn.open_browser(port)


if __name__ == '__main__':
    Timer(1, fn.open_browser(port)).start();
    app.run_server(debug=False, port=port)



