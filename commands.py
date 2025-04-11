import os
import re
import feedparser
import wikipedia
import requests
import random
from spotify_control import play_song, pause_song, resume_song, next_song, is_device_active
from utils import speak, speak_natural
from gui_state import window
import gui_state  # untuk flag waiting_for_genre


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


def get_anime_recommendation(genre_name):
    genre_map = {
        "aksi": 1,
        "petualangan": 2,
        "komedi": 4,
        "drama": 8,
        "fantasi": 10,
        "horror": 14,
        "romance": 22,
        "sci-fi": 24,
        "slice of life": 36,
        "isekai": 62
    }

    genre_id = genre_map.get(genre_name.lower())
    if not genre_id:
        speak("Maaf, aku belum punya rekomendasi untuk genre itu.")
        return

    try:
        url = f"https://api.jikan.moe/v4/anime?genres={genre_id}&order_by=score&sort=desc&limit=10"
        response = requests.get(url)
        data = response.json()

        if "data" in data and len(data["data"]) > 0:
            anime = random.choice(data["data"])
            title = anime["title"]
            synopsis = anime.get("synopsis", "Tidak ada sinopsis.")
            speak(f"Aku rekomendasikan anime berjudul {title}. {synopsis[:250]}...")
        else:
            speak("Maaf, aku tidak menemukan anime di genre itu.")
    except Exception as e:
        print("Error:", e)
        speak("Terjadi kesalahan saat mencari rekomendasi anime.")


def get_anime_title_only(genre_name):
    genre_map = {
        "aksi": 1,
        "petualangan": 2,
        "komedi": 4,
        "drama": 8,
        "fantasi": 10,
        "horror": 14,
        "romance": 22,
        "sci-fi": 24,
        "slice of life": 36,
        "isekai": 62
    }

    genre_id = genre_map.get(genre_name.lower())
    if not genre_id:
        speak("Genre itu belum aku kenali.")
        return

    try:
        url = f"https://api.jikan.moe/v4/anime?genres={genre_id}&order_by=score&sort=desc&limit=10"
        response = requests.get(url)
        data = response.json()

        if "data" in data and len(data["data"]) > 0:
            anime = random.choice(data["data"])
            title = anime["title"]
            speak(f"Anime {genre_name} yang aku rekomendasikan adalah {title}.")
        else:
            speak("Maaf, aku tidak menemukan anime dengan genre itu.")
    except Exception as e:
        print("Error:", e)
        speak("Terjadi kesalahan saat mengambil data anime.")


def get_current_season_anime():
    try:
        url = "https://api.jikan.moe/v4/seasons/now?sfw"
        response = requests.get(url)
        data = response.json()

        if "data" in data and len(data["data"]) > 0:
            anime = random.choice(data["data"])
            title = anime["title"]
            synopsis = anime.get("synopsis", "Tidak ada sinopsis.")
            speak(f"Salah satu anime musim ini adalah {title}. {synopsis[:250]}...")
        else:
            speak("Maaf, aku tidak menemukan anime yang sedang tayang.")
    except Exception as e:
        print("Error:", e)
        speak("Terjadi kesalahan saat mengambil data anime musim ini.")


def run_command(command):
    genre_keywords = [
        "aksi", "petualangan", "komedi", "drama",
        "fantasi", "romance", "horror", "sci-fi",
        "slice of life", "isekai"
    ]

    # Tangani perintah: "genre anime [komedi/drama/...]" ➜ hanya sebut judul
    if "genre anime" in command:
        for genre in genre_keywords:
            if genre in command:
                get_anime_title_only(genre)
                return

    # Jika sedang menunggu user sebut genre anime (setelah "rekomendasi anime")
    if gui_state.waiting_for_genre:
        for genre in genre_keywords:
            if genre in command:
                gui_state.waiting_for_genre = False
                get_anime_recommendation(genre)
                return
        speak("Genre itu belum aku kenali. Bisa sebut genre lain?")
        return

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

    elif "anime musim ini" in command or "anime terbaru" in command:
        get_current_season_anime()

    elif "rekomendasi anime" in command and "genre anime" not in command:
        found = False
        for genre in genre_keywords:
            if genre in command:
                get_anime_recommendation(genre)
                found = True
                break

        if not found:
            gui_state.waiting_for_genre = True
            speak("Kamu ingin genre anime yang seperti apa?")

    else:
        speak_natural([
            "Aku belum paham perintah itu.",
            "Coba ulangi dengan kata yang berbeda, ya.",
            "Perintah tidak dikenali."
        ])
