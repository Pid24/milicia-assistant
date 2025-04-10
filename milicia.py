import speech_recognition as sr
import pyttsx3
import os

recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Set voice (opsional)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Ganti sesuai suara yang diinginkan

def speak(text):
    print(f"Milicia: {text}")
    engine.say(text)
    engine.runAndWait()

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

    elif "buka file explorer" in command:
        os.system("explorer")
        speak("Membuka File Explorer")

    elif "keluar" in command or "exit" in command:
        speak("Sampai jumpa! Milicia pamit.")
        exit()

    else:
        speak("Perintah tidak saya kenal, coba lagi.")

# Main loop
speak("Halo! Saya Milicia. Siap membantu. Silakan beri perintah.")
while True:
    cmd = listen()
    if cmd:
        run_command(cmd)
