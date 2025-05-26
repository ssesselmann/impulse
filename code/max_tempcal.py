import time
import threading
import logging
import os
import re
import global_vars
import numpy as np
import shproto.dispatcher as dispatcher

from functions import get_serial_device_information, parse_device_info
from scipy.ndimage import gaussian_filter1d
from shproto.dispatcher import process_03

from global_vars import (
    tempcal_stability_tolerance,
    tempcal_stability_window_sec,
    tempcal_poll_interval_sec,
    tempcal_spectrum_duration_sec,
    tempcal_smoothing_sigma,
    tempcal_peak_search_range,
    tempcal_cancelled,
    tempcal_base_value,
    data_directory,
    write_lock
)

np.set_printoptions(threshold=np.inf)

# Ensure the data directory exists
os.makedirs(data_directory, exist_ok=True)

# Define log file path
log_path = os.path.join(data_directory, '_tempcal.log')

# Always get the logger by a unique name
tempcal_logger = logging.getLogger('tempcal')

# Ensure the logger level is appropriate
tempcal_logger.setLevel(logging.INFO)

# Remove all existing handlers (avoid duplicates in dev)
for handler in tempcal_logger.handlers[:]:
    tempcal_logger.removeHandler(handler)

# Create a fresh file handler every time
fh = logging.FileHandler(log_path, mode='w')  # use 'a' to append instead of overwrite
fh.setLevel(logging.INFO)

# Define log format
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
fh.setFormatter(formatter)

# Add the file handler to the logger
tempcal_logger.addHandler(fh)


def run_temperature_calibration(temp_delta, base_value=global_vars.tempcal_base_value, feedback_callback=None):

    log("⚙️ Starting temperature calibration sequence...", feedback_callback)

    process_03("-tc off")

    log("🛑 Turned off temperature compensation", feedback_callback)

    # Step 1: Wait for initial stable temperature
    t0 = wait_for_stable_temperature()
    # Step 2:
    h0 = collect_spectrum()
    # Step 3:
    p0 = find_peak_bin(h0)

    with global_vars.write_lock:
        # Step 4: Store first calibration point: (sequence=0)
        global_vars.tempcal_table = [(1, round(t0), base_value)]

    log(f"📌 Recorded: seq = 1, T = {t0:.1f}°C, Peak = {p0}, Base = {base_value}", feedback_callback)

    last_temp  = t0

    sequence   = 2  # Start next sequence at 2

    # Step 2: Loop through temperature deltas
    for delta in temp_delta:
        if global_vars.tempcal_cancelled:
            log("🛑 Calibration cancelled by user.", feedback_callback)
            return

        target_temp = last_temp + delta
        
        while float(get_temperature_only()) < target_temp:

            log(f"🌡 Waiting to reach ≥ {last_temp}/{target_temp:.1f}°C...", feedback_callback)

            if global_vars.tempcal_cancelled:
                log("🛑 Calibration cancelled during wait.", feedback_callback)
                return

            time.sleep(tempcal_poll_interval_sec)    

        # Step 3: Once temperature is reached, stabilize and collect
        t_now = wait_for_stable_temperature()

        h_now = collect_spectrum()

        p_now = find_peak_bin(h_now)

        if p0 == 0:
            raise ValueError("❌ Initial peak (p0) was zero — can't divide by zero.")

        new_base = round(base_value * (p_now / p0))  # Adjust base relative to first peak

        log(f"✅ Cycle #{sequence},{round(t_now)} C˚, Base {new_base}", feedback_callback)

        global_vars.tempcal_table.append((sequence, round(t_now), new_base))

        log(f"📌 Recorded: Seq={sequence}, T={t_now:.1f}°C, Peak={p_now}, Base = {new_base}", feedback_callback)

        last_temp = t_now

        sequence += 1

    # Step 4: Send calibration table to device
    log("\n📤 Sending calibration table to device...", feedback_callback)

    # Clear previous calibration data
    process_03("-tclear")

    for seq, T, B in global_vars.tempcal_table:

        cmd = f"-t {seq} {T} {B}"

        process_03(cmd)

        time.sleep(0.5)

        log(f"✔ Command: {cmd}", feedback_callback)

        
    log("✅ Turning temperature compensation on.", feedback_callback)

    process_03("-tc on")

    time.sleep(0.5)

    log("✅ Temperature calibration complete.", feedback_callback)

    dispatcher.stopflag = 1

    if hasattr(dispatcher, "_thread"):

        dispatcher._thread.join(timeout=1)

    return


