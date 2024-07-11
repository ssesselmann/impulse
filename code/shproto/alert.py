import time  # Importing the 'time' module
import shproto.dispatcher  # Importing the 'dispatcher' module from the 'shproto' package
import statistics  # Importing the 'statistics' module for mathematical statistics functions
import threading  # Importing the 'threading' module for multi-threading support
import os  # Importing the 'os' module for interacting with the operating system
import logging

# Initialize global variables
avg_cps = 0  # Global variable to store average cycles per second
alert_rised = 0  # Global variable to indicate if an alert is currently raised

# Initialize variables related to alert mode and synchronization
alert_stop = 0  # Global variable to control the stopping of the alert mode
alert_stop_lock = threading.Lock()  # Lock for synchronizing access to the alert_stop variable

# Parameters for averaging cycles and timeout values
avg_cycles = 30  # Number of cycles to collect for calculating average
avg_cycles_timeout = 5  # Timeout duration for each cycle in seconds

# Parameters for relaxation cycles and alert loop timeout
relax_cycles = 5  # Number of cycles to wait before deactivating alert mode
relax_ratio = 1.1  # Ratio for relaxing the alert condition
alert_loop_timeout = 5  # Timeout duration for each iteration of the alert loop in seconds

# Directory for storing spectrum data
spec_dir = os.path.expanduser("~/nanopro_data/")

# Function to enter alert mode based on a specified CPS ratio
def alertmode(spec_dir, cps_ratio=1.5):
    count = 0  # Counter for the number of cycles collected for averaging
    cps_arr = []  # List to store CPS values for averaging
    logger.info("Collecting average CPS, this will take about {} seconds.\n".format(avg_cycles * avg_cycles_timeout))
    
    # Collect average CPS values
    while count <= avg_cycles:
        with shproto.dispatcher.cps_lock:
            current_cps = shproto.dispatcher.cps
        if current_cps > 0:
            cps_arr.append(current_cps)
            avg_cps = statistics.median(cps_arr)
            count += 1
        time.sleep(avg_cycles_timeout)
    
    logger.info("Average CPS collected: {}, starting alert mode.\n".format(avg_cps))
    
    cur_relax_cycles = 0
    fd = None
    
    while True:
        with alert_stop_lock:
            if alert_stop:
                break
        
        with shproto.dispatcher.cps_lock:
            current_cps = shproto.dispatcher.cps
        
        if not alert_rised:
            if current_cps >= cps_ratio * avg_cps:
                ts = time.localtime()
                filename = "{}alert_{}_{}_{}__{}_{}_{}".format(spec_dir,
                                                               ts.tm_mday,
                                                               ts.tm_mon,
                                                               ts.tm_year,
                                                               ts.tm_hour,
                                                               ts.tm_min,
                                                               ts.tm_sec)
                print("Alert raised. Current CPS = {} > Avg CPS = {}. Start writing spectrum to {}".format(
                    current_cps,
                    avg_cps,
                    filename))
                fd = open(filename, "w")
                alert_rised = 1
        else:
            if current_cps <= current_cps * relax_ratio:
                cur_relax_cycles += 1
            else:
                fd.seek(0)
                for i in range(0, 8192):
                    fd.writelines("{}, {}\r\n".format(i + 1, shproto.dispatcher.histogram[i]))
                fd.flush()
                fd.truncate()
            
            if cur_relax_cycles > relax_cycles:
                logger.info("Alert gone. Current CPS = {}, for {} seconds\n".format(current_cps, relax_cycles * alert_loop_timeout))
                alert_rised = 0
                fd.close()
        
        time.sleep(alert_loop_timeout)
    
    logger.info("Exit alert mode.\n")

# Function to stop the alert mode
def stop():
    with alert_stop_lock:
        alert_stop = 1
