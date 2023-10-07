from common import (
    os,
    datetime,
    time,
    numpy as np,
    gradio as gr,
    load_dotenv,
    record_audio,
    play_audio_from_file, 
    play_audio_from_buffer,
)


def speak_mode_action(status, intermezzo):
    global recorded_audio, termination, intermezzo_played

    while termination:
        #reverse order as an example for some data processing
        audio_data = recorded_audio[::-1]
        # transform to desired format
        audio_data = (audio_data * 32767).astype(np.int16)

        # Wait until intermezzo_action is finished
        while not intermezzo_played:
            time.sleep(0.1)
            pass
        play_audio_from_buffer(audio_data)
        return gr.Textbox.update(value="record"), intermezzo
       
    if not termination:
        recorded_audio = record_audio(f"recorded_audio.wav",duration, fs, channels)
        termination = True
        if intermezzo_filepath:
            return gr.Textbox.update(value="recording_terminated"), gr.Textbox.update(value=f"Intermezzo timestamp {datetime.datetime.now()}")

def start_button_action(status):
    global termination, recorded_audio 
    if status == "record":
        termination = False
        recorded_audio = ""
        return gr.Textbox.update(value="recording")
    
def status_action(status):
    if status == "recording":
        return gr.Button.update(value="🎤 Recording...", interactive=False), status
    if status == "recording_terminated":
        return gr.Button.update(value="📢 Playing..."), status
    if status == "record":
        return gr.Button.update(value="🔴 Record", interactive=True), status

# this callback is important as during its execution, there are simultaneously running another processes in callback "speak_mode_action"
def intermezzo_action():
    global termination, intermezzo_played
    intermezzo_played = False
    if os.path.isfile(intermezzo_filepath) and intermezzo_filepath.lower().endswith(".wav"):
        play_audio_from_file(intermezzo_filepath)
    intermezzo_played = True
    termination = True

if __name__ == '__main__':

    # Load environment variables from .env file
    load_dotenv('.env')
    duration_str = os.environ.get('duration')
    duration = int(duration_str)
    fs_str = os.environ.get('fs')
    fs = int(fs_str)
    channels_str = os.environ.get('channels')
    channels = int(channels_str)
    
    current_directory = os.getcwd()
    intermezzo_filepath = os.path.join(current_directory, "Intermezzo.wav")


    # global variables
    intermezzo_played = False
    termination = False
    recorded_audio = ""

    # Gradio UI components
    with gr.Blocks(css="#chatbot .overflow-y-auto{height:800px}") as demo:
        start = gr.Button("🔴 Record")
        status = gr.Textbox("record", visible=False)  # only for UI "magic"
        intermezzo = gr.Textbox("", visible=False)  # only for UI magic

        start.click(start_button_action, status, status)
        start.click(speak_mode_action, [status, intermezzo], [status, intermezzo])
        status.change(status_action, status, [start, status])
        intermezzo.change(intermezzo_action, None, None)
        intermezzo.change(speak_mode_action, [status, intermezzo], [status, intermezzo])

    demo.launch()
    