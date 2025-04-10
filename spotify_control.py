import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables dari .env
load_dotenv()

# Autentikasi ke Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
))

def is_device_active():
    devices = sp.devices()
    return any(device["is_active"] for device in devices["devices"])

def play_song(uri, is_playlist=False):
    try:
        if not is_device_active():
            print("Tidak ada perangkat Spotify aktif.")
            return False

        if is_playlist:
            # Mainkan playlist/album penuh
            sp.start_playback(context_uri=uri)
        else:
            # Mainkan satu lagu saja
            sp.start_playback(uris=[uri])
        return True
    except Exception as e:
        print(f"Error saat play: {e}")
        return False

def pause_song():
    try:
        sp.pause_playback()
        return True
    except Exception as e:
        print(f"Error saat pause: {e}")
        return False

def resume_song():
    try:
        sp.start_playback()
        return True
    except Exception as e:
        print(f"Error saat resume: {e}")
        return False

def next_song():
    try:
        sp.next_track()
        return True
    except Exception as e:
        print(f"Error next lagu: {e}")
        return False
