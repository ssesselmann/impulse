# This page is the main pulse catcher file, it 
# collects, normalises and filters the pulses 
# ultimately saving the histogram file to JSON.
import pyaudio
import wave
import math
import time
import functions as fn
import sqlite3 as sql
import datetime
from collections import defaultdict
import csv

data 			= None
left_channel 	= None
device_list 		= fn.get_device_list()
path 			= None
plot 			= {}

# Function to catch pulses and output time, pulkse height and distortion
def pulsecatcher():

	# Start timer
	timer_start		= time.time()
	t0				= datetime.datetime.now()
	tb				= time.time()
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
	sample_length	= settings[11]

	coeff_1			= settings[18]
	coeff_2			= settings[19]
	coeff_3			= settings[20]
	flip 			= settings[22]

	# Create an array of ewmpty bins
	start = 0
	stop = bins * bin_size
	histogram = [0] * bins

	audio_format = pyaudio.paInt16
	device_channels = fn.get_max_input_channels(device_list, device)

	# Loads pulse shape from csv
	shapestring = fn.load_shape()

	# Converts string to float
	shape = [int(x) for x in shapestring]

	samples 	= []
	pulses 		= []
	left_data 	= []
	p = pyaudio.PyAudio()
	n = 0
	cps = 0

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
		t = time.time()
		# Read the audio data from the stream
		data = stream.read(chunk_size, exception_on_overflow=False)
		values = list(wave.struct.unpack("%dh" % (chunk_size * device_channels), data))
		# Extract every other element (left channel)
		left_channel = values[::2]
		#global plot_data
		for i, sample in enumerate(left_channel[:-sample_length]):
			samples = left_channel[i:i+sample_length]  # Get the first 51 samples
			# Flip inverts all samples if detector pulses are positive
			samples = [flip * x for x in samples]
			if samples[25] >= max(samples) and (max(samples)-min(samples)) > threshold and samples[25] < 32768:
				# Function normalises sample to zero
				normalised = fn.normalise_pulse(samples)
				# Converts normalised to integers
				normalised_int = [int(x + 0.5) for x in normalised]
				# Calculates distortion
				distortion = fn.distortion(normalised_int, shape)
				# Function calculates pulse height
				height = fn.pulse_height(normalised_int)
				# Filter
				if distortion < tolerance:
					# Sort pulse into correct bin
					bin_index = int(height/bin_size)
					# Add 1 to bin
					if bin_index < bins:
						histogram[bin_index] += 1
						n   += 1	
						cps += 1
						if t - timer_start >= 1:
							timer_start = t
							settings 		= fn.load_settings()
							coeff_1			= settings[18]
							coeff_2			= settings[19]
							coeff_3			= settings[20]
							max_counts      = settings[9]
							# Time capture
							t1 = datetime.datetime.now()
							te = time.time()
							elapsed = int(te - tb)
							fn.write_histogram_json(t0, t1, bins, n, elapsed, name, histogram, coeff_1, coeff_2, coeff_3)
							fn.write_cps_json(name,cps)
							cps = 0
							


					