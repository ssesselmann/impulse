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
import numpy as np

data 			= None
left_channel 	= None
path 			= None
device_list 	= fn.get_device_list()
plot 			= {}

global_cps      = 0
global_counts	= 0
grand_cps	= 0
read_size	= 0

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
	peakshift       = settings[28]

	peak 		    = int((sample_length-1)/2) + peakshift
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
	shape 		= [int(x) for x in shapestring]
	samples 	= []
	pulses 		= []
	left_data 	= []

	p = pyaudio.PyAudio()

	global global_cps
	global global_counts  

	global_cps 		= 0
	global_counts 	= 0
	elapsed 		= 0


	elapsed 		= 0
	grand_cps 		= 0
	read_size 		= 0

	# Open the selected audio input device
	stream = p.open(
		format   			= audio_format,
		channels    		= device_channels,
		rate  				= sample_rate,
		input  				= True,
		output  			= False,
		input_device_index  = device,
		frames_per_buffer   = chunk_size * 2)

	tla = time.time()
	read_size = 0
	rest = [ ]
	sum_dist = 0.0
	h_mult_sum = 0.
	dist_sum = 0.
	rejected_count = 0
	while condition and (global_counts < max_counts and elapsed <= max_seconds):
		# Read one chunk of audio data from stream into memory. 
		data = stream.read(chunk_size, exception_on_overflow=False)
		# Convert hex values into a list of decimal values
		values = list(wave.struct.unpack("%dh" % (chunk_size * device_channels), data))
		# Extract every other element (left channel)
		left_channel = values[::2]
		read_size += len(left_channel)
		# Flip inverts all samples if detector pulses are positive
		if flip != 1:
			left_channel = [flip * x for x in left_channel]

		left_channel = rest + left_channel
		skip_to = 0

		# Read through the list of left channel values and find pulse peaks
		for i, sample in enumerate(left_channel[:-sample_length]):
			if i < skip_to:
				continue
			# iterate through one sample lenghth at the time in quick succession, ta-ta-ta-ta-ta...
			samples = left_channel[i:i+sample_length]
			# Function calculates pulse height of all samples 
			# height = fn.pulse_height(samples)
			# Filter out noise
			if (samples[peak] == max(samples) 
					and (height := fn.pulse_height_q2(peak, samples)) > threshold 
#d#					and (height := samples[peak] - min(samples)) > threshold 
					and samples[peak] < 32768):
				# Function normalises sample to zero and converts to integer
				normalised = fn.normalise_pulse_h(24576, samples)
				# Compares pulse to sample and calculates distortion number
				distortion = fn.distortion(normalised, shape)
				# Filters out distorted pulses
				# h_add = 0.006 * distortion
				# h_add = 0.030 * distortion # D01 / ok ?
				# h_add = 0.020 * distortion # D02 / ok ? 132 394 874


#07#				h_mult =  distortion * 0.0000025	#d05 0.0000025/0.02 ok 7.6% 121 391 865

				# h_mult =  distortion * 0.0000050	#d09 0.0000020/0.015 ok 7.6% 121 391 865
				# h_mult =  distortion * 0.0000050 #d11 0.0000050/0.015 ok 7.6% 142/459/1015 / 2048/10/740v 100/3500
#d#				h_mult =  distortion * 0.0000030 #d11 0.0000050/0.015 ok 7.6% 142/459/1015 / 2048/10/740v 100/3500
#n#				if h_mult > 0.030:
#n#					h_mult = 0.030
				# h_add = .000075  * distortion * samples[peak] # bad..
				# height = samples[peak] + h_add - min(samples)

#d#				h_old = height
#d#				height *= (1 + h_mult)
#d#				delta_h = int(height/bin_size) - int(h_old/bin_size)

				#height = samples[peak];
#0#				if 0 and distortion >= tolerance and int(height/bin_size) > 500:
#0#					print("h=%8.1f mult=%12.8f add=%8.2f/%3d h: %4d -> %4d %4d d=%12.2f %4d" % (height, h_mult, 
#0#						h_mult*height, delta_h,
#0#						int(h_old/bin_size), int(height/bin_size),
#0#						i, distortion, skip_to))
				if distortion < tolerance:
					# advance next analyze pos to current + sample_length
					# skip_to = i + sample_length - 1
					skip_to = i + int(sample_length * 4 / 5)
					# Sorts pulse into correct bin
					bin_index = int(height/bin_size)

#					print("h=%8.1f mult=%12.8f add=%8.2f/%3d h: %4d -> %4d %4d d=%12.2f %4d" % (height, h_mult, 
#						h_mult*height, delta_h,
#						int(h_old/bin_size), int(height/bin_size),
#						i, distortion, skip_to))
#					if delta_h > 100:
#						print(samples);
#						print(distortion, tolerance)

					# Adds 1 to the correct bin
					if bin_index < bins:
						histogram[bin_index] 	+= 1
						histogram_3d[bin_index] += 1 
						global_counts  			+= 1	
						global_cps 				+= 1

#						h_mult = (height - samples[peak] + min(samples)) / height
#						h_mult_sum += h_mult
						dist_sum += distortion
#						add_dist = (height-samples[peak])/distortion/samples[peak]
#						sum_dist += add_dist
#						print("h: %8.1f delta: %10.4f dist: %10.0f  delta/dist: %8.6f delta/dist/h: %8.6f avg_Pers: %8.6f" % 
#							(height,
#							height-samples[peak], distortion, 
#							(height-samples[peak])/distortion,
#							(add_dist * 100),
#							sum_dist / global_counts * 100))
				else: # distortion < tolerance:
					rejected_count += 1

		rest = left_channel[i+1:]

		t1      = datetime.datetime.now() # Time capture
		te      = time.time()
		elapsed = te - tb
		if elapsed > 0:
			grand_cps = global_counts / elapsed
		else:
			grand_cps = 0

		# Saves histogram to json file at interval
		if te - tla >= t_interval:
			settings 		= fn.load_settings()
			filename        = settings[1]
			max_counts      = settings[9]
			max_seconds		= settings[26]
			coeff_1			= settings[18]
			coeff_2			= settings[19]
			coeff_3			= settings[20]

			global_cps = int(global_cps/(te-tla))
			
			if mode == 2:
				fn.write_histogram_json(t0, t1, bins, global_counts, int(elapsed), filename, histogram, coeff_1, coeff_2, coeff_3)
				fn.write_histogram_csv(t0, t1, bins, global_counts, int(elapsed), filename, histogram, coeff_1, coeff_2, coeff_3, read_size, elapsed)

			if mode == 3:
				fn.write_3D_intervals_json(t0, t1, bins, global_counts, int(elapsed), filename, histogram_3d, coeff_1, coeff_2, coeff_3)
				histogram_3d = [0] * bins

			tla = time.time()
#d#			print("elapsed=%4d cps=%.3f rate=%.2f h_mult_avg = %8.4f dist_avg = %10.2f" % (elapsed, 
#d#					global_counts/elapsed, read_size/elapsed/1000,
#d#					h_mult_sum/global_cps, dist_sum/global_cps))
			print("elapsed=%4d cps=%.3f reject_cps=%.3f rate=%.2f dist_avg = %10.2f" % (
					elapsed, 
					global_counts/elapsed, rejected_count/elapsed,
					read_size/elapsed/1000,
					dist_sum/global_cps))
			h_mult_sum = 0.
			dist_sum = 0.

			fn.write_cps_json(filename, global_cps)
			global_cps = 0
	
	p.terminate() # closes stream when done
	return						
											
