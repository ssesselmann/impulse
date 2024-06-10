import pyaudio
import wave
import os
import sqlite3 as sql
import pandas as pd
import numpy as np
import logging
from functions import get_path

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Define the directory where data files are stored
data_directory = os.path.join(os.path.expanduser("~"), "impulse_data")

def determine_pulse_sign(pulse):
    """Determine if the pulse is predominantly positive or negative."""
    return np.mean(pulse) > 0

def encode_pulse_sign(left_sign, right_sign):
    """Encode pulse signs into a numeric value."""
    left_digit = 1 if left_sign else 2
    right_digit = 1 if right_sign else 2
    return left_digit * 10 + right_digit

def align_pulse(pulse, peak_position):
    """Align the pulse so that its peak is in the middle."""
    max_idx = np.argmax(np.abs(pulse))
    shift = peak_position - max_idx
    return np.pad(pulse, (max(shift, 0), max(-shift, 0)), 'constant', constant_values=(0,))[:len(pulse)]

def capture_pulse_polarity(stereo, sample_rate, chunk_size, device, sample_length, peak, threshold):
    """Capture initial pulses to determine polarity."""
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
    pulse_sign_right = True if not stereo else None  # Default to True if stereo is False

    try:
        while pulse_sign_left is None or (stereo and pulse_sign_right is None):
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

                    if abs(samples[peak]) > threshold:
                        aligned_samples = align_pulse(samples, peak)
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


def shapecatcher(stereo):
    # Connect to the database and get settings
    database = get_path(f'{data_directory}/.data_v2.db')
    shapecsv = get_path(f'{data_directory}/shape.csv')

    conn = sql.connect(database)
    c = conn.cursor()
    c.execute("SELECT * FROM settings")
    settings = c.fetchall()[0]

    # Extract settings from the database
    name = settings[1]
    device = settings[2]
    sample_rate = settings[3]
    chunk_size = settings[4]
    threshold = 1000  # Hard coded for shapecatcher only
    tolerance = settings[6]
    bins = settings[7]
    bin_size = settings[8]
    max_counts = settings[9]
    shapecatches = settings[10]
    sample_length = settings[11]
    peakshift = settings[28]
    peak = int((sample_length - 1) / 2) + peakshift

    logger.info(f'Shapecatcher threshold fixed at {threshold}')
    logger.info(f'Shapecatcher says Stereo is {stereo}')

    # First, determine the pulse polarity
    pulse_sign_left, pulse_sign_right = capture_pulse_polarity(
        stereo, sample_rate, chunk_size, device, sample_length, peak, threshold)

    # Log the signs for debugging
    logging.info(f"Determined Pulse Signs Left: {pulse_sign_left} Right: {pulse_sign_right}")

    # Encode pulse signs into a numeric value
    encoded_pulse_sign = encode_pulse_sign(pulse_sign_left, pulse_sign_right)
    logging.info(f"Encoded Pulse Sign: {encoded_pulse_sign}")

    # Save the encoded pulse sign to the database
    conn = sql.connect(database)
    c = conn.cursor()
    c.execute("UPDATE settings SET flip = ? WHERE id = ?", (encoded_pulse_sign, settings[0]))
    conn.commit()
    conn.close()

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

    pulse_list_left = []
    pulse_list_right = []

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

                        print(f'Sample #{len(pulse_list)}')

                        # Break if enough pulses are collected
                        if len(pulse_list) >= shapecatches:
                            break

            # Check exit condition for loop
            if (len(pulse_list_left) >= shapecatches and (not stereo or len(pulse_list_right) >= shapecatches)):
                break

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

        # Save DataFrame to CSV, include index as the first column (row numbers)
        df.to_csv(shapecsv, index=True, index_label='Row')

    finally:
        # Clean up and close streams
        stream.stop_stream()
        stream.close()
        p.terminate()

    return pulses_sum_left, pulses_sum_right
