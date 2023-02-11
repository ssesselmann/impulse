# Reads data in CHUNK and looks for pulse peaks in position 26 of a 51 number array
# Repeats x times
# Calculates zip average
import pyaudio
import webbrowser
import wave
import numpy as np
import math
import csv
import json
import os
import sqlite3 as sql
import pandas as pd
from collections import defaultdict
from datetime import datetime


# Finds pulses in string of data over a given threshold
def find_pulses(left_channel):
    samples =[]
    pulses = []
    for i in range(len(left_channel) - 51):
        samples = left_channel[i:i+51]  # Get the first 51 samples
        if samples[25] >= max(samples) and (max(samples)-min(samples)) > 100 and samples[25] < 32768:
            pulses.append(samples)
    if len(pulses) != 0:  # If the list is empty
        next       
    return pulses   

# Calculates the average pulse shape
def average_pulse(sum_pulse, count):       
    average = []
    for x in sum_pulse:
        average.append(x / count)
    return average 

    # Normalises the average pulse shape
def normalise_pulse(average):
    normalised = []
    mean = sum(average) / len(average)   
    normalised = [n - mean for n in average]  
    # Converts normalised to integers
    normalised_int = [int(x) for x in normalised]
    # print(normalised)
    return normalised_int

    # Normalised pulse samples less normalised shape samples squared summed and rooted
def distortion(normalised, shape):
    product = [(x - y)**2 for x, y in zip(shape, normalised)]
    distortion = int(math.sqrt(sum(product)))

    return distortion

def pulse_height(passed):
    peak = passed[passed.index(max(passed))]
    trough = passed[passed.index(min(passed))]
    height = int(peak-trough)
    return height

    # Function to create bin_array 
def create_bin_array(start, stop, bin_size):
    return np.arange(start, stop, bin_size)

def histogram_count(n, bins):
    # find the bin for the input number
    for i in range(len(bins)):
        if n < bins[i]:
            bin_num = i
            break
    else:
        bin_num = len(bins)
    return bin_num

    #Function to bin pulse height
def update_bin(n, bins, bin_counts):
    bin_num = histogram_count(n, bins)
    bin_counts[bin_num] += 1
    return bin_counts

# This function writes histogram to JSON file according to NPESv1 schema.
def write_histogram_json(t0, t1, bins, n, elapsed, name, histogram, coeff_1, coeff_2, coeff_3):
    
    jsonfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', f"{name}.json")

    data =  {"schemaVersion":"NPESv1",
                "resultData":{
                    "startTime": t0.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "endTime": t1.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "energySpectrum":{
                        "numberOfChannels":bins,
                        "energyCalibration":{
                            "polynomialOrder":2,
                            "coefficients":[coeff_3,coeff_2,coeff_1]
                            },
                        "validPulseCount":n,
                        "measurementTime": elapsed,
                        "spectrum": histogram
                        }
                    }
                }

    with open(jsonfile, "w+") as f:
        json.dump(data, f)
     
# This function loads settings from sqli database
def load_settings():

    database = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data.db")
    settings        = []
    conn            = sql.connect(database)
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 
    settings        = c.fetchall()[0]
    return settings

# This function opens the csv and loads the pulse shape  
def load_shape():

    shapecsv = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'shape.csv')
   
    data = []
    if os.path.exists(shapecsv):
        with open(shapecsv, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                data.append(row[1])
                shape = [int(x) for x in data] #converts 'string' to integers in data
        return shape  
    else:
        shape = pd.DataFrame(data = {'Shape': [0]*51})   
        return shape 

# This function gets a list of audio devices connected to the computer           
def get_device_list():
    input_devices = []
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    for i in range(device_count):
        longrow = p.get_device_info_by_index(i)
        shortrow = extract_keys(longrow.copy(), ['index', 'name', 'maxInputChannels', 'maxOutputChannels', 'defaultSampleRate'])
        input_devices.append(shortrow)
    return input_devices

# Function extracts keys from dictionary
def extract_keys(dict_, keys):
    return {k: dict_.get(k, None) for k in keys}

# This function terminates the audio connection
def refresh_audio_devices():
    p = pyaudio.PyAudio()
    p.terminate()
    return

# Function to open browser on localhost
def open_browser(port):
    webbrowser.open_new("http://localhost:{}".format(port))    
    return

def create_dummy_csv(filepath):
    with open(filepath, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for i in range(0, 50):
            writer.writerow([i, 0])
 
# Function to automatically switch between positive and negative pulses
def detect_pulse_direction(samples):
    database = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data.db")
    if max(samples) >= 3000:
        conn = sql.connect(database)
        c = conn.cursor()
        query = f"UPDATE settings SET flip = 1 WHERE id=0;"
        c.execute(query)
        conn.commit()
        return 1

    if min(samples) <= -3000:
        conn = sql.connect(database)
        c = conn.cursor()
        query = f"UPDATE settings SET flip = -1 WHERE id=0;"
        c.execute(query)
        conn.commit()
        return -1
    else:
        return 0

