import pyaudio
import wave
import csv
import os
import time
import functions as fn
import sqlite3 as sql
import pandas as pd
import numpy as np
import logging
from collections import defaultdict
from functions import get_path

# Setup logging
logger = logging.getLogger(__name__)



# Define the directory where data files are stored
data_directory = os.path.join(os.path.expanduser("~"), "impulse_data")

def shapecatcher():
    # Connect to the database and get settings
    database = get_path(f'{data_directory}/.data_v2.db')

    shapecsv = get_path(f'{data_directory}/shape.csv')

    conn = sql.connect(database)
    c = conn.cursor()
    c.execute("SELECT * FROM settings")
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
    shapecatches    = settings[10]
    sample_length   = settings[11]
    peakshift       = settings[28]
    peak            = int((sample_length-1)/2) + peakshift

    print("selected device", device)

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                    channels=2,
                    rate=sample_rate,
                    input=True,
                    output=False,
                    frames_per_buffer=chunk_size * 2,
                    input_device_index=device)
 
    pulse_list_left  = []
    pulse_list_right = []

    right_channel_active = False

    try:
        while True:

            data = stream.read(chunk_size, exception_on_overflow=False)

            values = list(wave.struct.unpack("%dh" % (chunk_size * 2), data))

            left_channel = values[::2]

            right_channel = values[1::2]

            # Process each channel to detect pulses
            for channel, pulse_list in zip([left_channel, right_channel], [pulse_list_left, pulse_list_right]):

                for i in range(len(channel) - sample_length):

                    samples = channel[i:i + sample_length]

                    if (max(samples) - min(samples) > threshold and

                        samples[peak] == max(samples)):

                        pulse_list.append(samples)
                        # Mark right channel as active if pulses are detected
                        if channel == right_channel:

                            right_channel_active = True
                        # Break if enough pulses are collected
                        if len(pulse_list) >= shapecatches:
                            break

            # Check exit condition for loop
            if (len(pulse_list_left) >= shapecatches and (len(pulse_list_right) >= shapecatches or (not right_channel_active and len(pulse_list_right) == 0))):
                break

        # If the right channel had no activity, fill with zero-filled lists
        if not right_channel_active:
            # Create a list of zero-filled lists, each representing a pulse
            pulse_list_right = [[0] * sample_length for _ in range(shapecatches)]
          # Zeroes based on sample_length and shapecatches

        # Calculate average pulses
        pulses_sum_left = [int(sum(x) / len(x)) for x in zip(*pulse_list_left)] if pulse_list_left else []
        pulses_sum_right = [int(sum(x) / len(x)) for x in zip(*pulse_list_right)] if pulse_list_right else []


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