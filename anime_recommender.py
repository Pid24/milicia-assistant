import requests
import random
from utils import speak

def get_anime_recommendation(genre_name):
    # Map genre ke ID (Jikan)
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