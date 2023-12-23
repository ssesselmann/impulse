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
from dash import dcc, html
from dash.dependencies import Input, Output

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")

def show_tab0():

	database 	= fn.get_path(f'{data_directory}/.data.db')
	conn 		= sql.connect(database)
	c 			= conn.cursor()
	query 		= "SELECT * FROM user "

	c.execute(query) 

	user 			= c.fetchall()[0]
	first_name	  	= user[1]
	first_name_f	= user[2] 		 
	last_name	 	= user[3]
	last_name_f	 	= user[4] 					
	institution	 	= user[5]
	institution_f   = user[6] 	
	city			= user[7]
	city_f		  	= user[8] 	
	country			= user[9]
	country_f		= user[10]  
	email 			= user[11]
	email_f 		= user[12]
	phone   		= user[13]
	phone_f  		= user[14]
	website 		= user[15]
	website_f  		= user[16]
	social_url 		= user[17]
	social_url_f  	= user[18]
	notes 			= user[19]
	notes_f     	= user[20]
	api_key			= user[21]

	html_tab0 = html.Div(id = 'tab_0', children=[

		html.Div(id='tab0_text_box', children= [
			html.P(''),
			html.P(''),
			html.H1(f'{first_name} {last_name}\'s Details'),
			html.P('This page is intended for your personal details and all fields are stored on your local machine, so you don\'t have to worry about privacy.'),
			html.P('When you choose to publish one of your great spectra for other users to see, you can choose which fields to publish, putting you in control of your data.'),
			html.Hr(),

			dcc.Input(id='first_name', type='text', value=first_name, placeholder='Firstname', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='first_name_f',
				on= bool(first_name_f),
				color='green',
				className='my_checkbox'
			),
			html.Label(id='publish_label', children=' << Publish'),

			dcc.Input(id='last_name', type='text', value=last_name, placeholder='Lastname', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='last_name_f',
				on=bool(last_name_f),
				color='green',
				className='my_checkbox'
			),

			dcc.Input(id='institution', type='text', value=institution, placeholder='Institution', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='institution_f',
				on=bool(institution_f),
				color='green',
				className='my_checkbox'
			),

			dcc.Input(id='city', type='text', value=city, placeholder='City', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='city_f',
				on=bool(city_f),
				color='green',
				className='my_checkbox'
			),

			dcc.Input(id='country', type='text', value=country, placeholder='Country', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='country_f',
				on=bool(country_f),
				color='green',
				className='my_checkbox'
			),

			dcc.Input(id='email', type='text', value=email, placeholder='email', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='email_f',
				on=bool(email_f),
				color='green',
				className='my_checkbox'
			),

			dcc.Input(id='phone', type='text', value=phone, placeholder='+00 0000 000 000 phone', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='phone_f',
				on=bool(phone_f),
				color='green',
				className='my_checkbox'
			),

			dcc.Input(id='website', type='text', value=website, placeholder='www.domain.com', className='my_inputs', style={'margin-bottom': '10px'}),
			daq.BooleanSwitch(
				id='website_f',
				on=bool(website_f),
				color='green',
				className='my_checkbox'
			),

			dcc.Input(id='social_url', type='text', value=social_url, placeholder='social_url', className='my_inputs', style={'margin-bottom': '10px'}),
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
			dcc.Input(id='api_key', type='text', value=api_key, placeholder='api_key', className='my_inputs', style={'margin-bottom': '10px'}),
			html.Hr(),
			html.Div(id='output-div'),
			html.P('This page will be used for a new feature coming soon'),


		]),
	]) # end of page html_tab0 --------------------------------------------------

	return html_tab0

#---- Callback ----------------------------------------------------------
@app.callback(
	Output('output-div'		, 'children'),
	[Input('first_name'		, 'value'),
	 Input('first_name_f'	, 'on'),
	 Input('last_name'		, 'value'),
	 Input('last_name_f'	, 'on'),
	 Input('institution'	, 'value'),
	 Input('institution_f'	, 'on'),
	 Input('city'			, 'value'),
	 Input('city_f'			, 'on'),
	 Input('country'		, 'value'),
	 Input('country_f'		, 'on'),
	 Input('email'			, 'value'),
	 Input('email_f'		, 'on'),
	 Input('phone'			, 'value'),
	 Input('phone_f'		, 'on'),
	 Input('website'		, 'value'),
	 Input('website_f'		, 'on'),
	 Input('social_url'		, 'value'),
	 Input('social_url_f'	, 'on'),
	 Input('notes'			, 'value'),
	 Input('notes_f'		, 'on'),
	 Input('api_key'		, 'value')
	 ]) 

def update_output(first_name, first_name_f, last_name, last_name_f, 
				institution, institution_f, city, city_f, country, 
				country_f, email, email_f, phone, phone_f, website, 
				website_f, social_url, social_url_f, notes, notes_f, 
				api_key):


	database	= fn.get_path(f'{data_directory}/.data.db')
	conn		= sql.connect(database)
	c		    = conn.cursor()

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
		
		return 'Details saved'
	except Exception as e:
		return f'Error: {str(e)}'
