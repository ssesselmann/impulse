import pyaudio
import wave
import os
import pandas as pd
import numpy as np
import logging
import time
import global_vars
from functions import get_path, save_settings_to_json

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

sc_info = []

# Define the directory where data files are stored
data_directory = global_vars.data_directory

#   Determine if the pulse is predominantly positive or negative.
def determine_pulse_sign(pulse):
    sc_info.append('Checking pulse polarity')
    time.sleep(0.1)
    return np.mean(pulse) > 0

#   Encode pulse signs into a numeric value.
def encode_pulse_sign(left_sign, right_sign):
    left_digit = 1 if left_sign else 2
    right_digit = 1 if right_sign else 2
    sc_info.append(f'Saving pulse polarity')
    time.sleep(0.1)

    return left_digit * 10 + right_digit

#   Align the pulse so that its peak is in the middle.
def align_pulse(pulse, peak_position):
    max_idx = np.argmax(np.abs(pulse))
    shift = peak_position - max_idx
    return np.pad(pulse, (max(shift, 0), max(-shift, 0)), 'constant', constant_values=(0,))[:len(pulse)]

#   Capture initial pulses to determine polarity.
def capture_pulse_polarity(peak, timeout=30):

    with global_vars.write_lock:
        stereo          = bool(global_vars.stereo)
        sample_rate     = int(global_vars.sample_rate)
        chunk_size      = int(global_vars.chunk_size)
        device          = int(global_vars.device) 
        sample_length   = int(global_vars.sample_length)
        threshold       = 1000 

    p           = pyaudio.PyAudio()
    channels    = 2 if stereo else 1
    stream      = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    output=False,
                    frames_per_buffer=chunk_size * channels,
                    input_device_index=device)

    pulse_sign_left     = None
    pulse_sign_right    = True if not stereo else None  # Default to True if stereo is False

    start_time = time.time()

    try:
        while pulse_sign_left is None or (stereo and pulse_sign_right is None):
            # Check for timeout
            if time.time() - start_time > timeout:
                sc_info.append('No pulse on right channel.. Timeout')
                break

            # Read audio data
            data = stream.read(chunk_size, exception_on_overflow=False)

            # Unpack audio data
            values = list(wave.struct.unpack("%dh" % (chunk_size * channels), data))

            # Separate channels
            left_channel = values[::2] if stereo else values
            right_channel = values[1::2] if stereo else []

            # Process each channel to detect pulses
            for channel, pulse_list, channel_name in zip(
                [left_channel, right_channel] if stereo else [left_channel],
                [[], []] if stereo else [[]],
                ["left", "right"] if stereo else ["left"]
            ):
                for i in range(len(channel) - sample_length):
                    samples = channel[i:i + sample_length]

                    if abs(samples[int(peak)]) > threshold:
                        aligned_samples = align_pulse(samples, int(peak))
                        pulse_list.append(aligned_samples)
                        if len(pulse_list) >= 10:  # Use a small number for quick polarity determination
                            pulse_sign = determine_pulse_sign([sum(samples) for samples in pulse_list])
                            if channel_name == "left":
                                pulse_sign_left = pulse_sign
                            elif channel_name == "right" and stereo:
                                pulse_sign_right = pulse_sign
                            pulse_list.clear()
                            break
    finally:
        # Clean up the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

    return pulse_sign_left, pulse_sign_right

