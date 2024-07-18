#audio_spectrum_notes.py
import os
import numpy as np
import scipy.io.wavfile as wavfile
import pyaudio
import wave
import global_vars
from functions import peak_finder

def find_peaks(histogram, threshold_factor=0.01):
    """
    Identifies peaks in the histogram that are above a specified threshold.
    Args:
    - histogram: List or array of counts representing the histogram.
    - threshold_factor: Fraction of the maximum count value to be used as the threshold.
    Returns:
    - List of tuples where each tuple contains the position and value of a significant peak.
    """
    max_value = np.max(histogram)
    threshold = threshold_factor * max_value
    peaks = []
    for i in range(1, len(histogram) - 1):
        if histogram[i] > histogram[i - 1] and histogram[i] > histogram[i + 1] and histogram[i] > threshold:
            peaks.append((i, histogram[i]))
    return peaks

def make_wav_file(filename, gc, bpm=120, threshold_factor=0.01):
    """
    Generates a WAV file from the gamma spectrum histogram where each significant peak is represented
    as a pure frequency note played in the order of the histogram bins.
    Args:
    - filename: Name of the output WAV file.
    - gc: List or array representing the gamma spectrum histogram.
    - bpm: Beats per minute to determine the duration of each note.
    - threshold_factor: Fraction of the maximum count value to be used as the threshold.
    """
    with global_vars.write_lock:
        data_directory = global_vars.data_directory

    # Find peaks in the histogram
    peaks = find_peaks(gc, threshold_factor)
    if not peaks:
        return

    # Normalize the list of peak volumes to be between 0 and 1
    peak_volumes = np.array([volume for _, volume in peaks])
    min_volume = np.min(peak_volumes)
    max_volume = np.max(peak_volumes)
    volume_array = (peak_volumes - min_volume) / (max_volume - min_volume)  # Volume is a function of peak-y

    # Define frequencies for the range of a piano from C8 (4186 Hz) to A0 (27.5 Hz)
    num_bins = len(gc)
    min_frequency = 4186.0  # C8
    max_frequency = 27.5    # A0
    frequencies = np.logspace(np.log10(min_frequency), np.log10(max_frequency), num_bins)

    # Generate the frequency array based on peak positions
    peak_positions = np.array([position for position, _ in peaks])
    frequency_array = frequencies[peak_positions]  # Frequency is a function of peak-x

    # Sort peaks by their x-position to play from left to right
    sorted_indices = np.argsort(peak_positions)
    peak_positions = peak_positions[sorted_indices]
    frequency_array = frequency_array[sorted_indices]
    volume_array = volume_array[sorted_indices]

    # Calculate the duration of each note as a quarter note at the specified BPM
    duration_per_note = 60 / bpm  # duration of each quarter note in seconds
    sampling_rate = 48000  # number of samples taken per second
    time_array = np.arange(duration_per_note * sampling_rate) / sampling_rate

    # Create the signal array for all notes
    signal_array = np.array([], dtype=np.int16)

    for i, (volume, frequency) in enumerate(zip(volume_array, frequency_array)):
        # Generate the signal for the current note
        note_signal = volume * np.sin(2 * np.pi * frequency * time_array)
        # Normalize the note signal to be between -32767 and 32767 (16-bit range)
        scaled_note_signal = np.int16(note_signal / np.max(np.abs(note_signal)) * 32767)
        # Append the note signal to the overall signal array
        signal_array = np.concatenate((signal_array, scaled_note_signal))

    # Ensure the file path
    file_path = os.path.join(data_directory, f'{filename}.wav')
    
    # Save the audio file, overwriting if it exists
    wavfile.write(file_path, sampling_rate, signal_array)

    return

def play_wav_file(filename):
    """
    Plays the generated WAV file using the PyAudio library.
    Args:
    - filename: Name of the WAV file to be played.
    """
    with global_vars.write_lock:
        data_directory = global_vars.data_directory

    soundfile = os.path.join(data_directory, f'{filename}.wav')

    if not os.path.isfile(soundfile):
        return

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
