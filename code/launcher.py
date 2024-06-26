# launcher.py
import dash
import time
import os
import csv
import shutil
import logging
import functions as fn
import sqlite3 as sql
from server import app

logger              = logging.getLogger(__name__)
data_directory      = os.path.join(os.path.expanduser("~"), "impulse_data")
database            = fn.get_path(f'{data_directory}/.data_v2.db')
backup_db_filename  = "old_data.db"
backup_db           = os.path.join(data_directory, backup_db_filename)
old_db              = fn.get_path(f'{data_directory}/.data.db')
shapecsv            = fn.get_path(f'{data_directory}/shape.csv')
shapecsv_old        = fn.get_path(f'{data_directory}/shape-old.csv')

# Check if the "stereo" field exists in the settings table, and add it if it doesn't
def add_stereo_field_if_missing(conn):
    c = conn.cursor()
    c.execute("PRAGMA table_info(settings);")
    columns = [column[1] for column in c.fetchall()]
    
    if 'stereo' not in columns:
        c.execute("ALTER TABLE settings ADD COLUMN stereo BOOLEAN DEFAULT False;")
        conn.commit()
        logger.info(f'Added "stereo" field to settings table')

    if 'rolling_interval' not in columns:
        c.execute("ALTER TABLE settings ADD COLUMN rolling_interval INTEGER DEFAULT 60;")
        conn.commit()
        logger.info(f'Added "rolling_interval" field to settings table')    

if os.path.exists(old_db):
        # Rename the old database
        os.rename(old_db, backup_db)
        logger.info(f"Old database renamed to {backup_db}")

try:
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        logger.info(f'Created new data directory {data_directory}')

except:
    pass

try:
    if not os.path.exists(shapecsv):
        fn.create_dummy_csv(shapecsv)
        logger.info(f'Created a blank shape.csv file')
    else:
        try:
            # Open the CSV file and determine the number of columns
            with open(shapecsv, 'r', newline='') as file:
                reader = csv.reader(file)
                headers = next(reader, None)
                if headers and len(headers) == 2:  # Check if there are exactly two columns
                    # Rename the file if it has two columns
                    os.rename(shapecsv, shapecsv_old)
                    logger.info(f'Renamed shape.csv to shape_old.csv')
                    # Create a new dummy CSV with three columns
                    fn.create_dummy_csv(shapecsv)
                    logger.info(f'Created a new shape.csv with three columns')
        except Exception as e:
            logger.error(f'Failed to process the CSV file: {str(e)}')
except:
    pass

# Connects to database
conn    = sql.connect(database)
c       = conn.cursor()

try:
    # Add the stereo field if it is missing
    add_stereo_field_if_missing(conn)
except:
    logger.info(f'Attempted to add stereo field but database does not exist yet')
    pass
    
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
        compression     INTEGER DEFAULT 8,
        stereo          BOOLEAN DEFAULT False,
        rolling_interval INTEGER DEFAULT 60               
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
    logger.info(f'Created new database tables if required')


# Set the paths for isotopes and tbl folders
isotopes = "i"
tbl = "tbl"
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

