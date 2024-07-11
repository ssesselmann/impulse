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
import glob
import paramiko
import requests as req
import shproto.dispatcher
import serial.tools.list_ports
import global_vars

from pulsecatcher import pulsecatcher
from dash import dash_table
from scipy.signal import find_peaks, peak_widths
from collections import defaultdict
from datetime import datetime
from urllib.request import urlopen
from shproto.dispatcher import process_03

logger          = logging.getLogger(__name__)
cps_list        = []
data_directory  = global_vars.data_directory

# Finds pulses in string of data over a given threshold
def find_pulses(left_channel):

    pulses = []

    for i in range(len(left_channel) - 51):
        samples = left_channel[i:i + 51]  # Get the first 51 samples
        if samples[25] >= max(samples) and (max(samples) - min(samples)) > 100 and samples[25] < 32768:
            pulses.append(samples)
    return pulses

# Calculates the average pulse shape
def average_pulse(sum_pulse, count):
    return [x / count for x in sum_pulse]

# Normalizes the average pulse shape
def normalise_pulse(average):
    mean = sum(average) / len(average)
    normalised = [int(n - mean) for n in average]
    return normalised

def get_serial_device_information():
    with shproto.dispatcher.command_lock:
        shproto.dispatcher.command = "-inf"
        logger.info("Sending '-inf' command to device\n")
    time.sleep(0.1)

    with shproto.dispatcher.command_lock:
        device_info = shproto.dispatcher.inf_str
        shproto.dispatcher.inf_str = ""
    return device_info

def parse_device_info(info_string):
    components = info_string.split()
    settings = {}
    for i in range(0, len(components) - 1, 2):
        key = components[i]
        value = components[i + 1]
        if value.replace('.', '', 1).isdigit() and value.count('.') < 2:
            converted_value = float(value) if '.' in value else int(value)
        else:
            converted_value = value
        settings[key] = converted_value
    return settings

# Normalized pulse samples less normalized shape samples squared summed and rooted
def distortion(normalised, shape):
    product = [(x - y) ** 2 for x, y in zip(shape, normalised)]
    return int(math.sqrt(sum(product)))

# Function calculates pulse height
def pulse_height(samples):
    return max(samples) - min(samples)

# Function to create bin_array
def create_bin_array(start, stop, bin_size):
    return np.arange(start, stop, bin_size)

def histogram_count(n, bins):
    for i in range(len(bins)):
        if n < bins[i]:
            return i
    return len(bins)

# Function to bin pulse height
def update_bin(n, bins, bin_counts):
    bin_num = histogram_count(n, bins)
    bin_counts[bin_num] += 1
    return bin_counts


# This function writes a 2D histogram to JSON file according to NPESv2 schema.
def write_histogram_npesv2(t0, t1, bins, counts, elapsed, filename, histogram, coeff_1, coeff_2, coeff_3, device, location, spec_notes):
    jsonfile = get_path(os.path.join(global_vars.data_directory, f'{filename}.json'))
    data = {
        "schemaVersion": "NPESv2",
        "data": [
            {
                "deviceData": {
                    "softwareName": "IMPULSE",
                    "deviceName": "AUDIO-CODEC",
                },
                "sampleInfo": {
                    "name": filename,
                    "location": location,
                    "note": spec_notes,
                },
                "resultData": {
                    "startTime": t0.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "endTime": t1.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                    "energySpectrum": {
                        "numberOfChannels": bins,
                        "energyCalibration": {
                            "polynomialOrder": 2,
                            "coefficients": [coeff_3, coeff_2, coeff_1],
                        },
                        "validPulseCount": counts,
                        "measurementTime": elapsed,
                        "spectrum": histogram,
                    }
                }
            }
        ]
    }
    with open(jsonfile, "w+") as f:
        json.dump(data, f, separators=(',', ':'))


