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
from server import app, version
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
        theme  = global_vars.theme
        device = global_vars.device

    if device < 100:        # Sound card devices
        serial = 'none'
        audio = 'block'

    if device >= 100:
        serial = 'block'
        audio = 'none'     

    html_tab6 = html.Div(id='tab6', children=[
        html.Div(id='exit', children=[
            html.Button(id='exit-button', className='action_button', children=''),
            html.Div(dcc.Dropdown(
                id="theme",
                className='dropdown',
                options=[
                    {"label": "Light theme"   , "value": "light-theme"},
                    {"label": "Dark theme"   , "value": "dark-theme"},

                    # {"label": "Plasma"      , "value": "plasma"},
                    # {"label": "Orange"      , "value": "orange"},
                    # {"label": "Pink"        , "value": "pink"},
                    # {"label": "Sunburst"    , "value": "sunburst"},
                    # {"label": "Potassium"   , "value": "potassium"},
                    # {"label": "Under Water" , "value": "underwater"},
                    # {"label": "Milky Way"   , "value": "milkyway"},
                ],
                value=theme,  # pre-selected option
                clearable=False,
            )),
            html.Div(id='theme_output', children=' '),
            
            ]),

        html.Div(id='tab6_text_div', children=[
            html.Hr(),
            html.Div(id='manual', children=[
                html.H1(f'Impulse {version} Manual (Serial Devices)', style={'display': serial}),
                html.H1(f'Impulse {version} Manual (Audio Devices)', style={'display': audio}),

                html.P('Thank you for downloading and installing Impulse MCA, this open source software is written in Python with the intention that users may modify and adapt it to their own experiments.'),
                html.P('In the following text I shall describe how the software works and what each setting parameter does.'),
                
                html.H4('Using a Sound Card as an ADC', style={'display': audio}),
                html.P('Gamma radiation detectors with photomultiplier tubes PMTs, output pulses in the form of an analogue voltage. Typically the pulses are on the order of 4 µs. which is too fast for sampling by common sound cards, but by amplifying and passing the signal through a low pass filter the pulse can be stretched to 100 µs. and then it can be sampled by an audio codec. ', style={'display': audio}),
                html.P('Computer sound cards operate on an AC voltage of around +- 1V and are not compatible with old school NIM equipment unless the signal is attenuated down to the correct range.', style={'display': audio}),

                html.H4('This is the Serial Devices Manual', style={'display': serial}),
                html.P('These serial devices have the MCA and other functionality built into the hardware and take commands from the PC to change parameters. Impulse software controls the device by sending commands in the correct format to the device. Simply connect the device via the USB port and refresh your browser, then select the device from the dropdown menu on the second tab.', style={'display': serial}),
                html.P('After selecting a device from the pulldown menu, refresh the page, only fields specific to your device will show, this includes paragraphs on this page. If you are seing the wrong manual, go back to the device selection tab and select the correct device.'),

                html.H2('MY DETAILS tab'),
                html.P('This tab gives you control over your personal details and your published spectra. Your details are saved in json format in the \'~/impulse_data_2.0\' folder on your PC or Mac, and when you apply for an API an account is created for you on the gammaspectacular.com web server which mirrors the data on the client.'),
                html.P('Once you click the \'Request API\' button the server will respond by sending you an email with your personal API key, copy and paste the key into the api_key field.'),
                html.P('Only spectra you choose to publish will appear on the right-hand panel. By clicking the x in the last column you can delete a previously uploaded spectrum. This could be handy if you want to replace an old spectrum with a better one.'), 

                html.H2('IMPULSE tab'),

                html.H4('Select Device'),
                html.P('Your computer may have several devices connected, so we need to instruct the program which input to use, so just select the correct input device from the pulldown menu. Note, you will need to refresh the page after selecting device.'),
                
                html.H4('Command Entry', style={'display':serial}),
                html.P('Changing the settings on GS-MAX serial devices requires certain commands to be sent to the processor, these commands can be sent using the command input field. Note some commands are deliberately blocked for sdafety reasons.', style={'display':serial}),
                html.P('If you need to send critical calibration to your device, please contact the manufacturer.', style={'display':serial}),
                html.P('• Change voltage -U0 to -U255', style={'display':serial}),
                html.P('• Clicking submit on a blank field refreshes device data', style={'display':serial}),
                html.P('• Please refer to device manual for other commands', style={'display':serial}),
                
                html.H4('Max-Pulse-shape', style={'display':serial}),
                html.P("""
                    If you have purchased a GS-MAX with integral crystal you can ignore this section
                    however if you have a general purpose spectrometer like the GS-MAX-8000 which
                    will be used with different types of crystals, you may need to change the pulse 
                    shape settings. The GS-MAX-8000 factory default is for common NaI(Tl). 
                    Changing the pulse settings is done from tab1, after connecting to your serial device 
                    click on "Start Max pulse", watch as the pulses appear on the screen, then count the
                    number of samples (dots) to and including the peak (ignoring the first dot). For example 0, 1, 2, 3, 4, "5", this 
                    represents the number of rising samples, then count the number of samples in the tail of the pulse,
                    1,2,3,4,5,6,7,"8", this is the number of falling samples.
                    If this differs from your current device settings, you should send the following command to the device 
                    using the command input. "-ris 5" and "-fall 8". Your devise -will now correctly read the pulse height from your detector.
                    """, style={'display':serial}),

                html.Img(src='assets/max-shape.png',style={'display':serial, 'width':'50%', 'height':'auto'}),



                html.H4('Sample Rate', style={'display': audio}),
                html.P('Analogue to digital audio sampling involves taking a voltage reading of the analogue signal multiple times a second, the faster the sampling rate the more accurately we can reconstruct the signal. Most modern computers can handle audio sampling rates up to 384 kHz. Faster sampling will generally produce a better spectrum, but it also requires a longer pulse which limits the pulse acquisition rate. If your objective is to measure a high count rate you may want a shorter pulse and a lower sample rate. ', style={'display': audio}),
                
                html.H4('Buffer Size', style={'display': audio}),
                html.P('Audio streaming is continuous, but computers need to process information in batches, we refer to the batch as a buffer. Select a buffer size proportional to your sample rate, i.e. higher sample rate larger buffer size.', style={'display': audio}),
                
                html.H4('Pulses to Sample', style={'display': audio}),
                html.P('Audio sampling uses the shape method for filtering out pulse pile up (PPU), this method involves comparing each pulse to the mean average pulse, so this setting determines how many pulses to sample for the mean. The more samples you collect the closer to the mean you get, but remember more samples take more time to process. Start with a low number and experiment to find the optimum compromise between time and quality. In order that we sample a good average we discriminate the very small and very large pulses, this default can be found in _settings.json with variable names  `shape_lld` and `shape_uld`. You can manually edit this setting if required.', style={'display': audio}),
                
                html.H4('Sample Length', style={'display': audio}),
                html.P('This setting sets the length of the sample in sample points. Sample length in combination with the sample rate determines how much time it takes to sample a pulse and consequently affects the dead time. Dead time is the amount of time the computer can not process pulses, simply put you can’t measure more than one pulse within (1 second/ sample rate) * (number of samples), let’s take the example (1s/384,000 Hz)*51 samples = 132 µs, now as our pulses are randomly spaced we have to allow more time between pulses, typically three times as much time. We can calculate the maximum count rate as follows: 1s / 132µs / 3 = 2525 cps ', style={'display': audio}),
                html.P('WARNING: Setting both sample length and sample rate to maximum may cause loss of counts as the computer may not be able to keep up.', style={'display': audio}),

                html.H4('Pulse Shape', style={'display': audio}),
                html.P('What you see in the pulse shape graph is the left and right channel normalized positive pulse shape. The program runs a quick function to check if the pulses are negative or positive and automatically flips the pulses if necessary, therefore we have no setting for negative pulses. ', style={'display': audio}),
                html.P('The pulse shape method is unique to sound card spectroscopy, so lets take a look at how this function works. First of all it reads the audio stream in the left channel, looking for a strings of n samples where the peak sample matches the peak position and falls within a given upper and lower threshold. If required, this threshold can be modified manually in settings.json. Once the required number of pulses have been found, the sample strings are summed and normalised to obtain a mean average. This is repeated for the right channel if the stereo switch is set to ON. Finally the pulse shape is plotted on the graph.', style={'display': audio}),
                html.P('The mean pulse shape is saved in your data directory as shape.csv and will be used to calculate a distortion factor for every pulse (difference between mean pulse and found pulse) which will be used to filter your pulses.', style={'display': audio}),
                html.P('Note: Pulse energy must be within a minimum and maximum range for this function to work, so if nothing happens when you click the button, your gain might be too low or too high. This function looks for pulses within a given pulse height window, only pulses bigger than `shape_lld` and smaller than `shape_uld` are used, these settings can be manually updated in settings.json if required.', style={'display': audio}),

                html.H4('Distortion Curve', style={'display': audio}),
                html.P('The distortion curve plot has no other function than to help you to visualize where the distortion in your sampling is occurring. When you click the [Get Distortion Curve] button the computer collects n unfiltered samples, compares each one with the mean and assigns a distortion factor to each pulse. The distortion factors are then ordered by size and plotted on a graph. The shape of this graph will help you determine how tight to set your distortion tolerance when recording your spectrum on tab2. Shape distortion may be caused by pulse overlap or large pulses that exceed the capacity of the electronic circuit.', style={'display': audio}),

                html.H2('2D HISTOGRAM tab'),
                html.H4('Spectrum File Name (all devices)'),
                html.P('This is exactly what it says, you can name your spectrum anything you like, it will automatically save in the user home directory ~/impulse_data_2.0/myspectrum.json , the JSON file format is NPESv2 and is backwards compatible with NPESv1. NOTE! It is not possible to rename a file via this input, changing the filename will start a new spectrum. To rename a file go to the impulse_data_2.0 directory in your home folder. '),
                html.Div(html.A('https://github.com/OpenGammaProject/NPES-JSON', href='https://github.com/OpenGammaProject/NPES-JSON', target='_blank')),
                html.P(' '),
                html.H4('Number of Bins', style={'display': audio}),
                html.P('This sets the number of bins you want in your histogram, fgor audio devices you gace choose any number of bins up to 32768, but for practical reasons there is usually no reason to go higher than 3000 bins.', style={'display': audio}),
                
                html.H4('Bin Size', style={'display': audio}),
                html.P('This sets the bin size or pitch of your spectrum. The maximum value a positive pulse can have is 32,768, so for 1000 bins you might choose a bin size of 32.76, this would give you the full range. Note: it is common for electronic circuits to suffer distortion towards the upper end of the dynamic range, therefore you may achieve better resolution by lowering the gain and using a smaller bin size.', style={'display': audio}),
                html.H4('Resolution', style={'display': serial}),
                html.P('Select the number of channels from the dropdown list, this function compresses the full 8192 channel spectrum by 2, 4, 8 or 16 times', style={'display': serial}),

                html.H4('Stop Condition - Max Counts, Max Seconds'),
                html.P('Max Counts and Max seconds need to be set before clicking START, as these two arguments are inputs to a while loop, changing these settings during a recording will have no effect. The spectrum will automatically stop when either condition has been met.'),
                html.P('Note: If either field has been set to zero the spectrum will not run'),

                html.H4('Lost Counts'),
                html.P('These are the number of counts outside the set threshold'),

                html.H4('cps'),
                html.P('Calculated counts per second (total counts/total seconds)'),

                html.H4('LLD Threshold', style={'display': audio}),
                html.P('This setting sets the Lower Limit Discriminator. As we do not want to count the tiny electronic ripple on the baseline it is important that we set a sensible limit below which to ignore any pulses. If this limit has been set too low, it will appear as a tall peak in the first couple of bins on the left-hand side of your spectrum', style={'display': audio}),
                
                html.H4('Shape Tolerance', style={'display': audio}),
                html.P('This setting is related to the mean shape sample and distortion curve on tab1, so run the distortion check first and determine what level of distortion you are prepared to accept. Note, the tighter your tolerance for distortion, the more pulses will be dropped as a result and your count rate will not be accurate. Note!! Distortion typically increases with pulse height, setting distortion too low may result in loss of data at the high end of your spectrum.', style={'display': audio}),
                
                html.H4('Comparison spectrum'),
                html.P('This is an automatically generated pulldown menu which gets the contents of your impulse_data_2 folder and the subfolder [impulse_files/i] containing all the isotope spectra. Select any spectrum to compare'),
                
                html.H4('Show Comparison spectrum'),
                html.P('This switch simply hides and shows the comparison spectrum'),
                
                html.H4('Subtract Comparison'),
                html.P('As the name suggests this switch subtracts the comparison spectrum, bin for bin, from the main spectrum and is intended for background subtraction.'),
                
                html.H4('Energy by bin'),
                html.P('This function enhances the peaks exponentially towards the right in the spectrum the function (counts)*(bin) = energy by bin'),
                
                html.H4('Export to csv'),
                html.P('This function saves the spectrum as a simple csv file in your Downloads folder, activate the calibration switch before downloading if required.'),

                html.H4('Show Log'),
                html.P('This switch changes the y axis to log scale, a common way to make the high energy peaks visible.'),
                
                html.H4('Play Sound Button'),
                html.P('This button generates a wav file from the gaussian correlation (sigma) from the current spectrum and plays an arpeggio where the x axis represents the frequency of a piano keyboard and the y axis represents volume. Just a fun function.'),

                html.H4('Publish Spectrum Button'),
                html.P('Once you have recorded and calibrated a beautiful spectrum, share it with the wider community of Impulse users. You must obtain and save your API code on the My Details tab for permission to share files.'),

                html.H4('Calibration'),
                html.P('All calibration settings are on the 2D histogram tab, in this version you can enter up to 5 calibration points (bin = energy), the program will accept any number of calibration points from 1 to 5. When there are less than 3 calibration points a linear function is applied, and above this it defaults to a polynomial function. These calibration settings are automatically used for the 3D spectrum on tab3. The calibration switch turns the calibration on or off.'),
                html.P('Note !! Your standard calibration points are saved to your local settings.json, new spectra start recording with these settings. This is convenient if you are using the same detector setup all the time.'),

                html.H4('Recalibrate button'),
                html.P('This button allows you to update the notes and calibration settings of an existing pre-recorded spectrum file, great for making small adjustments to your files'),

                html.H4('Suppress Last Bin', style={'display': serial}),
                html.P('This is a boolean switch, which only appears for serial devices. When switch is OFF any counts with pulse height higher than the last bin will accumulate in the last bin, setting this swich to ON soppresses the last bin.', style={'display': serial}),

                html.H4('Coincidence', style={'display': audio}),
                html.P('The coincidence function only works when there is a signal connected to the right channel audio input. The boolean switch needs to be activated on before the start button is pressed', style={'display': audio}),
                html.P('When running a coincidence spectrum the default primary detector should always be the left channel, and the secondary or trigger detector connected to the right channel', style={'display': audio}),        
                html.P('Pulses are considered coincident when the secondary peak occurs within +3 or -3 sample points, therefore a higher sample rate will achieve a tighter coincidence.', style={'display': audio}),        

                html.H4('Peak width'),
                html.P('Impulse has a built-in function which can find peaks and calculate the resolution. The slider adjusts the width of the peaks, allowing you to increase or reduce the number of peaks found. Setting the peak width to off turns of all flags.'),

                html.H4('Toggle flags'),
                html.P('This switch allows you to lookup [bin number and counts], [energy and counts] or [isotope and energy]. Isotopes libraries are stored in the data folder and can be selected from the pulldown menu. Note: Spectrum must be accurately calibrated for isotope flags to show.'),

                html.H4('Isotope Lists'),
                html.P('There are several isotope lists in your data folder, these are stored in json format and can be selected from the pulldown menu on tab2. Common and less common gamma emitting isotopes have been separated into two tables to prevent too many showing on the screeen. You can duplicate and create your own isotope lists in json format and place them in the tbl directory. These will automatically appear in the pulldown selection menu (after browser refresh).'),

                html.H4('Gaussian Correlation'),
                html.P('This function identifies peaks which are hard to see with the naked eye, it takes the normalized spectrum and calculates the dot product of the gaussian shape with a standard deviation dependent bin number, the slider adjusts sigma, which determines how many bins to average the gaussian function.'),

                html.H4('Spectrum Notes'),
                html.P('This is an input where you can update the notes field on a spectrum after it has been recorded. Function may not work before the file exists, I suggest notating the file after it has been recorded'),

                html.H2('3D HISTOGRAM tab'),
                html.P('This page functions much the same way as the regular 2D histogram, with the added time axis. You can control the time interval between each update. NOTE: Because this spectrum writes a lot of data to the browser it is advisable to keep the number of channels and time intervals to a minimum'), 

                html.H2('COUNT RATE tab'),
                html.P('This is a line chart showing the counts per second and is entirely driven by the settings on tab-2 and tab-3. The sum average (green line) can be adjusted with the slider or for fine adjustment click on the slider and use your left-right arrow keys to move the slider in steps of one second.'),
                html.P('To avoid latency the cps chart will only display the last hour by default, however, the entire recording can be viewed with the Show Complete Dataset switch'),
                
                html.H2('REPOSITORY tab'),
                html.P('The is is a common repository where spectra published by all Impulse users appear. All published spectra are saved in NPESv2 json format and can be opened in many popular programs. Please contribute your spectra and make more data available to the community. The search field is a convenient way to find what you are looking for so make sure you give your published spectra a good name.'),
                html.P('The published spectra are stored on the gammaspectacular.com server hosted by Webcentral in Australia'),

                html.Hr(),
                html.H1('Hardware'),

                html.P('This program will work with any sound card spectrometer, GS-MAX or ATOM-NANO serial devices. Soundcard spectrometry was invented in Australia by professor Marek Dolleiser' ),
                html.P('and the first hardware ever made was the Gammaspectacular GS-1100A back in 2010.' ),
                html.P('Since then there have been many improvements to the hardware and today we have a highly developed product'), 
                html.P('working with a wide range of gamma scintillation detectors and geiger counters.'), 
                html.Div(' '),
                html.H4('GS-PRO-V5 Spectrometer (BYO detector)'),
                html.A('Order the GS-PRO-V5 Spectrometer here', href='https://www.gammaspectacular.com/blue/gamma-spectroscopy/gamma-spectrometers/gs-pro-v5?tracking=641198710758a', target='_blank'),
                
                html.H4('GS-MAX-8000 Spectrometer (BYO detector)'),
                html.A('Order the GS-MAX Spectrometer here', href='https://www.gammaspectacular.com/blue/gamma-spectroscopy/gamma-spectrometers/gs-max-8000?tracking=641198710758a', target='_blank'),

                html.H4('GSB-1515-NAI Complete spectrometry kit with 1.5 x 1.5" NaI(Tl) detector'),
                html.A('Order the GSB-1515-NAI Complete spectrometry kit', href='https://www.gammaspectacular.com/blue/gamma-spectroscopy/gamma-spectrometry-systems/GSB-1515-NAI?tracking=641198710758a', target='_blank'),
                
                html.H4('GSB-2020-NAI Complete spectrometry kit with 2.0 x 2.0" NaI(Tl) detector'),
                html.A('Order the GSB-1515-NAI Complete spectrometry kit', href='https://www.gammaspectacular.com/blue/gamma-spectroscopy/gamma-spectrometry-systems/GSB-2020-NAI?tracking=641198710758a', target='_blank'),
                html.Br(),
                html.Hr(),
                html.Br(),
                html.P('This program is Free open source software for the benefit of amateur and professional scientists. I welcome all suggestions and contributions that will make the program better.'), 
                html.Br(),
                html.P('Steven Sesselmann'),
                html.P('More information can be found at:'),
                html.Div(html.A('www.gammaspectacular.com', href='https://www.gammaspectacular.com', target='_blank' )),

                html.Div(id='add', children=[html.Img(src='assets/GSB-1515-KIT.png')])
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

@app.callback(Output('theme_output' , 'children'),
              [Input('theme'        , 'value')])
def theme_change(theme):
    if theme is None:
        raise PreventUpdate

    with global_vars.write_lock:
        global_vars.theme = theme
        fn.save_settings_to_json()
    
    logger.info(f'Theme changed to {theme}')

    return 'Restart to see new theme'

