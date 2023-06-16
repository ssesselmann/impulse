import os
import numpy as np
import simpleaudio as sa
import scipy.io.wavfile as wavfile

data_directory = os.path.join(os.path.expanduser("~"), "impulse_data")

def make_wav_file(filename, numbers):
    # Normalize the list of numbers to be between 0 and 1
    volume_array = np.array(numbers) / max(numbers)
    
    # Define the starting frequency and octave size
    base_frequency = 440  # A4 note
    octave_size = 12      # number of semitones in an octave
    
    # Generate the frequency array
    frequency_array = base_frequency * 2 ** (np.arange(len(numbers)) / octave_size)
    
    # Generate the time and signal arrays for a 3-second sound
    duration = 3          # duration of the sound in seconds
    sampling_rate = 48000 # number of samples taken per second
    time_array = np.arange(duration * sampling_rate) / sampling_rate
    signal_array = np.sin(2 * np.pi * np.outer(frequency_array, time_array))
    
    # Scale the signal array by the volume array and combine the channels
    scaled_signal = (signal_array.T * volume_array).T
    combined_signal = np.sum(scaled_signal, axis=0)
    
    # Scale the signal to be between -32767 and 32767 (16-bit range)
    scaled_signal = np.int16(combined_signal / np.max(np.abs(combined_signal)) * 32767)
    
    # Save the audio file
    wavfile.write(f'{data_directory}/{filename}.wav', sampling_rate, scaled_signal)

    return

def play_wav_file(filename):

    filename = f'{data_directory}/{filename}.wav'

    # Load the WAV file
    wave_obj = sa.WaveObject.from_wave_file(filename)
    
    # Create a new audio play instance and play the sound
    play_obj = wave_obj.play()
    
    # Wait for the sound to finish playing
    play_obj.wait_done()

