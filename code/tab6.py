# tab6.py
import dash
import dash_daq as daq
import os
import glob
import logging
import functions as fn
import global_vars

from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from server import app
from flask import request

logger = logging.getLogger(__name__)

data_directory = global_vars.data_directory

def show_tab6():
    # Get all the filenames in the folder with the extension ".json"
    files = glob.glob(os.path.join(data_directory, "*.json"))
    # Filter out filenames ending with "-cps.json"
    filtered_files = [file for file in files if not file.endswith("-cps.json")]
    # format options
    options = [{'label': os.path.basename(file), 'value': os.path.basename(file)} for file in filtered_files]
    # Sort the options alphabetically by label
    options_sorted = sorted(options, key=lambda x: x['label'])

    # Load theme from global_vars
    with global_vars.write_lock:
        theme = global_vars.theme

    html_tab6 = html.Div([
        html.Div(id='exit', children=[
            html.Button(id='exit-button', children=''),
            html.Div(dcc.Dropdown(
                id="theme",
                className='dropdown',
                options=[
                    {"label": "Lightgray", "value": "lightgray"},
                    {"label": "Orange", "value": "orange"},
                    {"label": "Pink", "value": "pink"},
                    {"label": "Sunburst", "value": "sunburst"},
                    {"label": "Potassium", "value": "potassium"},
                    {"label": "Under Water", "value": "underwater"},
                    {"label": "Milky Way", "value": "milkyway"},
                ],
                value=theme,  # pre-selected option
                clearable=False,
            )),
            html.Div(id='theme_output', children=' '),
            html.Div(dcc.Dropdown(
                id='export_histogram',
                className='dropdown',
                options=options_sorted,
                placeholder='Export spectrum to csv file',
                value=None
            )),
            html.Div(id='export_histogram_output_div', children=[
                html.P(id='export_histogram_output', children='')
            ])
        ]),

        html.Div(id='tab6_text_div', children=[
            html.Hr(),
            html.Div(id='manual', children=[
                html.H1('Impulse V2.0 Manual'),
                html.P('Thank you for downloading and installing Impulse gamma spectrometry, this open source software is written in Python with the intention that users may modify and adapt it to their own experiments.'),
                html.P('In the following text I shall describe how the software works and what each setting parameter does.'),
                
                html.H4('Using a Sound Card as an ADC'),
                html.P('Gamma radiation detectors with photomultipler tubes PMTs, output pulses in the form of an analogue voltage. Typically the pulses are on the order of 4 µs. which is too fast for sampling by commercial sound cards, but by amplifying and passing the signal through a low pass filter the pulse can be stretched to 100 µs. and then it can be sampled by an audio codec. '),
                html.P('Computer sound cards operate on an AC voltage of around +- 1V and are not compatible with old school NIM equipment unless the signal is attenuated down to the correct range.'),
                
                html.H2('My Details tab'),
                html.P('This tab gives you control over your personal details and your published spectra. Your details are saved in json format in the \'~/impulse_files\' folder on your PC or Mac, and when you apply for an API an account is created for you on the gammaspectacular.com web server which mirrors the data on the client.'),
                html.P('Once you click the \'Request API\' button the server will respond by sending you an email with your personal API key, copy and paste the key into the api_key field.'),
                html.P('Any spectra you publish will appear on the right-hand panel. By clicking the x in the last column you can delete a previously uploaded spectrum. This could be handy if you want to replace an old spectrum with a better one.'), 


                html.H2('Device and Control Tab'),

                html.H4('Device Specific Rendering'),
                html.P('After selecting a spectrometer device from the pulldown menu, refresh the page, fields specific to your device will show.'),

                
                html.H4('Select Device'),
                html.P('Your computer may have several devices connected, so we need to instruct the program which input to use, so just select the correct input device from the pulldown menu. Note, you may need to refresh the page.'),
                
                html.H4('Sample Rate'),
                html.P('Analogue to digital audio sampling involves taking a voltage reading of the analogue signal multiple times a second, the faster the sampling rate the more accurately we can reconstruct the signal. Most modern computers can handle audio sampling rates up to 384 kHz. Faster sampling will generally produce a better spectrum, but it also requires a longer pulse which limits the pulse acquisition rate. If your objective is to measure a high count rate you may want a shorter pulse and a lower sample rate. '),
                
                html.H4('Buffer Size'),
                html.P('Audio streaming is continuous, but computers need to process information in batches, we refer to the batch as a buffer. The default setting is 1024 samples which is the number of samples the computer reads into memory before looking for pulses. This setting may not be required in the future.'),
                
                html.H4('Pulses to Sample'),
                html.P('Audio sampling uses the shape method for filtering out PPU, this method involves comparing each pulse to the mean average pulse, so this setting determines how many pulses to sample for the mean. The more samples you collect the closer to the mean you get, but remember more samples take more time to process. Start with a low number and experiment to find the optimum compromise between time and quality. Note that pulses with a peak value below 3000, which translates to approximately 0.1 Volts or 10%.'),
                
                html.H4('Sample Length'),
                html.P('This setting sets the length of the sample in sample points. Sample length in combination with the sample rate determines how much time it takes to sample a pulse and consequently affects the dead time. Dead time is the amount of time the computer can not process pulses, simply put you can’t measure more than one pulse within (1 second/ sample rate) * (number of samples), let’s take the example (1s/384,000 Hz)*51 samples = 132 µs, now as our pulses are randomly spaced we have to allow more time between pulses, typically three times as much time. We can calculate the maximum count rate as follows: 1s / 132µs / 3 = 2525 cps '),
                html.P('WARNING: Setting both sample length and sample rate to maximum may cause loss of counts as the computer may not be able to keep up.'),

                html.H4('Pulse Shape'),
                html.P('What you see in the pulse shape graph is the left and right channel normalized positive pulse shape. The program runs a quick function to check if the pulses are negative or positive and automatically flips the pulses if necessary, therefore we have no setting for negative pulses. '),
                html.P('Note: Pulse energy must be within a minimum and maximum range for this function to work, so if nothing happens when you click the button, your gain might be too low or too high.'),

                html.H4('Distortion Curve'),
                html.P('The distortion curve plot has no other function than to help you to visualize where the distortion in your sampling is occurring. When you click the [Get Distortion Curve] button the computer collects n unfiltered samples, compares each one with the mean and assigns a distortion factor to each pulse. The distortion factors are then ordered by size and plotted on a graph. The shape of this graph will help you determine how tight to set your distortion tolerance when recording your spectrum on tab2. Shape distortion may be caused by pulse overlap or large pulses that exceed the capacity of the electronic circuit.'),

                html.H2('2D Histogram Tab'),
                html.H4('Spectrum File Name'),
                html.P('This is exactly what it says, you can name your spectrum anything you like, it will automatically save in the user home directory ~/impulse_files/myspectrum.json , the JSON file format is NPESv2 and is backwards compatible with NPESv1. NOTE! It is not possible to rename a file via this input, changing the filename will start a new spectrum. To rename a file go to the impulse_files directory in your home folder. '),
                html.Div(html.A('https://github.com/OpenGammaProject/NPES-JSON', href='https://github.com/OpenGammaProject/NPES-JSON', target='_blank')),
                
                html.H4('Number of Bins & Bin Size'),
                html.P('These two settings determine the number of bins you want in your histogram and the size of each bin. The default settings are 1000 bins and 30 arbitrary units per bin. These numbers have been chosen because it gives you a spectrum range of 3000 which is convenient for most gamma spectra as we are investigating 0 to 3000 keV.'),
                
                html.H4('Stop after n Counts'),
                html.P('As the title says, this setting tells the program when to stop. You can stop the program from executing at any time by entering zero into this field. remember the program will not run unless you have a positive integer in this field.'),
                
                html.H4('LLD Threshold'),
                html.P('This setting sets the Lower Limit Discriminator. As we do not want to count the tiny electronic ripple on the baseline it is important that we set a sensible limit below which to ignore any pulses. If this limit has been set too low, it will appear as a tall peak in the first couple of bins on the left-hand side of your spectrum'),
                
                html.H4('Shape Tolerance'),
                html.P('This setting is related to the mean shape sample and distortion curve on tab1, so run the distortion check first and determine what level of distortion you are prepared to accept. Note, the tighter your tolerance for distortion, the more pulses will be dropped as a result and your count rate will not be accurate. Note!! Distortion typically increases with pulse height, setting distortion too low may result in loss of data at the high end of your spectrum.'),
                
                html.H4('Comparison spectrum'),
                html.P('This is an automatically generated pulldown menu which gets the contents of your impulse_files folder and the subfolder [impulse_files/i] containing all the isotope spectra. Select any spectrum to compare'),
                
                html.H4('Show Comparison spectrum'),
                html.P('This switch simply hides and shows the comparison spectrum'),
                
                html.H4('Subtract Comparison'),
                html.P('As the name suggests this switch subtracts the comparison spectrum, bin for bin, from the main spectrum and is intended for background subtraction.'),
                
                html.H4('Energy by bin'),
                html.P('This function enhances the peaks exponentially towards the right in the spectrum the function (counts)*(bin) = energy by bin'),
                
                html.H4('Show Log'),
                html.P('This switch changes the y axis to log scale, a common way to make the high energy peaks visible.'),
                
                html.H4('Play Sound Button'),
                html.P('This button generates a wav file from the gaussian correlation (1 sigma) from the current spectrum and plays a 2-second cacophony where the x axis represents frequency and the y axis represents volume. The result is a unique chord for each spectrum. The initial wav file takes a moment to generate, but once generated it can be replayed instantly.'),

                html.H4('Update Calibration Button'),
                html.P('During normal recording your calibration settings are automatically saved in the JSON file, however when you want to re-calibrate a previously recorded spectrum you can do so by clicking on this button. The function opens the JSON file and edits the polynomial coefficients'),

                html.H4('Publish Spectrum Button'),
                html.P('Once you have recorded and calibrated a beautiful spectrum, share it with the wider community of Impulse users.'),

                html.H4('Find Isotopes Button'),
                html.P('This button switches isotope information on/off. It will only function when Calibration is switched on and Sigma is not zero. Isotope data comes from the isotopes.json file inside your impulse_files folder in your home directory. The isotopes.json file is not comprehensive, very low intensity and unlikely gamma have been removed to prevent the entire screen filling up with data. Users can add more isotopes to the json file manually if required.'),

                html.H4('Calibration'),
                html.P('The calibration switch turns calibration on or off. Energy calibration is done by a second-order polynomial fit. There are six fields where the user may enter three bins with three corresponding energies. By choosing a linear relationship between bins and energies you can achieve a linear spectrum and by choosing non-linear relationships you can correct for detectors that are non-linear. The typical use case would be to enter the bins and known energies from three widely spread gamma peaks.  '),
                html.P('Note !! Your standard calibration points are saved to your local settings.json, new spectra start recording with these settings. This is convenient if you are using the same detector setup all the time.'),

                html.H4('Coincidence'),
                html.P('The coincidence function only works when there is a signal connected to the right channel audio input. The boolean switch needs to be activated on before the start button is pressed'),
                html.P('When running a coincidence spectrum the default primary detector should always be the left channel, and the secondary or trigger detector connected to the right channel'),        
                html.P('Pulses are considered coincident when the secondary peak occurs within +3 or -3 sample points, therefore a higher sample rate will achieve a tighter coincidence.'),        


                html.H4('Peakfinder'),
                html.P('Impulse has a built-in function which can find peaks and calculate the resolution. The slider adjusts the tolerance, allowing you to increase or reduce the number of peaks found. There is a limit to how close together it can identify two peaks, this is due to the width of the notation only. '),
                
                html.H4('Gaussian Correlation'),
                html.P('This function identifies peaks which are hard to see with the naked eye, it takes the normalized spectrum and calculates the dot product of the gaussian shape with a standard deviation dependent bin number, the slider adjusts sigma, which determines how many bins to average the gaussian function.'),

                html.H4('Spectrum Notes'),
                html.P('This is an input where you can update the notes field on a spectrum after it has been recorded. Function may not work before the file exists, I suggest notating the file after it has been recorded'),

                html.H2('3D Histogram Tab'),
                html.P('This page functions much the same way as the regular 2D histogram, with the added time axis. You can control the time interval between each update. NOTE: Because this spectrum writes a lot of data to the browser it is advisable to keep the number of channels and time intervals to a minimum'), 

                html.H2('Count Rate Tab'),
                html.P('This is a line chart showing the counts per second and is entirely driven by the settings on tab-2 and tab-3. The rolling average (green line) can be adjusted with the slider or for fine adjustment click on the slider and use your left-right arrow keys to move the slider in steps of one second.'),
                html.P('To avoid latency the cps chart will only display the last hour by default, however, the entire recording can be viewed with the Show Complete Dataset switch'),
                
                html.H2('Repository tab'),
                html.P('The is is a common repository where spectra published by all Impulse users appear. All published spectra are saved in NPESv2 json format and can be opened in many popular programs. Please contribute your spectra and make more data available to the community. The search field is a convenient way to find what you are looking for so make sure you give your published spectra a good name.'),
                html.P('The published spectra are stored on the gammaspectacular.com server hosted by Webcentral in Australia'),

                html.Hr(),
                html.H1('Hardware'),

                html.Div('This program will work with any sound card spectrometer or ATOM-NANO serial device. Soundcard spectrometry was invented in Australia by professor Marek Dolleiser' ),
                html.Div('and the first hardware ever made was the Gammaspectacular GS-1100A back in 2010.' ),
                html.Div('Since then there have been many improvements to the hardware and today we have a highly developed product'), 
                html.Div('working with a wide range of gamma scintillation detectors and geiger counters.'), 

                html.H4('GS-PRO-V5 Spectrometer (BYO detector)'),
                html.A('Order the GS-PRO-V5 Spectrometer here', href='https://www.gammaspectacular.com/blue/gamma-spectroscopy/gamma-spectrometers/gs-pro-v5?tracking=641198710758a', target='_blank'),
                
                html.H4('GSB-1515-NAI Complete spectrometry kit with 1.5 x 1.5" NaI(Tl) detector'),
                html.A('Order the GSB-1515-NAI Complete spectrometry kit', href='https://www.gammaspectacular.com/blue/gamma-spectroscopy/gamma-spectrometry-systems/GSB-1515-NAI?tracking=641198710758a', target='_blank'),
                
                html.H4('GSB-2020-NAI Complete spectrometry kit with 2.0 x 2.0" NaI(Tl) detector'),
                html.A('Order the GSB-1515-NAI Complete spectrometry kit', href='https://www.gammaspectacular.com/blue/gamma-spectroscopy/gamma-spectrometry-systems/GSB-2020-NAI?tracking=641198710758a', target='_blank'),
                html.Br(),
                html.Hr(),
                html.Br(),
                html.Div('This program is Free open source software for the benefit of amateur and professional scientists. I welcome all suggestions and contributions that will make the program better.'), 
                html.Br(),
                html.Div('Steven Sesselmann'),
                html.Div('More information can be found at:'),
                html.Div(html.A('www.gammaspectacular.com', href='https://www.gammaspectacular.com', target='_blank' )),

                html.Div(id='add', children=[html.Img(src='https://www.gammaspectacular.com/steven/impulse/GSB-1515-KIT.png')])
            ])
        ])
    ])

    return html_tab6

@app.callback(Output('exit-button', 'children'),
              [Input('exit-button', 'n_clicks')])
def shutdown_server(n_clicks):
    if n_clicks is not None:
        fn.shutdown()
        logger.info('Port closed by user\n')
        return 'Port Closed'
    else:
        return 'Click to Exit'

@app.callback(Output('theme_output', 'children'),
              [Input('theme', 'value')])
def theme_change(value):
    if value is None:
        raise PreventUpdate

    with global_vars.write_lock:
        global_vars.theme = value
        fn.save_settings_to_json()
        logger.info('Settings saved from tab6\n')

    logger.info('User clicked Exit\n')
    return 'Restart to see new theme'

@app.callback(Output('export_histogram_output', 'children'),
              [Input('export_histogram', 'value')])
def export_histogram(filename):
    if filename is None:
        raise PreventUpdate
    fn.export_csv(filename)
    return f'{filename} exported as csv to ~/Downloads'
