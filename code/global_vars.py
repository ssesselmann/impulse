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

# Main spectrum
filename        = ""
histogram       = []
bins            = 1000
bin_size        = 30
elapsed         = 0
coefficients_1  = []
spec_notes      = ""
cps             = 0
counts          = 0
count_history   = []

# Spectrum 2 comparison
filename_2      = ""
histogram_2     = []
bins_2          = 1000
bin_size_2      = 30
counts_2        = 0
elapsed_2       = 0
coefficients_2  = []

# 3D spectrum
filename_3d     = ""
histogram_3d    = []
bins_3d         = 500
bin_size_3d     = 60
elapsed_3d      = 0
coefficients_3d = []
startTime3d     = ""
endTime3d       = ""


# Tab1 Settings
theme           = ""
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
max_bins        = 8192
threshold       = 100
tolerance       = 50000
t_interval      = 1
flip            = 1
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

# Nano settings
rolling_interval= 60
compression     = 8
