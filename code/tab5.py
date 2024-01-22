# tab5.py
import dash
import os
import logging
import requests
import dash_core_components as dcc
import plotly.graph_objs as go

from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from server import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")

total_pages = 1

def show_tab5():

    # Pagination buttons
    pagination_div = html.Div([
        html.Button('Previous', id='prev-page-button', n_clicks=0, style={'marginRight': '10px'}),
        html.Div(id='page-info', children=f'Page 1 of {total_pages}', style={'display': 'inline-block', 'marginRight': '10px'}),
        html.Button('Next', id='next-page-button', n_clicks=0),
        html.Div(id='current-page', style={'display': 'none'}, children='1')
    ], style={'textAlign': 'center', 'marginTop': '20px', 'marginBottom': '20px'})

    return html.Div([
        # Search input
        dcc.Input(
            id='tab5_search', 
            type='text', 
            placeholder='Search spectra', 
            autoFocus=True,
            style={'float': 'right', 'width':'200px', 'textAlign':'left', 'marginBottom':'20px', 'backgroundColor':'#D1E9F9', 'fontSize':18, 'padding':5}),
        
        html.H1("Public Spectrum Repository", style={'textAlign': 'center'}),
        # Container for the data rows
        html.Div(id='spectrum-data', style={'width': '90%', 'margin': 'auto'}),
        html.Div(id='total-pages', style={'display': 'none'}),
        html.Div(pagination_div),
        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),

    ], style={'width':'80%', 'padding':30,'height':1300,'margin':'auto', 'backgroundColor':'white'})



    return html_tab5

# ---- End of html - Start callbacks --------


@app.callback(
    [Output('spectrum-data', 'children'),
     Output('total-pages', 'children'),
     Output('current-page', 'children'),
     Output('page-info', 'children')],
    [Input('prev-page-button', 'n_clicks'),
     Input('next-page-button', 'n_clicks'),
     Input('tab5_search', 'value')],
     [State('current-page', 'children')]
)
def update_table_and_page_info(prev_clicks, next_clicks, search_value, current_page):

    total_pages  = '0'
    current_page = '1'

    # Determine the current page based on button clicks
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if 'next-page-button' in changed_id:
        current_page = int(current_page) + 1

    elif 'prev-page-button' in changed_id:
        current_page = max(int(current_page) - 1, 1)

    if not search_value:
        search_value = ''

    # Include current_page in the request
    response = requests.post('https://gammaspectacular.com/spectra/search', 
        data={'query': search_value, 'total_pages': total_pages,'current_page': current_page })    

    if response.status_code == 200:
        response_data   = response.json()
        spectra_data    = response_data['data']
        total_pages     = response_data['total_pages']

        # Creating a list of html.Div elements for each record
        data_divs       = []

        for record in spectra_data:

            id          = record['id']
            filename    = record['filename']
            date        = record['date']
            client_info = record['client']
            spectrum    = record.get('spectrum')

            first_name  = client_info.get('first_name', '')
            last_name   = client_info.get('last_name', '')
            institution = client_info.get('institution', 'N/A')
            city        = client_info.get('city', 'N/A')
            country     = client_info.get('country', 'N/A')
            email       = client_info.get('email', 'N/A')
            phone       = client_info.get('phone', 'N/A')
            web         = client_info.get('web', 'N/A')
            social      = client_info.get('social', 'N/A')
            notes       = client_info.get('notes', 'N/A')

            download    = f'https://www.gammaspectacular.com/spectra/files/{id}.json'

            fig         = []

            # Format file information
            file_info_div = html.Div([
                html.H3(f"File #  {id}"),
                html.P(filename),
                html.P(f"Date: {date}"),
                html.P(f"Channels: "),
                html.A("Download", href=download, target='_blank')
            ], style={'float': 'left', 'width': '20%'})

            # Format client information
            
            client_info_div = html.Div([
                html.P(f"Contributor: {first_name} {last_name}"),
                html.P(f"Institution: {institution}", style={'height':10}),
                html.P(f"City: {city}, {country}", style={'height':10}),
                html.P(f"email: {email} Phone: {phone}", style={'height':10}),
                html.P(html.A(web, href=web, target="_blank"), style={'height':10}),
                html.P(html.A(social, href=social, target="_blank"), style={'height':10}),
                html.P(f"Notes: {notes}"),
                # Include other client details as needed
            ], style={'float': 'left', 'width': '40%'})

            # Plot div - placeholder for now, replace with actual plot code as needed
            plot_div = html.Div([
                dcc.Graph(
                    figure=fig,
                    style={'height': '100%', 'width': '100%'}
                )
            ], style={'float': 'left', 'width': '30%'})


            # Combine the divs into a single row
            row_div = html.Div([file_info_div, client_info_div, plot_div], 
                style={'width': '100%', 'padding': 10, 'float': 'left', 'backgroundColor': 'white', 'clear': 'both'})

            # Generate a basic plot
            fig = go.Figure(data=[go.Scatter(
                y=spectrum, 
                mode='lines',
                fill='tozeroy',
                line=dict(color='black'),
                fillcolor='black'
            )])
            fig.update_layout(
                title=filename,
                title_font_size=14,
                height=225,
                width=450,
                margin=dict(l=5, r=5, t=30, b=5), 
                xaxis={'visible': True}, 
                yaxis={'visible': False}
            )

            # Plot div with the graph
            plot_div = html.Div([
                dcc.Graph(
                    figure=fig,
                    style={'height': '100%', 'width': '100%'}
                )
            ], style={'float': 'left', 'width': '40%'})

            # Combine the divs into a single row
            row_div = html.Div([file_info_div, client_info_div, plot_div], 
                style={'width': '100%', 'padding': 10, 'float': 'left', 'backgroundColor': 'white', 'clear': 'both'})

            data_divs.append(row_div)

        new_page_info = f"Page {current_page} of {total_pages}"

        return data_divs, total_pages, current_page, new_page_info

    else:

        return [], '0', '1', 'Page 1 of 0' 