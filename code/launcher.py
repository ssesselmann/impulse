# launcher.py
import dash
import time
import os
import csv
import shutil
import logging
import json
import global_vars
from server import app
import functions as fn  

logger                  = logging.getLogger(__name__)

data_directory          = os.path.join(os.path.expanduser("~"), "impulse_data_2.0")
settings_file           = os.path.join(data_directory, "_settings.json")
user_file               = os.path.join(data_directory, "_user.json")
shapecsv                = os.path.join(data_directory, "_shape.csv")

print(f'in launcher theme = {global_vars.theme}')

with global_vars.write_lock:
    global_vars.data_directory = data_directory
    global_vars.settings_file  = settings_file
    global_vars.user_settings  = user_file
    global_vars.shapecsv       = shapecsv

default_settings = {
    "filename": "my_spectrum",
    "device": 1,
    "sample_rate": 48000,
    "chunk_size": 1024,
    "threshold": 100,
    "tolerance": 50000,
    "bins": 1000,
    "bin_size": 30,
    "bins_2": 1000,
    "bin_2_size": 30,
    "max_counts": 1000000,
    "shapecatches": 10,
    "sample_length": 16,
    "calib_bin_1": 0,
    "calib_bin_2": 500,
    "calib_bin_3": 1000,
    "calib_e_1": 0,
    "calib_e_2": 1500,
    "calib_e_3": 3000,
    "coeff_1": 1,
    "coeff_2": 1,
    "coeff_3": 0,
    "comparison": "",
    "flip": 1,
    "peakfinder": 0,
    "log_switch": False,
    "epb_switch": False,
    "cal_switch": False,
    "theme": "lightgray",
    "sigma": 0,
    "max_seconds": 3600,
    "t_interval": 1,
    "peakshift": 0,
    "compression": 8,
    "stereo": False,
    "rolling_interval": 60,
    "coefficients_1":[],
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

try:
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        logger.info(f'Created new data directory {data_directory}\n')
except Exception as e:
    logger.error(f'Failed to create data directory: {str(e)}\n')

try:
    if not os.path.exists(shapecsv):
        fn.create_dummy_csv(shapecsv)
        logger.info(f'Created a blank shape.csv file \n')
    else:
        try:
            # Open the CSV file and determine the number of columns
            with open(shapecsv, 'r', newline='') as file:
                reader = csv.reader(file)
                headers = next(reader, None)
        except Exception as e:
            logger.error(f'Failed to process the CSV file: {str(e)}\n')
except Exception as e:
    logger.error(f'Error during initialization: {str(e)}\n')

# Ensure the settings and user files exist
create_file_if_not_exists(settings_file, default_settings)
create_file_if_not_exists(user_file, default_user)


# Set the paths for isotopes and tbl folders
isotopes    = "i"
tbl         = "tbl"
data_directory_path = os.path.join(data_directory, isotopes)
tbl_directory_path = os.path.join(data_directory_path, tbl)

# Check if the isotope folder exists in the data directory, if not, copy it
if not os.path.exists(data_directory_path):
    isotope_folder_path = os.path.join(os.getcwd(), isotopes)
    if os.path.exists(isotope_folder_path):
        shutil.copytree(isotope_folder_path, data_directory_path)

# Check if the tbl folder exists within the isotope folder, if not, copy it
if not os.path.exists(tbl_directory_path):
    tbl_folder_path = os.path.join(os.getcwd(), isotopes, tbl)
    if os.path.exists(tbl_folder_path):
        shutil.copytree(tbl_folder_path, tbl_directory_path)

with global_vars.write_lock:
    filename    = global_vars.filename
    comparison  = global_vars.comparison
    
fn.load_settings_from_json(settings_file)

logger.info(f'1... {filename} loaded\n')

fn.load_histogram(filename)

logger.info(f'2...2D {filename} loaded\n')

fn.load_histogram_2(comparison)

logger.info(f'3...2D {comparison} loaded\n')

fn.load_histogram_3d(filename)

logger.info(f'4...3D {filename} loaded\n')

fn.load_cps_file(filename)

logger.info(f'5...cps {filename} loaded\n')        


if __name__ == "__main__":
    app.run_server(debug=True)

# -- End of launcher.py