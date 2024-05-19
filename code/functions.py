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
import time
import os
import re
import platform
import threading
import sqlite3 as sql
import pandas as pd
import pulsecatcher as pc
import logging
import paramiko
import requests as req
import shproto.dispatcher
import serial.tools.list_ports

from dash import dash_table
from scipy.signal import find_peaks, peak_widths
from collections import defaultdict
from datetime import datetime
from urllib.request import urlopen
from shproto.dispatcher import process_03

logger          = logging.getLogger(__name__)
cps_list        = []
data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data")
run_flag_lock   = threading.Lock()
run_flag        = threading.Event() 

# Finds pulses in string of data over a given threshold
def find_pulses(left_channel):
    samples =[]
    pulses  = []
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
    normalised_int = [int(x) for x in normalised]
    return normalised_int

def get_serial_device_information():
    with shproto.dispatcher.command_lock:
        shproto.dispatcher.command = "-inf"
        logger.info("Sending '-inf' command to device")
    time.sleep(0.1)  

    with shproto.dispatcher.command_lock:  
        device_info = shproto.dispatcher.inf_str
        shproto.dispatcher.inf_str = ""
    return device_info

def parse_device_info(info_string):
    components = info_string.split()
    # Initialize a dictionary to hold the parsed settings
    settings = {}
    # Iterate over the components in pairs (step of 2)
    for i in range(0, len(components) - 1, 2):
        key = components[i]
        value = components[i + 1]
        # Attempt to convert numeric values, otherwise keep as string
        if value.replace('.', '', 1).isdigit() and value.count('.') < 2:
            # Convert to float if it contains a dot, indicating a decimal, otherwise to int
            converted_value = float(value) if '.' in value else int(value)
        else:
            # Keep as string for non-numeric values
            converted_value = value
        
        settings[key] = converted_value

    return settings    

    # Normalised pulse samples less normalised shape samples squared summed and rooted
def distortion(normalised, shape):
    product = [(x - y)**2 for x, y in zip(shape, normalised)]
    distortion = int(math.sqrt(sum(product)))

    return distortion
    # Function calculates pulse height
def pulse_height(samples):
    return max(samples)-min(samples)

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

# This function writes a 2D histogram to JSON file according to NPESv1 schema.
def write_histogram_json(t0, t1, bins, counts, elapsed, name, histogram, coeff_1, coeff_2, coeff_3):
    
    jsonfile = get_path(f'{data_directory}/{name}.json')

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
                        "validPulseCount":counts,
                        "measurementTime": elapsed,
                        "spectrum": histogram
                        }
                    }
                }

    with open(jsonfile, "w+") as f:
        json.dump(data, f, indent=4)


# This function writes a 2D histogram to JSON file according to NPESv1 schema.
def write_histogram_npesv2(t0, t1, bins, counts, elapsed, name, histogram, coeff_1, coeff_2, coeff_3, device, location, note):
    
    jsonfile = get_path(f'{data_directory}/{name}.json')

    data =  {"schemaVersion": "NPESv2",
              "data": [
                {
                  "deviceData": {
                    "softwareName": "IMPULSE",
                    "deviceName": "AUDIO-CODEC",
                  },
                  "sampleInfo": {
                    "name": name,
                    "location": location,
                    "note": note,
                  },
                  "resultData": {
                    "startTime": t0.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "endTime": t1.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "energySpectrum": {
                      "numberOfChannels": bins,
                      "energyCalibration": {
                        "polynomialOrder": 2,
                        "coefficients": [coeff_3,coeff_2,coeff_1],
                      },
                      "validPulseCount": counts,
                      "measurementTime": elapsed,
                      "spectrum": histogram
                    }
                  }
                }
              ]
            }

    with open(jsonfile, "w+") as f:
        json.dump(data, f, indent=4)        

