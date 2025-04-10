import speech_recognition as sr
from gtts import gTTS
import playsound
import tempfile
import os
import random
import threading
import customtkinter as ctk
import json
import feedparser
from spotify_control import play_song, pause_song, resume_song, next_song, is_device_active
import re

recognizer = sr.Recognizer()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

USER_DATA_FILE = "user_data.json"

def get_user_name():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("name", "pengguna")
    else:
        return "pengguna"

def set_user_name(name):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({"name": name}, f)

# Set nama user sekali saja
set_user_name("Rofid")

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

def get_latest_news(jumlah=3):
    url = "https://www.cnnindonesia.com/nasional/rss"
    feed = feedparser.parse(url)
    berita = []

    for entry in feed.entries[:jumlah]:
        title = entry.title.replace("&quot;", "\"").replace("&apos;", "'")
        berita.append(title)

    return berita

# === Kalkulator ===
def calculate(expression):
    try:
        # Menggunakan eval untuk mengevaluasi ekspresi matematika dari pengguna
        result = eval(expression)
        speak(f"Hasilnya adalah {result}")
    except Exception as e:
        speak("Maaf, ada kesalahan dalam perhitungan. Pastikan format perintah benar.")

# === Perintah untuk kalkulator ===
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

    elif "buka brave" in command:
        brave_path = r"C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        if os.path.exists(brave_path):
            os.startfile(brave_path)
            speak_natural([
                "Oke, membuka Brave.",
                "Brave browser sedang dibuka.",
                "Sebentar, aku buka Brave dulu ya."
            ])
        else:
            speak("Brave tidak ditemukan.")

    elif "buka browser" in command:
        speak("Kamu mau pakai browser apa? Chrome atau Brave?")

    elif "buka cmd" in command or "buka terminal" in command:
        os.startfile(r"C:\\Windows\\System32\\cmd.exe")
        speak("Command Prompt dibuka.")

    elif "buka notepad" in command:
        os.system("start notepad")
        speak("Notepad sudah dibuka.")

    elif "buka file explorer" in command or "buka folder" in command:
        os.system("explorer")
        speak("File Explorer dibuka.")

    elif "berita hari ini" in command:
        speak("Berikut beberapa berita terkini dari CNN Indonesia.")
        berita_list = get_latest_news()
        if berita_list:
            for berita in berita_list:
                speak(berita)
        else:
            speak("Maaf, aku tidak menemukan berita terbaru saat ini.")

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

    # Fitur Kalkulator
    elif "hitung" in command or "berapa hasil dari" in command or "berapakah" in command:
        expression = re.sub(r"[^0-9+\-*/().]", "", command)  # Hanya membolehkan angka dan operator
        if expression:
            calculate(expression)
        else:
            speak("Maaf, aku tidak bisa menangkap ekspresi matematikanya. Bisa dicoba lagi?")
    else:
        speak_natural([
            "Aku belum paham perintah itu.",
            "Coba ulangi dengan kata yang berbeda, ya.",
            "Perintah tidak dikenali."
        ])

# === GUI Setup (Modern & Rapi) ===
window = ctk.CTk()
window.title("Milicia Assistant")
window.geometry("720x540")
window.resizable(False, False)

user = get_user_name()

# === Frame Utama ===
main_frame = ctk.CTkFrame(window, corner_radius=15)
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# === Header (Judul + Toggle Tema) ===
header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
header_frame.pack(fill="x", padx=10, pady=(15, 5))

title_label = ctk.CTkLabel(header_frame, text=f"🧠 Halo {user}, Milicia siap membantu", font=("Segoe UI", 20, "bold"))
title_label.pack(side="left")

def toggle_theme():
    mode = ctk.get_appearance_mode()
    new_mode = "light" if mode == "Dark" else "dark"
    ctk.set_appearance_mode(new_mode)
    theme_btn.configure(text="🌙" if new_mode == "dark" else "🌞")

theme_btn = ctk.CTkButton(header_frame, text="🌞", width=40, command=toggle_theme)
theme_btn.pack(side="right", padx=5)

# === Status / Loader ===
status_var = ctk.StringVar(value="🔵 Menunggu perintah...")
status_label = ctk.CTkLabel(main_frame, textvariable=status_var, font=("Segoe UI", 12, "italic"))
status_label.pack(pady=(0, 5))

# === Tombol Dengarkan ===
listen_button = ctk.CTkButton(main_frame, text="🎙️ Mulai Mendengarkan", font=("Segoe UI", 14), width=220, height=40, command=listen_and_process)
listen_button.pack(pady=15)

# === Area Output Chat Style ===
output_area = ctk.CTkTextbox(main_frame, width=640, height=280, font=("Consolas", 12), corner_radius=12)
output_area.pack(pady=10)
output_area.insert("end", f"🤖 Milicia: Halo {user}! Saya siap membantu kamu hari ini.\n")
output_area.configure(state="disabled")

speak(f"Halo {user}! Saya Milicia. Senang bisa membantu kamu hari ini.")

window.mainloop()
