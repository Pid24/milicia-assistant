"""
commands.py — Sistem Perintah Hybrid (AI + System Commands)
Modul ini menangani perintah pengguna. Beberapa perintah sistem (buka app, keluar)
tetap ditangani secara langsung. Sisanya dilempar ke otak AI Ollama.
"""

import os
import re
from utils import speak, speak_natural
from gui_utils import log_output
from gui_state import window
import gui_state
from ollama_brain import ask_ollama


# === Perintah Sistem (langsung dieksekusi tanpa AI) ===

def open_chrome():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        os.startfile(chrome_path)
        speak("Oke, membuka Google Chrome.")
    else:
        speak("Chrome tidak ditemukan di sistem kamu.")


def open_brave():
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    if os.path.exists(brave_path):
        os.startfile(brave_path)
        speak("Membuka Brave browser.")
    else:
        speak("Brave tidak ditemukan di sistem kamu.")


def open_cmd():
    os.system("start cmd")
    speak("Command Prompt sudah dibuka.")


def open_notepad():
    os.system("start notepad")
    speak("Notepad sudah dibuka.")


def open_explorer():
    os.system("explorer")
    speak("File Explorer dibuka.")


def exit_app():
    speak_natural([
        "Sampai jumpa Rofid! Milicia pamit dulu.",
        "Oke, sampai ketemu lagi ya!",
        "Terima kasih, aku istirahat dulu."
    ])
    if window:
        window.destroy()


# === Daftar perintah sistem yang dikenali ===
SYSTEM_COMMANDS = {
    "buka chrome": open_chrome,
    "buka google chrome": open_chrome,
    "buka brave": open_brave,
    "buka browser brave": open_brave,
    "buka cmd": open_cmd,
    "buka terminal": open_cmd,
    "buka command prompt": open_cmd,
    "buka notepad": open_notepad,
    "buka file explorer": open_explorer,
    "buka folder": open_explorer,
    "keluar": exit_app,
    "exit": exit_app,
    "tutup milicia": exit_app,
}


def run_command(command: str):
    """
    Memproses perintah pengguna:
    1. Cek apakah perintah cocok dengan system command.
    2. Jika tidak, lempar ke otak AI Ollama untuk diproses.
    """
    command_lower = command.lower().strip()

    # Cek system commands
    for keyword, action in SYSTEM_COMMANDS.items():
        if keyword in command_lower:
            action()
            return

    # Kalau bukan system command, tanya AI
    log_output("🧠 Milicia sedang berpikir...")
    gui_state.is_processing = True

    try:
        ai_reply = ask_ollama(command)
        speak(ai_reply)
    except Exception as e:
        speak(f"Maaf, terjadi kesalahan: {str(e)}")
    finally:
        gui_state.is_processing = False
