import sys
import threading
import time
import json
import binascii
import re
import serial
import shproto
import shproto.port
import logging
import os
import platform
import functions as fn
from struct import *
from datetime import datetime


max_bins            = 8192
logger              = logging.getLogger(__name__)
stopflag            = 0
stopflag_lock       = threading.Lock()
spec_stopflag       = 0
spec_stopflag_lock  = threading.Lock()
histogram           = [0] * max_bins
histogram_lock      = threading.Lock()
command             = ""
command_lock        = threading.Lock()
pkts03              = 0
pkts04              = 0
total_pkts          = 0
dropped             = 0
total_time          = 0
cpu_load            = 0
cps                 = 0
cps_lock            = threading.Lock()
lost_impulses       = 0
last_counts         = 0
data_directory      = None
cps_list            = []

serial_number       = ""
calibration         = [0., 1., 0., 0., 0.]
calibration_updated = 0
calibration_lock    = threading.Lock()
inf_str             = ''

logger = logging.getLogger(__name__)

# This function communicates with the device
def start(sn=None):
    READ_BUFFER = 1
    shproto.dispatcher.clear()
    with shproto.dispatcher.stopflag_lock:
        shproto.dispatcher.stopflag = 0
    nano = shproto.port.connectdevice(sn)
    response = shproto.packet()
    while not shproto.dispatcher.stopflag:
        if shproto.dispatcher.command is not None and len(shproto.dispatcher.command) > 0:
            if command == "-rst":
                shproto.dispatcher.clear()
            tx_packet = shproto.packet()
            tx_packet.cmd = shproto.MODE_TEXT
            tx_packet.start()
            for i in range(len(command)):
                tx_packet.add(ord(command[i]))
            tx_packet.stop()
            nano.write(tx_packet.payload)
            with shproto.dispatcher.command_lock:
                shproto.dispatcher.command = ""
        if nano.in_waiting == 0:
            time.sleep(0.1)
            continue
        READ_BUFFER = max(nano.in_waiting, READ_BUFFER)
        #rx_byte_arr = nano.read(size=READ_BUFFER)
        try:
            rx_byte_arr = nano.read(size=READ_BUFFER)
        except serial.SerialException as e:
            logger.error(f"SerialException: {e}")
            break  # Exit the loop if there's a serial exception
        for rx_byte in rx_byte_arr:
            response.read(rx_byte)
            if response.dropped:
                shproto.dispatcher.dropped += 1
                shproto.dispatcher.total_pkts += 1
            if not response.ready:
                continue
            shproto.dispatcher.total_pkts += 1
            if response.cmd == shproto.MODE_TEXT:
                shproto.dispatcher.pkts03 += 1
                resp_decoded = bytes(response.payload[:len(response.payload) - 2])
                resp_lines = []
                try:
                    resp_decoded = resp_decoded.decode("ascii")
                    resp_lines = resp_decoded.splitlines()
                    if re.search('^VERSION', resp_decoded):
                        shproto.dispatcher.inf_str = resp_decoded
                        shproto.dispatcher.inf_str = re.sub(r'\[[^]]*\]', '...', shproto.dispatcher.inf_str, count = 2)
                        logger.info("Got nano-pro settings: {}".format(shproto.dispatcher.inf_str))
                except UnicodeDecodeError:
                    logger.info("Unknown non-text response in dispatecher line 100")

                if len(resp_lines) == 40:
                    shproto.dispatcher.serial_number = "{}".format(resp_lines[39]);
                    logger.info("Found nano-pro serial # {}".format(shproto.dispatcher.serial_number))
                    b_str =  ''
                    for b in resp_lines[0:10]:
                        b_str += b
                    crc = binascii.crc32(bytearray(b_str, 'ascii')) % 2**32
                    if (crc == int(resp_lines[10],16)):
                        with shproto.dispatcher.calibration_lock:
                            shproto.dispatcher.calibration[0] = unpack('d', int((resp_lines[0] + resp_lines[1]),16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[1] = unpack('d', int((resp_lines[2] + resp_lines[3]),16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[2] = unpack('d', int((resp_lines[4] + resp_lines[5]),16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[3] = unpack('d', int((resp_lines[6] + resp_lines[7]),16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[4] = unpack('d', int((resp_lines[8] + resp_lines[9]),16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration_updated = 1
                        logger.info("Got calibration: {}".format(shproto.dispatcher.calibration))
                    else:
                        logger.info("Wrong crc for calibration values got: {:08x} expected: {:08x}".format(int(resp_lines[10],16), crc))
	
                response.clear()
            elif response.cmd == shproto.MODE_HISTOGRAM:
                shproto.dispatcher.pkts01 += 1
                offset = response.payload[0] & 0xFF | ((response.payload[1] & 0xFF) << 8)
                count = int((response.len - 2) / 4)
                with shproto.dispatcher.histogram_lock:
                    for i in range(0, count):
                        index = offset + i
                        if index < len(shproto.dispatcher.histogram):
                            value = (response.payload[i * 4 + 2]) | \
                                    ((response.payload[i * 4 + 3]) << 8) | \
                                    ((response.payload[i * 4 + 4]) << 16) | \
                                    ((response.payload[i * 4 + 5]) << 24)
                            shproto.dispatcher.histogram[index] = value & 0x7FFFFFF
                response.clear()
            elif response.cmd == shproto.MODE_PULSE: ### debug mode, pulse shape
                if pulse_file_opened != 1:
                    fd_pulses = open("/tmp/pulses.csv", "w+")
                    pulse_file_opened = 1

                #print("<< got pulse", fd_pulses)
                shproto.dispatcher.pkts01 += 1
                offset = response.payload[0] & 0xFF | ((response.payload[1] & 0xFF) << 8)
                count = int((response.len - 2) / 2)
                pulse = []
                for i in range(0, count):
                    index = offset + i
                    if index < len(shproto.dispatcher.histogram):
                        value = (response.payload[i * 2 + 2]) | \
                                ((response.payload[i * 2 + 3]) << 8)
                        pulse = pulse + [(value & 0x7FFFFFF)]
                    fd_pulses.writelines("{:d} ".format(value & 0x7FFFFFF))
                fd_pulses.writelines("\n")
                fd_pulses.flush()
                # print("len: ", count, "shape: ", pulse)
                response.clear()
            elif response.cmd == shproto.MODE_STAT:
                shproto.dispatcher.pkts04 += 1
                shproto.dispatcher.total_time = (response.payload[0] & 0xFF) | \
                                                ((response.payload[1] & 0xFF) << 8) | \
                                                ((response.payload[2] & 0xFF) << 16) | \
                                                ((response.payload[3] & 0xFF) << 24)
                shproto.dispatcher.cpu_load = (response.payload[4] & 0xFF) | ((response.payload[5] & 0xFF) << 8)
                shproto.dispatcher.cps = (response.payload[6] & 0xFF) | \
                                         ((response.payload[7] & 0xFF) << 8) | \
                                         ((response.payload[8] & 0xFF) << 16) | \
                                         ((response.payload[9] & 0xFF) << 24)
                if response.len >= (11 + 2):
                    shproto.dispatcher.lost_impulses = (response.payload[10] & 0xFF) | \
                                                       ((response.payload[11] & 0xFF) << 8) | \
                                                       ((response.payload[12] & 0xFF) << 16) | \
                                                       ((response.payload[13] & 0xFF) << 24)
                if response.len >= (15 + 2):
                    shproto.dispatcher.total_pulse_width = (response.payload[14] & 0xFF) | \
                                                       ((response.payload[15] & 0xFF) << 8) | \
                                                       ((response.payload[16] & 0xFF) << 16) | \
                                                       ((response.payload[17] & 0xFF) << 24)
                response.clear()
            else:
                print("Wtf received: cmd:{}\r\npayload: {}".format(response.cmd, response.payload))
                response.clear()
    nano.close()

# This function writes the 2D spectrum to a JSON file

def process_01(filename, compression, device, t_interval):  # Compression reduces the number of channels by 8, 4, or 2
    logger.debug(f'dispatcher.process_01({filename})')

    global counts
    global last_counts

    counts          = 0
    last_counts     = 0
    compression     = int(compression)
    t0              = time.time()
    dt              = 0
    compressed_bins = int(max_bins / compression)

    settings        = fn.load_settings()
    max_counts      = settings[9]
    coeff_1         = settings[18]
    coeff_2         = settings[19]
    coeff_3         = settings[20]
    max_seconds     = settings[26]


    # Define the histogram list
    hst             = [0] * max_bins  # Initialize the original histogram list

    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag) and (counts < max_counts and dt <= max_seconds):

        time.sleep(t_interval)

        # Get the current time
        t1 = time.time()

        # Calculate the time difference
        dt = int(t1 - t0)

        # Convert float timestamps to datetime objects
        start_time = datetime.fromtimestamp(t0)
        end_time = datetime.fromtimestamp(t1)

        # Fetch the histogram from the device
        hst = shproto.dispatcher.histogram

        # Clear counts in the last bin
        hst[-1] = 0

        # Combine every 8 elements into one for compression
        compressed_hst = [sum(hst[i:i + compression]) for i in range(0, max_bins, compression)]

        # Sum total counts
        counts = sum(compressed_hst)

        cps = (counts - last_counts)  # Strictly not cps but counts per loop in this while loop!! (need to fix)

        data = {
            "schemaVersion": "NPESv2",
            "data": [
                {
                    "deviceData": {
                        "softwareName": "IMPULSE",
                        "deviceName": "{}{}".format(device, shproto.dispatcher.serial_number)
                    },
                    "sampleInfo": {
                        "name": filename,
                        "location": "",
                        "note": ""
                    },
                    "resultData": {
                        "startTime": start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "endTime": end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                        "energySpectrum": {
                            "numberOfChannels": compressed_bins,
                            "energyCalibration": {
                                "polynomialOrder": 2,
                                "coefficients": [coeff_3, coeff_2, coeff_1]
                            },
                            "validPulseCount": counts,
                            "measurementTime": dt,
                            "spectrum": compressed_hst
                        }
                    }
                }
            ]
        }


        json_data = json.dumps(data, separators=(",", ":"))

        # Construct the full path to the file
        file_path = os.path.expanduser('~/impulse_data/' + filename + '.json')

        # Open the JSON file in "write" mode for each iteration
        with open(file_path, "w") as wjf:
            wjf.write(json_data)

        fn.write_cps_json(filename, cps)

        last_counts = counts

    return    

# This function writes the 3D spectrum to a JSON file

def process_02(filename, compression, t_interval):
    logger.info(f'dispatcher.process_01({filename})')

    global counts
    global last_counts
    global total_counts  # New variable to store total counts

    counts          = 0
    last_counts     = 0
    total_counts    = 0  # Initialize total counts
    compression     = int(compression)
    t0              = time.time()
    compressed_bins = int(max_bins / compression)

    filename        = filename + '_3d'
    file_path       = os.path.expanduser('~/impulse_data/' + filename + '.json')

    settings        = fn.load_settings()
    coeff_1         = settings[18]
    coeff_2         = settings[19]
    coeff_3         = settings[20]

    # Initialize last_compressed_hst
    last_compressed_hst = [0] * compressed_bins

    # Write the initial JSON schema to the file without the spectrum field
    initial_data = {
        "schemaVersion": "NPESv1",
        "resultData": {
            "startTime": int(t0 * 1e6),  # Convert seconds to microseconds
            "energySpectrum": {
                "numberOfChannels": compressed_bins,
                "energyCalibration": {
                    "polynomialOrder": 2,
                    "coefficients": [float(coeff_3), float(coeff_2), float(coeff_1)]
                },
                "validPulseCount": counts,
                "totalPulseCount": total_counts,  # New field for total counts
                "measurementTime": 0,
                "spectrum": []
            }
        }
    }

    with open(file_path, "w") as wjf:
        json.dump(initial_data, wjf, separators=(",", ":"))

    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag):
        time.sleep(t_interval)

        # Get the current time in microseconds
        t1 = int(time.time() * 1e6)

        # Fetch the histogram and counts from the device
        hst = shproto.dispatcher.histogram
        counts = sum(hst)

        # Clear counts in the last bin
        hst[-1] = 0

        # Combine every 'compression' elements into one for compression
        compressed_hst = [sum(hst[i:i + compression]) for i in range(0, max_bins, compression)]

        # Calculate net counts in each bin
        net_compressed_hst = [current - last for current, last in zip(compressed_hst, last_compressed_hst)]

        # Update total counts
        total_counts += counts

        last_counts = counts
        last_compressed_hst = compressed_hst

        # Load existing data from the JSON file
        existing_data = load_existing_data(file_path)

        # Check if the spectrum field exists, and if not, add it
        if "spectrum" not in existing_data["resultData"]["energySpectrum"]:
            existing_data["resultData"]["energySpectrum"]["spectrum"] = []

        # Append the new histogram to the existing spectrum
        existing_data["resultData"]["energySpectrum"]["spectrum"].append(net_compressed_hst)

        # Update the endTime, validPulseCount, totalPulseCount, and measurementTime
        existing_data["resultData"]["endTime"] = t1
        existing_data["resultData"]["energySpectrum"]["validPulseCount"] = counts
        existing_data["resultData"]["energySpectrum"]["totalPulseCount"] = total_counts
        existing_data["resultData"]["energySpectrum"]["measurementTime"] = int((t1 - initial_data["resultData"]["startTime"]) / 1e6)

        # Write the updated data back to the file
        with open(file_path, "w") as wjf:
            json.dump(existing_data, wjf, separators=(",", ":"))

    return


def load_existing_data(file_path):
    existing_data = {}

    # Load existing data if the file exists
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                pass

    return existing_data

def process_03(_command):
    with shproto.dispatcher.command_lock:
        shproto.dispatcher.command = _command
        logger.info(f'Command received (dispatcher):{_command}')
        return

def stop():

    with shproto.dispatcher.stopflag_lock:
        process_03('-sto')
        time.sleep(0.5)
        shproto.dispatcher.stopflag = 1
        logger.info('Stop flag set(dispatcher)')
        time.sleep(0.5)
        return

def spec_stop():

    with shproto.dispatcher.spec_stopflag_lock:
        shproto.dispatcher.spec_stopflag = 1

        logger.info('Stop flag set(dispatcher)')
        return

def clear():
    with shproto.dispatcher.histogram_lock:
        shproto.dispatcher.histogram        = [0] * max_bins
        shproto.dispatcher.pkts01           = 0
        shproto.dispatcher.pkts03           = 0
        shproto.dispatcher.pkts04           = 0
        shproto.dispatcher.total_pkts       = 0
        shproto.dispatcher.cpu_load         = 0
        shproto.dispatcher.cps              = 0
        shproto.dispatcher.total_time       = 0
        shproto.dispatcher.lost_impulses    = 0
        shproto.dispatcher.total_pulse_width = 0
        shproto.dispatcher.dropped          = 0
