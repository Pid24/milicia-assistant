import os
import re
import feedparser
import wikipedia
from spotify_control import play_song, pause_song, resume_song, next_song, is_device_active
from utils import speak, speak_natural


def calculate(expression):
    try:
        result = eval(expression)
        speak(f"Hasilnya adalah {result}")
    except Exception:
        speak("Maaf, ada kesalahan dalam perhitungan. Pastikan format perintah benar.")

def get_latest_news(jumlah=3):
    url = "https://www.cnnindonesia.com/nasional/rss"
    feed = feedparser.parse(url)
    berita = []

    for entry in feed.entries[:jumlah]:
        title = entry.title.replace("&quot;", "\"").replace("&apos;", "'")
        berita.append(title)

    return berita

def search_wikipedia(query):
    try:
        wikipedia.set_lang("id")
        summary = wikipedia.summary(query, sentences=2)
        speak(summary)
    except wikipedia.DisambiguationError:
        speak("Topiknya terlalu umum. Bisa lebih spesifik?")
    except wikipedia.PageError:
        speak("Maaf, aku tidak menemukan informasi itu.")
    except Exception:
        speak("Terjadi kesalahan saat mencari informasi.")

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
        exit()

    elif "hitung" in command or "berapa hasil dari" in command or "berapakah" in command:
        expression = re.sub(r"[^0-9+\-*/().]", "", command)
        if expression:
            calculate(expression)
        else:
            speak("Maaf, aku tidak bisa menangkap ekspresi matematikanya. Bisa dicoba lagi?")

    elif command.startswith("apa itu ") or command.startswith("siapa itu ") or "jelaskan" in command:
        keyword = command.replace("apa itu ", "").replace("siapa itu ", "").replace("jelaskan", "").strip()
        if keyword:
            speak(f"Aku cari tahu tentang {keyword} ya...")
            search_wikipedia(keyword)
        else:
            speak("Mau cari tahu tentang apa?")
    else:
        speak_natural([
            "Aku belum paham perintah itu.",
            "Coba ulangi dengan kata yang berbeda, ya.",
            "Perintah tidak dikenali."
        ])
