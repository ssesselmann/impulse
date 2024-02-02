# tab0.py
import plotly.graph_objects as go
import functions as fn
import distortionchecker as dcr
import sqlite3 as sql
import shapecatcher as sc
import os
import logging
import requests as req
import dash_daq as daq
from server import app
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State

logger = logging.getLogger(__name__)

data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")

n_clicks = None

def show_tab0():

    database     = fn.get_path(f'{data_directory}/.data_v2.db')
    conn         = sql.connect(database)
    c             = conn.cursor()
    query         = "SELECT * FROM user "

    c.execute(query) 

    user            = c.fetchall()[0]
    first_name      = user[1]
    first_name_f    = user[2]          
    last_name       = user[3]
    last_name_f     = user[4]                     
    institution     = user[5]
    institution_f   = user[6]     
    city            = user[7]
    city_f          = user[8]     
    country         = user[9]
    country_f       = user[10]  
    email           = user[11]
    email_f         = user[12]
    phone           = user[13]
    phone_f         = user[14]
    website         = user[15]
    website_f       = user[16]
    social_url      = user[17]
    social_url_f    = user[18]
    notes           = user[19]
    notes_f         = user[20]
    api_key         = user[21]

    html_tab0 = html.Div(id = 'tab_0', children=[

        html.Div(id='tab0_frame', children=[

            html.Div(id='tab0_box_1', children= [
                html.P(''),
                html.P(''),
                html.H1(f'My Details'),
                html.P('This page is intended for your personal details and all fields are stored on your local machine, so you don\'t have to worry about privacy.'),
                html.P('When you choose to publish one of your great spectra for other users to see, you can choose which fields to publish, putting you in control of your data.'),
                html.Hr(),
                html.Div(id='publish_label', children='Publish'),

                dcc.Input(id='first_name', type='text', value=first_name, placeholder='Firstname', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='first_name_f',
                    on= bool(first_name_f),
                    color='green',
                    className='my_checkbox'
                ),
                
                dcc.Input(id='last_name', type='text', value=last_name, placeholder='Lastname', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='last_name_f',
                    on=bool(last_name_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Input(id='institution', type='text', value=institution, placeholder='Institution', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='institution_f',
                    on=bool(institution_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Input(id='city', type='text', value=city, placeholder='City', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='city_f',
                    on=bool(city_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Input(id='country', type='text', value=country, placeholder='Country', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='country_f',
                    on=bool(country_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Input(id='email', type='text', value=email, placeholder='email', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='email_f',
                    on=bool(email_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Input(id='phone', type='text', value=phone, placeholder='+00 0000 000 000 phone', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='phone_f',
                    on=bool(phone_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Input(id='website', type='text', value=website, placeholder='www.domain.com', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='website_f',
                    on=bool(website_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Input(id='social_url', type='text', value=social_url, placeholder='social_url', className='my_inputs', style={'marginBottom': '10px'}),
                daq.BooleanSwitch(
                    id='social_url_f',
                    on=bool(social_url_f),
                    color='green',
                    className='my_checkbox'
                ),

                dcc.Textarea(id='notes', value=notes, placeholder='notes', className='my_inputs'),
                daq.BooleanSwitch(
                    id='notes_f',
                    on=bool(notes_f),
                    color='green',
                    className='my_checkbox',
                ),
                html.Hr(),
                dcc.Input(id='api_key', type='text', value=api_key, placeholder='api_key', className='my_inputs', style={'marginBottom': '10px', 'fontSize':'8px', 'width':'80%'}),
                html.Button('Request API', id='get_api', style={'marginLeft':'10px'}),
                html.Div(id='get_api_output', children=''),
                html.Hr(),
                html.Div(id='output-div'),
                html.Button('Update my spectra', id='update_my_spectra', style={'visibility':'hidden'}),
                html.P(id='delete_output', children=''),

                ]),
            
            # Box to disply My Published spectra.
            html.Div(id='tab0_box_2', children= [
                
                ]),
            ]), #end of frame
                
        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),


    ]) # end of page html_tab0 --------------------------------------------------

    return html_tab0

#---- Callback to update database-----------------------------------------------
@app.callback(
    Output('output-div'        , 'children'),
    [Input('first_name'        , 'value'),
     Input('first_name_f'    , 'on'),
     Input('last_name'        , 'value'),
     Input('last_name_f'    , 'on'),
     Input('institution'    , 'value'),
     Input('institution_f'    , 'on'),
     Input('city'            , 'value'),
     Input('city_f'            , 'on'),
     Input('country'        , 'value'),
     Input('country_f'        , 'on'),
     Input('email'            , 'value'),
     Input('email_f'        , 'on'),
     Input('phone'            , 'value'),
     Input('phone_f'        , 'on'),
     Input('website'        , 'value'),
     Input('website_f'        , 'on'),
     Input('social_url'        , 'value'),
     Input('social_url_f'    , 'on'),
     Input('notes'            , 'value'),
     Input('notes_f'        , 'on'),
     Input('api_key'        , 'value')
     ]) 

def update_output(first_name, first_name_f, last_name, last_name_f, 
                institution, institution_f, city, city_f, country, 
                country_f, email, email_f, phone, phone_f, website, 
                website_f, social_url, social_url_f, notes, notes_f, 
                api_key):


    database    = fn.get_path(f'{data_directory}/.data_v2.db')
    conn        = sql.connect(database)
    c            = conn.cursor()

    try:
        query = f"""
            UPDATE user
            SET 
                first_name = '{first_name}', 
                first_name_f = {first_name_f},
                last_name = '{last_name}', 
                last_name_f = {last_name_f},
                institution = '{institution}', 
                institution_f = {institution_f},
                city = '{city}', 
                city_f = {city_f},
                country = '{country}', 
                country_f = {country_f},
                email = '{email}', 
                email_f = {email_f},
                phone = '{phone}', 
                phone_f = {phone_f},
                website = '{website}', 
                website_f = {website_f},
                social_url = '{social_url}', 
                social_url_f = {social_url_f},
                notes = '{notes}', 
                notes_f = {notes_f},
                api_key = '{api_key}'
            WHERE id = 0
        """
        
        c.execute(query)
        conn.commit()

        logger.info(f'User infor saved to database')
        
        return 'Details saved'
    except Exception as e:
        return f'Error: {str(e)}'


# -----Request API button -----------------------------

@app.callback(
    Output('get_api_output', 'children'),
    Input('get_api', 'n_clicks'),
    [State('first_name'        , 'value'),
     State('first_name_f'    , 'on'),
     State('last_name'        , 'value'),
     State('last_name_f'    , 'on'),
     State('institution'    , 'value'),
     State('institution_f'    , 'on'),
     State('city'            , 'value'),
     State('city_f'            , 'on'),
     State('country'        , 'value'),
     State('country_f'        , 'on'),
     State('email'            , 'value'),
     State('email_f'        , 'on'),
     State('phone'            , 'value'),
     State('phone_f'        , 'on'),
     State('website'        , 'value'),
     State('website_f'        , 'on'),
     State('social_url'        , 'value'),
     State('social_url_f'    , 'on'),
     State('notes'            , 'value'),
     State('notes_f'        , 'on')
    ]
)


def request_api_key(n_clicks, first_name, first_name_f, last_name, 
                    last_name_f, institution, institution_f, city,
                    city_f, country, country_f, email, email_f,
                    phone, phone_f, website, website_f, social_url,
                    social_url_f, notes, notes_f):

    if n_clicks is None or n_clicks == 0:
        return "Click the button to get your API key"
    else:
        # Construct the data payload
        data = {
            "first_name": first_name,
            "first_name_f": first_name_f,
            "last_name": last_name,
            "last_name_f": last_name_f, 
            "institution": institution, 
            "institution_f": institution_f, 
            "city": city,
            "city_f": city_f, 
            "country": country, 
            "country_f": country_f, 
            "email": email, 
            "email_f": email_f,
            "phone": phone, 
            "phone_f": phone_f, 
            "website": website, 
            "website_f": website_f, 
            "social_url": social_url,
            "social_url_f": social_url_f, 
            "notes": notes, 
            "notes_f": notes_f
        }

        # URL of your server endpoint
        url = "https://gammaspectacular.com/spectra/request_api_key"

        # Sending a POST request to the server
        try:
            response = req.post(url, json=data)
            if response.status_code == 200:
                # Handle successful response
                logger.info(f'API Key succsessfully requested')
                return "API key requested. Please check your email."
            else:
                # Handle error in response
                logger.error(f'Error requesting API key: {response.text}')

                return f"Error requesting API key: {response.text}"

        except req.exceptions.RequestException as e:
            # Handle request exception
            logger.error(f'Error requesting API key: {e}')
            return f"An error occurred: {e}"

        return "API key requested. Please check your email."

@app.callback(
    Output('tab0_box_2', 'children'),
    [Input('update_my_spectra', 'n_intervals')]  
)
def update_my_spectra(n):

    api_key = fn.get_api_key()

    response = req.post('https://www.gammaspectacular.com/spectra/get_my_spectra', data={'api_key': api_key})

    if response.status_code == 200:
        spectra_data = response.json()

    # Convert data for DataTable
        data_for_table = [
            {
                'ID': spectrum['id'],
                'Date': spectrum['datetime'],
                'Filename': spectrum['filename'],
                # Format the download link as markdown
                'Download': f"[Download](https://www.gammaspectacular.com/spectra/files/{spectrum['id']}.json)",
                'Delete':"X"
            } for spectrum in spectra_data
        ]
        

        table = html.Div([
            
            html.H1('My Published Spectra'),
            dash_table.DataTable(
                id='my_spectra_table',
                data=data_for_table,
                columns=[
                    {'name': 'ID', 'id': 'ID'},
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Filename', 'id': 'Filename'},
                    {'name': 'Download', 'id': 'Download', 'presentation': 'markdown'},
                    {'name': 'Delete', 'id': 'Delete'}
                ],
                style_cell={'width': 'auto', 'text-align':'center', 'fontFamily':'Arial', 'height': '12px'},
                markdown_options={"link_target": "_blank"}  # Open links in new tab
            )
        ])

        return table

    else:
        logger.error(f'Error in  tab0 update_my_spectra()')
        return html.P(f'Error fetching data')

@app.callback(
    Output('delete_output', 'children'),  # Output to display some deletion status
    Input('my_spectra_table', 'active_cell'),  # Input from the DataTable
    State('my_spectra_table', 'data')  # State of the data in the DataTable
)
def delete_spectrum(active_cell, data):
    if active_cell and active_cell['column_id'] == 'Delete':
        row_id = data[active_cell['row']]['ID']
        api_key = fn.get_api_key()

        try:
            response = req.post('https://www.gammaspectacular.com/spectra/delete', data={'api_key': api_key, 'spectrum_id': row_id})

            if response.status_code == 200:
                return f"Spectrum with ID {row_id} has been deleted."
            else:
                # Return a more informative error message
                logger.error(f'Error deleting spectrum: {response.text}')
                return f"Error deleting spectrum: {response.text}"

        except Exception as e:
            # Return the error message for debugging
            logger.error(f'Error deleting spectrum tab0: {e}')
            return f"An error occurred: {str(e)}"

    return ""   

