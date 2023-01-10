# Reads data in CHUNK and looks for pulse peaks in position 26 of a 51 number array
# Repeats x times
# Calculates zip average
import pyaudio
import wave
import numpy as np

peak = 0.0
trough = 0.0
height = 0.0
p = pyaudio.PyAudio()


# Finds pulses in data over a given threshold
def find_pulses(left_channel):
    pulses = []
    for i in range(len(left_channel) - 51):
        samples = left_channel[i:i+51]  # Get the first 51 samples
        if samples[25] >= max(samples) and (max(samples)-min(samples)) > 1000 and samples[25] < 32000:
            pulses.append(samples)
            print(pulses[0]) # For debugging
    return pulses

def running_pulses(left_channel, audio_format, device_channels, rate, device_index, chunk):
    # Open the selected audio input device
    stream = p.open(
        format=audio_format,
        channels=device_channels,
        rate=rate,
        input=True,
        output=False,
        input_device_index=device_index,
        frames_per_buffer=chunk)
    pulses = []
    data = stream.read(chunk, exception_on_overflow=True)
    values = list(wave.struct.unpack("%dh" % (chunk * device_channels), data))
    # Extract every other element (left channel)
    left_channel = values[::2]

    for i in range(len(left_channel) - 51):
        samples = left_channel[i:i+51]  # Get the first 51 samples
        if samples[25] >= max(samples) and (max(samples)-min(samples)) > 100 and samples[25] < 32000:
            pulses.append(samples)
    
    return pulses   

#
def sum_pulses(pulses):
    pulse_shape = np.zeros(51,dtype=int)
    for i in range(len(pulses)):      
        pulse_shape = np.add(pulse_shape, pulses[i])                
    return pulse_shape     

# Calculates the average pulse shape
def average_pulse(sum_pulse, count):       
    average = []
    for x in sum_pulse:
        average.append(x / count)
    return average 

# Normalises the average pulse shape
def normalise_pulse(average):
    normalised = []
    mean = sum(average) / len(average)   
    normalised = [n - mean for n in average]  
    return normalised

def shape_filter(pulse):
    passed = []
    pulse = pulse[0]
    if pulse[25] >= max(pulse) and (max(pulse)-min(pulse)) > 100 and pulse[25] < 32000:
        return passed

def pulse_height(passed):
    passed = passed[0]   
    peak = passed[passed.index(max(passed))]
    trough = passed[passed.index(min(passed))]
    height = peak-trough

    return height