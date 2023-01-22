import pyaudio
import wave
import math
import time
import functions as fn
import sqlite3 as sql
import datetime
from collections import defaultdict
import csv

# Start timer
t0				= datetime.datetime.now()
tb				= time.time()
data 			= None
left_channel 	= None
devices 		= fn.get_device_list()
path 			= None
plot 			= {}


# Function to catch pulses and output time, pulkse height and distortion
def pulsecatcher(mode):

	settings 		= fn.load_settings()

	name            = settings[1]
	device          = settings[2]             
	sample_rate     = settings[3]
	chunk_size      = settings[4]                        
	threshold       = settings[5]
	tolerance       = settings[6]
	bins            = settings[7]
	bin_size        = settings[8]
	max_counts      = settings[9]
	energy_per_bin 	= settings[10]

	# Create an array of ewmpty bins
	start = 0
	stop = bins * bin_size

	histogram = [0] * bins


	# bin_array = fn.create_bin_array(start, stop, bin_size)
	# print('bin_array',bin_array)
	# bin_counts = defaultdict(int)
	# print('bin_counts', bin_counts)
	audio_format = pyaudio.paInt16
	device_channels = devices[device]['maxInputChannels']

	shapestring = fn.load_shape()
	# Convert string to float
	shape = [int(x) for x in shapestring]

	samples 	= []
	pulses 		= []
	left_data 	= []
	p = pyaudio.PyAudio()
	n =0

	# Open the selected audio input device
	stream = p.open(
		format=audio_format,
		channels=device_channels,
		rate=sample_rate,
		input=True,
		output=False,
		input_device_index=device,
		frames_per_buffer=chunk_size)

	while n <= max_counts:
		# Read the audio data from the stream
		data = stream.read(chunk_size, exception_on_overflow=False)
		values = list(wave.struct.unpack("%dh" % (chunk_size * device_channels), data))
		# Extract every other element (left channel)
		left_channel = values[::2]

		#global plot_data
		for i in range(len(left_channel) - 51):
			samples = left_channel[i:i+51]  # Get the first 51 samples
		  
			if samples[25] >= max(samples) and (max(samples)-min(samples)) > threshold and samples[25] < 32768:

				# Time capture
				t1 = datetime.datetime.now()
				te = time.time()
				elapsed = int(te - tb)

				# Function normalises sample to zero
				normalised = fn.normalise_pulse(samples)
				# Function calculates pulse distortion

				# Converts normalised to integers
				normalised_int = [int(round(x)) for x in normalised]

				# Calculates distortion
				distortion = fn.distortion(normalised_int, shape)

				# Function calculates pulse height
				height = fn.pulse_height(normalised_int)
				
				if distortion < tolerance:
					
					bin_index = int(height/bin_size)

					if bin_index < bins:

						histogram[bin_index] += 1

						n += 1

						if n % 10 == 0:

							fn.write_histogram_json(t0, t1, bins, n, elapsed, name, histogram)

					


					