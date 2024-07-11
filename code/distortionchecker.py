import pyaudio
import wave
import logging
import functions as fn
import global_vars

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Function to catch pulses and output time, pulse height, and distortion
def distortion_finder(stereo):

    with global_vars.write_lock:
        device          = global_vars.device
        sample_rate     = global_vars.sample_rate
        chunk_size      = global_vars.chunk_size
        threshold       = global_vars.threshold
        flip            = global_vars.flip
        sample_length   = global_vars.sample_length
        peakshift       = global_vars.peakshift
        shapecatches    = global_vars.shapecatches
    
    peak            = int((sample_length - 1) / 2) + peakshift
    audio_format    = pyaudio.paInt16
    channels        = 2 if stereo else 1
    # Load pulse shapes from CSV for both channels
    shapes          = fn.load_shape()
    left_shape      = [int(x) for x in shapes[0]]
    right_shape     = [int(x) for x in shapes[1]]
    p                       = pyaudio.PyAudio()
    distortion_list_left    = []
    distortion_list_right   = []
    count_left              = 0
    count_right             = 0

    logger.info(f'Distortionchecker says Stereo == {stereo}\n')

    if flip     == 11:
        flip_left   = 1
        flip_right  = 1
    elif flip   == 12:
        flip_left   = 1
        flip_right  = -1  
    elif flip   == 21:
        flip_left   = -1
        flip_right  = 1
    elif flip   == 22:
        flip_left   = -1
        flip_right  = -1        

    # Open the selected audio input device
    stream = p.open(
                format=audio_format, 
                channels=channels, 
                rate=sample_rate,
                input=True, 
                output=False, 
                input_device_index=device,
                frames_per_buffer=chunk_size
                )

    try:
        while count_left < shapecatches or (stereo and count_right < shapecatches):
            # Read the audio data from the stream
            data    = stream.read(chunk_size, exception_on_overflow=False)
            values  = list(wave.struct.unpack("%dh" % (chunk_size * channels), data))

            # Extract both left and right channels
            left_channel    = values[::2] if stereo else values
            right_channel   = values[1::2] if stereo else []

            for i in range(len(left_channel) - sample_length):
                if count_left < shapecatches:
                    left_samples = left_channel[i:i + sample_length]
                    left_samples = [flip_left * x for x in left_samples]
                    if left_samples[peak] == max(left_samples) and (max(left_samples) - min(left_samples)) > threshold:
                        left_normalised     = fn.normalise_pulse(left_samples)
                        left_normalised_int = [int(round(x)) for x in left_normalised]
                        left_distortion     = fn.distortion(left_normalised_int, left_shape)
                        distortion_list_left.append(left_distortion)
                        count_left += 1

                if stereo and count_right < shapecatches:
                    right_samples = right_channel[i:i + sample_length]
                    right_samples = [flip_right * x for x in right_samples]
                    if right_samples[peak] == max(right_samples) and (max(right_samples) - min(right_samples)) > threshold:
                        right_normalised = fn.normalise_pulse(right_samples)
                        right_normalised_int = [int(round(x)) for x in right_normalised]
                        right_distortion = fn.distortion(right_normalised_int, right_shape)
                        distortion_list_right.append(right_distortion)
                        count_right += 1

            # Check if both counts have reached shapecatches
            if not stereo and count_left >= shapecatches:
                break

            # Break the outer loop if both counts are satisfied
            if stereo and (count_left >= shapecatches) and (count_right >= shapecatches):
                break

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    distortion_list_left.sort()
    max_left = max(distortion_list_left)
    logger.info(f'Max distortion left {max_left}\n')

    # Handle inactive right channel
    if not stereo:
        return distortion_list_left, ["0"] * len(distortion_list_left)  # Return a list of zeros of equal length to left list
    else:
        distortion_list_right.sort()
        max_right = max(distortion_list_right)
        logger.info(f'Max distortion right {max_right}\n')
        return distortion_list_left, distortion_list_right
