import speech_recognition as sr
from gtts import gTTS
import playsound
import tempfile
import os
from spotify_control import play_song, pause_song, resume_song, next_song

recognizer = sr.Recognizer()

def speak(text):
    print(f"Milicia: {text}")
    tts = gTTS(text=text, lang='id')

    # Simpan file sementara di folder Temp
    temp_path = os.path.join(tempfile.gettempdir(), "milicia_temp.mp3")
    tts.save(temp_path)

    # Mainkan audio
    playsound.playsound(temp_path)

    # Hapus file setelah diputar
    os.remove(temp_path)


def listen():
    with sr.Microphone() as source:
        print("🎙️ Mendengarkan...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio, language='id-ID')
            print(f"🗣️ Kamu bilang: {command}")
            return command.lower()
        except sr.UnknownValueError:
            speak("Maaf, saya tidak mengerti.")
            return ""
        except sr.RequestError:
            speak("Gagal terhubung ke layanan suara.")
            return ""

def run_command(command):
    if "buka chrome" in command:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            os.startfile(chrome_path)
            speak("Membuka Google Chrome")
        else:
            speak("Chrome tidak ditemukan")

    elif "buka cmd" in command or "buka terminal" in command:
        cmd_path = r"C:\Windows\System32\cmd.exe"
        os.startfile(cmd_path)
        speak("Membuka Command Prompt")

    elif "buka notepad" in command:
        os.system("start notepad")
        speak("Membuka Notepad")

    elif "buka file explorer" in command or "buka folder" in command:
        os.system("explorer")
        speak("Membuka File Explorer")

    elif "putar lagu" in command:
        # Ganti URI dengan lagu favorit kamu dari Spotify
        song_uri = "spotify:track:10nyNJ6zNy2YVYLrcwLccB"  # Contoh
        if play_song(song_uri):
            speak("Memutar lagu favorit kamu")
        else:
            speak("Maaf, gagal memutar lagu")

    elif "pause lagu" in command:
        if pause_song():
            speak("Lagu dijeda")
        else:
            speak("Gagal menjeda lagu")

    elif "lanjutkan lagu" in command or "resume lagu" in command:
        if resume_song():
            speak("Melanjutkan lagu")
        else:
            speak("Gagal melanjutkan lagu")

    elif "next lagu" in command or "lagu berikutnya" in command:
        if next_song():
            speak("Lagu berikutnya diputar")
        else:
            speak("Gagal memutar lagu berikutnya")

    elif "keluar" in command or "exit" in command:
        speak("Sampai jumpa! Milicia pamit.")
        exit()

    else:
        speak("Perintah tidak saya kenal, coba lagi.")

# 🔁 Loop utama
speak("Halo! Saya Milicia. Siap membantu. Silakan beri perintah.")
while True:
    cmd = listen()
    if cmd:
        run_command(cmd)