def get_temperature_only(attempts: int = 3, delay: float = 0.5) -> float:

    for attempt in range(1, attempts + 1):
        # 1) clear any previous response
        dispatcher.inf_str = ""
        
        # 2) send the command
        process_03("-inf")
        
        # 3) wait for the device to respond
        time.sleep(delay)
        
        # 4) grab whatever came back
        response = dispatcher.inf_str or ""
        #print(f"[get_temperature_only] Attempt {attempt}/{attempts}, inf_str={repr(response)}")
        
        # 5) try to parse out T1
        match = re.search(r'T1[:= ]+([0-9]+\.[0-9]+|[0-9]+)', response)
        if match:
            return float(match.group(1))
        
    # if we get here, every attempt failed
    raise ValueError(f"❌ Could not extract T1 after {attempts} attempts; last response was {repr(response)}")

def wait_for_stable_temperature(tolerance=tempcal_stability_tolerance,
                                window_sec=tempcal_stability_window_sec,
                                feedback_callback=None,
                                poll_interval=tempcal_poll_interval_sec):

    readings    = []
    stable_time = 0
    window_size = int(window_sec / poll_interval)

    log(f"🕒 Waiting for temperature to stabilize (Δ < {tolerance}°C over {window_sec}s)...", feedback_callback)

    while True:
        temp = float(get_temperature_only())
        readings.append(temp)

        if len(readings) >= window_size:
            window  = readings[-window_size:]
            delta   = max(window) - min(window)

            if delta < tolerance:
                stable_time += poll_interval
            else:
                stable_time = 0

            log(f"🌡️  T = {temp:.2f}°C | Δ = {delta:.2f}°C | stable for {stable_time}/{window_sec}s", feedback_callback)

            if stable_time >= window_sec:
                log(f"✅ Temperature stabilized at {temp:.2f}°C", feedback_callback)
                return temp
        else:
            log(f"🌡️  T = {temp:.2f}°C | gathering initial readings...", feedback_callback)

        time.sleep(poll_interval)

def collect_spectrum(duration_sec=global_vars.tempcal_spectrum_duration_sec, compression=1, feedback_callback=None):
    """Collects spectrum data for `duration_sec` seconds using dispatcher.process_01."""

    filename    = "tempcal_run"
    device      = "MAX"  # or "det", if that's correct in your build
    t_interval  = 1
    dispatcher.spec_stopflag    = 0
    dispatcher.stopflag         = 0
    # Start dispatcher thread if needed
    thread      = threading.Thread(target=dispatcher.start)
    thread.start()

    # Apply standard initialization sequence
    dispatcher.process_03('-mode 0')
    time.sleep(0.4)

    dispatcher.process_03('-rst')
    time.sleep(0.4)

    dispatcher.process_03('-sta')
    time.sleep(0.4)

    log(f"⏳ Collecting spectrum for {duration_sec} seconds...", feedback_callback)

    # Start collection thread
    spectrum_thread = threading.Thread(target=dispatcher.process_01,args=(filename, compression, device, t_interval))

    spectrum_thread.start()

    # Countdown log
    start = time.time()

    while time.time() - start < duration_sec:
        remaining = duration_sec - int(time.time() - start)
        log(f"   ...{remaining} seconds remaining", feedback_callback)
        time.sleep(10)

    # Stop the collection
    dispatcher.spec_stopflag = 1
    spectrum_thread.join(timeout=5)

    log("✅ Spectrum collection complete.", feedback_callback)

    dispatcher.process_03('-sto')
    time.sleep(0.4)

    with global_vars.write_lock:
        return global_vars.histogram.copy()

def find_peak_bin(
    histogram,
    sigma=global_vars.tempcal_smoothing_sigma,
    search_range=global_vars.tempcal_peak_search_range,
    feedback_callback=None
):

    log(f"🔍 Looking for peak with σ={sigma}, range={search_range}", feedback_callback)

    # 1) Smooth the histogram
    smoothed = gaussian_filter1d(histogram, sigma=sigma)

    # 2) Unpack and sanity‐check the range
    search_start, search_end = search_range

    if search_start < 0 or search_end < search_start:
        raise ValueError(f"❌ Invalid search_range {search_range}")
    
    if search_start >= len(smoothed):
        raise ValueError(f"❌ Search start {search_start} outside histogram size {len(smoothed)}")
    
    if search_end > len(smoothed):
        search_end = len(smoothed)  

    # 3) Extract region of interest and find its maximum
    roi = smoothed[search_start:search_end]

    if roi.size == 0:
        raise CalibrationError(f"No data in range {search_range}")

    peak_offset = int(np.argmax(roi))
    peak_index  = search_start + peak_offset

    log(f"📍 Peak found at channel {peak_index}", feedback_callback)
    return peak_index

# Define the global log() function
def log(msg, feedback_callback=None):
    print(msg)
    tempcal_logger.info(msg)
    if feedback_callback:
        feedback_callback(msg)