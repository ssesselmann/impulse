import pyaudio
import numpy as np
import pyaudio
import wave
import time
import global_vars
import pandas as pd

from functions import save_settings_to_json

# Setup logging (optional, if logging is desired)
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

sc_info = []

# Align the pulse so that its peak is in the middle (no changes to this method)
def align_pulse(pulse, peak_position):
    max_idx = np.argmax(np.abs(pulse))
    shift = peak_position - max_idx
    return np.pad(pulse, (max(shift, 0), max(-shift, 0)), 'constant', constant_values=(0,))[:len(pulse)]

# Determine if a pulse is predominantly positive or negative
def determine_pulse_sign(pulse):
    max_val = np.max(pulse)
    min_val = np.min(pulse)
    return max_val > abs(min_val)

def encode_pulse_sign(left_sign, right_sign):
    left_digit = 1 if left_sign else 2
    right_digit = 1 if right_sign else 2
    sc_info.append(f'Saving pulse polarity')
    time.sleep(0.1)
    return left_digit * 10 + right_digit


# Capture and test polarity for a single channel
def capture_channel_polarity(channel_data, sample_length, shape_lld, peak):
    pulse_list = []
    consecutive_pulses_same_polarity = 0
    previous_polarity = None

    for i in range(len(channel_data) - sample_length):
        samples = channel_data[i:i + sample_length]

        if abs(max(samples)) > shape_lld:
            aligned_samples = align_pulse(samples, int(peak))
            current_polarity = determine_pulse_sign(aligned_samples)

            if previous_polarity is None:
                previous_polarity = current_polarity

            if current_polarity == previous_polarity:
                consecutive_pulses_same_polarity += 1
            else:
                consecutive_pulses_same_polarity = 1  # Reset counter for new polarity
                previous_polarity = current_polarity

            if consecutive_pulses_same_polarity >= 20:
                return current_polarity

    return None

#   Capture initial pulses to determine polarity.
def capture_pulse_polarity(timeout=30):
    with global_vars.write_lock:
        stereo = bool(global_vars.stereo)
        sample_rate = int(global_vars.sample_rate)
        chunk_size = int(global_vars.chunk_size)
        device = int(global_vars.device) 
        sample_length = int(global_vars.sample_length)
        shape_lld = int(global_vars.shape_lld)
        peak = int((sample_length - 1) / 2 + global_vars.peakshift)

    p = pyaudio.PyAudio()
    channels = 2 if stereo else 1
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    output=False,
                    frames_per_buffer=chunk_size * channels,
                    input_device_index=device)

    pulse_sign_left = None
    pulse_sign_right = None

    start_time = time.time()

    try:
        while pulse_sign_left is None or (stereo and pulse_sign_right is None):
            if time.time() - start_time > timeout:
                sc_info.append('Polarity detection timeout.')
                break

            # Read audio data
            data = stream.read(chunk_size, exception_on_overflow=False)
            values = list(wave.struct.unpack("%dh" % (chunk_size * channels), data))

            # Separate channels
            left_channel = values[::2] if stereo else values  # Left channel data
            right_channel = values[1::2] if stereo else []    # Right channel data, empty if mono

            # Determine polarity for left channel
            if pulse_sign_left is None:
                pulse_sign_left = capture_channel_polarity(left_channel, sample_length, shape_lld, peak)

            # Determine polarity for right channel (if stereo)
            if stereo and pulse_sign_right is None:
                pulse_sign_right = capture_channel_polarity(right_channel, sample_length, shape_lld, peak)

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    # Encode the pulse polarity into a two-digit number
    if pulse_sign_left is not None:
        left_digit = 1 if pulse_sign_left else 2
    else:
        left_digit = 0  # Use 0 to indicate no pulse detection

    if stereo and pulse_sign_right is not None:
        right_digit = 1 if pulse_sign_right else 2
    else:
        right_digit = 0  # Use 0 to indicate no pulse detection or mono

    encoded_pulse_sign = left_digit * 10 + right_digit

    # Save encoded result to global_vars
    with global_vars.write_lock:
        global_vars.flip = encoded_pulse_sign

    # Return both pulse signs (left and right) for unpacking
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
        shape_lld       = global_vars.shape_lld
        shape_uld       = global_vars.shape_uld
        pc              = 0

    peak            = int(((int(sample_length) - 1) / 2) + int(peakshift))

    logger.info(f'Shapecatcher shape_lld fixed at {shape_lld}\n')

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
        # Collect pulses from the left channel
        while len(pulse_list_left) < shapecatches:
            # Read audio data
            data = stream.read(chunk_size, exception_on_overflow=False)
            # Unpack audio data
            values = list(wave.struct.unpack("%dh" % (chunk_size * channels), data))    
            # Separate the left channel
            left_channel = values[::2] if stereo else values
            # Process the left channel to detect pulses
            for i in range(len(left_channel) - sample_length):
                samples = left_channel[i:i + sample_length]
                if shape_lld < abs(samples[peak]) < shape_uld and samples[peak] == max(samples):
                    aligned_samples = align_pulse(samples, peak)
                    # Flip the data if necessary
                    if not pulse_sign_left:
                        aligned_samples = [-s for s in aligned_samples]
                    pulse_list_left.append(aligned_samples)
                    pcl = len(pulse_list_left)
                    sc_info.append(f'Looking for pulses on left channel: {pcl}')
                if len(pulse_list_left) >= shapecatches:
                    break

        # If stereo mode is enabled, collect pulses from the right channel
        if stereo:
            while len(pulse_list_right) < shapecatches:
                # Read audio data
                data = stream.read(chunk_size, exception_on_overflow=False)
                # Unpack audio data
                values = list(wave.struct.unpack("%dh" % (chunk_size * channels), data))
                # Separate the right channel
                right_channel = values[1::2]
                # Process the right channel to detect pulses
                for i in range(len(right_channel) - sample_length):
                    samples = right_channel[i:i + sample_length]
                    if shape_lld < abs(samples[peak]) < shape_uld and samples[peak] == max(samples):
                        aligned_samples = align_pulse(samples, peak)
                        # Flip the data if necessary
                        if not pulse_sign_right:
                            aligned_samples = [-s for s in aligned_samples]
                        pulse_list_right.append(aligned_samples)
                        pcr = len(pulse_list_right)
                        sc_info.append(f'Looking for pulses on right channel: {pcr}')
                    if len(pulse_list_right) >= shapecatches:
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
