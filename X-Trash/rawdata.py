import pyaudio
import wave
import math

# Set up the audio stream
p          = pyaudio.PyAudio()
FORMAT     = pyaudio.paInt16
CHANNELS   = 2
RATE       = 48000
CHUNK      = 2048
pi         = math.pi

# Get a list of available audio input devices
device_info = p.get_host_api_info_by_index(0).get('deviceCount')
input_devices = []
for i in range(device_info):
  #      if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
        input_devices.append(p.get_device_info_by_host_api_device_index(0, i))
 #       else:
 #              input_devices.append()

# Print the list of available input devices
for i, device in enumerate(input_devices):
        if device['name'] == 'USB AUDIO  CODEC':
                if device['maxInputChannels'] >0:
                        print(f"{i}: {device['name']} input")   
                else:
                        print(f"{i}: {device['name']} output") 
        else:
                print(f"{i}: {device['name']}")

print(' ')        

# Prompt the user to select an input device
device_index = int(input("Enter the number of the audio input device to use: "))

# print a blank line of space
print(' ')

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
print(' ')


# Open the selected audio input device
stream = p.open(
    format=FORMAT,
    channels=device_channels,
    rate=RATE,
    input=True,
    output=False,
    input_device_index=device_index,
    frames_per_buffer=CHUNK)

prev_sample = 0  # Initialize the previous sample to 0
chunk_data = []  # Initialize the chunk data list


# Read and process the audio data in a loop
while True:
    # Read the audio data from the stream
    data = stream.read(CHUNK, exception_on_overflow=True)

    # Unpack the data and print the values to the console
    values = list(wave.struct.unpack("%dh" % (CHUNK * CHANNELS), data))
    left_channel = values[::2]  # Extract every other element (left channel)
    #print(left_channel)


    # Iterate over the left channel samples
    for sample in left_channel:
        if sample >= 100 + prev_sample:  # Check if the sample is greater than the previous sample by 100 or more
            # Save 29 samples before the trigger and 30 samples after the trigger
            chunk_data = left_channel[left_channel.index(sample) - 29:left_channel.index(sample) + 30]
            

        # Calculate the mean of the chunk data
            mean = sum(chunk_data) / len(chunk_data)
            # Subtract the mean from each sample and square the result
            squared = [(sample - mean) ** 2 for sample in chunk_data]
            # Calculate the mean of the squared values
            rms = math.sqrt(sum(squared) / len(squared)) * pi
            print(int(rms))  # Print the mean of squares
        prev_sample = sample  # Update the previous sample

# Clean up the audio stream
stream.stop_stream()
stream.close()
p.terminate()