# This function writes 3D intervals to NPESv1 JSON
def write_3D_intervals_json(t0, t1, bins, counts, elapsed, filename, interval_number, coeff_1, coeff_2, coeff_3):

    jsonfile = get_path(f'{data_directory}/{filename}_3d.json')
    
    if not os.path.isfile(jsonfile):
        data = {
            "schemaVersion": "NPESv1",
            "resultData": {
                "startTime": t0.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "endTime": t1.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "energySpectrum": {
                    "numberOfChannels": bins,
                    "energyCalibration": {
                        "polynomialOrder": 2,
                        "coefficients": [coeff_3, coeff_2, coeff_1]
                    },
                    "validPulseCount": 0,
                    "measurementTime": 0,
                    "spectrum":[]
                }
            }
        }
    else:
        with open(jsonfile, "r") as f:
            data = json.load(f)

    # Update the existing values
    data["resultData"]["energySpectrum"]["validPulseCount"] = counts
    data["resultData"]["energySpectrum"]["measurementTime"] = elapsed
    data["resultData"]["energySpectrum"]["spectrum"].extend([interval_number])  # Wrap intervals in a list

    with open(jsonfile, "w") as f:
        json.dump(data, f, indent=4)

# This function writes counts per second to json
def write_cps_json(filename, cps):
    global cps_list
    jsonfile = get_path(f'{data_directory}/{filename}-cps.json')
    cps_list.append(cps)
    data     = {'cps': cps_list }
    with open(jsonfile, "w+") as f:
        json.dump(data, f, indent=4)
 
# Clears global counts per second list   
def clear_global_cps_list():
    global cps_list
    cps_list = []

# This function loads settings from sqli database
def load_settings():

    database = get_path(f'{data_directory}/.data_v2.db')
    settings        = []
    conn            = sql.connect(database)
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 
    settings        = c.fetchall()[0]
    return settings

