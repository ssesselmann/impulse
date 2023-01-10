import pyaudio
import wave
import math
import functions as mps
import pulsecatcher as pc

# Set up the audio stream
p          = pyaudio.PyAudio()
audio_format = pyaudio.paInt16
rate       = 192000
chunk      = 2048
# Set filter parameter
threshold  = 100
tolerance  = 8000

sum_pulses = []
pulses = []
average =[]
normalised = []

# Get a list of available audio input devices
device_info = p.get_host_api_info_by_index(0).get('deviceCount')
input_devices = []
for i in range(device_info):
    input_devices.append(p.get_device_info_by_host_api_device_index(0, i))

# Print the list of available input devices
for i, device in enumerate(input_devices):
        if device['name'] == 'USB AUDIO  CODEC':
                if device['maxInputChannels'] >0:
                        print(f"{i}: {device['name']} input")   
                else:
                        print(f"{i}: {device['name']} output") 
        else:
                print(f"{i}: {device['name']}")

print(' ')  # Line of space

# Prompt the user to select an input device
device_index = int(input("Enter the number of the audio input device to use: "))

print(' ') # Line of space
print('Input device Index is ', device_index)

# Get the number of channels that the selected device supports
device_channels = p.get_device_info_by_host_api_device_index(0,device_index).get('maxInputChannels')
print('Input device channels is ', device_channels)

# Print a confirmation message
print(f"Input device is {input_devices[device_index]['name']}")

# Get the format of the selected device
device_format = p.get_device_info_by_host_api_device_index(0, device_index).get('format')
print('Input device format is', device_format)

# print a blank line of space
print(' ') # Line of space
print("Calculating mean pulse shape......", "\n")
# Open the selected audio input device
stream = p.open(
    format=audio_format,
    channels=device_channels,
    rate=rate,
    input=True,
    output=False,
    input_device_index=device_index,
    frames_per_buffer=chunk)

# Read and process the audio data 200 times
for i in range(200):
    # Read the audio data from the stream
    data = stream.read(chunk, exception_on_overflow=True)
    values = list(wave.struct.unpack("%dh" % (chunk * device_channels), data))
    # Extract every other element (left channel)
    left_channel = values[::2]  
    pulses = pulses+mps.find_pulses(left_channel)

# ----------- pulse shape startup routine ------------------------

# Get list length
count = len(pulses)
# Sum lists of pulses
sum_pulses = mps.sum_pulses(pulses).tolist()
# Average sum pulses
average = mps.average_pulse(sum_pulses, count) 
# normalise sum pulses
shape = mps.normalise_pulse(average)

#----- Begin data collection --------------------------

pc.pulsecatcher(
        left_channel, 
        audio_format, 
        device_channels, 
        rate, device_index, 
        chunk, 
        shape,
        threshold,
        tolerance)

# ---------- Clean up the audio stream
stream.stop_stream()
stream.close()
p.terminate()