# Function to create a blank JSON NPESv2 schema filename_3d.json
def write_blank_json_schema(filename, device):
    jsonfile = get_path(f'{global_vars.data_directory}/{filename}_3d.json')
    data = {
        "schemaVersion": "NPESv2",
        "data": [
            {
                "deviceData": {
                    "softwareName": "IMPULSE",
                    "deviceName": device
                },
                "sampleInfo": {
                    "name": filename,
                    "location": "",
                    "note": ""
                },
                "resultData": {
                    "startTime": "",
                    "endTime": "",
                    "energySpectrum": {
                        "numberOfChannels": 0,
                        "energyCalibration": {
                            "polynomialOrder": 2,
                            "coefficients": []
                        },
                        "validPulseCount": 0,
                        "measurementTime": 0,
                        "spectrum": []
                    }
                }
            }
        ]
    }
    
    try:
        with open(jsonfile, "w") as f:
            json.dump(data, f, separators=(',', ':'))
        logger.info(f"Blank JSON schema created: {jsonfile}\n")
    except Exception as e:
        logger.error(f"Error writing blank JSON file: {e}\n")


# Function to update keys and append histogram
def update_json_3d_file(t0, t1, bins, counts, elapsed, filename, last_histogram, coeff_1, coeff_2, coeff_3, device):
    
    jsonfile = get_path(os.path.join(global_vars.data_directory, f'{filename}_3d.json'))
    
    # Check if the file exists
    if not os.path.isfile(jsonfile):
        logger.info(f"JSON file does not exist, creating new file: {jsonfile}\n")
        
        data = {
                "schemaVersion": "NPESv2",
                "data": [
                    {
                        "deviceData": {
                            "softwareName": "IMPULSE",
                            "deviceName":device
                        },
                        "sampleInfo": {
                            "name":filename,
                            "location": "",
                            "note": ""
                        },
                        "resultData": {
                            "startTime":t0.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                            "endTime":t1.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                            "energySpectrum": {
                                "numberOfChannels":bins,
                                "energyCalibration": {
                                    "polynomialOrder": 2,
                                    "coefficients":[coeff_3, coeff_2, coeff_1]
                                },
                                "validPulseCount":counts,
                                "measurementTime":elapsed,
                                "spectrum":last_histogram,
                            }
                        }
                    }
                ]
            }
        
        try:
            with open(jsonfile, "w+") as f:
                json.dump(data, f, separators=(',', ':'))
            logger.info(f"New JSON 3D file created: {jsonfile}\n")
        except Exception as e:
            logger.error(f"Error writing new JSON file: {e}\n")
        return
    
    # If file exists, update the existing data
    try:
        with open(jsonfile, "r") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON file: {e}\n")
        return
    
    # Update the necessary fields
    result_data = data["data"][0]["resultData"]
    result_data["startTime"] = t0.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    result_data["endTime"] = t1.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    result_data["energySpectrum"]["numberOfChannels"] = bins
    result_data["energySpectrum"]["energyCalibration"]["coefficients"] = [coeff_3, coeff_2, coeff_1]
    result_data["energySpectrum"]["validPulseCount"] = counts
    result_data["energySpectrum"]["measurementTime"] = elapsed
    result_data["energySpectrum"]["spectrum"].append(last_histogram)
    
    try:
        with open(jsonfile, "w") as f:
            json.dump(data, f, separators=(',', ':'))
        logger.info(f"JSON 3D file updated: {jsonfile}")
    except Exception as e:
        logger.error(f"Error writing JSON file: {e}")



# This function writes counts per second to JSON
def write_cps_json(filename, count_history, elapsed):

    data_directory = global_vars.data_directory
    cps_file_path = os.path.join(data_directory, f"{filename}_cps.json")
    # Ensure count_history is a flat list of integers
    valid_count_history = [int(item) for sublist in count_history for item in (sublist if isinstance(sublist, list) else [sublist]) if isinstance(item, int) and item >= 0]
    cps_data = {
        "count_history": valid_count_history,
        "elapsed": elapsed
    }
    try:
        with open(cps_file_path, 'w') as file:
            json.dump(cps_data, file, separators=(',', ':'))
    except Exception as e:
        logger.error(f"Error saving CPS data to {cps_file_path}: {e}\n")
     
    return    

