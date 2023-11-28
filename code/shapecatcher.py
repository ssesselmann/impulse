# This page contains a function to generate a pulse shape file
# First it finds a list of pulses, then
# the pulses are summed, averaged and normalised, 
# finally saved as a csv file.
# Ultimately this file should also be a JSON file as I have too many file types here. 

import pyaudio
import wave
import math
import csv
import os
import time
import sqlite3 as sql
import functions as fn
import pandas as pd
from collections import defaultdict


# Starts timer
t0 					= time.perf_counter() 
data 				= None
left_channel 		= []
sample_list 		= []
data_directory  	= os.path.join(os.path.expanduser("~"), "impulse_data")

# Function to catch pulses and output time, pulkse height and distortion
def shapecatcher():

	database 		= fn.get_path(f'{data_directory}/.data.db')
	shapecsv 		= fn.get_path(f'{data_directory}/shape.csv')
	n 				= 0
	shape 			= None
	samples_sum 	= None
	samples 		= None
	left_channel	= None
	summed 			= None
	shapecatches	= None
	sample_length 	= None
	pulse_list		= []

	conn = sql.connect(database)
	c = conn.cursor()
	query = "SELECT * FROM settings "
	c.execute(query) 
	settings = c.fetchall()[0]

	name            = settings[1]
	device          = settings[2]             
	sample_rate     = settings[3]
	chunk_size      = settings[4]                        
	threshold       = settings[5]
	tolerance       = settings[6]
	bins            = settings[7]
	bin_size        = settings[8]
	max_counts      = settings[9]
	shapecatches 	= settings[10]
	sample_length	= settings[11]
	peak 			= int((sample_length-1)/2)

	# Create an array of empty bins
	start 			= 0
	stop 			= bins * bin_size
	bin_array 		= fn.create_bin_array(start, stop, bin_size)
	bin_counts 		= defaultdict(int)

	threshold 		= 3200
	
	threshold_trace = [threshold] * sample_length

	try:
		# Get audio parameters
		device_list 	= fn.get_device_list()
		device_channels = fn.get_max_input_channels(device)
		p 				= pyaudio.PyAudio()
		audio_format 	= pyaudio.paInt16
		
		# Open the selected audio input device
		stream = p.open(
			format  			= audio_format,
			channels   			= device_channels,
			rate   				= sample_rate,
			input  				= True,
			output   			= False,
			input_device_index  = device,
			frames_per_buffer   = chunk_size * 2)

		# Loops through and finds a number of pulses (shapecatches) as loaded from settings
		while True:
			# Read the audio data stream
			data = stream.read(chunk_size, exception_on_overflow=False)
			# Convert hex to numbers
			values = list(wave.struct.unpack("%dh" % (chunk_size * device_channels), data))
		    # Extract every other element (left channel)
			left_channel = values[::2]
			# Cycle through list of sample strings
			#for i in range(len(left_channel) - sample_length):
			for i, sample in enumerate(left_channel[:-sample_length]):	
				# Get the first string of  samples
				samples = left_channel[i:i+sample_length]  
				# Function checks if pulse is positive or negative
				flip = fn.detect_pulse_direction(samples)
				# Flips samples if pulse is positive
				samples = [flip * x for x in samples]
				# Find pulses based only on the peak height being in the middle 80% of 32000
				if samples[peak] >= max(samples) and (max(samples)-min(samples)) > threshold and samples[peak] < 28800:
					# gather a list of samples 
					pulse_list.append(samples)
					# Counter
					n += 1
					# Stop[ afer n samples]
					if n >= (shapecatches-1): # number of pulses to average
						# close stream
						p.terminate()
						# Zip sum all lists
						pulses_sum = [sum(x)/len(pulse_list) for x in zip(*pulse_list)] 
						# Normalise summed list
						shape = fn.normalise_pulse(pulses_sum)
						# convert floats to ints
						shape_int = [int(x) for x in shape]
						# Format and save to csv file
						df = pd.DataFrame(shape_int)
						# Save Pulse Direction to database
						database = fn.get_path(f'{data_directory}/.data.db')
						conn = sql.connect(database)
						c = conn.cursor()
						query = f"UPDATE settings SET flip = {flip} WHERE id=0;"
						c.execute(query)
						conn.commit()
						# Write to csv
						df.to_csv(shapecsv, index='Shape', header=0)

						return shape_int, threshold_trace	
	except:

		shape_int = [0] * sample_length

		return shape_int, threshold_trace


	    