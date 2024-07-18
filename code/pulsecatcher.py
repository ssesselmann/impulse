import pyaudio
import wave
import math
import threading
import time
import datetime
import logging
import global_vars
import functions as fn

logger = logging.getLogger(__name__)

# Function reads audio stream and finds pulses then outputs time, pulse height and distortion
def pulsecatcher(mode, run_flag, run_flag_lock):
    
    # Start timer
    t0                      = datetime.datetime.now()
    time_start              = time.time()
    time_last_save          = time_start
    time_last_save_time     = time_start  # corrected variable initialization
    array_3d                = []
    spec_notes              = ""

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

    right_threshold = 1000  # Set a stricter threshold for right channel to filter out noise    

    audio_format    = pyaudio.paInt16
    p               = pyaudio.PyAudio()
    device_channels = p.get_device_info_by_index(device)['maxInputChannels']

    # Loads pulse shape from csv
    shapes          = fn.load_shape()
    left_shape      = [int(x) for x in shapes[0]]
    right_shape     = [int(x) for x in shapes[1]]

    samples         = []
    pulses          = []
    left_data       = []
    right_data      = []

    last_count      = 0

    # Global variables
    with global_vars.write_lock:
        global_vars.elapsed         = 0
        global_vars.counts          = 0
        global_vars.histogram       = [0] * bins
        global_vars.count_history   = []
    
    # Local Variables
    local_elapsed = 0
    local_counts = 0
    local_histogram = [0] * bins
    local_count_history = []
    
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

    while global_vars.run_flag.is_set() and local_counts < max_counts and local_elapsed <= max_seconds:
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

        logger.debug(f"Left channel data: {left_channel[:10]}\n")
        logger.debug(f"Right channel data: {right_channel[:10]}\n")

        # Extend detection to right channel for mode 4
        right_pulses = []

        if mode == 4:
            for i in range(len(right_channel) - sample_length):
                samples = right_channel[i:i + sample_length]
                height = fn.pulse_height(samples)
                if samples[peak] == max(samples) and abs(height) > right_threshold and samples[peak] < 32768:
                    right_pulses.append((i + peak, height))
                    logger.debug(f"Right channel pulse detected at index {i}: height {height} sample = {samples}\n")

        # Read through the list of left channel values and find pulse peaks
        for i in range(len(left_channel) - sample_length):
            samples = left_channel[i:i + sample_length]
            height = fn.pulse_height(samples)
            if samples[peak] == max(samples) and abs(height) > threshold and samples[peak] < 32768:

                if mode == 4:

                    coincident_pulse = None

                    for rp in right_pulses:

                        if i + peak - 3 <= rp[0] <= i + peak + 3:

                            coincident_pulse = rp

                            break

                    if not coincident_pulse:

                        continue  # Skip this pulse if no coincident pulse found
                    else:

                        logger.debug(f"Coincidence index {i}, height {height}, Right pulse at index {coincident_pulse[0]}, height {coincident_pulse[1]}\n")

                normalised = fn.normalise_pulse(samples)
                distortion = fn.distortion(normalised, left_shape)
                if distortion < tolerance:
                    bin_index = int(height / bin_size)
                    if bin_index < bins:
                        local_histogram[bin_index] += 1
                        local_counts += 1

        t1 = datetime.datetime.now()  # Time capture
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

                global_vars.count_history.append(counts_per_sec)

                if mode == 2:
                    global_vars.histogram = local_histogram

                if mode == 3:
                    interval_histogram = [local_histogram[i] - last_histogram[i] for i in range(bins)]
                    global_vars.histogram_3d.append(interval_histogram)
                    last_histogram = local_histogram.copy()

            local_count_history.append(counts_per_sec)
            last_count      = local_counts
            time_last_save  = time_this_save

        # Save data to global_variables once per minute
        if time_this_save - time_last_save_time >= 60 * t_interval or not global_vars.run_flag.is_set():
            location    = ""
            spec_notes  = ""
            
            if mode == 2 or mode == 4:
                fn.write_histogram_npesv2(t0, t1, bins, local_counts, int(local_elapsed), filename, local_histogram, coeff_1, coeff_2, coeff_3, device, location, spec_notes)
                fn.write_cps_json(filename, local_count_history, int(local_elapsed))

            if mode == 3:
                with global_vars.write_lock:
                    histogram_3d = global_vars.histogram_3d
                fn.update_json_3d_file(t0, t1, bins_3d, local_counts, local_elapsed, filename_3d, histogram_3d, coeff_1, coeff_2, coeff_3, device)
            
            time_last_save_time = time.time()

    p.terminate()  # closes stream when done
    global_vars.run_flag.clear()  # Ensure the CPS thread also stops
    return
