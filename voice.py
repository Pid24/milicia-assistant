"""voice.py — Modul pengenalan suara untuk Milicia AI Assistant."""

import speech_recognition as sr
import threading
import gui_state
from commands import run_command
from utils import speak, speak_natural
from gui_utils import log_output
import time
import json
import vosk
import pyaudio

recognizer = sr.Recognizer()


# Kalibrasi noise awal sekali saja agar tidak lag saat dipanggil
def init_calibration():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
    except:
        pass

threading.Thread(target=init_calibration, daemon=True).start()

def listen_and_process():
    """Memulai thread baru untuk menangkap input suara."""
    # Cegah double-click saat AI sedang berpikir
    if gui_state.is_processing:
        return
    gui_state.is_processing = True
    threading.Thread(target=handle_voice_input, daemon=True).start()


def handle_voice_input():
    """Menangkap suara dari mikrofon, konversi ke teks, dan proses."""
    gui_state.is_processing = True
    gui_state.status_var.set("🎙️ Mendengarkan...")
    
    try:
        with sr.Microphone() as source:
            log_output("─" * 40)
            log_output("🎙️ Mendengarkan... (bicara sekarang)")

            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
            gui_state.status_var.set("🧠 Sedang memproses...")
            command = recognizer.recognize_google(audio, language='id-ID')
            log_output(f"🗣️ Rofid: {command}")
            run_command(command.lower())

    except sr.WaitTimeoutError:
        speak("Hmm, aku nggak dengar apa-apa. Coba tekan tombol lagi ya.")
    except sr.UnknownValueError:
        speak_natural([
            "Maaf, aku nggak menangkap itu.",
            "Bisa diulangi lagi?",
            "Sepertinya suaranya kurang jelas.",
        ])
    except sr.RequestError:
        speak("Gagal terhubung ke layanan pengenalan suara. Cek koneksi internet kamu ya.")
    except Exception as e:
        log_output(f"⚠️ Error: {e}")
    finally:
        gui_state.is_processing = False
        gui_state.status_var.set("🔵 Siap mendengarkan...")


def start_wake_word_listener():
    """Menjalankan engine Vosk di background untuk menunggu kata sakti"""
    threading.Thread(target=wake_word_loop, daemon=True).start()

def wake_word_loop():
    try:
        model = vosk.Model("vosk_model")
    except Exception as e:
        log_output("⚠️ Gagal memuat Vosk. Pastikan model sudah diunduh.")
        return

    p = pyaudio.PyAudio()
    
    while True:
        if not gui_state.handsfree_mode:
            time.sleep(1)
            continue
            
        if gui_state.is_processing:
            time.sleep(1)
            continue
            
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()
            rec = vosk.KaldiRecognizer(model, 16000)
            
            while gui_state.handsfree_mode and not gui_state.is_processing:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower()
                    
                    if "milicia" in text or "militia" in text or "melissa" in text or "hey me" in text or "hey" in text or "mili" in text:
                        stream.stop_stream()
                        stream.close()
                        
                        log_output("🔔 Panggilan 'Hei Milicia' terdeteksi.")
                        speak("Ya Rofid?")
                        listen_and_process()
                        break 
                        
            if stream.is_active() or not stream.is_stopped():
                stream.stop_stream()
                stream.close()
                
        except Exception as e:
            time.sleep(1)
            continue
