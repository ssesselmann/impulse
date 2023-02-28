
import dash
import dash_daq as daq
import sys
import functions as fn
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from server import app
from flask import request

def show_tab4():

    html_tab4 = html.Div([ 
        html.H1(children='Thanks for using impulse, see you back soon!'),
        html.Button(id='exit-button', children=''),
        html.Div(children='Always exit the program by clicking the red button, this prevents processes running after browser window is closed.'),
        
        


        html.Div(id='tab4_text_div', children=[
            html.Hr(),
            html.Div(id='manual', children=[
                html.H2('Impulse Manual'),
                html.P('Thank you for downloading and installing Impulse gamma spectrometry, this open source software is written in Python with the intention that users may modify and adapt it to their own experiments.'),
                html.P('In the following text I shall describe how the software works and what each setting parameter does.'),
                html.H4('Using a Sound Card as an ADC'),
                html.P('Gamma radiation detectors with photomultipler tubes PMTs, output pulses in the form of an analogue voltage. Typically the pulses are on the order of 4 µs. which is too fast for sampling by commercial sound cards, but by aplifying and passing the signal through a low pass filter the pulse can be stretched to 100 µs. and then it can be sampled by an audio codec. '),
                html.P('Computer sound cards operate on an AC voltage of around +- 1V and are not compatible with old school NIM equipment unless the signal is attenuated down to the correct range.'),
                html.H2('Tab1 - Settings and Control'),
                html.H4('Enter Device Index'),
                html.P('Your computer may have several audio devices connected, so we need to instruct the program which audio input device to use, so click on the button called [Get Device Table] and identify your input device, then set your input devise to the index number in the first column.'),
                html.H4('Sample Rate'),
                html.P('Analogue to digital audio sampling involves taking a voltage reading of the analogue signal multiple times a second, the faster the sampling rate the more accurately we can reconstruct the signal. Most modern computers can handle audio sampling rates up to 384 kHz. Faster sampling will generally produce a better spectrum, but it also requires a longer pulse which limits the pulse acquisistion rate. If your objective is to measure a high count rate you may want a shorter pulse with a lower sample rate. '),
                html.H4('Buffer Size'),
                html.P('Audio streaming is continuous, but computers need to process the information in batches, we refer to the batch sise as a buffer. The default setting is 1024 samples which is the number of samples the computer reads into memory before looking for pulses. This setting may not be required in the future.'),
                html.H4('Pulses to Sample'),
                html.P('Impulse uses the shape method for filtering out PPU, this methos involves comparing each pulse to the mean average pulse, so this setting determines how many pulses to use for calculating the mean. The more samples you collect the closer to the mean you get, but remember more samples take more time to process. Start with a low number and experiment to find the optimum compromise between time and quality'),
                html.H4('Sample Length'),
                html.P('This setting sets the length of the sample in sample points. This setting in combination with the sample rate determines how much time it takes to sample one pulse and consequently affects the dead time. Dead time is the amount of time a computer can not process pulses, simply put you cant measure more than one pulse within (1 second/ sample rate) * (number of samples), lets take the example (1s/384,000 Hz)*51 samples = 132 µs, now as our pulses are randomly spaced we have to allow more time between pulses, typically three times as much time. We can calculate the maximum count rate as follows: 1s/132 µs/3 = 2525 cps '),
                html.H4('Distortion Curve'),
                html.P('The distortion curve plot has no other function than to help you to visualise where the distortion in your sampling is occurring. When you click the [Get Distortion Curve] button the computer collects n unfiltered samples, compares each one with the mean and assigns a distortion factor to each pulse. The distortion factors are then ordered by size and plotted on a graph. The shape of this graph will help you determine how tight to set your distortion tolerance when recording your spectrum on tab2. Shape distortion may be caused by pulse overlap or large pulses that exceed the capacity of the electronic circuit.'),


                html.H2('Tab2 - Pulse Height Histogram'),
                html.H4('Spectrum File Name'),
                html.P('This is exactly what it says, you can name your spectrum anything you like, it will automatically save in ~/impulse/code/data/myspectrum.json , the JSON file format is NPESv1 and is compatible with  '),
                html.Div(dcc.Link('https://github.com/OpenGammaProject/NPES-JSON', 'https://github.com/OpenGammaProject/NPES-JSON')),
                html.H4('Number of Bins & Bin Size'),
                html.P('These setting determine the number of bins you want in your histogram and the size of each bin. The default settings are 1000 bins and 30 arbitrary units per bin. These numbers have been chosen because it gives you a spectrum range of 3000 which is convenient for most gamma spectra as we are investigating 0 to 3000 keV.'),
                html.H4('Stop after n Counts'),
                html.P('As the title says, this setting tells the program when to stop. You can stop the program from executing at any time by entering zero into this field. remember the program will not start if you have a zero in this field.'),
                html.H4('LLD Threshold'),
                html.P('This setting sets the Lower Limit Discriminator. As we do not want to count the minute electronic ripple on the basline it is important that we set a sensible limit below which to ignore any pulses. If this limit has been set too low, it will app[ear as a tall peak in the first coule of bins on the left hand side of your spectrum'),
                html.H4('Shape Tolerance'),
                html.P('This setting is related to the mean shape sample and distortion curve on tab1, so run the distortion check first and determine what level of distortion you are prepared to accept. Note, the tighter your tolerance for distortion, the more pulses will be dropped as a result and your count rate will not be accurate. '),
                html.H4('Overlay'),
                html.P('This field is for the name of any json spectrum file in the data folder you wish to use as a comparison or overlay specterum. A common use would be to first record a background spectrum and then use that spectrum as a comparison for your source spectrum. You can also access a large library with 480 isotope gamma lines by entering [ i/Cs137 ] or any other isotope in the same format (look into ~impulse/code/data/i/ for the whole list). '),
                html.H4('Show Comparison'),
                html.P('This switch simpy hides and shows the comparison spectrum'),
                html.H4('Subtract Comparison'),
                html.P('As the name suggests this switch subracts the comparison spectrum from the main spectrum and is intended for background subtraction.'),
                html.H4('Energy per bin'),
                html.P('This function enhances the peaks exponentially towards the right in the spectrum the function is simply (counts)*(bin) = '),
                html.H4('Show Log'),
                html.P('This switch changes the y axis to log scale, a common way to make the high energy peaks visible.'),
                html.H4('Calibration'),
                html.P('The calibration switch turns calibration on or off. Energy calibration is done by a second order polynomial fit. There are six fields where the user may enter three bins with three corresponding energies. By choosing a linear relationship between bins and energies you can achieve a linear spectrum and by choosing non linear relationships you can correct for detectors that are non linear. The typical use case would be to enter the bins and known ebnergies from three widely spread gamma peaks.  '),
                html.H4('Peakfinder'),
                html.P('Impulse has a built in function which can find peaks and calculate the resolution. The slider adjusts the width tolerance of the found peaks, allowing you to increase or reduce the number of peaks found. There is a limit to how close together it can identify two peaks, this is due to the width of the notation only. '),
                html.H2('Tab3 - Count Rate Histogram'),
                html.P('This is a graphical representation of the count rate over time and is entirely driven by the settings on the previous tab1 and tab2. No options or settings on this page yet.'),
                html.Hr(),
                html.H1('The GS-PRO-V5 Spectrometer'),
                html.Div('This program operates with a sound card spectrometer, this technology was invented in Australia by professor Marek Dolleiser' ),
                html.Div('and the first hardware ever made was the Gammaspectacular GS-1100A back in 2010.' ),
                html.Div('Since then there has been many improvements to the hardware and today we have a highly developed product'), 
                html.Div('working with a wide range of gamma scintillation detectors and geiger counters.'), 
                html.Br(),
                html.Div('More information can be found at:'),
                html.Div(dcc.Link('https://www.gammaspectacular.com', 'https://www.gammaspectacular.com' )),
                html.Br(),
                html.Div('This software is Free open source software and everyone is invoted to contribute.'), 
                html.Br(),
                html.Div('Steven Sesselmann'),
                html.Div(id='add', children=[html.Img(src='https://www.gammaspectacular.com/steven/impulse/gs_pro_v5.png')])
                ])]

            )]),

    return html_tab4

@app.callback(Output('exit-button', 'children'),
              [Input('exit-button', 'n_clicks')])

def shutdown_server(n_clicks):
    if n_clicks is not None:
        fn.shutdown()
        return 'Port Closed'
    else:
        return 'Click to Exit'