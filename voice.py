"""voice.py — Modul pengenalan suara untuk Milicia AI Assistant."""

import speech_recognition as sr
import threading
import gui_state
from commands import run_command
from utils import speak, speak_natural
from gui_utils import log_output

recognizer = sr.Recognizer()


def listen_and_process():
    """Memulai thread baru untuk menangkap input suara."""
    # Cegah double-click saat AI sedang berpikir
    if gui_state.is_processing:
        return
    threading.Thread(target=handle_voice_input, daemon=True).start()


def handle_voice_input():
    """Menangkap suara dari mikrofon, konversi ke teks, dan proses."""
    gui_state.status_var.set("🎙️ Mendengarkan...")
    with sr.Microphone() as source:
        log_output("─" * 40)
        log_output("🎙️ Mendengarkan... (bicara sekarang)")

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
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

    gui_state.status_var.set("🔵 Siap mendengarkan...")
