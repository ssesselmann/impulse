import wave

# Open the wave file in read mode
with wave.open('sample.wav', 'rb') as wav_read:
    # Get the current parameters of the wave file
    params = wav_read.getparams()

    # Modify the frame rate parameter
    params = params[:2] + (48000,) + params[3:]

    # Open a new wave file in write mode
    with wave.open('modified.wav', 'wb') as wav_write:
        # Set the modified parameters of the wave file
        wav_write.setparams(params)

        # Read and write the audio data from the wave file
        data = wav_read.readframes(1024)
        while data:
            wav_write.writeframes(data)
            data = wav_read.readframes(1024)