def shapecatcher():

    # Extract settings from global_vars
    with global_vars.write_lock:
        name            = global_vars.filename
        device          = global_vars.device
        sample_rate     = global_vars.sample_rate
        chunk_size      = global_vars.chunk_size
        tolerance       = global_vars.tolerance
        bins            = global_vars.bins
        bin_size        = global_vars.bin_size
        max_counts      = global_vars.max_counts
        shapecatches    = global_vars.shapecatches
        sample_length   = global_vars.sample_length
        peakshift       = global_vars.peakshift
        stereo          = global_vars.stereo

    peak            = int(((int(sample_length) - 1) / 2) + int(peakshift))
    threshold       = 1000  # Hard coded for shapecatcher only
    logger.info(f'Shapecatcher threshold fixed at {threshold}\n')

    logger.info(f'Shapecatcher says Stereo is {stereo}\n')

    if stereo:
        sc_info.append(f'Preparing for {sample_rate} kHz stereo')
    else:
        sc_info.append(f'Preparing for {sample_rate} kHz mono')

    time.sleep(0.1)

    
    # First, determine the pulse polarity
    pulse_sign_left, pulse_sign_right = capture_pulse_polarity(peak)

    if stereo and pulse_sign_right is None:
        sc_info.append('No pulse on right channel... Exiting.')
        return [], []

    # Log the signs for debugging
    logger.info(f"Determined Pulse Signs Left: {pulse_sign_left} Right: {pulse_sign_right}\n")
    sc_info.append(f"Positive pulse Left: {pulse_sign_left} Right: {pulse_sign_right}")

    # Encode pulse signs into a numeric value
    encoded_pulse_sign = encode_pulse_sign(pulse_sign_left, pulse_sign_right)

    logging.info(f"Encoded Pulse Sign: {encoded_pulse_sign}")

    # Save the encoded pulse sign to global_vars and JSON
    with global_vars.write_lock:
        global_vars.flip = encoded_pulse_sign
        
    save_settings_to_json()

    # Reinitialize PyAudio for shape catching
    p = pyaudio.PyAudio()
    channels = 2 if stereo else 1
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    output=False,
                    frames_per_buffer=chunk_size * channels,
                    input_device_index=device)

    pulse_list_left  = []
    pulse_list_right = []

    sc_info.append(f'Collecting pulses')

    try:
        while True:
            # Read audio data
            data = stream.read(chunk_size, exception_on_overflow=False)

            # Unpack audio data
            values = list(wave.struct.unpack("%dh" % (chunk_size * channels), data))

            # Separate channels
            left_channel = values[::2] if stereo else values
            right_channel = values[1::2] if stereo else []

            # Process each channel to detect pulses
            for channel, pulse_list, channel_name, pulse_sign in zip(
                [left_channel, right_channel] if stereo else [left_channel],
                [pulse_list_left, pulse_list_right] if stereo else [pulse_list_left],
                ["left", "right"] if stereo else ["left"],
                [pulse_sign_left, pulse_sign_right] if stereo else [pulse_sign_left]
            ):
                for i in range(len(channel) - sample_length):
                    samples = channel[i:i + sample_length]

                    if abs(samples[peak]) > threshold and samples[peak] == max(samples):
                        aligned_samples = align_pulse(samples, peak)

                        # Flip the data if necessary
                        if not pulse_sign:
                            aligned_samples = [-s for s in aligned_samples]

                        pulse_list.append(aligned_samples)

                        # Break if enough pulses are collected
                        if len(pulse_list) >= shapecatches:
                            break

            # Check exit condition for loop
            if (len(pulse_list_left) >= shapecatches and (not stereo or len(pulse_list_right) >= shapecatches)):
                break

        sc_info.append(f'Calculating mean shape')
        time.sleep(0.1)

        # Calculate average pulses
        pulses_sum_left = [int(sum(x) / len(x)) for x in zip(*pulse_list_left)] if pulse_list_left else []
        pulses_sum_right = [int(sum(x) / len(x)) for x in zip(*pulse_list_right)] if pulse_list_right else []

        # Ensure both arrays have the same length
        if len(pulses_sum_left) != len(pulses_sum_right):
            max_length = max(len(pulses_sum_left), len(pulses_sum_right))
            pulses_sum_left = (pulses_sum_left + [0] * max_length)[:max_length]
            pulses_sum_right = (pulses_sum_right + [0] * max_length)[:max_length]

        # Save data to CSV
        df = pd.DataFrame({
            'Left': pulses_sum_left,
            'Right': pulses_sum_right
        })

        # Convert columns to integer type to ensure all values are integers
        df['Left'] = df['Left'].astype(int)
        df['Right'] = df['Right'].astype(int)

        sc_info.append(f'Saving shape.csv')

        # Save DataFrame to CSV, include index as the first column (row numbers)
        shapecsv = global_vars.shapecsv #get_path(f'{data_directory}/_shape.csv')
        df.to_csv(shapecsv, index=True, index_label='Row')

    finally:
        # Clean up and close streams
        stream.stop_stream()
        stream.close()
        p.terminate()

        sc_info.append(f' ')

    return pulses_sum_left, pulses_sum_right
