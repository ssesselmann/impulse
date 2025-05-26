import threading
import json
import os

# for caching the last “-inf” + “-cal” query
cached_device_info    = None
cached_device_info_ts = 0.0
serial_number = 0

# Flags
run_flag        = threading.Event()
run_flag_lock   = threading.Lock()
write_lock      = threading.Lock()

# Global variables
data_directory  = ""
settings_file   = ""
user_settings   = ""
shapecsv        = ""

# Main spectrum
filename        = "my_spectrum"
histogram       = []
bins            = 1000
bin_size        = 30
elapsed         = 0
coefficients_1  = []
spec_notes      = ""
cps             = 0
counts          = 0
dropped_counts  = 0
count_history   = []
compression     = 1
polynomial_fn   = ""
max_pulse_shape = []
suppress_last_bin = False
max_pulse_length = 20
max_pulse_height = 3000
flags_selected   = ""

# Spectrum 2 comparison
filename_2      = "background"
histogram_2     = []
bins_2          = 1000
bin_size_2      = 30
counts_2        = 0
elapsed_2       = 0
coefficients_2  = []

# 3D spectrum
filename_3d     = "my_3d_spectrum"
histogram_3d    = []
bins_3d         = 500
bin_size_3d     = 60
elapsed_3d      = 0
coefficients_3d = []
startTime3d     = ""
endTime3d       = ""
compression3d   = 16


# Tab1 Settings
theme           = "light-theme"
device          = 1
sample_rate     = 48000
sample_length   = 16
shapecatches    = 10
chunk_size      = 1024
stereo          = False
peakshift       = 0
shape_lld       = 500
shape_uld       = 10000

# Tab2 Settings
max_counts      = 1000000
max_seconds     = 3600
max_bins        = 8192
threshold       = 100
tolerance       = 50000
t_interval      = 1
flip            = 1
sigma           = 0
peakfinder      = 0
coi_window      = 2
val_flag        = False

log_switch      = False
epb_switch      = False
cal_switch      = False
coi_switch      = False

calib_bin_1     = 0
calib_bin_2     = 0
calib_bin_3     = 0
calib_bin_4     = 0
calib_bin_5     = 0

calib_e_1       = 0
calib_e_2       = 0
calib_e_3       = 0
calib_e_4       = 0
calib_e_5       = 0

coeff_1         = 1
coeff_2         = 1
coeff_3         = 0

# Nano settings
rolling_interval= 60

# temperature Compensation
tempcal_table                   = []
tempcal_stability_tolerance     = 0         # °C threshold for stability
tempcal_stability_window_sec    = 0         # seconds to hold stable temperature
tempcal_poll_interval_sec       = 0         # seconds between temperature polls
tempcal_spectrum_duration_sec   = 0         # seconds per spectrum collection
tempcal_smoothing_sigma         = 0         # Gaussian smoothing factor
tempcal_peak_search_range       = []        # bin range to search for the photopeak
tempcal_cancelled               = False     # Cancelled
tempcal_base_value              = 0         # Max integral value
tempcal_num_runs                = 2         # Number of calibration points
tempcal_delta                   = 5         # Temperature difference between runs



