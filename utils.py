import os
import tempfile
import random
from gtts import gTTS
import playsound
from gui_utils import log_output

def speak(text: str):
    """Mengucapkan teks menggunakan Google TTS dan menampilkan log di GUI."""
    log_output(f"Milicia: {text}")
    tts = gTTS(text=text, lang='id')
    temp_path = os.path.join(tempfile.gettempdir(), "milicia_temp.mp3")
    tts.save(temp_path)
    playsound.playsound(temp_path)
    os.remove(temp_path)

def speak_natural(options: list[str]):
    """Memilih salah satu kalimat dari list untuk diucapkan (secara acak)."""
    if not options:
        speak("Aku tidak tahu harus bilang apa.")
    else:
        speak(random.choice(options))
