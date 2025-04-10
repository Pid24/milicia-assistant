import speech_recognition as sr
from gtts import gTTS
import playsound
import tempfile
import os
import random
import threading
import customtkinter as ctk
from spotify_control import play_song, pause_song, resume_song, next_song, is_device_active

recognizer = sr.Recognizer()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# === GUI Functions ===
def speak(text):
    log_output(f"Milicia: {text}")
    tts = gTTS(text=text, lang='id')
    temp_path = os.path.join(tempfile.gettempdir(), "milicia_temp.mp3")
    tts.save(temp_path)
    playsound.playsound(temp_path)
    os.remove(temp_path)

def speak_natural(options):
    speak(random.choice(options))

def listen_and_process():
    threading.Thread(target=handle_voice_input).start()

def handle_voice_input():
    with sr.Microphone() as source:
        log_output("\n🎙️ Mendengarkan...")
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

def log_output(message):
    output_area.configure(state="normal")
    output_area.insert("end", f"{message}\n")
    output_area.configure(state="disabled")
    output_area.see("end")

def run_command(command):
    if "buka chrome" in command:
        chrome_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if os.path.exists(chrome_path):
            os.startfile(chrome_path)
            speak_natural([
                "Oke, membuka Google Chrome.",
                "Chrome sedang dibuka untukmu.",
                "Sebentar, aku buka Chrome-nya ya."
            ])
        else:
            speak("Chrome tidak ditemukan.")

    elif "buka cmd" in command or "buka terminal" in command:
        os.startfile(r"C:\\Windows\\System32\\cmd.exe")
        speak("Command Prompt dibuka.")

    elif "buka notepad" in command:
        os.system("start notepad")
        speak("Notepad sudah dibuka.")

    elif "buka file explorer" in command or "buka folder" in command:
        os.system("explorer")
        speak("File Explorer dibuka.")

    elif "putar lagu" in command:
        if not is_device_active():
            speak("Kamu belum membuka Spotify. Silakan buka dan putar lagu sebentar dulu ya.")
            return
        playlist_uri = "spotify:playlist:7mEK7dZsNKyunIBL5nOLZQ"
        if play_song(playlist_uri, is_playlist=True):
            speak_natural([
                "Playlist favorit kamu aku putar sekarang.",
                "Lagu-lagu dari playlist kamu sedang dimainkan.",
                "Aku putarkan playlist andalanmu sekarang!"
            ])
        else:
            speak("Maaf, gagal memutar playlist.")

    elif "pause lagu" in command:
        if pause_song():
            speak("Lagu dijeda.")
        else:
            speak("Gagal menjeda lagu.")

    elif "lanjutkan lagu" in command or "resume lagu" in command:
        if resume_song():
            speak("Melanjutkan lagu.")
        else:
            speak("Gagal melanjutkan lagu.")

    elif "next lagu" in command or "lagu berikutnya" in command:
        if not is_device_active():
            speak("Tidak ada lagu yang sedang diputar. Mainkan lagu dulu ya.")
            return
        if next_song():
            speak("Lanjut ke lagu berikutnya.")
        else:
            speak("Maaf, gagal skip lagu.")

    elif "keluar" in command or "exit" in command:
        speak_natural([
            "Sampai jumpa! Milicia pamit dulu.",
            "Oke, sampai ketemu lagi ya!",
            "Terima kasih, aku keluar dulu."
        ])
        window.destroy()

    else:
        speak_natural([
            "Aku belum paham perintah itu.",
            "Coba ulangi dengan kata yang berbeda, ya.",
            "Perintah tidak dikenali."
        ])

# === GUI Setup ===
window = ctk.CTk()
window.title("Milicia Assistant")
window.geometry("600x480")

title_label = ctk.CTkLabel(window, text="🟢 Milicia Siap Membantu", font=("Segoe UI", 18, "bold"))
title_label.pack(pady=20)

listen_button = ctk.CTkButton(window, text="🎙️ Mulai Mendengarkan", font=("Segoe UI", 14), command=listen_and_process)
listen_button.pack(pady=10)

output_area = ctk.CTkTextbox(window, width=520, height=250, font=("Consolas", 12))
output_area.pack(pady=15)
output_area.insert("end", "Milicia siap digunakan...\n")
output_area.configure(state="disabled")

speak("Halo! Saya Milicia. Senang bisa membantu kamu hari ini.")

window.mainloop()