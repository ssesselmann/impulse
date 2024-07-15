import threading
import json
import os

# Flags
run_flag        = threading.Event()
run_flag_lock   = threading.Lock()
write_lock      = threading.Lock()

# Global variables
data_directory  = ""
settings_file   = ""
user_settings   = ""
shapecsv        = ""

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
spec_notes      = ""

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
log_switch      = False
epb_switch      = False
cal_switch      = False
coi_switch      = False

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

