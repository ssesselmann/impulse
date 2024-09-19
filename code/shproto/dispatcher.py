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
import global_vars
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

with global_vars.write_lock:
    data_directory  = global_vars.data_directory

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
        try:
            rx_byte_arr = nano.read(size=READ_BUFFER)
        except serial.SerialException as e:
            logger.error(f"SerialException: {e}\n")
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
                        shproto.dispatcher.inf_str = re.sub(r'\[[^]]*\]', '...', shproto.dispatcher.inf_str, count=2)
                        logger.info(f"Got nano-pro settings:\n {shproto.dispatcher.inf_str} \n")
                except UnicodeDecodeError:
                    logger.info("Unknown non-text response in dispatcher line 100\n")

                if len(resp_lines) == 40:
                    shproto.dispatcher.serial_number = "{}".format(resp_lines[39])
                    logger.info("Found nano-pro serial # {}\n".format(shproto.dispatcher.serial_number))
                    b_str = ''
                    for b in resp_lines[0:10]:
                        b_str += b
                    crc = binascii.crc32(bytearray(b_str, 'ascii')) % 2**32
                    if crc == int(resp_lines[10], 16):
                        with shproto.dispatcher.calibration_lock:
                            shproto.dispatcher.calibration[0] = unpack('d', int((resp_lines[0] + resp_lines[1]), 16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[1] = unpack('d', int((resp_lines[2] + resp_lines[3]), 16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[2] = unpack('d', int((resp_lines[4] + resp_lines[5]), 16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[3] = unpack('d', int((resp_lines[6] + resp_lines[7]), 16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration[4] = unpack('d', int((resp_lines[8] + resp_lines[9]), 16).to_bytes(8, 'little'))[0]
                            shproto.dispatcher.calibration_updated = 1
                        logger.info("Got calibration: {}\n".format(shproto.dispatcher.calibration))
                    else:
                        logger.info("Dispatcher Wrong crc for calibration values got: {:08x} expected: {:08x}".format(int(resp_lines[10], 16), crc))

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
            elif response.cmd == shproto.MODE_PULSE:  # debug mode, pulse shape
                if pulse_file_opened != 1:
                    fd_pulses = open("/tmp/pulses.csv", "w+")
                    pulse_file_opened = 1

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
                logger.info("Received: cmd:{}\r\npayload: {}\n".format(response.cmd, response.payload))
                response.clear()
    nano.close()


# This process records the 2D histogram (spectrum)
def process_01(filename, compression, device, t_interval):
    logger.info(f'dispatcher.process_01({filename})')

    global counts, last_counts

    counts              = 0
    last_counts         = 0
    compression         = int(compression)
    max_bins            = 8192
    t0                  = time.time()
    elapsed             = 0
    compressed_bins     = int(max_bins / compression)

    with global_vars.write_lock:
        global_vars.bins    = int(max_bins / compression)
        # Load settings from global_vars
        max_counts          = global_vars.max_counts
        coeff_1             = global_vars.coeff_1
        coeff_2             = global_vars.coeff_2
        coeff_3             = global_vars.coeff_3
        max_seconds         = global_vars.max_seconds
        t_interval          = global_vars.t_interval
        suppress_last_bin   = global_vars.suppress_last_bin

    # Define the histogram list
    hst = [0] * max_bins  # Initialize the original histogram list

    # Initialize last update and save times
    last_update_time    = time.time()
    last_save_time      = time.time()

    # Initialize count history
    count_history = []

    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag) and (counts < max_counts and elapsed <= max_seconds):

        time.sleep(t_interval)

        # Get the device time
        t1          = time.time()        

        # Convert float timestamps to datetime objects
        start_time  = datetime.fromtimestamp(t0)
        end_time    = datetime.fromtimestamp(t1)

        # Fetch the histogram from the device
        with shproto.dispatcher.histogram_lock:
            hst = shproto.dispatcher.histogram.copy()
            tt  = shproto.dispatcher.total_time

        # Time elapsed from device
        elapsed     = tt 

        # Clear counts in the last bin
        if suppress_last_bin:
            hst[-1] = 0

        # Combine every 8 elements into one for compression
        compressed_hst = [sum(hst[i:i + compression]) for i in range(0, max_bins, compression)]

        # Sum total counts
        counts = sum(compressed_hst)

        # Calculate counts per second (CPS)
        with cps_lock:
            cps             = (counts - last_counts)
            global_vars.cps = cps

        # Append CPS to count history in a thread-safe manner
        with global_vars.write_lock:
            count_history.append(cps)
            global_vars.count_history = count_history  

        # Update global variables once per second
        if t1 - last_update_time >= 1 * t_interval:
            with global_vars.write_lock:
                data_directory              = global_vars.data_directory
                global_vars.counts          = counts
                global_vars.elapsed         = elapsed
                global_vars.count_history   = count_history 
                global_vars.histogram       = compressed_hst
                global_vars.cps             = cps
                spec_notes                  = global_vars.spec_notes

            last_update_time = t1

        # Save JSON files once every 60 seconds
        if t1 - last_save_time >= 60 or shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag:

            logger.info(f'shproto process_01 attempting to save {filename}.json\n')

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
                            "note": spec_notes,
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
                                "measurementTime": elapsed,
                                "spectrum": compressed_hst
                            }
                        }
                    }
                ]
            }

            json_data = json.dumps(data, separators=(",", ":"))

            # Construct the full path to the file
            file_path = os.path.join(data_directory, f'{filename}.json')

            logger.info(f'file path = {file_path}\n')

            # Open the JSON file in "write" mode for each iteration
            with open(file_path, "w") as wjf:
                wjf.write(json_data)

            # Save CPS data to a separate JSON file
            cps_data = {
                "filename": filename,
                "count_history": count_history,
                "elapsed": elapsed
            }

            cps_file_path = os.path.join(data_directory, f'{filename}_cps.json')

            logger.info(f'CPS file path = {cps_file_path}\n')

            # Open the CPS JSON file in "write" mode for each iteration
            with open(cps_file_path, "w") as cps_wjf:
                json.dump(cps_data, cps_wjf)

            last_save_time = t1

        last_counts = counts

    return

# This process records the 3D histogram 9spectrum)
def process_02(filename_3d, compression, device, t_interval):  # Compression reduces the number of channels by 8, 4, or 2
    logger.info(f'dispatcher.process_02 ({filename_3d})\n')

    global counts, last_counts, histogram_3d

    counts              = 0
    last_counts         = 0
    total_counts        = 0
    compression3d         = int(compression)
    max_bins            = 8192
    t0                  = time.time()
    elapsed             = 0
    hst3d               = []
    compressed_bins     = int(max_bins / compression3d)
    last_hst            = [0] * compressed_bins

    with global_vars.write_lock:
        data_directory      = global_vars.data_directory
        global_vars.bins3d    = int(max_bins / compression3d)
        # Set local variables
        max_counts          = global_vars.max_counts
        coeff_1             = global_vars.coeff_1
        coeff_2             = global_vars.coeff_2
        coeff_3             = global_vars.coeff_3
        max_seconds         = global_vars.max_seconds
        t_interval          = global_vars.t_interval

    # Define the histogram list
    hst = [0] * max_bins  # Initialize the original histogram list

    # Initialize last update and save times
    last_update_time = time.time()
    last_save_time = time.time()

    # Initialize count history
    count_history = []

    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag) and (counts < max_counts and elapsed <= max_seconds):

        time.sleep(t_interval)

        # Get the device time
        t1 = time.time()

        # Calculate the time difference
        elapsed = int(t1 - t0)

        # Convert float timestamps to datetime objects
        start_time = datetime.fromtimestamp(t0)
        end_time = datetime.fromtimestamp(t1)

        # Fetch the histogram from the device
        with shproto.dispatcher.histogram_lock:
            hst = shproto.dispatcher.histogram.copy()

        # Clear counts in the last bin
        hst[-1] = 0

        # Combine every 'compression' elements into one for compression
        compressed_hst = [sum(hst[i:i + compression]) for i in range(0, max_bins, compression)]

        # Sum total counts
        counts = sum(compressed_hst)

        cps = (counts - last_counts)  # Strictly not cps but counts per loop in this while loop!! (need to fix)

        # Append CPS to count history
        count_history.append(cps)

        # Calculate net counts in each bin
        this_hst = [a - b for a, b in zip(compressed_hst, last_hst)]
        hst3d.append(this_hst)

        # Update global variables once per second
        if t1 - last_update_time >= 1 * t_interval:

            with global_vars.write_lock:
                global_vars.counts          = counts
                global_vars.elapsed         = elapsed
                global_vars.count_history   = count_history  # Update count history
                global_vars.histogram_3d    = hst3d

            with cps_lock:
                global_vars.cps             = cps    

            last_update_time = t1

        # Save JSON files once every 60 seconds or when global_vars.run_flag.clear()
        if t1 - last_save_time >= 60 or shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag:

            logger.info(f'shproto process_02 attempting to save {filename_3d}_3d.json\n')

            data = {
                "schemaVersion": "NPESv2",
                "data": [
                    {
                        "deviceData": {
                            "softwareName": "IMPULSE",
                            "deviceName": "{}{}".format(device, shproto.dispatcher.serial_number)
                        },
                        "sampleInfo": {
                            "name": filename_3d,
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
                                "measurementTime": elapsed,
                                "spectrum": hst3d
                            }
                        }
                    }
                ]
            }

            json_data = json.dumps(data, separators=(",", ":"))

            # Construct the full path to the file
            file_path = os.path.join(data_directory, f'{filename_3d}_3d.json')

            logger.info(f'file path = {file_path}\n')

            # Open the JSON file in "write" mode for each iteration
            with open(file_path, "w") as wjf:
                wjf.write(json_data)

            # Save CPS data to a separate JSON file
            cps_data = {
                "filename": filename_3d,
                "count_history": count_history,
                "elapsed": elapsed
            }

            cps_file_path = os.path.join(data_directory, f'{filename_3d}_cps.json')

            logger.info(f'CPS file path = {cps_file_path}\n')

            # Open the CPS JSON file in "write" mode for each iteration
            with open(cps_file_path, "w") as cps_wjf:
                json.dump(cps_data, cps_wjf)

            last_save_time = t1

        last_counts = counts
        last_hst    = compressed_hst

    return

