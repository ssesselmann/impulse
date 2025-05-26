import sys
import os
import shutil
import logging
import json
import global_vars
from server import app
import functions as fn  
import dash

logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Define paths
data_directory  = os.path.join(os.path.expanduser("~"), "impulse_data_2.0")
settings_file   = os.path.join(data_directory, "_settings.json")
user_file       = os.path.join(data_directory, "_user.json")
shapecsv        = os.path.join(data_directory, "_shape.csv")
i_directory     = os.path.join(data_directory, "i")
tbl_directory   = os.path.join(i_directory, "tbl")
shortlist       = os.path.join(data_directory, i_directory, tbl_directory, "gamma-a.json")
longlist        = os.path.join(data_directory, i_directory, tbl_directory, "gamma-b.json")

# Set global variables
with global_vars.write_lock:
    global_vars.data_directory  = data_directory
    global_vars.settings_file   = settings_file
    global_vars.user_settings   = user_file
    global_vars.shapecsv        = shapecsv

# Default settings and user data
default_settings = {
    "bin_size": 10,
    "bin_size_2": 10,
    "bin_size_3d": 60,
    "bins": 3000,
    "bins_2": 3000,
    "bins_3d": 500,
    "supress_last_bin": False,
    "cal_switch": False,
    "calib_bin_1": 1500,
    "calib_bin_2": 0,
    "calib_bin_3": 0,
    "calib_bin_4": 0,
    "calib_bin_5": 0,
    "calib_e_1": 1500,
    "calib_e_2": 0,
    "calib_e_3": 0,
    "calib_e_4": 0,
    "calib_e_5": 0,
    "chunk_size": 2048,
    "coeff_1": 1,
    "coeff_2": 1,
    "coeff_3": 0,
    "coefficients_1": [],
    "coi_switch": False,
    "coi_window": 2,
    "compression": 8,
    "compression3d": 16,
    "device": 1,
    "epb_switch": False,
    "filename": "my-spectrum",
    "filename_2": "background",
    "filename_3d": "my-3d-spectrum",
    "flip": 11,
    "log_switch": False,
    "max_counts": 1000000,
    "max_seconds": 3600,
    "max_bins": 1000,
    "peakfinder": 0,
    "peakshift": 0,
    "rolling_interval": 60,
    "sample_length": 16,
    "sample_rate": 48000,
    "shapecatches": 10,
    "sigma": 0,
    "stereo": False,
    "t_interval": 1,
    "theme": "light-theme",
    "threshold": 100,
    "tolerance": 50000,
    "shape_lld": 500,
    "shape_uld": 10000,
    "flags_selected":"",
    "tempcal_table": [],
    "tempcal_stability_tolerance": 0.5,
    "tempcal_stability_window_sec": 300,
    "tempcal_poll_interval_sec": 10,
    "tempcal_spectrum_duration_sec": 60,
    "tempcal_smoothing_sigma": 1.5,
    "tempcal_peak_search_range": [1500, 6000],
    "tempcal_cancelled": False,
    "tempcal_base_value": 18300,
    "tempcal_num_runs": 2,
    "tempcal_delta": 5
}

default_user = {
    "first_name": "first_name",
    "first_name_f": True,
    "last_name": "last_name",
    "last_name_f": True,
    "institution": "institution",
    "institution_f": True,
    "city": "city",
    "city_f": True,
    "country": "country",
    "country_f": True,
    "email": "user@domain.com",
    "email_f": False,
    "phone": "prefix + phone",
    "phone_f": False,
    "website": "https://yourdomain.com",
    "website_f": True,
    "social_url": "social url",
    "social_url_f": True,
    "notes": "notes about my research",
    "notes_f": True,
    "api_key": "click request api and copy code from email"
}

def create_file_if_not_exists(file_path, default_content):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(default_content, f, indent=4)
        logger.info(f'Created new file at {file_path}\n')

# 1. Check if data directory exists, if not create it
if not os.path.exists(data_directory):
    os.makedirs(data_directory)
    logger.info(f'Created new data directory {data_directory}\n')

# 2. Check if _settings.json file exists, if not create the file
create_file_if_not_exists(settings_file, default_settings)

# 3. Check if _user.json file exists, if not create it
create_file_if_not_exists(user_file, default_user)

# 4. Check if there is an "i" directory in the data directory, if not copy it from resources
if not os.path.exists(i_directory):
    isotope_folder_path = resource_path("i")
    if os.path.exists(isotope_folder_path):
        shutil.copytree(isotope_folder_path, i_directory)
        logger.info(f'Copied i directory to {i_directory}\n')
# 5. Check if there is a "tbl" directory in the "i" directory, if not copy it from resources
if not os.path.exists(tbl_directory):
    tbl_folder_path = resource_path(os.path.join("i", "tbl"))
    if os.path.exists(tbl_folder_path):
        shutil.copytree(tbl_folder_path, tbl_directory)
        logger.info(f'Copied tbl directory to {tbl_directory}\n')

# 6. Check if "gamma-a.json" exists in the i_directory, if not copy it from resources
if not os.path.exists(shortlist):  # Check if gamma-a.json exists
    source_a = os.path.join(resource_path("i"), "tbl", "gamma-a.json")  # Path to the source gamma-a.json
    if os.path.exists(source_a):  # Ensure the source files exists
        shutil.copy(source_a, shortlist)  # Copy the file to the destination
        logger.info(f'Copied gamma-a.json to i/tbl\n')
    else:
        logger.warning(f'Source file gamma-a.json does not exist at {source_a}\n')

# 7. Check if "gamma-a.json" exists in the i_directory, if not copy it from resources
if not os.path.exists(longlist):  # Check if gamma-a.json exists
    source_b = os.path.join(resource_path("i"), "tbl", "gamma-b.json")  # Path to the source gamma-a.json
    if os.path.exists(source_b):  # Ensure the source files exists
        shutil.copy(source_b, longlist)  # Copy the file to the destination
        logger.info(f'Copied gamma-b.json to i/tbl\n')
    else:
        logger.warning(f'Source file gamma-b.json does not exist at {source_a}\n')        

with global_vars.write_lock:
    filename    = global_vars.filename
    filename_2  = global_vars.filename_2
    filename_3d = global_vars.filename_3d

try:
    fn.load_settings_from_json(settings_file)
    time.sleep(1)
    logger.info(f'1...{settings_file} loaded\n')
except:
     logger.info(f'Loading settings failed\n')   

try:
    fn.load_histogram(filename)
    logger.info(f'2...2D {filename}.json loaded\n')
except:
     logger.info(f'Loading {filename}.json failed\n')  
try:
    fn.load_histogram_2(filename_2)
    logger.info(f'3...2D {filename_2}.json loaded\n')
except:
     logger.info(f'Loading {filename_2}.json failed\n') 
try:
    fn.load_cps_file(filename)
    logger.info(f'4...cps {filename}_cps.json loaded\n')
except:
     logger.info(f'Loading {filename}_cps.json failed\n')    

if __name__ == "__main__":
    app.run_server(debug=True)
