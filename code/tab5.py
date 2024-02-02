# tab5.py
import dash
import os
import logging
import json
import requests
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import numpy as np

from dash import html, dcc
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from server import app
from functions import fetch_json

logger = logging.getLogger(__name__)

data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")

total_pages = 1


def show_tab5():

    modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Full Resolution Histogram")),
        dbc.ModalBody([
            dcc.Graph(id='detailed-histogram'),
            html.Div([
                dcc.Checklist(id='linlog',
                    options=[{'label': ' Log Scale', 'value': 'log'}],
                    value=[], 
                    inline=True,
                ),
            ]),
        ]),
        dbc.ModalFooter(dbc.Button("Close", id="close-modal", className="ml-auto")),
    ],
    id="modal",
    size="xl",  # xtra large modal
    is_open=False,  # Initially closed
)

    # Pagination buttons
    pagination_div = html.Div([
        html.Button('Previous', id='prev-page-button', n_clicks=0, style={'marginRight': '10px'}),
        html.Div(id='page-info', children=f'Page 1 of {total_pages}', style={'display': 'inline-block', 'marginRight': '10px'}),
        html.Button('Next', id='next-page-button', n_clicks=0),
        html.Div(id='current-page', style={'display': 'none'}, children='1')
    ], style={'textAlign': 'center', 'marginTop': '20px', 'marginBottom': '20px', 'width': '300px', 'margin': 'auto'})

    return html.Div([

        html.Div(id='t5_heading', children=[  
            
            html.H1("Public Spectrum Repository"),
            html.H3('Record a great spectrum,'),
            html.H3('Give it a descriptive name,'),
            
            # Search input
            dcc.Input(id='tab5_search', 
                    type='text', 
                    placeholder='Search spectra', 
                    autoFocus=True,
                    style={'float': 'right', 'width':'200px', 'marginRight':'10%','backgroundColor':'#e6f2ff', 'fontSize':18, 'padding':5}),
            html.H3('Publish it for the world to see !'),
            
            html.P('Note: Calibration on thumb nail spectra may be out due to data compression', style={'fontSize':'10px'}),
            html.Hr(),
            
        ], style={'width':'90%', 'margin':'auto', 'textAlign':'left'}),

        # Container for the data rows
        html.Div(id='spectrum-data', style={'width': '90%', 'margin': 'auto'}),
        html.Div(id='total-pages', style={'display': 'none'}),

        html.Div(children=[
            html.Div(pagination_div),
        ], style ={'width':'100%'}), 

        html.Div(children=[ html.Img(id='footer', src='https://www.gammaspectacular.com/steven/impulse/footer.gif')]),

        modal,

    ], style={'width':'96%', 'padding':30,'height':'100%','margin':'auto', 'backgroundColor':'white', 'textAlign':'center'})

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
    i            = 0
    value_list   = []
    buttons      = []

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
        current_page    = response_data['current_page']

        # Creating a list of html.Div elements for each record
        data_divs       = []
        

        for record in spectra_data:
            
            id          = record['id']

            value_list.append(id)
            
            filename    = record['filename']
            date        = record['date']
            client_info = record['client']
            spectrum    = record['npes']['data'][0]['resultData']['energySpectrum']['spectrum']
            location    = record['npes']['data'][0]['sampleInfo']['location']
            specnote    = record['npes']['data'][0]['sampleInfo']['note']
            coefficients= record['npes']['data'][0]['resultData']['energySpectrum']['energyCalibration']['coefficients']
            channels_l  = record['npes']['data'][0]['resultData']['energySpectrum']['numberOfChannels']
            spec_notes  = record['npes']['data'][0]["sampleInfo"]["note"]
            
            channels_s  = len(spectrum)
            x_factor    = channels_l/channels_s
            x_values    = [i * x_factor for i in range(channels_s)]

            coeff_1     = coefficients[2] 
            coeff_2     = coefficients[1]
            coeff_3     = coefficients[0] + 5 # botch !
            calib_x     = [coeff_1*x**2 + coeff_2*x + coeff_3 for x in x_values]

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

            button = html.Button(
                'zoom', 
                id={'type': 'zoom-button', 'value': str(id)},
                n_clicks=0,
            )
            buttons.append(button)

            # Format file information
            file_info_div = html.Div(id='tab5_col_1', children=[
                html.H4(f"#  {id}"),
                html.P(filename),
                html.P(f"{date}"),
                html.P(f"Channels: {channels_l}"),
                html.A("Download", href=download, target='_blank'),
            ], style={'textAlign':'left','width': '130px', 'padding': '10px'})

            

            # Format client information
            client_info_div = html.Div(id='tab5_col_2', children=[
                html.P(f"{first_name} {last_name}"),
                html.P(f"{institution}", style={'height':10}),
                html.P(f"{city} - {country}", style={'height':10}),
                html.P(f"e: {email}", style={'height':10, 'fontSize':10}),
                html.P(f"p: {phone}", style={'height':10}),
                html.P(html.A(web, href=web, target="_blank"), style={'height':10, 'fontSize':10}),
                html.P(html.A(social, href=social, target="_blank"), style={'height':10, 'fontSize':10}),
                html.P(f"Note: {notes}"),
                # Include other client details as needed
            ], style={'width': '250px', 'padding':'10px'})

            notes_div = html.Div(id='tab5_col_3', children=[
                html.P(id='spec_notes', children =[spec_notes]),

                ], style={'width':'200px', 'height':'175px', 'marginRight':10, 'padding':'5px', 'marginTop':'30px', 'backgroundColor':'#e6f2ff'})


            plot_div = html.Div(id='tab5_col_4', children=[dcc.Graph(figure=fig)]),

            button_div = html.Div(id='tab5_col_5', children=[button], style={
                'width': '70px',  # Ensure units are specified for width and height
                'height': '200px',
                'display': 'flex',  # Make the div a flex container
                'flex-direction': 'column',  # Stack children vertically
                'justify-content': 'flex-end',  # Align children to the end (bottom) of the container
                })


            # Generate a basic plot
            fig = go.Figure(data=[go.Scatter(
                x = calib_x,
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
                width=400,
                plot_bgcolor='#e6f2ff',
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
            ])

            i = i+1

            # Combine the divs into a single row
            row_div = html.Div([file_info_div, client_info_div, notes_div, plot_div, button_div], 
                style={
                    'display':'flex',
                    'flex-wrap':'wrap',
                    'align-items': 'flex-start',  
                    'justify-content': 'center',  
                    'width':'100%',
                    'clear': 'both',
                    })

            data_divs.append(row_div)

        new_page_info = f"Page {current_page} of {total_pages}"

        
        return data_divs, total_pages, current_page, new_page_info

    else:

        return [], '0', '1', 'Page 1 of 0'

# ------------- zoom functions below here------------------


@app.callback(
    [Output('modal', 'is_open'),  # This output toggles the modal
     Output('detailed-histogram', 'figure')],  # This output updates the figure in the graph within the modal
    [Input({'type': 'zoom-button', 'value': ALL}, 'n_clicks'),
     Input('close-modal', 'n_clicks'),
     Input('linlog', 'value')],
    [State('modal', 'is_open'), 
    State('detailed-histogram', 'figure')]
)
def toggle_modal(zoom_clicks, close_clicks, linlog, is_open, current_figure):
    ctx = dash.callback_context

    if not ctx.triggered:

        raise PreventUpdate

    triggered_id, triggered_prop = ctx.triggered[0]['prop_id'].split('.')

    if 'close-modal' in triggered_id:

        return False, dash.no_update  # Ensure the modal is closed

    scale = 'log' if 'log' in linlog else 'linear'

    # Check if the scale toggle was the trigger
    if 'linlog' in triggered_id:
        if current_figure:
            # Update only the y-axis scale of the current figure
            current_figure['layout']['yaxis']['type'] = scale
            return is_open, current_figure
    try:
        # Attempt to parse the triggered_id if it's expected to be in JSON format
         if any(click and 'zoom-button' in triggered_id for click in zoom_clicks):
            parsed_id = json.loads(triggered_id.replace('zoom-button.', ''))
            filename = parsed_id['value']

            if any(click > 0 for click in zoom_clicks):

                file = fetch_json(filename)

                if file:
                    y_values        = file['data'][0]['resultData']['energySpectrum']['spectrum']
                    x_values        = list(range(len(y_values)))
                    coefficients    = file['data'][0]['resultData']['energySpectrum']['energyCalibration']['coefficients']
                    title           = file['data'][0]['sampleInfo']['name']

                    # Ensure x_values is a NumPy array
                    x_values_np = np.array(x_values)

                    # Calculate new x_values using the second-order polynomial
                    calibrated_x = coefficients[2] * x_values_np**2 + coefficients[1] * x_values_np + coefficients[0]

                    

                    figure = go.Figure(
                        data=[go.Scatter(
                            y=y_values, 
                            x=calibrated_x,

                            mode='markers',
                            marker=dict(color='lightgreen', size=1, 
                            line=dict( color='yellow', width=1),
                        ))])

                    # Customize the layout
                    figure.update_layout(
                        title=title,
                        title_x=0.5,  # Center the title
                        xaxis=dict(showgrid=True, gridcolor='gray', gridwidth=1 ),
                        xaxis_title='energy',
                        yaxis=dict(showgrid=True, gridcolor='gray', gridwidth=1, type=scale),
                        yaxis_title='counts',
                        font=dict(family="Arial, Bold", size=16, color="#ffffff"),
                        margin=dict(l=10, r=100, t=40, b=60),
                        plot_bgcolor='black',
                        paper_bgcolor='black',  
                    

                        shapes=[  # Add shapes for horizontal and vertical lines
                            # Horizontal line
                            go.layout.Shape(
                                type="line",
                                x0=min(x_values),
                                x1=max(x_values),
                            ),
                            # Vertical line
                            go.layout.Shape(
                                type="line",
                                y0=min(y_values),
                                y1=max(y_values),
                            )]
                        )

                    return not is_open, figure  # Toggle the modal state and update the figure

    except json.JSONDecodeError:

        raise PreventUpdate

    return is_open, dash.no_update  # Default action if no conditions are met
