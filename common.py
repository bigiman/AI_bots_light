import os

# Set environment variables
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import time
import datetime
from pydub import AudioSegment
from pydub.playback import play
import sounddevice
import simpleaudio
import numpy
import gradio
from scipy.io import wavfile
from dotenv import load_dotenv
from audio_utils import record_audio, play_audio_from_file, play_audio_from_buffer

