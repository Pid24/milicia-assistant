import speech_recognition as sr
import threading
import gui_state
from commands import run_command
from utils import speak, speak_natural
from gui_utils import log_output

recognizer = sr.Recognizer()

def listen_and_process():
    threading.Thread(target=handle_voice_input).start()

def handle_voice_input():
    gui_state.status_var.set("🎙️ Mendengarkan...")  # Set indikator status GUI

    with sr.Microphone() as source:
        log_output("🎙️ Mendengarkan...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio, language='id-ID')
            log_output(f"🗣️ Kamu bilang: {command}")
            run_command(command.lower())
        except sr.UnknownValueError:
            speak_natural([
                "Maaf, aku nggak menangkap itu.",
                "Bisa diulangi lagi?",
                "Sepertinya aku tidak mengerti."
            ])
        except sr.RequestError:
            speak("Gagal terhubung ke layanan suara.")

    gui_state.status_var.set("🔵 Menunggu perintah...")