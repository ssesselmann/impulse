import pyaudio
import wave
import math
import functions as fn
import pandas as pd
import time
from collections import defaultdict
import csv

# Start timer
t0 = time.perf_counter()

#function creates bins
start = 0
stop = 33000
bin_size = 20
bins = fn.create_bins(start, stop, bin_size)
bin_counts = defaultdict(int)
data = None
left_channel = None
 
plot = {}
pulses = {}
sample_list = []

# Function to catch pulses and output time, pulkse height and distortion
def shapecatcher():
	count = 0
	samples 	= []
	pulses 		= []
	left_channel= []
	summed = []
	p = pyaudio.PyAudio()

	audio_format = pyaudio.paInt16

	settings = fn.load_settings()

	values = [row[1] for row in settings[1:]]

	input_index     = int(values[0])
	input_rate      = int(values[1])
	input_chunk     = int(values[2])
	input_lld       = int(values[3])
	input_tolerance = int(values[4])
	input_path      = values[5]

	devices = fn.get_device_list()

	#print(devices[input_index])

	device_channels = devices[input_index]['maxInputChannels']
	
	#print(input_index, input_rate, input_chunk, input_lld, input_tolerance, input_path, device_channels)

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
		data = stream.read(input_chunk, exception_on_overflow=False)
		values = list(wave.struct.unpack("%dh" % (input_chunk * device_channels), data))

	    # Extract every other element (left channel)
		left_channel = values[::2]
		
		#print(left_channel)
		for i in range(len(left_channel) - 51):
			samples = left_channel[i:i+51]  # Get the first 51 samples
			# Discriminate samples LLD and ULD
			if samples[25] >= max(samples) and (max(samples)-min(samples)) > 50 and samples[25] < 30000:
				# Gather a list of samples 
				sample_list.append(samples)
				# Counter
				count += 1
				# Stop[ afer n samples]
				if count > 100:
					# Zip sum all lists
					samples_sum = [sum(x)/100 for x in zip(*sample_list)]
					# Normalise summed list
					shape = fn.normalise_pulse(samples_sum)
					# Format and save to csv file
					df = pd.DataFrame(shape)
					df.to_csv("Sites/github/gs_plot/data/shape.csv", index='Shape', header=1)
					return shape  	



    