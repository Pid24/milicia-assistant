"""utils.py — Fungsi utilitas suara (Text-to-Speech) untuk Milicia."""

import random
import datetime
import io
import time
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from gtts import gTTS
from gui_utils import log_output


def speak(text: str):
    """Mengucapkan teks menggunakan Google TTS dan menampilkan log di GUI."""
    log_output(f"🤖 Milicia: {text}")
    try:
        tts = gTTS(text=text, lang='id')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Inisialisasi pygame mixer jika belum
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        pygame.mixer.music.load(fp, "mp3")
        pygame.mixer.music.play()
        
        # Tunggu sampai suara selesai
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        log_output(f"⚠️ Gagal memutar suara: {e}")


def speak_natural(options: list[str]):
    """Memilih salah satu kalimat dari list untuk diucapkan (secara acak)."""
    if not options:
        speak("Aku tidak tahu harus bilang apa.")
    else:
        speak(random.choice(options))


def get_time_greeting() -> str:
    """Mengembalikan sapaan yang sesuai dengan waktu lokal saat ini."""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Selamat Pagi"
    elif 12 <= hour < 15:
        return "Selamat Siang"
    elif 15 <= hour < 19:
        return "Selamat Sore"
    else:
        return "Selamat Malam"
