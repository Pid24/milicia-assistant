import os
import tempfile
import random
from gtts import gTTS
import playsound
from gui_utils import log_output

def speak(text):
    log_output(f"Milicia: {text}")
    tts = gTTS(text=text, lang='id')
    temp_path = os.path.join(tempfile.gettempdir(), "milicia_temp.mp3")
    tts.save(temp_path)
    playsound.playsound(temp_path)
    os.remove(temp_path)

def speak_natural(options):
    speak(random.choice(options))