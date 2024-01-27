# distortionchecker.py
# This page is the main pulse catcher file, it 
# collects, normalises and filters the pulses 
# ultimately saving the histogram file to JSON.
import pyaudio
import wave
import math
import functions as fn
import sqlite3 as sql
import csv

from collections import defaultdict

data 			= None
left_channel 	= None
device_list 	= fn.get_device_list()
path 			= None
plot 			= {}

# Function to catch pulses and output time, pulkse height and distortion
def distortion_finder():

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
	shapecatches	= settings[10]

	coeff_1			= settings[18]
	coeff_2			= settings[19]
	coeff_3			= settings[20]
	flip 			= settings[22]
	sample_length	= settings[11]
	peakshift		= settings[28]

	# Create an array of ewmpty bins
	start = 0
	stop = bins * bin_size
	histogram = [0] * bins

	peak = int((sample_length-1)/2) + peakshift

	audio_format = pyaudio.paInt16
	device_channels = fn.get_max_input_channels(device)

	# Loads pulse shape from csv
	shapestring = fn.load_shape()

	# Converts string to float
	shape = [int(x) for x in shapestring]

	n = 0
	p = pyaudio.PyAudio()

	samples 		= []
	left_data 		= []
	distortion_list = []

	# Open the selected audio input device
	stream = p.open(
		format=audio_format,
		channels=device_channels,
		rate=sample_rate,
		input=True,
		output=False,
		input_device_index=device,
		frames_per_buffer=chunk_size)

	while True:
		# Read the audio data from the stream
		data = stream.read(chunk_size, exception_on_overflow=False)
		values = list(wave.struct.unpack("%dh" % (chunk_size * device_channels), data))
		# Extract every other element (left channel)
		left_channel = values[::2]
		#global plot_data
		for i in range(len(left_channel) - sample_length):
			samples = left_channel[i:i+sample_length]  # Get the first 51 samples
			# Flip inverts all samples if detector pulses are positive
			samples = [flip * x for x in samples]
			if samples[peak] >= max(samples) and (max(samples)-min(samples)) > threshold and samples[peak] < 32768:
				# Function normalises sample to zero
				normalised = fn.normalise_pulse(samples)
				# Converts normalised to integers
				normalised_int = [int(round(x)) for x in normalised]
				# Calculates distortion
				distortion = fn.distortion(normalised_int, shape)
				# Append distortion
				distortion_list.append(distortion)
				distortion_list.sort()
				n +=1

		if n >= shapecatches:
			p.terminate()
			break

	return distortion_list	
					
