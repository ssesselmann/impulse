import wave

# Set the audio parameters
num_channels = 1
sample_width = 2
sample_rate = 48000
num_frames = 48000  # One second of audio

# Open a wave file for writing
wave_file = wave.open('audio/sample.wav', 'w')

# Set the audio parameters
wave_file.setnchannels(num_channels)
wave_file.setsampwidth(sample_width)
wave_file.setframerate(sample_rate)

# Create a blank audio buffer
audio_buffer = b'\x00' * num_frames * num_channels * sample_width

# Write the audio data to the wave file
wave_file.writeframes(audio_buffer)

# Close the wave file
wave_file.close()
