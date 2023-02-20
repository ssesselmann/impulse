# Reads data in CHUNK and looks for pulse peaks in position 26 of a 51 number array
# Repeats x times
# Calculates zip average
import pyaudio
import webbrowser
import wave
import numpy as np
import subprocess
import math
import csv
import json
import os
import platform
import sqlite3 as sql
import pandas as pd
from scipy.signal import find_peaks, peak_widths
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
    
    jsonfile = get_path(f'data/{name}.json')

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

    database = get_path('data.db')
    settings        = []
    conn            = sql.connect(database)
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 
    settings        = c.fetchall()[0]
    return settings

# This function opens the csv and loads the pulse shape  
def load_shape():

    shapecsv = get_path('data/shape.csv')
   
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

# Function extracts keys from dictionary
def extract_keys(dict_, keys):
    return {k: dict_.get(k, None) for k in keys}

# This function terminates the audio connection
def refresh_audio_devices():
    try:
        p = pyaudio.PyAudio()
        p.terminate()
        time.sleep(1)
        return
    except:
        return

# This function gets a list of audio devices connected to the computer           
def get_device_list():
    refresh_audio_devices()
    input_devices = [{'index': 99, 'name': 'device name', 'maxInputChannels': 99, 'maxOutputChannels': 99, 'defaultSampleRate': 99}]
    p = pyaudio.PyAudio()
    try:
        device_count = p.get_device_count()
        input_devices = [extract_keys(p.get_device_info_by_index(i), ['index', 'name', 'maxInputChannels', 'maxOutputChannels', 'defaultSampleRate']) for i in range(device_count) if p.get_device_info_by_index(i)['maxInputChannels'] >= 1]
        return input_devices
    except:
        return[99,'no device', 99, 99, 99]     

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
    if max(samples) >= 3000:
        return 1
    if min(samples) <= -3000:
        return -1
    else:
        return 0

def get_path(filename):
    name = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]

    if platform.system() == "Darwin":
        from AppKit import NSBundle
        file = NSBundle.mainBundle().pathForResource_ofType_(name, ext)
        return file or os.path.realpath(filename)
    else:
        return os.path.realpath(filename)

def restart_program():
    subprocess.Popen(['python', 'app.py'])
    return

def shutdown():
    print('Shutting down server...')
    os._exit(0)

def peakfinder(y_values, prominence, min_width):
    # y * bin to give higher value toweards the right
    y_bin = [y * i for i, y in enumerate(y_values)]
    # Find all peaks of prominence
    peaks, _ = find_peaks(y_bin, prominence=prominence)
    # Get the fwhm for all foundpeaks
    widths, _, _, _ = peak_widths(y_values, peaks, rel_height=0.5)
    # Filter out peaks where width >= min-width
    filtered_peaks = [p for i, p in enumerate(peaks) if widths[i] >= min_width * i]
    # Define array
    fwhm = []
    # Get widths of filtered_peaks
    for i in range(len(filtered_peaks)):
        w, _, _, _ = peak_widths(y_values, [filtered_peaks[i]], rel_height=0.5)
        w = np.round(w,1)
        fwhm.append(w[0])
    return filtered_peaks, fwhm


