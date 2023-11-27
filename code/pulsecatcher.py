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
path 			= None
device_list 	= fn.get_device_list()
plot 			= {}

global_cps      = 0
global_counts	= 0

# Function reads audio stream and finds pulses then outputs time, pulse height and distortion
def pulsecatcher(mode):

	# Start timer
	t0				= datetime.datetime.now()
	tb				= time.time()	#time beginning
	tla = 0

	# Get the following from settings
	settings 		= fn.load_settings()
	filename        = settings[1]
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
	max_seconds     = settings[26]
	t_interval      = settings[27]

	peak 			= fn.target_peak_position(sample_length)
	condition       = True

	# Create an array of empty bins
	start 			= 0
	stop 			= bins * bin_size
	histogram 		= [0] * bins
	histogram_3d 	= [0] * bins
	audio_format 	= pyaudio.paInt16
	device_channels = fn.get_max_input_channels(device)

	# Loads pulse shape from csv
	shapestring = fn.load_shape()

	# Converts string to float
	shape = [int(x) for x in shapestring]
	samples 	= []
	pulses 		= []
	left_data 	= []

	p = pyaudio.PyAudio()

	global global_cps 

	global_cps = 0

	global global_counts 

	global_counts = 0

	elapsed = 0

	# Open the selected audio input device
	stream = p.open(
		format=audio_format,
		channels=device_channels,
		rate=sample_rate,
		input=True,
		output=False,
		input_device_index=device,
		frames_per_buffer=chunk_size)

	while condition and (global_counts < max_counts and elapsed <= max_seconds):
		# Read one chunk of audio data from stream into memory. 
		data = stream.read(chunk_size, exception_on_overflow=False)
		# Convert hex values into a list of decimal values
		values = list(wave.struct.unpack("%dh" % (chunk_size * device_channels), data))
		# Extract every other element (left channel)
		left_channel = values[::2]
		# Flip inverts all samples if detector pulses are positive
		if flip != 1:
			left_channel = [flip * x for x in left_channel]
		# Read through the list of left channel values and find pulse peaks
		for i, sample in enumerate(left_channel[:-sample_length]):
			# iterate through one sample lenghth at the time in quick succession, ta-ta-ta-ta-ta...
			samples = left_channel[i:i+sample_length]
			# Function calculates pulse height of all samples 
			height = fn.pulse_height(samples)
			# Filter out noise
			if samples[peak] == max(samples) and height > threshold and samples[peak] < 32768:
				# Function normalises sample to zero and converts to integer
				normalised = fn.normalise_pulse(samples)
				# Compares pulse to sample and calculates distortion number
				distortion = fn.distortion(normalised, shape)
				# Filters out distorted pulses
				if distortion < tolerance:
					# Sorts pulse into correct bin
					bin_index = int(height/bin_size)
					# Adds 1 to the correct bin
					if bin_index < bins:
						histogram[bin_index] 	+= 1
						histogram_3d[bin_index] += 1 
						global_counts  			+= 1	
						global_cps 				+= 1

		t1 = datetime.datetime.now() # Time capture
		te = time.time()
		elapsed = te - tb

		# Saves histogram to json file at interval
		if te - tla >= t_interval:
			settings 		= fn.load_settings()
			filename        = settings[1]
			max_counts      = settings[9]
			max_seconds		= settings[26]
			coeff_1			= settings[18]
			coeff_2			= settings[19]
			coeff_3			= settings[20]

			global_cps = int(global_cps/t_interval)
			
			if mode == 2:
				fn.write_histogram_json(t0, t1, bins, global_counts, int(elapsed), filename, histogram, coeff_1, coeff_2, coeff_3)
				tla = time.time()

			if mode == 3:
				fn.write_3D_intervals_json(t0, t1, bins, global_counts, int(elapsed), filename, histogram_3d, coeff_1, coeff_2, coeff_3)
				histogram_3d = [0] * bins
				tla = time.time()

			fn.write_cps_json(filename, global_cps)
			global_cps = 0
	
	p.terminate() # closes stream when done
	return						
											
