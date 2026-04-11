"""utils.py — Fungsi utilitas suara (Text-to-Speech) untuk Milicia."""

import random
import datetime
import io
import time
import os
import threading
import asyncio

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import edge_tts
from gui_utils import log_output

# Lock untuk mencegah dua speak() berjalan bersamaan (tumpang tindih audio)
_speak_lock = threading.Lock()

# === Konfigurasi Suara ===
# Voice options (Indonesian):
#   - "id-ID-GadisNeural"  → Suara cewek Indonesia (natural & friendly)
#   - "id-ID-ArdiNeural"   → Suara cowok Indonesia
# Bisa juga pakai suara bahasa lain, contoh:
#   - "en-US-AvaNeural"    → Suara cewek English (US)
#   - "ja-JP-NanamiNeural" → Suara cewek Jepang
VOICE_NAME = "id-ID-GadisNeural"
VOICE_RATE = "+0%"    # Kecepatan bicara: "-10%" lebih pelan, "+10%" lebih cepat
VOICE_PITCH = "+0Hz"  # Nada suara: "+5Hz" lebih tinggi, "-5Hz" lebih rendah


async def _edge_tts_to_bytes(text: str) -> bytes:
    """Generate audio bytes dari Edge TTS (async)."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE_NAME,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH,
    )
    audio_data = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.write(chunk["data"])
    return audio_data.getvalue()


def speak(text: str):
    """Mengucapkan teks menggunakan Edge TTS (Microsoft Neural Voice)."""
    log_output(f"🤖 Milicia: {text}")
    with _speak_lock:
        try:
            # Jalankan async edge-tts di thread ini
            audio_bytes = asyncio.run(_edge_tts_to_bytes(text))
            
            fp = io.BytesIO(audio_bytes)
            
            # Inisialisasi pygame mixer jika belum
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                
            pygame.mixer.music.load(fp, "mp3")
            pygame.mixer.music.play()
            
            # Tunggu sampai suara selesai
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
        except Exception as e:
            log_output(f"⚠️ Edge TTS gagal: {e}, mencoba fallback gTTS...")
            _speak_fallback_gtts(text)


def _speak_fallback_gtts(text: str):
    """Fallback ke Google TTS jika Edge TTS gagal."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='id')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        pygame.mixer.music.load(fp, "mp3")
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        log_output(f"⚠️ Gagal memutar suara (fallback): {e}")


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
