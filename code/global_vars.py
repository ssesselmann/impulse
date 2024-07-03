import threading
import json
import os

# Global variables
data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data_2.0")
settings_file   = os.path.join(data_directory, "_settings.json")
user_settings   = os.path.join(data_directory, "_user.json")
shapecsv        = os.path.join(data_directory, "_shape.csv")

# Flags
run_flag        = threading.Event()
run_flag_lock   = threading.Lock()
write_lock      = threading.Lock()

# Global counts and measurements
counts          = 0
elapsed         = 0
elapsed_2       = 0
counts_2        = 0
cps             = 0
temp_counts     = 0
flip            = 1

coefficients_1  = []
coefficients_2  = []
count_history   = []
histogram       = []
histogram_2     = []
histogram_3d    = []

# Tab1 Settings
theme           = "lightgray"
max_bins        = 8192
device          = 1
sample_rate     = 48000
sample_length   = 16
shapecatches    = 10
chunk_size      = 1024
stereo          = False
peakshift       = 0
# Tab2 Settings
max_counts      = 1000000
max_seconds     = 3600
filename        = "my_spectrum"
bins            = 1000
threshold       = 100
tolerance       = 50000
bin_size        = 30
t_interval      = 1
comparison      = ""
bins_2          = 10000
bin_2_size      = 30
sigma           = 0
peakfinder      = 0

calib_bin_1     = 0
calib_bin_2     = 500
calib_bin_3     = 1000

calib_e_1       = 0
calib_e_2       = 1500
calib_e_3       = 3000

coeff_1         = 1
coeff_2         = 1
coeff_3         = 0

# Tab3 settings
compression     = 8
rolling_interval= 60

def load_settings_from_json():
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            for key, value in settings.items():
                if key in ["device", "sample_rate", "chunk_size", "threshold", "tolerance", "bins", "bin_size", "max_counts", "shapecatches", "sample_length", "calib_bin_1", "calib_bin_2", "calib_bin_3", "max_seconds", "max_bins", "t_interval", "peakshift", "compression", "rolling_interval"]:
                    globals()[key] = int(value)
                elif key in ["calib_e_1", "calib_e_2", "calib_e_3", "coeff_1", "coeff_2", "coeff_3", "peakfinder", "sigma"]:
                    globals()[key] = float(value)
                else:
                    globals()[key] = value

def save_settings_to_json():
    settings = {key: globals()[key] for key in [
        "flip", "theme", "max_bins", "device", "sample_rate", "sample_length", "shapecatches", 
        "chunk_size", "stereo", "peakshift", "max_counts", "max_seconds", "filename", 
        "bins", "threshold", "tolerance", "bin_size", "t_interval", "comparison", 
        "bins_2", "bin_2_size", "sigma", "peakfinder", "calib_bin_1", "calib_bin_2", "calib_bin_3", 
        "calib_e_1", "calib_e_2", "calib_e_3", "coeff_1", "coeff_2", "coeff_3", "rolling_interval", "compression"
    ]}
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)

# Load settings on startup
load_settings_from_json()
