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

peak = 0.0
trough = 0.0
height = 0.0
p = pyaudio.PyAudio()


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
    #print("pass ",passed)  
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

    with open(f"../data/{name}.json", "w+") as f:
        json.dump(data, f)
     
# This function loads settings from sqli database
def load_settings():
    settings        = []
    conn            = sql.connect("data.db")
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 
    settings        = c.fetchall()[0]
    return settings

# This function opens the csv and loads the pulse shape  
def load_shape():
    data = []
    if os.path.exists('../data/shape.csv'):
        with open('../data/shape.csv', 'r') as f:
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
    device_info = p.get_host_api_info_by_index(0).get('deviceCount')
    for i in range(device_info):
        input_devices.append(p.get_device_info_by_host_api_device_index(0, i).copy())
    return input_devices

# This function terminates the audio connection
def refresh_audio_devices():
    p = pyaudio.PyAudio()
    p.terminate()
    return

# Function to open browser on localhost
def open_browser(port):
    webbrowser.open_new("http://localhost:{}".format(port))    
    return