# This function opens the csv and loads the pulse shape  
def load_shape():
    shapecsv = get_path(f'{data_directory}/shape.csv')
    data_left = []
    data_right = []

    if os.path.exists(shapecsv):
        with open(shapecsv, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            for row in reader:
                data_left.append(row[1])   # Assuming the second column contains the left channel data
                data_right.append(row[2])  # Assuming the third column contains the right channel data

        # Converts 'string' to integers in data
        shape_left = [int(x) for x in data_left]
        shape_right = [int(x) for x in data_right]
                
        return shape_left, shape_right
    else:
        # Returns default shapes of zeros if file doesn't exist
        default_length = 51  # Modify this number if a different default length is required
        return ([0] * default_length, [0] * default_length)


# Function extracts keys from dictionary
def extract_keys(dict_, keys):
    return {k: dict_.get(k, None) for k in keys}

# This function terminates the audio connection
def refresh_audio_device_list():
    try:
        p = pyaudio.PyAudio()
        p.terminate()
        time.sleep(1)
        return
    except:
        return

# Function to query settings database 
def get_device_number():
    database = get_path(f'{data_directory}/.data_v2.db')
    conn            = sql.connect(database)
    c               = conn.cursor()
    query           = "SELECT * FROM settings "
    c.execute(query) 
    settings        = c.fetchall()[0]
    device          = settings[2]
    return device

# This function gets a list of audio device_list connected to the computer           
def get_device_list():
    refresh_audio_device_list()
    p = pyaudio.PyAudio()
    try:
        device_count = p.get_device_count()
        input_device_list = [
            (p.get_device_info_by_index(i)['name'], p.get_device_info_by_index(i)['index'])
            for i in range(device_count)
            if p.get_device_info_by_index(i)['maxInputChannels'] >= 1
        ]
        p.terminate()
        return input_device_list
    except:
        p.terminate()
        return [('no device', 99)]

def get_serial_device_list():
    # Get a list of available serial ports
    all_ports = serial.tools.list_ports.comports()

    # Define criteria for selecting serial devices
    manufacturer_criteria = "FTDI"
    #product_criteria = "FT232R USB UART"

    # Create a list of tuples to store selected serial device information as couples
    serial_device_list = []

    # Filter and assign unique integer indexes to selected serial devices starting from 100
    serial_index = 100
    for port in all_ports:
        if 1 or port.manufacturer == manufacturer_criteria:
            serial_device_list.append((port.device, serial_index))
            serial_index += 1
    return serial_device_list
         
# Returns maxInputChannels in an unordered list
def get_max_input_channels(device):
    p = pyaudio.PyAudio()
    channels = p.get_device_info_by_index(device)['maxInputChannels']
    return channels

# Function to open browser on localhost
def open_browser(port):
    webbrowser.open_new("http://localhost:{}".format(port))    
    return

def create_dummy_csv(filepath):
    with open(filepath, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for i in range(0, 50):
            writer.writerow([i, 0,0])
 
# Function to automatically switch between positive and negative pulses
def detect_pulse_direction(samples):
    if max(samples) >= 3000:
        return 1
    if min(samples) <= -3000:
        return -1
    else:
        return 0

def get_path(filename):
    name, ext = os.path.splitext(filename)

    if platform.system() == "Darwin":
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        file = os.path.join(bundle_dir, f"{name}{ext}")
        return file if os.path.exists(file) else os.path.realpath(filename)
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
    peaks, _ = find_peaks(y_bin, prominence=prominence, distance = 40)
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


def gaussian_correl(data, sigma):
    correl_values = []
    data_len = len(data)
    std = math.sqrt(data_len)
    x_max = round(sigma * std)
    gauss_values = [math.exp(-(k**2) / (2 * std**2)) for k in range(-x_max, x_max)]
    avg = sum(gauss_values) / len(gauss_values)

    for index in range(data_len):
        result_val = 0
        for k in range(-x_max, x_max):
            idx = index + k
            if 0 <= idx < data_len:
                result_val += data[idx] * (gauss_values[k + x_max] - avg)

        value = max(0, result_val)
        correl_values.append(int(value))

    max_data = max(data)
    max_correl_value = max(correl_values)
    scaling_factor = 0.8 * max_data / max_correl_value
    correl_values = [int(value * scaling_factor) for value in correl_values]

    return correl_values

def start_recording(mode):
    global run_flag
    # Start the thread
    run_flag.set()  # Set the Event to indicate recording should start
    audio_record = threading.Thread(target=pc.pulsecatcher, args=(mode, run_flag, run_flag_lock))
    audio_record.start()
    clear_global_cps_list()
    logger.info(f'Recording started in mode {mode}')
    return

def stop_recording():
    global run_flag
    with run_flag_lock:
        run_flag.clear() 
    logger.info('Recording stopped')    
    return    

def export_csv(filename):
    # Get the path to the user's download folder
    download_folder = os.path.expanduser("~/Downloads")
    # Remove the ".json" extension from the filename
    base_filename = filename.rsplit(".", 1)[0]
    # Give output file a name
    output_file = f'{base_filename}.csv'
    # Load json file
    with open(f'{data_directory}/{filename}') as f:
        data = json.load(f)

    if data["schemaVersion"]  == "NPESv2":
        data = data["data"][0] # This makes it backwards compatible

    # Extract data from json file
    spectrum     = data["resultData"]["energySpectrum"]["spectrum"]
    coefficients = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
    # Make sure coefficient[2] is not negative
    if coefficients[2] <= 0:
        coefficients[2] = 0
    # Open file in Download directory
    with open(os.path.join(download_folder, output_file), "w", newline="") as f:
        # Write to file
        writer = csv.writer(f)
        # Write heading row
        writer.writerow(["bin", "counts"])
        # Write each row
        for i, value in enumerate(spectrum):
            # Calculate energies
            e = round((i**coefficients[2] + i*coefficients[1]+coefficients[0]),2)
            writer.writerow([e, value])   
    return

def update_coeff(filename, coeff_1, coeff_2, coeff_3):
    with open(f'{data_directory}/{filename}.json') as f:
        data = json.load(f)

    if data["schemaVersion"]  == "NPESv1":
        coefficients    = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
        coefficients[0] = coeff_3
        coefficients[1] = coeff_2
        coefficients[2] = coeff_1

    elif data["schemaVersion"]  == "NPESv2":
        coefficients    = data["data"][0]["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
        coefficients[0] = coeff_3
        coefficients[1] = coeff_2
        coefficients[2] = coeff_1

    with open(f'{data_directory}/{filename}.json', 'w') as f:
        json.dump(data, f, indent=4)

    return

# removes the path from serial device list Mac only
def cleanup_serial_options(options):
    prefix_to_remove = '/dev/cu.usbserial-'
    for item in options:
        if 'label' in item and item['label'].startswith(prefix_to_remove):
            item['label'] = 'Serial # ' + item['label'][len(prefix_to_remove):]

    return options    

def get_api_key(): # Fetch api_key from table user

    try:
        database    = get_path(f'{data_directory}/.data_v2.db')
        conn        = sql.connect(database)
        c           = conn.cursor()
        query       = "SELECT api_key FROM user LIMIT 1"
        # Carry out query
        c.execute(query)
        # assign api_key
        api_key = c.fetchone() 
        # return result
        return api_key[0] if api_key else None

    except Exception as e:
        print(f"code/functions/get_api_key() failed: {e}")
        return None

    finally:
        conn.close()

def publish_spectrum(filename):

    logger.info(f'Publish button clicked for {filename}')
    # routing address
    url = "https://gammaspectacular.com/spectra/publish_spectrum"

    # gets client api
    api_key = get_api_key()

    logger.info(f'Api key obtained {api_key}')

    # local file directory
    spectrum_file_path = f'{data_directory}/{filename}.json'

    # Prepare the file and data payload for the POST request
    try:
        with open(spectrum_file_path, 'rb') as file:

            files = {'file': (filename, file)}
            data  = {'api_key': api_key}
            
            # Sending a POST request to the server
            response = req.post(url, files=files, data=data)

            # Handle successful response
            if response.status_code == 200:

                logger.info(f'{filename} Published ok')

                return f'{filename}\npublished:\n{response}'

            # Handle error in response
            else:
                logger.info(f'code/functions/publish_spectrum {response.text}')
                return f'Error from /code/functions/publish_spectrum: {response.text}'

    # Handle request exception
    except req.exceptions.RequestException as e:
        return f'code/functions/publish_spectrum: {e}'

    except FileNotFoundError:
        logger.info(f'Error from /code/functions/publish_spectrum: {spectrum_file_path}')
        return f'Error from /code/functions/publish_spectrum: {spectrum_file_path}'

    except Exception as e:
        logger.info(f'Error from /code/functions/publish_spectrum: {e}')
        return f'Error from /code/functions/publish_spectrum: {e}'

def update_json_notes(filename, spec_notes):

    try:
        with open(f'{data_directory}/{filename}.json') as f:
            data = json.load(f)

        if data["schemaVersion"]  == "NPESv2":
            
            data["data"][0]["sampleInfo"]["note"] = spec_notes

        else:
            return "Wrong file format"    
            
        with open(f'{data_directory}/{filename}.json', 'w') as f:
            json.dump(data, f, indent=4)

        return "Spec notes Written"

    except Exception as e:

        logger.info(f'Error in /code/functions.update_json_notes {e}')

def get_spec_notes(filename):

    try:
        with open(f'{data_directory}/{filename}.json') as f:
            data = json.load(f)

        if data["schemaVersion"]  == "NPESv2":
            spec_notes = data["data"][0]["sampleInfo"]["note"]

        return spec_notes

    except:
        
        return 'Not writing'    

def fetch_json(file_id):
    url = f'https://www.gammaspectacular.com/spectra/files/{file_id}.json'
    
    try:
        response = req.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)
        
        if response.status_code == 200:
            return response.json()  # Returns the JSON content of the response
        else:
            return None  # Handle unexpected status codes as needed
    except req.exceptions.RequestException as e:
        print(f"Error fetching JSON: {e}")
        return None  # Handle network or request-related errors     

def execute_serial_command(input_cmd):

    with shproto.dispatcher.command_lock:
        shproto.dispatcher.command = input_cmd
        logger.info(f"Sending command {input_cmd} to device")

        return

def generate_device_settings_table():

    shproto.dispatcher.spec_stopflag = 0
    dispatcher = threading.Thread(target=shproto.dispatcher.start)  
    dispatcher.start()

    time.sleep(0.1)

    dev_info = get_serial_device_information()

    info_dict   = parse_device_info(dev_info)

    # Assuming parsed_settings is your dictionary from the previous step
    version     = info_dict.get('VERSION')
    rise        = info_dict.get('RISE')
    fall        = info_dict.get('FALL')
    noise       = info_dict.get('NOISE')
    frequency   = info_dict.get('F')
    max_value   = info_dict.get('MAX')
    hysteresis  = info_dict.get('HYST')
    mode        = info_dict.get('MODE')
    step        = info_dict.get('STEP')
    temperature = info_dict.get('t')
    pot1        = info_dict.get('POT')
    pot2        = info_dict.get('POT2')
    t1_status   = info_dict.get('T1')
    t2_status   = info_dict.get('T2')
    t3_status   = info_dict.get('T3')
    prise       = info_dict.get('Prise')
    srise       = info_dict.get('Srise')
    output      = info_dict.get('OUT')
    pfall       = info_dict.get('Pfall')
    sfall       = info_dict.get('Sfall')
    tc_status   = info_dict.get('TC')
    tcpot_status= info_dict.get('TCpot')
    tco         = info_dict.get('Tco')
    tp          = info_dict.get('TP')
    pileup      = info_dict.get('PileUp')
    pileup_thr  = info_dict.get('PileUpThr')

    process_03('-cal')

    serial      = shproto.dispatcher.serial_number


    table = dash_table.DataTable(
        columns=[
            {"id": "Setting", "name": "Firmware settings"},
            {"id": "cmd", "name": "Command"},
            {"id": "Value", "name": "Value"}
        ],
        data=[
            {"Setting": "Version", "cmd":"-", "Value": version},
            {"Setting": "Serial number", "cmd":"status", "Value": serial},
            {"Setting": "Samples for X (pulse rise)", "cmd":"-ris", "Value": rise},
            {"Setting": "Samples for Y (pulse fall)", "cmd":"-fall", "Value": fall},
            {"Setting": "Lower Limit Discriminator LLD", "cmd":"-nos", "Value": noise},
            {"Setting": "ADC Sample Frequency", "cmd":"-frq", "Value": frequency},
            {"Setting": "Max integral value", "cmd":"-max", "Value": max_value},
            {"Setting": "Hysteresis value", "cmd":"-hyst", "Value": hysteresis},
            {"Setting": "Working Mode [0, 1, 2]", "cmd":"-mode", "Value": mode},
            {"Setting": "Discriminator step (>1)", "cmd":"-step", "Value": step},
            {"Setting": "High Voltage (0-255)", "cmd":"-U", "Value": pot1},
            {"Setting": "Baseline trim (0-255)", "cmd":"-V", "Value": pot2},
            {"Setting": "Temperature sensor 1", "cmd":"status", "Value": f"{t1_status} C˚"},
            {"Setting": "Energy Window (-win X1 X2)", "cmd":"-win", "Value": output},
            #{"Setting": "Pulse Pile Up (PPU) rise", "Value": pfall},
            #{"Setting": "Pulse Pile Up (PPU) fall", "Value": sfall},
            {"Setting": "Temp. compensation status", "cmd":"status", "Value": tcpot_status},
            {"Setting": "Temp. compensation table", "cmd":"status", "Value": tco},
            #{"Setting": "Time between integral", "Value": tp},
        ],
        style_cell={
            'textAlign': 'left',
            'padding': '4px',  
            'fontSize': '12px',  
            'fontFamily': 'Arial'  
        },
        style_cell_conditional=[
            {'if': {'column_id': 'Setting'}, 'width': '60%'},
            {'if': {'column_id': 'cmd'}, 'width':'10%'},
            {'if': {'column_id': 'Value'}, 'width': '30%'}
        ]
    )

    return table

# Check if commands sent to processor is safe 
def allowed_command(cmd):

    allowed_command_patterns = [
    r"^-U[0-9]{1,3}$",  # Matches -U followed by up to three digits (0-255)
    r"^-V[0-9]{1,3}$",  
    r"^-sto$",
    r"^-nos[0-9]{1,3}$" 
    ]    

    secret_prefix = "+"

    if cmd is None or not isinstance(cmd, str):
        return False

    if cmd.startswith("+"):
        return True

    for pattern in allowed_command_patterns:
        if re.match(pattern, cmd):
            return True 

    return False

def is_valid_json(file_path):
    try:
        with open(file_path, 'r') as f:
            data = f.read()
            if not data.strip():
                return False
            json.loads(data)
        return True
    except (json.JSONDecodeError, FileNotFoundError):
        return False