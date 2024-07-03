#audio_spectrum.py
import os
import numpy as np
import scipy.io.wavfile as wavfile
import pyaudio
import wave
import global_vars

data_directory = global_vars.data_directory

def make_wav_file(filename, gc):
    # Normalize the list of numbers to be between 0 and 1
    volume_array = np.array(gc) / np.max(gc)

    # Define the starting frequency and octave size
    base_frequency = 440  # A4 note
    octave_size = 12  # number of semitones in an octave

    # Generate the frequency array
    frequency_array = base_frequency * 2 ** (np.arange(len(gc)) / octave_size)

    # Generate the time and signal arrays for a 2-second sound
    duration = 2  # duration of the sound in seconds
    sampling_rate = 48000  # number of samples taken per second
    time_array = np.arange(duration * sampling_rate) / sampling_rate

    # Create the signal array
    signal_array = np.zeros_like(time_array)

    for volume, frequency in zip(volume_array, frequency_array):
        signal_array += volume * np.sin(2 * np.pi * frequency * time_array)

    # Normalize the combined signal to be between -32767 and 32767 (16-bit range)
    scaled_signal = np.int16(signal_array / np.max(np.abs(signal_array)) * 32767)

    # Save the audio file
    wavfile.write(os.path.join(data_directory, f'{filename}.wav'), sampling_rate, scaled_signal)

    return

def play_wav_file(filename):
    soundfile = os.path.join(data_directory, f'{filename}.wav')

    # Open the WAV file
    wf = wave.open(soundfile, 'rb')

    # Create an instance of the PyAudio class
    p = pyaudio.PyAudio()

    # Open a stream for playing the audio
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Read the audio data in chunks and play it
    chunk = 1024
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    # Cleanup
    stream.stop_stream()
    stream.close()
    p.terminate()

    return
