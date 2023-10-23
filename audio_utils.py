import os
import time
from pydub import AudioSegment
from pydub.playback import play
import sounddevice as sd
import simpleaudio as sa
import numpy as np
from scipy.io import wavfile
import asyncio
import websockets


async def record_audio_websocket(uri, filename, duration, fs, threshold_db=-30, min_nonsilence_duration=0.1, min_silence_duration=1):
    print("Connecting to the WebSocket...")
    audio_buffer = []

    # Constants for monitoring non-silence
    nonsilence_frames = int(fs * min_nonsilence_duration)
    above_threshold_count = 0
    nonsilence_detected = False

    # Constants for monitoring silence
    silence_frames = int(fs * min_silence_duration)
    below_threshold_count = 0
    silence_detected = False

    async def on_message(websocket, message):
        audio_data = np.frombuffer(message, dtype=np.float32)
        audio_buffer.append(audio_data)

        if np.max(audio_data) >= 10 ** (threshold_db / 20):
            above_threshold_count += len(audio_data)
            below_threshold_count = 0
        else:
            below_threshold_count += len(audio_data)

        if above_threshold_count >= nonsilence_frames and not nonsilence_detected:
            nonsilence_detected = True

        if below_threshold_count >= silence_frames and nonsilence_detected and not silence_detected:
            print("Stopped recording due to silence.")
            silence_detected = True

    async with websockets.connect(uri) as websocket:
        print("Connected to the WebSocket.")
        start_time = time.time()

        while time.time() - start_time < duration and not silence_detected:
            await asyncio.sleep(0.1)  # Adjust the sleep interval as needed

        print("Recording finished.")

        # Combine and process the received audio data
        audio_data = np.concatenate(audio_buffer, axis=0)

        # Save the audio data to a file
        with open(filename, 'wb') as file:
            file.write(audio_data.tobytes())

        print(f"Saved {filename}")


# # Example usage:
# asyncio.get_event_loop().run_until_complete(record_audio_websocket('wss://your_twilio_websocket_uri', 'output.wav', duration, fs))


def record_audio(filename, duration, fs, channels, threshold_db=-30, min_nonsilence_duration=0.1, min_silence_duration=1):
    print("Recording...")
    audio_buffer = []

    # Constants for monitoring non-silence
    nonsilence_frames = int(fs * min_nonsilence_duration)
    above_threshold_count = 0
    nonsilence_detected = False

    # Constants for monitoring silence
    silence_frames = int(fs * min_silence_duration)
    below_threshold_count = 0
    silence_detected = False

    def callback(indata, frames, time, status):
        nonlocal above_threshold_count, nonsilence_detected, below_threshold_count, silence_detected

        if status:
            print(f"Error in callback: {status}")

        if np.max(indata) >= 10 ** (threshold_db / 20):
            above_threshold_count += frames

        if np.max(indata) < 10 ** (threshold_db / 20):
            below_threshold_count += frames
        else:
            below_threshold_count = 0

        audio_buffer.append(indata.copy())

        if above_threshold_count >= nonsilence_frames and not nonsilence_detected:
            nonsilence_detected = True

        if below_threshold_count >= silence_frames and nonsilence_detected and not silence_detected:
            print("Stopped recording due to silence.")
            silence_detected = True

    with sd.InputStream(callback=callback, channels=channels, samplerate=fs, dtype='float32'):
        start_time = time.time()
        while time.time() - start_time < duration:
            if silence_detected:
                break
            time.sleep(0.1)  # Adjust the sleep interval as needed

    print("Finished recording.")
    # Concatenate the audio buffer and skip the first 44 bytes (WAV header)
    audio_data = np.concatenate(audio_buffer, axis=0)
    audio_data = audio_data[44:]
    audio_data /= np.max(np.abs(audio_data))

    # # if we wanted to save the file.
    # wavfile.write(filename, fs, audio_data)
    # print(f"Saved {filename}")
    
    return audio_data

def play_audio_from_file(filename):
    format = os.path.splitext(filename)[1]
    audio = AudioSegment.from_file(filename, format)  
    play(audio)  

def play_audio_from_buffer(audio_data):
    play_obj = sa.play_buffer(audio_data, 1, 2, 16000)  # 1 channel, 2 bytes per sample, 16000 Hz sample rate
    # Wait for audio to finish playing
    play_obj.wait_done() 