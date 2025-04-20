IMPULSE
-------
Python Script MCA for gamma spectrometry.
----------------------------------------
 This program reads a stream of data from the PC sound card and picks out pulses, the pulses are subsequently filtered and written to a JSON file in a special format called [NPESv2-JSON](https://github.com/OpenGammaProject/NPES-JSON). A live histogram and counts per second can be viewed in the browser tabs. 

 The current version of Impulse is also compatible with Atom-Nano and GS-Max devices with USB serial communication.
 When used in serial device mode the already completed spectrum is retrieved from the device and the program performs the display monitor function only.
 
The Easy Way
------------
Not too concerned about downloading the latest changes and just want to try Impulse ? 
Download the precompiled executable for Mac or Windows from Gammaspectacular.com

https://www.gammaspectacular.com/blue/software-downloads/impulse


Raw Code Installation Method (Windows, Mac or Linux)
-------------------------------------------
Step 1)
-------
Download and install the latest version of Python from the official site, consider upgrading if you are on an old version ... www.python.org

Step 2)
------- 
Download Impulse from the Github repository here https://github.com/ssesselmann/impulse

Step 3)
-------
Unzip the package to the preferred location on your drive, something like ~/python/ for all your python scripts.

Step 4)
-------
Open your terminal to the command line and navigate to the folder ~/python/impulse-main

Step 5)
------- 
Impulse requires some additional python libraries installed, so copy and paste the following into your terminal;

First you will need to install or upgrade pip, pip is a catalogue of available python extensions.

Install or upgrade to the latest version of pip..
```
python -m pip install --upgrade pip
```
Windows or Linux
```
pip install -r requirements_pc.txt
```
Mac
```
pip3 install -r requirements_mac.txt
```


Step 6)
------- 
Now from the impulse-main directory run the program by typing 
```
python code/impulse.py
```
mac users may have to type
```
python3 code/impulse.py
```
Fingers crossed your default browser should open up and show tab 1

Troubleshooting
---------------
Look for any error messages in the terminal. A common problem is a missing library, if so try installing it separatelly.
```
pip install ??????
```

Always exit the program from tab 4 by clicking the exit button (important)

When it's all working you can access the program in your browser at;

http://localhost:8050
 


Requests
------------

* Build interval histogram with Dead time calculation 
* Show Subtraction in spectrum name
* Save background subtracted spectra


If anyone has requests for additional features please contact me via the "Contact us" link at gammaspectacular.com


Steven Sesselmann

Gammaspectacular.com

