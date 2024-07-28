import pyaudio
import wave
import math
import threading
import time
import datetime
import logging
import queue
import global_vars
import functions as fn

logger = logging.getLogger(__name__)

# Function to save data in a separate thread
def save_data(save_queue):
    while True:
        data = save_queue.get()
        if data is None:
            break
        t0                  = data['t0']
        t1                  = data['t1']
        bins                = data['bins']
        local_counts        = data['local_counts']
        local_elapsed       = data['local_elapsed']
        filename            = data['filename']
        local_histogram     = data['local_histogram']
        coeff_1             = data['coeff_1']
        coeff_2             = data['coeff_2']
        coeff_3             = data['coeff_3']
        device              = data['device']
        location            = data['location']
        spec_notes          = data['spec_notes']
        local_count_history = data['local_count_history']

        if 'filename_3d' in data:
            filename_3d = data['filename_3d']
            last_minute      = data['last_minute']
            fn.update_json_3d_file(t0, t1, bins, local_counts, local_elapsed, filename_3d, last_minute, coeff_1, coeff_2, coeff_3, device)
        else:
            fn.write_histogram_npesv2(t0, t1, bins, local_counts, local_elapsed, filename, local_histogram, coeff_1, coeff_2, coeff_3, device, location, spec_notes)
            fn.write_cps_json(filename, local_count_history, local_elapsed)

