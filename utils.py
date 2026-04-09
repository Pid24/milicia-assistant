"""utils.py — Fungsi utilitas suara (Text-to-Speech) untuk Milicia."""

import os
import tempfile
import random
import uuid
from gtts import gTTS
import playsound
from gui_utils import log_output


def speak(text: str):
    """Mengucapkan teks menggunakan Google TTS dan menampilkan log di GUI."""
    log_output(f"🤖 Milicia: {text}")
    try:
        tts = gTTS(text=text, lang='id')
        # Gunakan nama file unik agar tidak bentrok antar thread
        temp_path = os.path.join(tempfile.gettempdir(), f"milicia_{uuid.uuid4().hex[:8]}.mp3")
        tts.save(temp_path)
        playsound.playsound(temp_path)
        # Hapus file setelah selesai diputar
        try:
            os.remove(temp_path)
        except OSError:
            pass
    except Exception as e:
        log_output(f"⚠️ Gagal memutar suara: {e}")


def speak_natural(options: list[str]):
    """Memilih salah satu kalimat dari list untuk diucapkan (secara acak)."""
    if not options:
        speak("Aku tidak tahu harus bilang apa.")
    else:
        speak(random.choice(options))
