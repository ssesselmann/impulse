import pyaudio
import wave
import struct
from flask import Flask, Response

app = Flask(__name__)

@app.route('/audio')
def audio():
    def generate():
        with wave.open('audio/sample.wav', 'rb') as wav:
            

            p = pyaudio.PyAudio()


            # Select the audio input device by its index
            device_index = 0  # Replace this with the index of the desired device
            input_device_info = p.get_device_info_by_index(device_index)
            print(input_device_info)

            # Open a streaming socket using PyAudio
            stream = p.open(format=p.get_format_from_width(2),
                            channels=1,
                            rate=48000,  # Set the sample rate to 48 kHz
                            output=True)

            # Read and stream audio data from the wave file
            data = wav.readframes(1024)
            while data:
                # Unpack the binary data into a sequence of audio samples
                audio_data = struct.unpack('{n}h'.format(n=len(data)//2), data)
                
                # Yield the audio data as a string
                yield ' '.join(str(x) for x in audio_data)

                stream.write(data)
                data = wav.readframes(1024)
                print(audio_data)

            # Close the stream and PyAudio instance
            stream.stop_stream()
            stream.close()
            p.terminate()

    return Response(generate())

if __name__ == '__main__':
    app.run()
