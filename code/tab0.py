# tab0.py
import plotly.graph_objects as go
import functions as fn
import distortionchecker as dcr
import shapecatcher as sc
import os
import global_vars
import logging
import requests as req
import dash_daq as daq
from server import app
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import json

logger = logging.getLogger(__name__)

with global_vars.write_lock:
    data_directory      = global_vars.data_directory
    user_settings_file  = global_vars.user_settings

n_clicks = None

def load_user_settings():
    if os.path.exists(user_settings_file):
        with open(user_settings_file, 'r') as file:
            return json.load(file)
    return {
        "first_name": "",
        "first_name_f": False,
        "last_name": "",
        "last_name_f": False,
        "institution": "",
        "institution_f": False,
        "city": "",
        "city_f": False,
        "country": "",
        "country_f": False,
        "email": "",
        "email_f": False,
        "phone": "",
        "phone_f": False,
        "website": "",
        "website_f": False,
        "social_url": "",
        "social_url_f": False,
        "notes": "",
        "notes_f": False,
        "api_key": ""
    }

def save_user_settings(settings):
    with open(user_settings_file, 'w') as file:
        json.dump(settings, file, indent=4)

def show_tab0():
    user = load_user_settings()

    html_tab0 = html.Div(id='tab_0', children=[
        html.Div(id='tab0-frame', children=[
            html.Div(id='tab0_box_1', children=[
                html.P(''),
                html.P(''),
                html.H1('My details'),
                html.P('This page is intended for your personal details and all fields are stored on your local machine, so you don\'t have to worry about privacy.'),
                html.P('When you choose to publish one of your great spectra for other users to see, you can choose which fields to publish, putting you in control of your data.'),
                html.Hr(),
                html.Div(id='publish_label', children='Publish'),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='first_name', type='text', value=user['first_name'], placeholder='Firstname', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='first_name_f',
                        on=bool(user['first_name_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='last_name', type='text', value=user['last_name'], placeholder='Lastname', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='last_name_f',
                        on=bool(user['last_name_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='institution', type='text', value=user['institution'], placeholder='Institution', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='institution_f',
                        on=bool(user['institution_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='city', type='text', value=user['city'], placeholder='City', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='city_f',
                        on=bool(user['city_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='country', type='text', value=user['country'], placeholder='Country', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='country_f',
                        on=bool(user['country_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='email', type='text', value=user['email'], placeholder='email', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='email_f',
                        on=bool(user['email_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='phone', type='text', value=user['phone'], placeholder='+00 0000 000 000 phone', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='phone_f',
                        on=bool(user['phone_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='website', type='text', value=user['website'], placeholder='www.domain.com', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='website_f',
                        on=bool(user['website_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Input(id='social_url', type='text', value=user['social_url'], placeholder='social_url', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='social_url_f',
                        on=bool(user['social_url_f']),
                        color='green',
                        className='my_checkbox'
                    )]),

                html.Div(className='tab0row', children=[
                    dcc.Textarea(id='notes', value=user['notes'], placeholder='notes', className='my_inputs'),
                    daq.BooleanSwitch(
                        id='notes_f',
                        on=bool(user['notes_f']),
                        color='green',
                        className='my_checkbox',
                    )]),

                html.Hr(),
                dcc.Input(id='api_key', type='text', value=user['api_key'], placeholder='api_key', className='my_inputs', style={'marginBottom': '10px', 'fontSize': '8px', 'width': '80%'}),
                html.Button('Request API',
                            id='get_api',
                            className='action_button',
                            style={'width': 100, 'marginLeft': '10px'}
                            ),
                html.Div(id='get_api_output', children=''),
                html.P(),
                html.Div(id='output-div'),
                html.Button('Update my spectra', id='update_my_spectra', style={'visibility': 'hidden'}),
                html.P(id='delete_output', children=''),

            ]),

            html.Div(id='tab0_box_2', children=[
            ]),
           html.Div(children=[html.Img(id='footer', src='assets/footer.gif')]), 
        ]),

        

    ])

    return html_tab0

@app.callback(
    Output('output-div', 'children'),
    [Input('first_name', 'value'),
     Input('first_name_f', 'on'),
     Input('last_name', 'value'),
     Input('last_name_f', 'on'),
     Input('institution', 'value'),
     Input('institution_f', 'on'),
     Input('city', 'value'),
     Input('city_f', 'on'),
     Input('country', 'value'),
     Input('country_f', 'on'),
     Input('email', 'value'),
     Input('email_f', 'on'),
     Input('phone', 'value'),
     Input('phone_f', 'on'),
     Input('website', 'value'),
     Input('website_f', 'on'),
     Input('social_url', 'value'),
     Input('social_url_f', 'on'),
     Input('notes', 'value'),
     Input('notes_f', 'on'),
     Input('api_key', 'value')
     ])
def update_output(first_name, first_name_f, last_name, last_name_f,
                  institution, institution_f, city, city_f, country,
                  country_f, email, email_f, phone, phone_f, website,
                  website_f, social_url, social_url_f, notes, notes_f,
                  api_key):

    user_settings = {
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
        "notes_f": notes_f,
        "api_key": api_key
    }

    try:
        save_user_settings(user_settings)
        logger.info('User info saved to JSON file\n')
        return 'Details saved'
    except Exception as e:
        logger.error(f'Error saving user info: {e}\n')
        return f'Error: {str(e)}'

@app.callback(
    Output('get_api_output', 'children'),
    Input('get_api', 'n_clicks'),
    [State('first_name', 'value'),
     State('first_name_f', 'on'),
     State('last_name', 'value'),
     State('last_name_f', 'on'),
     State('institution', 'value'),
     State('institution_f', 'on'),
     State('city', 'value'),
     State('city_f', 'on'),
     State('country', 'value'),
     State('country_f', 'on'),
     State('email', 'value'),
     State('email_f', 'on'),
     State('phone', 'value'),
     State('phone_f', 'on'),
     State('website', 'value'),
     State('website_f', 'on'),
     State('social_url', 'value'),
     State('social_url_f', 'on'),
     State('notes', 'value'),
     State('notes_f', 'on')
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

        url = "https://gammaspectacular.com/spectra/request_api_key"

        try:
            response = req.post(url, json=data)
            if response.status_code == 200:
                logger.info('API Key successfully requested\n')
                return "API key requested. Please check your email."
            else:
                logger.error(f'Error requesting API key: {response.text}\n')
                return f"Error requesting API key: {response.text}"

        except req.exceptions.RequestException as e:
            logger.error(f'Error requesting API key: {e}\n')
            return f"An error occurred: {e}"

@app.callback(
    Output('tab0_box_2', 'children'),
    [Input('update_my_spectra', 'n_intervals')]
)
def update_my_spectra(n):
    user_settings = load_user_settings()
    api_key = user_settings.get('api_key')

    if not api_key:
        logger.error('API key is missing\n')
        return html.P('Error: API key is missing')

    try:
        response = req.post('https://www.gammaspectacular.com/spectra/get_my_spectra', data={'api_key': api_key})

        if response.status_code == 200:
            spectra_data = response.json()

            data_for_table = [
                {
                    'ID': spectrum['id'],
                    'Date': spectrum['datetime'],
                    'Filename': spectrum['filename'],
                    'Download': f"[Download](https://www.gammaspectacular.com/spectra/files/{spectrum['id']}.json)",
                    'Delete': "del"
                } for spectrum in spectra_data
            ]

            table = html.Div([
                html.H1('My published spectra'),
                dash_table.DataTable(
                    id='my-spectra-table',
                    data=[
                        {
                            'ID': spectrum['id'],
                            'Date': spectrum['datetime'],
                            'Filename': spectrum['filename'],
                            'Download': f"[Download](https://www.gammaspectacular.com/spectra/files/{spectrum['id']}.json)",
                            'Delete': "del"
                        } for spectrum in spectra_data
                    ],
                    columns=[
                        {'name': 'ID', 'id': 'ID'},
                        {'name': 'Date', 'id': 'Date'},
                        {'name': 'Filename', 'id': 'Filename'},
                        {'name': 'Download', 'id': 'Download', 'presentation': 'markdown'},
                        {'name': 'Delete', 'id': 'Delete'}
                    ],
                    markdown_options={"link_target": "_blank"}
                )
            ])



            return table

        else:
            logger.error(f'Error fetching spectra data: {response.status_code} - {response.text}\n')
            return html.P(f'Error fetching data: {response.status_code}')

    except req.exceptions.RequestException as e:
        logger.error(f'Error fetching spectra data: {e}\n')
        return html.P('No internet connection - unable to update')

@app.callback(
    Output('delete_output', 'children'),
    Input('my-spectra-table', 'active_cell'),
    State('my-spectra-table', 'data')
)
def delete_spectrum(active_cell, data):
    if active_cell and active_cell['column_id'] == 'Delete':
        row_id = data[active_cell['row']]['ID']
        user_settings = load_user_settings()
        api_key = user_settings.get('api_key')

        if not api_key:
            logger.error('API key is missing\n')
            return 'Error: API key is missing'

        try:
            response = req.post('https://www.gammaspectacular.com/spectra/delete', data={'api_key': api_key, 'spectrum_id': row_id})

            if response.status_code == 200:
                return f"Spectrum with ID {row_id} has been deleted."
            else:
                logger.error(f'Error deleting spectrum: {response.text}\n')
                return f"Error deleting spectrum: {response.text}"

        except Exception as e:
            logger.error(f'Error deleting spectrum: {e}\n')
            return f"An error occurred: {str(e)}"

    return ""