# Function reads audio stream and finds pulses then outputs time, pulse height, and distortion
def pulsecatcher(mode, run_flag, run_flag_lock):
    
    # Start timer
    t0                  = datetime.datetime.now()
    time_start          = time.time()
    time_last_save      = time_start
    time_last_save_time = time_start  # corrected variable initialization
    array_3d            = []
    spec_notes          = ""

    # Load settings from global variables
    with global_vars.write_lock:
        last_histogram  = [0] * global_vars.bins  # Initialize last_histogram
        filename        = global_vars.filename
        filename_3d     = global_vars.filename_3d
        device          = global_vars.device
        sample_rate     = global_vars.sample_rate
        chunk_size      = global_vars.chunk_size
        threshold       = global_vars.threshold
        tolerance       = global_vars.tolerance
        bins            = global_vars.bins
        bins_3d         = global_vars.bins_3d
        bin_size        = global_vars.bin_size
        bin_size_3d     = global_vars.bin_size_3d
        max_counts      = global_vars.max_counts
        sample_length   = global_vars.sample_length
        coeff_1         = global_vars.coeff_1
        coeff_2         = global_vars.coeff_2
        coeff_3         = global_vars.coeff_3
        flip            = global_vars.flip
        max_seconds     = global_vars.max_seconds
        t_interval      = global_vars.t_interval
        peakshift       = global_vars.peakshift
        peak            = int((sample_length - 1) / 2) + peakshift
        spec_notes      = global_vars.spec_notes
        # Set global vars
        global_vars.elapsed         = 0
        global_vars.counts          = 0
        global_vars.histogram       = [0] * bins
        global_vars.count_history   = []

    if mode == 3:
        bin_size    = bin_size_3d
        bins        = bins_3d

    # Fixed variables
    right_threshold = 1000  # Threshold for right channel   
    audio_format    = pyaudio.paInt16
    p               = pyaudio.PyAudio()
    device_channels = p.get_device_info_by_index(device)['maxInputChannels']
    shapes          = fn.load_shape() # Loads pulse shape from csv
    left_shape      = [int(x) for x in shapes[0]]
    right_shape     = [int(x) for x in shapes[1]]
    samples         = []
    pulses          = []
    left_data       = []
    right_data      = []
    last_count      = 0
    local_elapsed       = 0
    local_counts        = 0
    local_histogram     = [0] * bins
    local_count_history = []
    right_pulses        = []

    last_minute_histogram_3d = []
    
    # Open the selected audio input device
    stream = p.open(
        format=audio_format,
        channels=2,
        rate=sample_rate,
        input=True,
        output=False,
        input_device_index=device,
        frames_per_buffer=chunk_size * 2
    )

    save_queue  = queue.Queue()
    save_thread = threading.Thread(target=save_data, args=(save_queue,))
    save_thread.start()
    
    # This is the main pulsecatcher while loop
    while global_vars.run_flag.is_set() and local_counts < max_counts and local_elapsed <= max_seconds:
        # Read one chunk of audio data from stream into memory.
        data    = stream.read(chunk_size, exception_on_overflow=False)
        # Convert hex values into a list of decimal values
        values  = list(wave.struct.unpack("%dh" % (chunk_size * 2), data))
        # Extract every other element (left channel)
        left_channel    = values[::2]
        right_channel   = values[1::2]

        # Flip the samples if inputs are positive
        if flip == 22:
            left_channel    = [flip * x for x in left_channel]
            right_channel   = [flip * x for x in right_channel]
        if flip == 12:
            right_channel   = [flip * x for x in right_channel]
        if flip == 21:
            left_channel    = [flip * x for x in left_channel]

        # Extend detection to right channel if mode == 4
        if mode == 4:
            for i in range(len(right_channel) - sample_length):
                samples = right_channel[i:i + sample_length]
                height = fn.pulse_height(samples)
                if samples[peak] == max(samples) and abs(height) > right_threshold and samples[peak] < 32768:
                    right_pulses.append((i + peak, height))
                    logger.debug(f"Right channel pulse detected at index {i}: height {height} sample = {samples}\n")

        # Read through the list of left channel values and find pulse peaks
        for i in range(len(left_channel) - sample_length):
            samples     = left_channel[i:i + sample_length]
            height      = fn.pulse_height(samples)

            if samples[peak] == max(samples) and abs(height) > threshold and samples[peak] < 32768:

                if mode == 4:
                    coincident_pulse = None
                    for rp in right_pulses:
                        if i + peak - 3 <= rp[0] <= i + peak + 3:
                            coincident_pulse = rp
                            break
                    if not coincident_pulse:
                        continue  # Skip if no coincident pulse found
                    else:

                        logger.debug(f"Coincidence index {i}, height {height}, Right pulse at index {coincident_pulse[0]}, height {coincident_pulse[1]}\n")

                normalised = fn.normalise_pulse(samples)
                distortion = fn.distortion(normalised, left_shape)
                
                if distortion < tolerance:
                    bin_index = int(height / bin_size)

                    if bin_index < bins:
                        local_histogram[bin_index] += 1
                        local_counts += 1
        # Time capture
        t1 = datetime.datetime.now()  
        time_this_save = time.time()
        local_elapsed = int(time_this_save - time_start)

        # reduce overhead by updating global variables once per second
        if time_this_save - time_last_save >= 1 * t_interval:
            counts_per_sec = local_counts - last_count

            with global_vars.write_lock:
                global_vars.cps         = counts_per_sec
                global_vars.counts      = local_counts
                global_vars.elapsed     = local_elapsed
                global_vars.spec_notes  = spec_notes
                
                if mode == 2:
                    global_vars.histogram = local_histogram
                    global_vars.count_history.append(counts_per_sec)

                if mode == 3:

                    interval_histogram = [local_histogram[i] - last_histogram[i] for i in range(bins)]

                    global_vars.histogram_3d.append(interval_histogram)

                    last_minute_histogram_3d.append(interval_histogram)

                    last_histogram = local_histogram.copy()

            local_count_history.append(counts_per_sec)
            last_count      = local_counts
            time_last_save  = time_this_save


        # Save data to global_variables once per minute
        if time_this_save - time_last_save_time >= 10 * t_interval or not global_vars.run_flag.is_set():
            save_data_dict = {
                't0': t0, 
                't1': t1, 
                'bins': bins, 
                'local_counts': local_counts, 
                'local_elapsed': local_elapsed,
                'filename': filename, 
                'local_histogram': local_histogram, 
                'coeff_1': coeff_1, 
                'coeff_2': coeff_2,
                'coeff_3': coeff_3, 
                'device': device, 
                'location': '', 
                'spec_notes': spec_notes,
                'local_count_history': local_count_history
            }
            
            if mode == 3:
                save_data_dict['filename_3d'] = filename_3d
                save_data_dict['last_minute'] = last_minute_histogram_3d
            save_queue.put(save_data_dict)
            last_minute_histogram = []
            time_last_save_time = time.time()

    # Signal the save thread to exit
    save_queue.put(None)
    save_thread.join()
    
    p.terminate()  # closes stream when done
    global_vars.run_flag.clear()  # Ensure the CPS thread also stops
    return
