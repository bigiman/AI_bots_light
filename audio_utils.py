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
from twilio.rest import Client

def get_audio_data(call_sid):
    TWILIO_ACCOUNT_SID = 'your_account_sid'
    TWILIO_AUTH_TOKEN = 'your_auth_token'
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # Retrieve the call recording associated with the Call SID
    call = client.calls(call_sid).fetch()
    recording_url = call.recordings.list()[0].uri

    # Download the audio recording
    audio_data = client.request("GET", recording_url).content

    return audio_data

# # Example usage:
# call_sid = 'your_call_sid'  # Replace with the actual Call SID
# audio_data = get_audio_data(call_sid)

async def record_audio_to_websocket(uri, duration, fs, channels, threshold_db=-30, min_nonsilence_duration=0.1, min_silence_duration=1):
    print("Recording...")

    # Constants for monitoring non-silence
    nonsilence_frames = int(fs * min_nonsilence_duration)
    above_threshold_count = 0
    nonsilence_detected = False

    # Constants for monitoring silence
    silence_frames = int(fs * min_silence_duration)
    below_threshold_count = 0
    silence_detected = False

    async with websockets.connect(uri) as websocket:
        while True:
            # Replace the microphone input with your audio data source
            audio_data = get_audio_data()  # Implement this function to obtain audio data

            if audio_data is None:
                break

            # Process audio data as needed
            if np.max(audio_data) >= 10 ** (threshold_db / 20):
                above_threshold_count += 1
            else:
                below_threshold_count += 1

            # Send audio data to the WebSocket server
            await websocket.send(audio_data.tobytes())

            if above_threshold_count >= nonsilence_frames and not nonsilence_detected:
                nonsilence_detected = True

            if below_threshold_count >= silence_frames and nonsilence_detected and not silence_detected:
                print("Stopped recording due to silence.")
                silence_detected = True

    print("Finished recording.")

# # Example usage:
# asyncio.get_event_loop().run_until_complete(record_audio_to_websocket("ws://your_websocket_server_address", 10, 44100, 1))


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