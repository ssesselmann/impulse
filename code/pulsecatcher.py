import pyaudio
import wave
import math
import functions as mps
import time
from collections import defaultdict
import csv

# Start timer
start = time.perf_counter()



#function creates bins
start = 0
stop = 33000
bin_size = 20
bins = mps.create_bins(start, stop, bin_size)

bin_counts = defaultdict(int)

data = None
left_channel = None
 
plot = {}

# Function to catch pulses and output time, pulkse height and distortion
def pulsecatcher(left_channel, audio_format, device_channels, rate, device_index, chunk, shape, threshold, tolerance):
	
	samples =[]
	pulses = []
	p = pyaudio.PyAudio()
	left_data = []
	path = "/Sites/github/gs-plot/data/plot.csv"

	# Open the selected audio input device
	stream = p.open(
	    format=audio_format,
	    channels=device_channels,
	    rate=rate,
	    input=True,
	    output=False,
	    input_device_index=device_index,
	    frames_per_buffer=chunk)

	while True:
		# Read the audio data from the stream
	    data = stream.read(chunk, exception_on_overflow=True)
	    values = list(wave.struct.unpack("%dh" % (chunk * device_channels), data))
	    # Extract every other element (left channel)
	    left_channel = values[::2]
	    global plot_data

	    for i in range(len(left_channel) - 51):
	        samples = left_channel[i:i+51]  # Get the first 51 samples
	      
	        if samples[25] >= max(samples) and (max(samples)-min(samples)) > threshold and samples[25] < 32768:
	        	# Time capture
	        	end = time.perf_counter()
	        	elapsed = int((end - start) * 1000000)
	        	# Function normalises sample to zero
	        	normalised = mps.normalise_pulse(samples)
	        	# Function calculates pulse distortion
	        	distortion = mps.distortion(normalised, shape)
	        	# Function calculates pulse height
	        	height = mps.pulse_height(normalised)
	        	if distortion < tolerance:
		        	# prints data to console
		        	#print(elapsed,",",height,",",distortion)
	        		#print(height,"\n")

	        		# Drop pulse height into bins
	        		plot_data = mps.update_bin(height, bins, bin_counts)
	        		plot = dict(plot_data)
        			#print(plot,"\n")
        			fn.write_to_csv('Sites/github/gs_plot/data/shape.csv', plot)
        			#time.sleep(100)
        				

        			


    