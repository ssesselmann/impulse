IMPULSE
-------
Python Script MCA for gamma spectrometry.
----------------------------------------
 This program reads a stream of data from the PC sound card and picks out pulses, the pulses are subsequently filtered and written to a JSON file in a special format called [NPESv2-JSON](https://github.com/OpenGammaProject/NPES-JSON). A live histogram and counts per second can be viewed in the browser tabs. 

 The current version of Impulse is also compatible with Atom-Nano and GS-Max devices with USB serial communication.
 When used in serial device mode the already completed spectrum is retrieved from the device and the program performs the display monitor function only.
 
Installation Method (Windows, Mac or Linux)
-------------------------------------------
Step 1)
-------
Download and install the latest version of Python from the official site, consider upgrading if you are on an old version ... www.python.org

Step 2)
------- 
Download Impulse from the Github repository here https://github.com/ssesselmann/impulse

Step 3)
-------
Unzip the package to the preferred location on your drive

Step 4)
-------
Open your terminal to the command line and navigate to the folder ~/impulse-main

Step 5)
------- 
Impulse requires some additional python libraries installed, so copy and paste the following into your terminal;

Windows
```
pip install -r requirements.txt
```
Mac
```
pip3 install -r requirements_mac.txt
```
Linux
```
pip install -r requirements_pc.txt
```

Step 6)
------- 
Now run the program by typing 
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
 

Change log
------------------------

0) creating a settings database in sqlite3
1) Obtaining an indexed table of audio devices 
2) Selecting Audio input device
3) Reading the audio stream and finding pulses
4) Function to find the average sample vanues in a list of n pulses
5) Function to normalise a pulse
6) Function to save the normalised pulse as a csv file (needs changing to JSON)
7) Browser layout with tabs
8) Tab for editing settings and capturing pulse shape
9) Graph to display captured pulse
10) Function to calculate pulse distortion
11) Function to read data stream, find pulses and append counts to histogram
12) Function to save histogram in JSON format
13) Tab for displaying pulse height histogram and filter settings
14) Assigned program name "impulse"
15) Tidy up and move all styling to assets/styles.css
16) Added function to show spectrum in log scale
17) Added polynomial pulse height calibration and save calibration data
18) Completed method for subtracting a background spectrum
19) Added 482 isotope peak libraries in json format
20) Program now auto detects negative pulse direction and inverts samples
21) Modified devise list to only show input devices
22) Wrapped shape function in a try: except: in case no audio device is available.
23) Fixed an issue where the x axis changed scale when comparison was switched on.
24) Added peakfinder function with resolution notation (Bug prevents notation showing in log scale)
25) Added new function and chart to display distortion curve (useful) 
26) Added tab3 with counts per second histogram, data saves to json file
27) Improved layout compatibility with smaller screens.
28) Added user manual to tab 4
29) Added gaussian correlation trace to spectrum with sadjustable sigma
30) Tidied up appearance and moved the polynomial function, added text for gaussian correlation on tab4
31) Fixed fatal bug related to gaussian slider and saves slider position to settings
32) Fixed problem with calibration (8 March 2023 14:19 AET)
33) Fixed fatal indentation error (9 March 2023 10:38 AET)
34) Put back stop button on tab 2 (9 March 2023 19.52 AET)
35) Added option for switching theme between fun/boring (9 March 2023 23:06 AET)
36) Fixed bug in pulsecatcher.py and distortionchecker.py, pulse peak in wrong position (10 March 2023 17:00 AET)
37) Added news and updates field on tab1
38) removed duplicate pulse height calculation on pulsecatcher.py (10 March 2023 12:43 AET)
39) Rearranged settings and added pulse length in time (12 March 2023 14:00)
40) Fixed bug relating to count rates below 1 second (13 March 2023 10:30 AET)
41) Changed count rate histogram to line plot with markers and 10 sec rolling average (14 March 2023 17.39 AET)
42) Added function on tab-4 for exporting histogram file as csv
43) Added pink theme
44) Added drop down menu for comparison spectra and isotope spectra
45) Added soundbyte button which plays a chord for any spectrum
46) Changes soundbyte to play gaussian correlation instead of full histogram (cleaner sound)
47) Added a threshold line to the pulse shape chart 
48) Fixed bug with start/stop buttons causing run to stop when switching tabs.
49) Fixed y axis autorange when running difference spectrum
50) Added warning for long dead time and options for shorter pulse length
51) Added function to update calibration on prerecorded spectrum
52) Added option to stop after n seconds
53) Added tab4 with 3D Histogram
54) Minor changes to layout + remove one dependancy
55) Fixed Start and Stop buttons using threading to interrupt loop
56) Major update for use with GS-MAX 
57) Bug fix - Start button fixed
58) Added user table to local database for later use in publishing spectra
60) Added functionality for publishing spectra to a public repository.


Things to do
------------
* Build functionality for right channel recording and coincidence counting
* Build interval histogram with Dead time calculation 
* Show Subtraction in spectrum name
* Save background subtracted spectra


If anyone has requests for additional features please contact me via the "Contact us" link at gammaspectacular.com


Steven Sesselmann

Gammaspectacular.com

