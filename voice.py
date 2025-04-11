import speech_recognition as sr
import threading
import gui_state
from commands import run_command
from utils import speak, speak_natural
from gui_utils import log_output
import random

recognizer = sr.Recognizer()
silence_timer = None  # Timer untuk mendeteksi diam

def start_silence_timer():
    global silence_timer
    if silence_timer:
        silence_timer.cancel()
    silence_timer = threading.Timer(12, on_user_silent)
    silence_timer.start()

def cancel_silence_timer():
    global silence_timer
    if silence_timer:
        silence_timer.cancel()

def on_user_silent():
    speak(random.choice([
        "Kamu masih di sana?",
        "Aku standby ya, nggak kemana-mana kok.",
        "Kalau kamu butuh bantuanku, tinggal ngomong aja ya!"
    ]))

def listen_and_process():
    threading.Thread(target=handle_voice_input).start()

def handle_voice_input():
    gui_state.status_var.set("🎙️ Mendengarkan...")  # Set indikator status GUI
    with sr.Microphone() as source:
        log_output("🎙️ Mendengarkan...")
        start_silence_timer()  # Mulai timer saat mulai mendengarkan

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
            cancel_silence_timer()  # Batalkan timer jika ada input
            command = recognizer.recognize_google(audio, language='id-ID')
            log_output(f"🗣️ Kamu bilang: {command}")
            run_command(command.lower())
        except sr.WaitTimeoutError:
            cancel_silence_timer()
            speak("Hmm, aku nggak dengar apa-apa barusan.")
        except sr.UnknownValueError:
            cancel_silence_timer()
            speak_natural([
                "Maaf, aku nggak menangkap itu.",
                "Bisa diulangi lagi?",
                "Sepertinya aku tidak mengerti."
            ])
        except sr.RequestError:
            cancel_silence_timer()
            speak("Gagal terhubung ke layanan suara.")

    gui_state.status_var.set("🔵 Menunggu perintah...")
