import pyaudio
import wave
import math
import functions as mps
import time

start = time.perf_counter()

def pulsecatcher(left_channel, audio_format, device_channels, rate, device_index, chunk, shape):

	samples =[]
	pulses = []
	p      = pyaudio.PyAudio()
	left_data = []

	# Open the selected audio input device
	stream = p.open(
	    format=audio_format,
	    channels=device_channels,
	    rate=rate,
	    input=True,
	    output=False,
	    input_device_index=device_index,
	    frames_per_buffer=chunk)

	while True:
		# Read the audio data from the stream
	    data = stream.read(chunk, exception_on_overflow=True)
	    values = list(wave.struct.unpack("%dh" % (chunk * device_channels), data))
	    # Extract every other element (left channel)
	    left_channel = values[::2]

	    
	    for i in range(len(left_channel) - 51):
	        samples = left_channel[i:i+51]  # Get the first 51 samples

	        if samples[25] >= max(samples) and (max(samples)-min(samples)) > 100 and samples[25] < 32000:
	        	# Time capture
	        	end = time.perf_counter()
	        	elapsed = int((end - start) * 1000000)
	        	# Function normalises sample to zero
	        	normalised = mps.normalise_pulse(samples)
	        	# Function calculates pulse distortion
	        	distortion = mps.distortion(normalised, shape)
	        	# Function calculates pulse height
	        	height = mps.pulse_height(normalised)
	        	# prints data to console
	        	print(elapsed,",",height,",",distortion)
	        	
        		
	    