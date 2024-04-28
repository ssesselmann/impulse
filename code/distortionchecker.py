import pyaudio
import wave
import functions as fn

# Function to catch pulses and output time, pulse height, and distortion
def distortion_finder():
    settings        = fn.load_settings()
    device          = settings[2]
    sample_rate     = settings[3]
    chunk_size      = settings[4]
    threshold       = settings[5]
    flip            = settings[22]
    sample_length   = settings[11]
    peakshift       = settings[28]
    shapecatches    = settings[10]
    peak            = int((sample_length - 1) / 2) + peakshift

    audio_format    = pyaudio.paInt16
    device_channels = fn.get_max_input_channels(device)

    # Load pulse shapes from CSV for both channels
    shapes          = fn.load_shape()
    left_shape      = [int(x) for x in shapes[0]]
    right_shape     = [int(x) for x in shapes[1]]

    # Check if right channel is inactive (all zeros)
    right_active    = not all(v == 0 for v in right_shape)

    p = pyaudio.PyAudio()
    distortion_list_left = []
    distortion_list_right = []
    count_left = 0
    count_right = 0

    # Open the selected audio input device
    stream = p.open(format=audio_format, channels=device_channels, rate=sample_rate,
                    input=True, output=False, input_device_index=device,
                    frames_per_buffer=chunk_size)

    try:
        while count_left < shapecatches or (right_active and count_right < shapecatches):
            # Read the audio data from the stream
            data = stream.read(chunk_size, exception_on_overflow=False)
            values = list(wave.struct.unpack("%dh" % (chunk_size * device_channels), data))

            # Extract both left and right channels
            left_channel = values[0::2]
            right_channel = values[1::2]

            for i in range(len(left_channel) - sample_length):
                if count_left < shapecatches:
                    left_samples = left_channel[i:i + sample_length]
                    left_samples = [flip * x for x in left_samples]
                    if left_samples[peak] >= max(left_samples) and (max(left_samples) - min(left_samples)) > threshold:
                        left_normalised = fn.normalise_pulse(left_samples)
                        left_normalised_int = [int(round(x)) for x in left_normalised]
                        left_distortion = fn.distortion(left_normalised_int, left_shape)
                        distortion_list_left.append(left_distortion)
                        count_left += 1

                if right_active and count_right < shapecatches:
                    right_samples = right_channel[i:i + sample_length]
                    right_samples = [flip * x for x in right_samples]
                    if right_samples[peak] >= max(right_samples) and (max(right_samples) - min(right_samples)) > threshold:
                        right_normalised = fn.normalise_pulse(right_samples)
                        right_normalised_int = [int(round(x)) for x in right_normalised]
                        right_distortion = fn.distortion(right_normalised_int, right_shape)
                        distortion_list_right.append(right_distortion)
                        count_right += 1

                if count_left >= shapecatches and (not right_active or count_right >= shapecatches):
                    break

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    distortion_list_left.sort()
    # Handle inactive right channel
    if not right_active:
        return distortion_list_left, "0" * len(distortion_list_left)  # Return a string of zeros of equal length to left list
    else:
        distortion_list_right.sort()
        return distortion_list_left, distortion_list_right

