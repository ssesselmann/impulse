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
data_directory = os.path.join(os.path.expanduser("~"), "impulse_data_2.0")
settings_file = os.path.join(data_directory, "_settings.json")
user_file = os.path.join(data_directory, "_user.json")
shapecsv = os.path.join(data_directory, "_shape.csv")
i_directory = os.path.join(data_directory, "i")
tbl_directory = os.path.join(i_directory, "tbl")

# Set global variables
with global_vars.write_lock:
    global_vars.data_directory = data_directory
    global_vars.settings_file = settings_file
    global_vars.user_settings = user_file
    global_vars.shapecsv = shapecsv

# Default settings and user data
default_settings = {
    "bin_size": 30,
    "bin_size_2": 30,
    "bin_size_3d": 60,
    "bins": 1000,
    "bins_2": 1000,
    "bins_3d": 500,
    "cal_switch": False,
    "calib_bin_1": 0,
    "calib_bin_2": 250,
    "calib_bin_3": 500,
    "calib_bin_4": 750,
    "calib_bin_5": 1000,
    "calib_e_1": 0,
    "calib_e_2": 750,
    "calib_e_3": 1500,
    "calib_e_4": 2250,
    "calib_e_5": 3000,
    "chunk_size": 2048,
    "coeff_1": 1,
    "coeff_2": 1,
    "coeff_3": 0,
    "coefficients_1": [],
    "coi_switch": False,
    "compression": 8,
    "device": 1,
    "epb_switch": False,
    "filename": "my_spectrum",
    "filename_2": "background",
    "filename_3d": "my_spectrum",
    "flip": 1,
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
    "theme": "plasma",
    "threshold": 100,
    "tolerance": 50000,
    "shape_lld": 500,
    "shape_uld": 3000
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

with global_vars.write_lock:
    filename    = global_vars.filename
    filename_2  = global_vars.filename_2
    filename_3d = global_vars.filename_3d

try:
    fn.load_settings_from_json(settings_file)
    logger.info(f'1... {filename} loaded\n')
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
