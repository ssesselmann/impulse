# launcher.py
import dash
import time
import os
import shutil
import logging
import functions as fn
import sqlite3 as sql
from server import app

logger = logging.getLogger(__name__)

data_directory = os.path.join(os.path.expanduser("~"), "impulse_data")

database = fn.get_path(f'{data_directory}/.data_v2.db')
old_db = fn.get_path(f'{data_directory}/.data.db')

logger.info('Created a new database .data_v2.db')

if os.path.exists(old_db):
        # Create a new name for the old database
        backup_db_filename = "old_data.db"
        backup_db = os.path.join(data_directory, backup_db_filename)
        # Rename the old database
        os.rename(old_db, backup_db)
        logger.info(f"Old database renamed to {backup_db}")


shapecsv = fn.get_path(f'{data_directory}/shape.csv')

try:
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
except:
    pass

try:
    if not os.path.exists(shapecsv):
        fn.create_dummy_csv(shapecsv)
except:
    pass

# Connects to database
conn    = sql.connect(database)
c       = conn.cursor()

# This query creates a table in the database when used for the first time
query   = """CREATE TABLE IF NOT EXISTS settings (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,  
        name            TEXT    DEFAULT 'my_spectrum',      
        device          INTEGER DEFAULT 1,                           
        sample_rate     INTEGER DEFAULT 48000,             
        chunk_size      INTEGER DEFAULT 1024,               
        threshold       INTEGER DEFAULT 100,                
        tolerance       INTEGER DEFAULT 50000,              
        bins            INTEGER DEFAULT 1000,               
        bin_size        INTEGER DEFAULT 30,                 
        max_counts      INTEGER DEFAULT 1000000,              
        shapecatches    INTEGER DEFAULT 10,                 
        sample_length   INTEGER DEFAULT 16,                 
        calib_bin_1     INTEGER DEFAULT 0,                  
        calib_bin_2     INTEGER DEFAULT 500,                
        calib_bin_3     INTEGER DEFAULT 1000,               
        calib_e_1       REAL    DEFAULT 0,                  
        calib_e_2       REAL    DEFAULT 1500,               
        calib_e_3       REAL    DEFAULT 3000,               
        coeff_1         REAL    DEFAULT 1,                  
        coeff_2         REAL    DEFAULT 1,                  
        coeff_3         REAL    DEFAULT 0,                  
        comparison      TEXT    DEFAULT '',                 
        flip            INTEGER DEFAULT 1,                  
        peakfinder      REAL    DEFAULT 0,
        theme           TEXT    DEFAULT 'lightgray',
        sigma           REAL    DEFAULT 0,
        max_seconds     INTEGER DEFAULT 3600,
        t_interval      INTEGER DEFAULT 1,
        peakshift       INTEGER DEFAULT 0,
        compression     INTEGER DEFAULT 8               
        );"""

# This query inserts the first record in settings with defaults
query2  =  f'INSERT INTO settings (id, name) SELECT 0, "myspectrum" WHERE NOT EXISTS (SELECT 1 FROM settings WHERE id = 0);'


query3 = """CREATE TABLE IF NOT EXISTS user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    DEFAULT 'first_name',
    first_name_f    BOOLEAN DEFAULT 1,
    last_name       TEXT    DEFAULT 'last_name',
    last_name_f     BOOLEAN DEFAULT 1,
    institution     TEXT    DEFAULT 'institution',
    institution_f   BOOLEAN DEFAULT 1,
    city            TEXT    DEFAULT 'city',
    city_f          BOOLEAN DEFAULT 1,
    country         TEXT    DEFAULT 'country',
    country_f       BOOLEAN DEFAULT 1,    
    email           TEXT    DEFAULT 'user@domain.com',
    email_f         BOOLEAN DEFAULT 0,
    phone           TEXT    DEFAULT 'prefix + phone',
    phone_f         BOOLEAN DEFAULT 0,
    website         TEXT    DEFAULT 'www.yourdomain.com',
    website_f       BOOLEAN DEFAULT 1,
    social_url      TEXT    DEFAULT 'www.facebook.com',
    social_url_f    BOOLEAN DEFAULT 1,
    notes           TEXT    DEFAULT 'notes about my research',
    notes_f         BOOLEAN DEFAULT 1,
    api_key         TEXT    DEFAULT 'xyz'
    );"""

# This query inserts the first record in settings with defaults
query4  =  f'INSERT INTO user (id, first_name) SELECT 0, "first_name" WHERE NOT EXISTS (SELECT 1 FROM user WHERE id = 0);'

# This excecutes the sqli query
with conn:
    c.execute(query).execute(query2).execute(query3).execute(query4)
    conn.commit()

# This script places the isotope sample spectra into the data directory when the program is run the first time
isotopes = "i"
data_directory_path = os.path.join(data_directory, isotopes)

if not os.path.exists(data_directory_path):
    isotope_folder_path = os.path.join(os.getcwd(), isotopes)
    if os.path.exists(isotope_folder_path):
        shutil.copytree(isotope_folder_path, data_directory_path)