# Clears global counts per second list
def clear_global_cps_list():
    with global_vars.write_lock:
        global_vars.counts = 0
        global_vars.count_history = []


# This function opens the CSV and loads the pulse shape
def load_shape():
    shapecsv = global_vars.shapecsv
    data_left = []
    data_right = []
    if os.path.exists(shapecsv):
        with open(shapecsv, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            for row in reader:
                data_left.append(row[1])  # Assuming the second column contains the left channel data
                data_right.append(row[2])  # Assuming the third column contains the right channel data
        shape_left = [int(x) for x in data_left]
        shape_right = [int(x) for x in data_right]
        return shape_left, shape_right
    else:
        default_length = 51
        return ([0] * default_length, [0] * default_length)

# Function extracts keys from dictionary
def extract_keys(dict_, keys):
    return {k: dict_.get(k, None) for k in keys}

# This function terminates the audio connection
def refresh_audio_device_list():
    try:
        p = pyaudio.PyAudio()
        p.terminate()
        time.sleep(0.1)
    except:
        pass

# Function to query settings database
def get_device_number():
    
    return global_vars.device

# This function gets a list of audio devices connected to the computer
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
    all_ports = serial.tools.list_ports.comports()
    manufacturer_criteria = "FTDI"
    serial_device_list = []
    serial_index = 100
    for port in all_ports:
        if port.manufacturer == manufacturer_criteria:
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

def create_dummy_csv(filepath):
    with open(filepath, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for i in range(50):
            writer.writerow([i, 0, 0])

# Function to automatically switch between positive and negative pulses
def detect_pulse_direction(samples):
    if max(samples) >= 3000:
        return 1
    if min(samples) <= -3000:
        return -1
    return 0

def get_path(filename):
    name, ext = os.path.splitext(filename)
    if platform.system() == "Darwin":
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        file = os.path.join(bundle_dir, f"{name}{ext}")
        return file if os.path.exists(file) else os.path.realpath(filename)
    return os.path.realpath(filename)

def restart_program():
    subprocess.Popen(['python', 'app.py'])

def shutdown():
    logger.info('Shutting down server...\n')
    os._exit(0)

def peak_finder(y_values, prominence, min_width):
    y_bin = [y * i for i, y in enumerate(y_values)]
    peaks, _ = find_peaks(y_bin, prominence=prominence, distance=40)
    widths, _, _, _ = peak_widths(y_values, peaks, rel_height=0.5)
    filtered_peaks = [p for i, p in enumerate(peaks) if widths[i] >= min_width * i]
    fwhm = [round(peak_widths(y_values, [p], rel_height=0.5)[0][0], 1) for p in filtered_peaks]
    return filtered_peaks, fwhm

def gaussian_correl(data, sigma):
    correl_values = []
    data_len = len(data)
    std = math.sqrt(data_len)
    x_max = round(sigma * std)
    gauss_values = [math.exp(-(k ** 2) / (2 * std ** 2)) for k in range(-x_max, x_max)]
    avg = sum(gauss_values) / len(gauss_values)
    for index in range(data_len):
        result_val = 0
        for k in range(-x_max, x_max):
            idx = index + k
            if 0 <= idx < data_len:
                result_val += data[idx] * (gauss_values[k + x_max] - avg)
        correl_values.append(max(0, int(result_val)))
    max_data = max(data)
    max_correl_value = max(correl_values)
    scaling_factor = 0.8 * max_data / max_correl_value if max_correl_value != 0 else 1
    return [int(value * scaling_factor) for value in correl_values]

def handle_modal_confirmation(start_clicks, confirm_clicks, cancel_clicks, filename, is_open, suffix=''):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id.startswith("start"):
        file_exists = os.path.exists(f'{global_vars.data_directory}/{filename}{suffix}.json')

        if file_exists:
            return True, f'Overwrite "{filename}{suffix}"?'

    elif button_id in ["confirm-overwrite-tab3", "cancel-overwrite-tab3"]:
        return False, ''

    return False, ''


def start_recording(mode):

    logger.info(f'functions start_recording({mode})\n')

    with global_vars.write_lock:
        filename = global_vars.filename
        global_vars.run_flag.clear()

    clear_global_vars(mode)

    write_cps_json(filename, [[0]], 0)

    with global_vars.run_flag_lock:
        global_vars.run_flag.set()  # Set the run flag
        logger.info(f"Recording started in mode {mode}.\n")

    if mode == 2:
        # Start 2D spectrum recording logic
        logger.info("Starting 2D spectrum recording...\n")
        try:
            if callable(pulsecatcher):
                thread = threading.Thread(target=pulsecatcher, args=(2, global_vars.run_flag, global_vars.run_flag_lock))
                thread.start()
                logger.info("2D spectrum recording thread started.\n")
            else:
                logger.error("pulsecatcher is not callable.\n")
        except Exception as e:
            logger.error(f"Error starting 2D spectrum recording thread: {e}\n")

    elif mode == 3:
        # Start 3D spectrum recording logic
        with global_vars.write_lock:
            filename = global_vars.filename
        logger.info("Starting 3D spectrum recording...\n")
        try:
            if callable(pulsecatcher):
                thread = threading.Thread(target=pulsecatcher, args=(3, global_vars.run_flag, global_vars.run_flag_lock))
                thread.start()
                logger.info("3D spectrum recording thread started.\n")
            else:
                logger.error("pulsecatcher is not callable.\n")
        except Exception as e:
            logger.error(f"Error starting 3D spectrum recording thread: {e}\n")

    else:
        logger.error("Invalid recording mode specified.\n")


# clear variables
def clear_global_vars(mode):
    logger.info('1..running clear_global_vars\n')
    if mode == 2:
        with global_vars.write_lock:
            global_vars.count_history   = []
            global_vars.counts          = 0
            global_vars.cps             = 0
            global_vars.elapsed         = 0
            global_vars.histogram       = [0] * global_vars.bins

    if mode == 3:
        logger.info('2..clear_global_vars mode is (3)\n')
        file_path = os.path.join(global_vars.data_directory, f'{global_vars.filename}_3d.json')

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"3..deleting file: {file_path}\n")
            else:
                logger.warning(f"4..file does not exist: {file_path}\n")
        except Exception as e:
            logger.error(f"ERROR deleting file {file_path}: {e}\n")

        global_vars.count_history   = []
        global_vars.counts          = 0
        global_vars.cps             = 0
        global_vars.elapsed         = 0
        global_vars.histogram_3d    = []

    return

def clear_global_cps_list():
    with global_vars.write_lock:
        global_vars.global_cps = 0
        global_vars.count_history = []

def stop_recording():
    with global_vars.write_lock:
        global_vars.run_flag.clear()
    logger.info('functions recording stopped\n')
    return

def export_csv(filename):
    download_folder = os.path.expanduser("~/Downloads")
    base_filename = filename.rsplit(".", 1)[0]
    output_file = f'{base_filename}.csv'
    with open(f'{data_directory}/{filename}') as f:
        data = json.load(f)
    if data["schemaVersion"] == "NPESv2":
        data = data["data"][0]
    spectrum = data["resultData"]["energySpectrum"]["spectrum"]
    coefficients = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
    if coefficients[2] <= 0:
        coefficients[2] = 0
    with open(os.path.join(download_folder, output_file), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["bin", "counts"])
        for i, value in enumerate(spectrum):
            e = round((i ** coefficients[2] + i * coefficients[1] + coefficients[0]), 2)
            writer.writerow([e, value])

def update_coeff(filename, coeff_1, coeff_2, coeff_3):
    with open(f'{data_directory}/{filename}.json') as f:
        data = json.load(f)
    if data["schemaVersion"] == "NPESv1":
        coefficients = data["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
    elif data["schemaVersion"] == "NPESv2":
        coefficients = data["data"][0]["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
    coefficients[0] = coeff_3
    coefficients[1] = coeff_2
    coefficients[2] = coeff_1
    with open(f'{data_directory}/{filename}.json', 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    # update global_vars
    global_vars.coeff_1 = coeff_3
    global_vars.coeff_2 = coeff_2 
    global_vars.coeff_3 = coeff_1 
    global_vars.coefficients_1 = [coeff_3, coeff_2, coeff_1]

# removes the path from serial device list Mac only
def cleanup_serial_options(options):
    prefix_to_remove = '/dev/cu.usbserial-'
    for item in options:
        if 'label' in item and item['label'].startswith(prefix_to_remove):
            item['label'] = 'Serial # ' + item['label'][len(prefix_to_remove):]
    return options

import json
import os

def get_api_key():
    try:
        user_file_path = get_path(f'{data_directory}/_user.json')

        if not os.path.exists(user_file_path):

            logger.error(f"User file not found: {user_file_path}\n")
            
            return None

        with open(user_file_path, 'r') as file:
            user_data = json.load(file)

        api_key = user_data.get('api_key', None)

        return api_key

    except Exception as e:

        logger.error(f"code/functions/get_api_key() failed: {e}\n")

        return None

def publish_spectrum(filename):
    logger.info(f'functions.publish_spectrum {filename}\n')
    url = "https://gammaspectacular.com/spectra/publish_spectrum"
    api_key = get_api_key()
    logger.info(f'Api key obtained {api_key}\n')
    spectrum_file_path = f'{data_directory}/{filename}.json'
    try:
        with open(spectrum_file_path, 'rb') as file:
            files = {'file': (filename, file)}
            data = {'api_key': api_key}
            response = req.post(url, files=files, data=data)
            if response.status_code == 200:
                logger.info(f'{filename} Published ok\n')
                return f'{filename}\npublished:\n{response}'
            else:
                logger.error(f'code/functions/publish_spectrum {response.text}\n')
                return f'Error from /code/functions/publish_spectrum: {response.text}'
    except req.exceptions.RequestException as e:
        logger.error(f'code/functions/publish_spectrum: {e}\n')
        return f'code/functions/publish_spectrum: {e}'
    except FileNotFoundError:
        logger.error(f'Error from /code/functions/publish_spectrum: {spectrum_file_path}\n')
        return f'Error from /code/functions/publish_spectrum: {spectrum_file_path}'
    except Exception as e:
        logger.error(f'Error from /code/functions/publish_spectrum: {e}\n')
        return f'Error from /code/functions/publish_spectrum: {e}'



def update_json_notes(filename, spec_notes):
    with global_vars.write_lock:
        data_directory = global_vars.data_directory

    try:
        file_path = f'{data_directory}/{filename}.json'
        
        # Read the existing JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Update the notes
        if "data" in data and isinstance(data["data"], list) and "sampleInfo" in data["data"][0]:
            data["data"][0]["sampleInfo"]["note"] = spec_notes
        else:
            logger.error(f"Unexpected JSON structure in {filename}.json\n")
            return
        
        # Write the updated JSON back to the file
        with open(file_path, 'w') as f:
            json.dump(data, f, separators=(',', ':'))
        
        logger.info(f'Notes updated: {spec_notes}\n')
        
    except Exception as e:
        logger.error(f'Error in update_json_notes: {e}\n')



def get_spec_notes(filename):
    try:
        with open(f'{data_directory}/{filename}.json') as f:
            data = json.load(f)
        if data["schemaVersion"] == "NPESv2":
            return data["data"][0]["sampleInfo"]["note"]
    except:
        return 'Not writing'

def fetch_json(file_id):
    url = f'https://www.gammaspectacular.com/spectra/files/{file_id}.json'
    try:
        response = req.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            return response.json()
        return None
    except req.exceptions.RequestException as e:
        logger.error(f"Error fetching JSON: {e}\n")
        return None

def execute_serial_command(input_cmd):
    with shproto.dispatcher.command_lock:
        shproto.dispatcher.command = input_cmd
        logger.info(f"Sending command {input_cmd} to device\n")

def generate_device_settings_table():
    shproto.dispatcher.spec_stopflag = 0
    dispatcher = threading.Thread(target=shproto.dispatcher.start)
    dispatcher.start()
    time.sleep(0.1)
    dev_info = get_serial_device_information()
    info_dict = parse_device_info(dev_info)
    process_03('-cal')
    serial = shproto.dispatcher.serial_number
    table = dash_table.DataTable(
        columns=[
            {"id": "Setting", "name": "Firmware settings"},
            {"id": "cmd", "name": "Command"},
            {"id": "Value", "name": "Value"}
        ],
        data=[
            {"Setting": "Version", "cmd": "-", "Value": info_dict.get('VERSION')},
            {"Setting": "Serial number", "cmd": "status", "Value": serial},
            {"Setting": "Samples for X (pulse rise)", "cmd": "-ris", "Value": info_dict.get('RISE')},
            {"Setting": "Samples for Y (pulse fall)", "cmd": "-fall", "Value": info_dict.get('FALL')},
            {"Setting": "Lower Limit Discriminator LLD", "cmd": "-nos", "Value": info_dict.get('NOISE')},
            {"Setting": "ADC Sample Frequency", "cmd": "-frq", "Value": info_dict.get('F')},
            {"Setting": "Max integral value", "cmd": "-max", "Value": info_dict.get('MAX')},
            {"Setting": "Hysteresis value", "cmd": "-hyst", "Value": info_dict.get('HYST')},
            {"Setting": "Working Mode [0, 1, 2]", "cmd": "-mode", "Value": info_dict.get('MODE')},
            {"Setting": "Discriminator step (>1)", "cmd": "-step", "Value": info_dict.get('STEP')},
            {"Setting": "High Voltage (0-255)", "cmd": "-U", "Value": info_dict.get('POT')},
            {"Setting": "Baseline trim (0-255)", "cmd": "-V", "Value": info_dict.get('POT2')},
            {"Setting": "Temperature sensor 1", "cmd": "status", "Value": f"{info_dict.get('T1')} C˚"},
            {"Setting": "Energy Window (-win X1 X2)", "cmd": "-win", "Value": info_dict.get('OUT')},
            {"Setting": "Temp. compensation status", "cmd": "status", "Value": info_dict.get('TCpot')},
            {"Setting": "Temp. compensation table", "cmd": "status", "Value": info_dict.get('Tco')}
        ],
        style_cell={
            'textAlign': 'left',
            'padding': '4px',
            'fontSize': '12px',
            'fontFamily': 'Arial'
        },
        style_cell_conditional=[
            {'if': {'column_id': 'Setting'}, 'width': '60%'},
            {'if': {'column_id': 'cmd'}, 'width': '10%'},
            {'if': {'column_id': 'Value'}, 'width': '30%'}
        ]
    )
    return table

# Check if commands sent to processor is safe
def allowed_command(cmd):
    allowed_command_patterns = [
        r"^-U[0-9]{1,3}$",
        r"^-V[0-9]{1,3}$",
        r"^-sto$",
        r"^-nos[0-9]{1,3}$"
    ]
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



def get_options():
    with global_vars.write_lock:
        data_directory = global_vars.data_directory

    files = [os.path.relpath(file, data_directory).replace("\\", "/")
             for file in glob.glob(os.path.join(data_directory, "**", "*.json"), recursive=True)]
    
    options = [{'label': "~ " + os.path.basename(file), 'value': file} if "i/" in file and file.endswith(".json")
        else {'label': os.path.basename(file), 'value': file} for file in files]

    options = [opt for opt in options if not opt['value'].endswith("_cps.json")]
    options = [opt for opt in options if not opt['value'].endswith("_3d.json")]
    options = [opt for opt in options if not opt['value'].endswith("_settings.json")]
    options = [opt for opt in options if not opt['value'].endswith("_user.json")]

    options_sorted = sorted(options, key=lambda x: x['label'])
    for file in options_sorted:
        file['label'] = file['label'].replace('.json', '')
        file['value'] = file['value'].replace('.json', '')

    return options_sorted

# Calibrates the x-axis of the Gaussian correlation
def calibrate_gc(gc, coefficients):
    channels = np.arange(len(gc))
    x_values = np.polyval(coefficients, channels)
    gc_calibrated = list(zip(x_values, gc))
    return gc_calibrated

# Opens and reads the isotopes.json file
def get_isotopes(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Finds the peaks in gc (Gaussian correlation)
def find_peaks_in_gc(gc, sigma):
    width = sigma * 2
    peaks, _ = find_peaks(gc, width=width)
    return peaks

# Finds matching isotopes in the JSON data file
def matching_isotopes(gc_calibrated, peaks, data, sigma):
    matches = {}
    for idx, peak_idx in enumerate(peaks):
        x, y = gc_calibrated[peak_idx]
        if y > 4:
            matched_isotopes = [
                isotope for isotope in data
                if abs(isotope['energy'] - x) <= sigma * 2
            ]
            if matched_isotopes:
                matches[idx] = (x, y, matched_isotopes)
    return matches

# functions.py

def reset_stores():
    return {
        'store_count_history': [],
        'store_load_flag_tab3': False,
        'store_load_flag_tab4': False,
    }


def save_settings_to_json():

    settings = {key: getattr(global_vars, key) for key in [
        "flip", 
        "theme", 
        "max_bins", 
        "device", 
        "sample_rate", 
        "sample_length", 
        "shapecatches",
        "chunk_size", 
        "stereo", 
        "peakshift", 
        "max_counts", 
        "max_seconds", 
        "filename",
        "bins", 
        "threshold", 
        "tolerance", 
        "bin_size", 
        "t_interval", 
        "comparison",
        "bins_2", 
        "bin_2_size", 
        "sigma", 
        "peakfinder", 
        "calib_bin_1", 
        "calib_bin_2", 
        "calib_bin_3",
        "calib_e_1", 
        "calib_e_2", 
        "calib_e_3", 
        "coeff_1", 
        "coeff_2", 
        "coeff_3", 
        "rolling_interval", 
        "compression",
    ]}
    with open(global_vars.settings_file, 'w') as f:
        json.dump(settings, f, indent=4)
        logger.info('functions save_settings_to_json(done)\n')
    return    


def load_settings_from_json():
    path = global_vars.settings_file

    if os.path.exists(path):
        with open(path, 'r') as f:
            settings = json.load(f)

            logger.info(f'settings={settings}\n')

            for key, value in settings.items():
                if key in [
                    "flip", "theme", "max_bins", "device", "sample_rate", "sample_length", "shapecatches",
                    "chunk_size", "stereo", "peakshift", "max_counts", "max_seconds", "filename",
                    "bins", "threshold", "tolerance", "bin_size", "t_interval", "comparison",
                    "bins_2", "bin_2_size", "sigma", "peakfinder", "calib_bin_1", "calib_bin_2", "calib_bin_3",
                    "calib_e_1", "calib_e_2", "calib_e_3", "coeff_1", "coeff_2", "coeff_3", "rolling_interval", "compression",
                ]:
                    try:
                        setattr(global_vars, key, int(value))
                    except ValueError:
                        setattr(global_vars, key, value)
                elif key in ["calib_e_1", "calib_e_2", "calib_e_3", "coeff_1", "coeff_2", "coeff_3", "peakfinder", "sigma"]:
                    try:
                        setattr(global_vars, key, float(value))
                    except ValueError:
                        setattr(global_vars, key, value)
                else:
                    setattr(global_vars, key, value)   
                    logger.info(f'load settings completed {settings}\n')                      

def load_histogram(filename):
    with global_vars.write_lock:
        data_directory = global_vars.data_directory

    data = {}
    path = get_path(os.path.join(data_directory, f'{filename}.json'))

    try:
        # Read the JSON file
        with open(path, 'r') as file:
            data = json.load(file)

            # Validate the schema version
            if data["schemaVersion"] == "NPESv2":
                with global_vars.write_lock:
                    global_vars.histogram = data["data"][0]["resultData"]["energySpectrum"]["spectrum"]
                    global_vars.bins = data["data"][0]["resultData"]["energySpectrum"]["numberOfChannels"]
                    global_vars.elapsed = data["data"][0]["resultData"]["energySpectrum"]["measurementTime"]
                    global_vars.coefficients_1 = data["data"][0]["resultData"]["energySpectrum"]["energyCalibration"]["coefficients"]
                    global_vars.spec_notes = data["data"][0]["sampleInfo"]["note"]
                    global_vars.counts = sum(global_vars.histogram)

                return True
            else:
                print("Invalid schema version.")
                return False

    except Exception as e:
        logger.info(f"Error in functions load_histogram({e})\n")
        return False

def load_histogram_2(filename):
    path = get_path(os.path.join(global_vars.data_directory, f'{filename}.json'))
    try:
        with open(path, 'r') as file:

            data = json.load(file)

        if data["schemaVersion"] == "NPESv2":
            result_data = data["data"][0]["resultData"]["energySpectrum"]
            global_vars.histogram_2     = result_data["spectrum"]
            global_vars.bins_2          = result_data["numberOfChannels"]
            global_vars.elapsed_2       = result_data["measurementTime"]
            global_vars.coefficients_2  = result_data["energyCalibration"]["coefficients"]
            global_vars.counts_2        = result_data["validPulseCount"]
            return True
        else:
            logger.info("Unsupported schema version\n")
            return False

    except Exception as e:

        logger.info(f"Error loading histogram_2 from {filename}: {e}\n")
        return False


def load_histogram_3d(filename):

    logging.info('1.. load_histogram_3d\n')

    file_path = os.path.join(global_vars.data_directory, f'{filename}_3d.json')
    
    if not os.path.exists(file_path):
        logger.error(f"load_histogram_3d File not found: {file_path}\n")
        return

    try:
        with open(file_path, 'r') as file:
            logger.info('2.. loading 3d file\n')
            data = json.load(file)
            logger.info('3.. loading 3d file\n')
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}\n")
        return

    try:
        with global_vars.write_lock:
            global_vars.histogram_3d = data['data'][0]['resultData']['energySpectrum']['spectrum']
            global_vars.counts = data['data'][0]['resultData']['energySpectrum']['validPulseCount']
            global_vars.elapsed = data['data'][0]['resultData']['energySpectrum']['measurementTime']
            global_vars.coeff_1 = data['data'][0]['resultData']['energySpectrum']['energyCalibration']['coefficients'][0]
            global_vars.coeff_2 = data['data'][0]['resultData']['energySpectrum']['energyCalibration']['coefficients'][1]
            global_vars.coeff_3 = data['data'][0]['resultData']['energySpectrum']['energyCalibration']['coefficients'][2]

        logger.info(f"4.. global_vars updated from {file_path}\n")
    except KeyError as e:
        logger.error(f"Missing expected data key in {file_path}: {e}\not")

def load_cps_file(filename):

    data_directory  = global_vars.data_directory
    cps_file_path   = os.path.join(data_directory, f"{filename}_cps.json")

    if not os.path.exists(cps_file_path):
        return
    try:
        with open(cps_file_path, 'r') as file:
            cps_data = json.load(file)

            count_history = cps_data.get('count_history', [])
            elapsed = cps_data.get('elapsed', 0)

            # Flatten the nested list and ensure all values are integers
            if isinstance(count_history, list):
                valid_count_history = [int(item) for item in count_history if isinstance(item, int) and item >= 0]
            else:
                raise ValueError("Invalid format for 'cps' in JSON file. Expected a list of integers.")

            # Update global variables
            global_vars.count_history = valid_count_history
            global_vars.elapsed = int(elapsed)

            return cps_data

    except json.JSONDecodeError as e:
        raise ValueError(f"Error loading cps JSON from {cps_file_path}: {e}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while loading CPS data from {cps_file_path}: {e}")        




