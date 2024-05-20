import pyaudio
import wave
import math
import threading
import time
import functions as fn
import sqlite3 as sql
import datetime
import logging
from collections import defaultdict

data            = None
left_channel    = None
global_cps      = 0
mean_cps        = 0
global_counts   = 0
run_flag        = True
run_flag_lock   = threading.Lock()
write_lock      = threading.Lock()

logger = logging.getLogger(__name__)

# Function reads audio stream and finds pulses then outputs time, pulse height and distortion
def pulsecatcher(mode, run_flag, run_flag_lock):

    # Start timer
    t0              = datetime.datetime.now()
    tb              = time.time()   # time beginning
    tla = 0

    # Get the following from settings
    settings        = fn.load_settings()
    filename        = settings[1]
    device          = settings[2]             
    sample_rate     = settings[3]
    chunk_size      = settings[4]                        
    threshold       = settings[5]
    tolerance       = settings[6]
    bins            = settings[7]
    bin_size        = settings[8]
    max_counts      = settings[9]
    sample_length   = settings[11]
    coeff_1         = settings[18]
    coeff_2         = settings[19]
    coeff_3         = settings[20]
    flip            = settings[22]
    max_seconds     = settings[26]
    t_interval      = settings[27]
    peakshift       = settings[28]
    peak            = int((sample_length-1)/2) + peakshift

    right_threshold = 1000  # Set a stricter threshold for right channel to filter out noise

    # Create an array of empty bins
    histogram       = [0] * bins
    histogram_3d    = [0] * bins
    audio_format    = pyaudio.paInt16
    device_channels = fn.get_max_input_channels(device)

    # Loads pulse shape from csv
    shapes = fn.load_shape()
    left_shape = [int(x) for x in shapes[0]]
    right_shape = [int(x) for x in shapes[1]]

    samples     = []
    pulses      = []
    left_data   = []
    right_data  = []

    p = pyaudio.PyAudio()

    global mean_cps
    global global_counts  

    global_cps      = 0
    global_counts   = 0
    elapsed         = 0

    # Open the selected audio input device
    stream = p.open(
        format              = audio_format,
        channels            = 2,
        rate                = sample_rate,
        input               = True,
        output              = False,
        input_device_index  = device,
        frames_per_buffer   = chunk_size * 2)

    while run_flag.is_set() and (global_counts < max_counts and elapsed <= max_seconds):
        # Read one chunk of audio data from stream into memory. 
        data = stream.read(chunk_size, exception_on_overflow=False)
        # Convert hex values into a list of decimal values
        values = list(wave.struct.unpack("%dh" % (chunk_size * 2), data))

        # Extract every other element (left channel)
        left_channel = values[::2]
        right_channel = values[1::2]

        # Flip inverts all samples if detector pulses are positive
        if flip == 22:
            left_channel = [flip * x for x in left_channel]
            right_channel = [flip * x for x in right_channel]

        if flip == 12:
            right_channel = [flip * x for x in right_channel]

        if flip == 21:
            left_channel = [flip * x for x in left_channel]

        logger.debug(f"Left channel data: {left_channel[:10]}")
        logger.debug(f"Right channel data: {right_channel[:10]}")

        # Extend detection to right channel for mode 4
        right_pulses = []
        
        if mode == 4:
            for i in range(len(right_channel) - sample_length):
                samples = right_channel[i:i+sample_length]
                height = fn.pulse_height(samples)
                if samples[peak] == max(samples) and abs(height) > right_threshold and samples[peak] < 32768:
                    right_pulses.append((i + peak, height))
                    logger.debug(f"Right channel pulse detected at index {i}: height {height} sample = {samples}")

        # Read through the list of left channel values and find pulse peaks
        for i in range(len(left_channel) - sample_length):
            # iterate through one sample length at the time in quick succession, ta-ta-ta-ta-ta...
            samples = left_channel[i:i+sample_length]
            # Function calculates pulse height of all samples 
            height = fn.pulse_height(samples)
            # Filter out noise
            if samples[peak] == max(samples) and abs(height) > threshold and samples[peak] < 32768:

                if mode == 4:
                    # Check for coincident pulses within 3 sample indices
                    coincident_pulse = None
                    for rp in right_pulses:
                        if i + peak - 3 <= rp[0] <= i + peak + 3:
                            coincident_pulse = rp
                            break
                    if not coincident_pulse:
                        continue  # Skip this pulse if no coincident pulse found
                    else:
                        logger.debug(f"Coincidence found: Left pulse at index {i}, height {height}, Right pulse at index {coincident_pulse[0]}, height {coincident_pulse[1]}")

                # Function normalises sample to zero and converts to integer
                normalised = fn.normalise_pulse(samples)
                # Compares pulse to sample and calculates distortion number
                distortion = fn.distortion(normalised, left_shape)
                # Filters out distorted pulses
                if distortion < tolerance:
                    # Sorts pulse into correct bin
                    bin_index = int(height/bin_size)
                    # Adds 1 to the correct bin
                    if bin_index < bins:
                        histogram[bin_index]    += 1
                        histogram_3d[bin_index] += 1 
                        global_counts           += 1    
                        global_cps              += 1

        t1      = datetime.datetime.now() # Time capture
        te      = time.time()
        elapsed = int(te - tb)

        # Saves histogram to json file at interval
        if te - tla >= t_interval:
            settings        = fn.load_settings()
            filename        = settings[1]
            max_counts      = settings[9]
            max_seconds     = settings[26]
            coeff_1         = settings[18]
            coeff_2         = settings[19]
            coeff_3         = settings[20]
            global_cps      = int(global_cps/t_interval)
            location        = ""
            note            = ""
            mean_cps        = global_cps
            
            if mode == 2 or mode == 4:
                with write_lock:
                    fn.write_histogram_npesv2(t0, t1, bins, global_counts, int(elapsed), filename, histogram, coeff_1, coeff_2, coeff_3, device, location, note )                                           
                    tla = time.time()

            if mode == 3:
                with write_lock:
                    fn.write_3D_intervals_json(t0, t1, bins, global_counts, int(elapsed), filename, histogram_3d, coeff_1, coeff_2, coeff_3)
                    histogram_3d = [0] * bins
                    tla = time.time()

            with write_lock:
                fn.write_cps_json(filename, global_cps, elapsed)
                global_cps = 0
    
    p.terminate() # closes stream when done
    return                      
