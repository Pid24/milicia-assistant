import speech_recognition as sr
from gtts import gTTS
import playsound
import tempfile
import os
import random
from spotify_control import play_song, pause_song, resume_song, next_song, is_device_active

recognizer = sr.Recognizer()

def speak(text):
    print(f"Milicia: {text}")
    tts = gTTS(text=text, lang='id')
    temp_path = os.path.join(tempfile.gettempdir(), "milicia_temp.mp3")
    tts.save(temp_path)
    playsound.playsound(temp_path)
    os.remove(temp_path)

def speak_natural(options):
    speak(random.choice(options))

def listen():
    with sr.Microphone() as source:
        print("🎙️ Mendengarkan...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio, language='id-ID')
            print(f"🗣️ Kamu bilang: {command}")
            return command.lower()
        except sr.UnknownValueError:
            speak_natural([
                "Maaf, aku nggak menangkap itu.",
                "Bisa diulangi lagi?",
                "Sepertinya aku tidak mengerti."
            ])
            return ""
        except sr.RequestError:
            speak("Gagal terhubung ke layanan suara.")
            return ""

def run_command(command):
    if "buka chrome" in command:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
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
        os.startfile(r"C:\Windows\System32\cmd.exe")
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

        # GANTI KE PLAYLIST KAMU
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
        exit()

    else:
        speak_natural([
            "Aku belum paham perintah itu.",
            "Coba ulangi dengan kata yang berbeda, ya.",
            "Perintah tidak dikenali."
        ])

# 🔁 Loop utama
speak("Halo! Saya Milicia. Senang bisa membantu kamu hari ini.")
while True:
    cmd = listen()
    if cmd:
        run_command(cmd)