def load_json_data(file_path):
    logger.info(f'dispatcher.load_json_data({file_path})\n')
    if os.path.exists(file_path):
        with open(file_path, "r") as rjf:
            return json.load(rjf)
    else:
        return {
            "schemaVersion": "NPESv1",
            "resultData": {
                "startTime": int(time.time() * 1e6),  # Convert seconds to microseconds
                "energySpectrum": {
                    "numberOfChannels": 0,
                    "energyCalibration": {
                        "polynomialOrder": 2,
                        "coefficients": []
                    },
                    "validPulseCount": 0,
                    "totalPulseCount": 0,
                    "measurementTime": 0,
                    "spectrum": []
                }
            }
        }

# This process is used for sending commands to the Nano device
def process_03(_command):
    with shproto.dispatcher.command_lock:
        shproto.dispatcher.command = _command
        logger.info(f'dispatcher.process_03({_command})\n')
        return

def stop():
    logger.info('shproto.stop triggered\n')
    with shproto.dispatcher.stopflag_lock:
        process_03('-sto')
        logger.info('process_03(-sto)\n')
        time.sleep(0.1)
        shproto.dispatcher.stopflag = 1
        logger.info('Stop flag set(dispatcher)\n')
        time.sleep(0.1)
        return

def spec_stop():
    with shproto.dispatcher.spec_stopflag_lock:
        shproto.dispatcher.spec_stopflag = 1

        logger.info('Stop flag set(dispatcher)\n')
        return

def clear():
    with shproto.dispatcher.histogram_lock:
        shproto.dispatcher.histogram            = [0] * max_bins
        shproto.dispatcher.pkts01               = 0
        shproto.dispatcher.pkts03               = 0
        shproto.dispatcher.pkts04               = 0
        shproto.dispatcher.total_pkts           = 0
        shproto.dispatcher.cpu_load             = 0
        shproto.dispatcher.cps                  = 0
        shproto.dispatcher.total_time           = 0
        shproto.dispatcher.lost_impulses        = 0
        shproto.dispatcher.total_pulse_width    = 0
        shproto.dispatcher.dropped              = 0
