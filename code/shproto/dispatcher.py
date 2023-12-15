import sys
import threading
import time
import json
import shproto
import shproto.port
import logging
import os
import platform
import functions as fn

logger              = logging.getLogger(__name__)
stopflag            = 0
stopflag_lock       = threading.Lock()
spec_stopflag       = 0
spec_stopflag_lock  = threading.Lock()
histogram           = [0] * 8192
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
        rx_byte_arr = nano.read(size=READ_BUFFER)
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
                try:
                    resp_decoded = resp_decoded.decode("ascii")
                except UnicodeDecodeError:
                    print("Unknown non-text response.")
                print("<< {}".format(resp_decoded))
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
                if response.len >= (15 + 2):
                    shproto.dispatcher.lost_impulses = (response.payload[10] & 0xFF) | \
                                                       ((response.payload[11] & 0xFF) << 8) | \
                                                       ((response.payload[12] & 0xFF) << 16) | \
                                                       ((response.payload[13] & 0xFF) << 24)
                response.clear()
            else:
                print("Wtf received: cmd:{}\r\npayload: {}".format(response.cmd, response.payload))
                response.clear()
    nano.close()


def process_01(filename, compression): # Compression reduces number of channels bt 8, 4 or 2
    logger.debug(f'dispatcher.process_01({filename})')

    global counts
    global last_counts

    counts          = 0
    last_counts     = 0
    compression     = int(compression)
    t0              = time.time()
    dt              = 0
    original_bins   = 8192
    compressed_bins = int(original_bins/compression)

    settings        = []
    settings        = fn.load_settings()
    coeff_1         = settings[18]
    coeff_2         = settings[19]
    coeff_3         = settings[20]

    # Define histogram list
    hst = [0] * original_bins  # Initialize the original histogram list

    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag):

        time.sleep(1)

        # Get the current time
        t1 = time.time()

        # Calculate time difference
        dt = int(t1 - t0)

        # Fetch histogram from device
        hst = shproto.dispatcher.histogram

        # Clear counts in the last bin
        hst[-1] = 0

        # Combine every 8 elements into one for compression
        compressed_hst = [sum(hst[i:i + compression]) for i in range(0, original_bins, compression)]

        # Sum total counts
        counts = sum(compressed_hst)

        cps    = (counts - last_counts) # Strictly not cps but counts per loop in this while loop !! (need to fix)

        # The rest of your JSON data and file writing logic remains the same
        data = {
            "schemaVersion": "NPESv1",
            "resultData": {
                "startTime": t0,
                "endTime": t1,
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
        json_data = json.dumps(data, separators=(",", ":"))

        # Construct the full path to the file
        file_path = os.path.expanduser('~/impulse_data/' + filename + '.json')

        # Open the JSON file in "write" mode for each iteration
        with open(file_path, "w") as wjf:
            wjf.write(json_data)

        fn.write_cps_json(filename, cps)

        last_counts = counts

    return    

def process_02(filename, compression):
    logger.debug(f'dispatcher.process_01({filename})')

    print('process_02()')

    global counts
    global last_counts
    global total_counts  # New variable to store total counts

    counts = 0
    last_counts = 0
    total_counts = 0  # Initialize total counts
    compression = int(compression)
    t0 = time.time()
    original_bins = 8192
    compressed_bins = int(original_bins / compression)

    filename = filename + '_3d'
    file_path = os.path.expanduser('~/impulse_data/' + filename + '.json')

    settings = fn.load_settings()
    coeff_1 = settings[18]
    coeff_2 = settings[19]
    coeff_3 = settings[20]

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
            }
        }
    }

    with open(file_path, "w") as wjf:
        json.dump(initial_data, wjf, separators=(",", ":"))

    while not (shproto.dispatcher.spec_stopflag or shproto.dispatcher.stopflag):
        time.sleep(1)

        # Get the current time in microseconds
        t1 = int(time.time() * 1e6)

        # Fetch histogram and counts from device
        hst = shproto.dispatcher.histogram
        counts = sum(hst)

        # Clear counts in the last bin
        hst[-1] = 0

        # Combine every 'compression' elements into one for compression
        compressed_hst = [sum(hst[i:i + compression]) for i in range(0, original_bins, compression)]

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
        logger.debug(f'Command received (dispatcher):{_command}')
        print('process03:', _command)    


def stop():
    with shproto.dispatcher.stopflag_lock:
        shproto.dispatcher.stopflag = 1
        logger.debug('Stop flag set(dispatcher)')

def spec_stop():
    with shproto.dispatcher.spec_stopflag_lock:
        shproto.dispatcher.spec_stopflag = 1
        logger.debug('Stop flag set(dispatcher)')
        print('Stop function')

def clear():
    with shproto.dispatcher.histogram_lock:
        shproto.dispatcher.histogram        = [0] * 8192
        shproto.dispatcher.pkts01           = 0
        shproto.dispatcher.pkts03           = 0
        shproto.dispatcher.pkts04           = 0
        shproto.dispatcher.total_pkts       = 0
        shproto.dispatcher.cpu_load         = 0
        shproto.dispatcher.cps              = 0
        shproto.dispatcher.total_time       = 0
        shproto.dispatcher.lost_impulses    = 0
        shproto.dispatcher.dropped          = 0

