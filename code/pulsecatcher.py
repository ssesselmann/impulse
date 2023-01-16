import pyaudio
import wave
import math
import functions as fn
import time
from collections import defaultdict
import csv

# Start timer
start = time.perf_counter()



#function creates bins
start = 0
stop = 33000
bin_size = 50
bins = fn.create_bins(start, stop, bin_size)
bin_counts = defaultdict(int)
data = None
left_channel = None
devices = fn.get_device_list()
 
plot = {}

# Function to catch pulses and output time, pulkse height and distortion
def pulsecatcher():


	settings = fn.load_settings()
	values = [row[1] for row in settings[1:]]
	input_index     = int(values[0])
	input_rate      = int(values[1])
	input_chunk     = int(values[2])
	input_lld       = int(values[3])
	input_tolerance = int(values[4])
	input_path      = values[5]

	audio_format = pyaudio.paInt16
	device_channels = devices[input_index]['maxInputChannels']

	shapestring = fn.load_shape(input_path)
	# Convert string to float
	shape = [float(x) for x in shapestring]


	samples 	=[]
	pulses 		= []
	left_data 	= []
	p = pyaudio.PyAudio()

	path = f'{input_path}plot.csv'

	# Open the selected audio input device
	stream = p.open(
	    format=audio_format,
	    channels=device_channels,
	    rate=input_rate,
	    input=True,
	    output=False,
	    input_device_index=input_index,
	    frames_per_buffer=input_chunk)

	while True:
		# Read the audio data from the stream
	    data = stream.read(input_chunk, exception_on_overflow=True)

	    values = list(wave.struct.unpack("%dh" % (input_chunk * device_channels), data))
	    # Extract every other element (left channel)
	    left_channel = values[::2]

	    #global plot_data

	    for i in range(len(left_channel) - 51):
	        samples = left_channel[i:i+51]  # Get the first 51 samples
	      
	        if samples[25] >= max(samples) and (max(samples)-min(samples)) > input_lld and samples[25] < 32768:
	        	# Time capture
	        	end = time.perf_counter()
	        	elapsed = int((end - start) * 1000000)
	        	# Function normalises sample to zero
	        	normalised = fn.normalise_pulse(samples)
	        	# Function calculates pulse distortion

	        	# Converts normalised to integers
	        	normalised_int = [int(round(x)) for x in normalised]

	        	# Calculates distortion
	        	distortion = fn.distortion(normalised_int, shape)

	        	# Function calculates pulse height
	        	height = fn.pulse_height(normalised_int)
	        	if distortion < input_tolerance:
		        	# prints data to console
		        	#print(elapsed,",",height,",",distortion)
	        		#print(height,"\n")

	        		# Drop pulse height into bins
	        		plot_data = fn.update_bin(height, bins, bin_counts)
	        		plot = dict(plot_data)
        			#print(plot,"\n")
        			fn.write_to_csv('Sites/github/gs_plot/data/plot.csv', plot)
        			
        				

        			


    