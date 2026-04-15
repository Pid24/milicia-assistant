"""
commands.py — Sistem Perintah Hybrid (Smart Router + AI)
Modul ini memproses perintah pengguna dengan pendekatan hybrid:
1. Smart Router mendeteksi intent aksi (buka app, volume, cari, dll) via regex/keyword.
2. Jika aksi terdeteksi → eksekusi langsung via actions.py, lalu minta AI buat respons natural.
3. Jika tidak terdeteksi → kirim ke AI untuk dijawab sebagai percakapan biasa.

Pendekatan ini lebih reliable daripada mengandalkan model kecil untuk function calling.
"""

import os
import re
import threading
import customtkinter as ctk

from utils import speak, speak_natural
from gui_utils import log_output
from gui_state import window
import gui_state
from brain import ask_ai, ask_ai_simple, ask_ai_detailed, add_to_history
from actions import (
    open_website, open_application, shutdown_computer, restart_computer,
    lock_screen, set_volume, get_battery_status, get_system_info,
    take_screenshot, search_files, search_web, search_news, open_file,
    _execute_shutdown, _execute_restart, analyze_screen
)


# === Perintah Kritis (langsung dieksekusi tanpa AI karena harus instan) ===

def sleep_mode():
    gui_state.handsfree_mode = False
    if hasattr(gui_state, 'handsfree_switch') and gui_state.handsfree_switch:
        gui_state.handsfree_switch.deselect()
    speak("Baiklah, mode dengar otomatis dimatikan. Fokus ya! Kamu bisa panggil aku lagi dengan menyalakan tombol di aplikasi atau klik Tray Icon.")


def exit_app():
    speak_natural([
        "Sampai jumpa Rofid! Milicia pamit dulu.",
        "Oke, sampai ketemu lagi ya!",
        "Terima kasih, aku istirahat dulu."
    ])
    if gui_state.hard_quit:
        gui_state.hard_quit()
    elif window:
        window.destroy()


# Perintah kritis yang TIDAK memerlukan AI (harus berjalan meskipun Ollama offline)
CRITICAL_COMMANDS = {
    "keluar": exit_app,
    "exit": exit_app,
    "tutup milicia": exit_app,
    "matikan suara": sleep_mode,
    "mode tidur": sleep_mode,
    "tidur": sleep_mode,
    "jangan ganggu": sleep_mode,
    "fokus game": sleep_mode,
}


# =============================================
# SMART ROUTER — Deteksi intent aksi via regex
# =============================================

# Daftar website populer dan aliasnya
WEBSITE_MAP = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "github": "https://github.com",
    "facebook": "https://facebook.com",
    "instagram": "https://instagram.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "reddit": "https://reddit.com",
    "whatsapp": "https://web.whatsapp.com",
    "tiktok": "https://tiktok.com",
    "linkedin": "https://linkedin.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "chatgpt": "https://chat.openai.com",
    "gmail": "https://mail.google.com",
    "drive": "https://drive.google.com",
    "maps": "https://maps.google.com",
    "netflix": "https://netflix.com",
    "twitch": "https://twitch.tv",
    "wikipedia": "https://wikipedia.org",
    "tokopedia": "https://tokopedia.com",
    "shopee": "https://shopee.co.id",
}

# Daftar nama app yang dikenali
APP_NAMES = [
    "chrome", "brave", "vscode", "vs code", "visual studio code",
    "notepad", "cmd", "terminal", "powershell",
    "explorer", "file explorer", "calculator", "kalkulator",
    "paint", "spotify", "discord", "telegram", "obs",
    "word", "excel", "settings", "pengaturan",
    "task manager",
]

# Mapping alias nama app ke key di APP_REGISTRY
APP_ALIAS = {
    "vs code": "vscode",
    "visual studio code": "vscode",
    "file explorer": "explorer",
    "kalkulator": "calculator",
    "pengaturan": "settings",
}


def detect_action(command: str):
    """
    Mendeteksi apakah perintah pengguna mengandung intent aksi.
    Returns: (action_name, result_string) jika aksi terdeteksi, atau None.
    """
    cmd = command.lower().strip()

    # --- Buka Website (URL eksplisit) ---
    url_match = re.search(r'buka\s+(https?://\S+)', cmd)
    if url_match:
        url = url_match.group(1)
        result = open_website(url)
        return ("open_website", result)

    # --- Buka Website (domain langsung: buka google.com) ---
    domain_match = re.search(r'buka\s+(\S+\.\S+)', cmd)
    if domain_match:
        url = domain_match.group(1)
        result = open_website(url)
        return ("open_website", result)

    # --- Buka Website (nama populer: buka youtube) ---
    for site_name, site_url in WEBSITE_MAP.items():
        if re.search(rf'buka\s+{re.escape(site_name)}', cmd):
            result = open_website(site_url)
            return ("open_website", result)

    # --- Buka Aplikasi ---
    # Urutkan dari nama terpanjang dulu agar "vs code" cocok sebelum "code"
    sorted_apps = sorted(APP_NAMES, key=len, reverse=True)
    for app in sorted_apps:
        if re.search(rf'buka\s+{re.escape(app)}', cmd):
            app_key = APP_ALIAS.get(app, app)
            result = open_application(app_key)
            return ("open_application", result)

    # --- Volume Control ---
    vol_match = re.search(r'volume\s*(?:ke\s*)?(\d+)', cmd)
    if vol_match:
        level = int(vol_match.group(1))
        result = set_volume(level)
        return ("set_volume", result)

    # Variasi: naikkan/turunkan volume
    if re.search(r'(naikkan|besarkan|keraskan)\s*volume', cmd):
        result = set_volume(80)
        return ("set_volume", result)
    if re.search(r'(turunkan|kecilkan|pelankan)\s*volume', cmd):
        result = set_volume(30)
        return ("set_volume", result)
    if re.search(r'(mute|matikan)\s*volume', cmd) or re.search(r'volume\s*(mute|mati)', cmd):
        result = set_volume(0)
        return ("set_volume", result)

    # --- Shutdown ---
    if re.search(r'(matikan|shutdown|shut\s*down)\s*(komputer|pc|laptop)', cmd):
        return ("shutdown", "__CONFIRM_SHUTDOWN__")

    # --- Restart ---
    if re.search(r'(restart|reboot)\s*(komputer|pc|laptop)?', cmd):
        return ("restart", "__CONFIRM_RESTART__")

    # --- Lock Screen ---
    if re.search(r'(kunci|lock)\s*(layar|screen|pc|komputer|laptop)', cmd):
        result = lock_screen()
        return ("lock_screen", result)

    # Aksi-aksi kognitif dan informasi dinamis (web search, berita, baterai, dll)
    # akan diteruskan ke Gemini agar bisa dikelola via Tool Calling asli.
    return None


# =============================================
# DIALOG KONFIRMASI GUI (untuk aksi berbahaya)
# =============================================

def _show_confirmation_dialog(action_type: str, ai_message: str):
    """
    Menampilkan dialog konfirmasi di GUI sebelum menjalankan aksi berbahaya.
    Dipanggil dari main thread via window.after().
    """
    if action_type == "shutdown":
        title = "⚠️ Konfirmasi Shutdown"
        message = "Milicia akan mematikan komputer dalam 30 detik.\nApakah kamu yakin?"
        action_fn = _execute_shutdown
    elif action_type == "restart":
        title = "⚠️ Konfirmasi Restart"
        message = "Milicia akan me-restart komputer dalam 30 detik.\nApakah kamu yakin?"
        action_fn = _execute_restart
    else:
        return

    # Buat dialog popup
    dialog = ctk.CTkToplevel(gui_state.window)
    dialog.title(title)
    dialog.geometry("420x220")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)
    dialog.configure(fg_color="#1a1a2e")

    # Grab focus
    dialog.grab_set()
    dialog.focus_force()

    # Icon peringatan
    warning_label = ctk.CTkLabel(
        dialog,
        text="⚠️",
        font=("Segoe UI", 48),
        text_color="#e74c3c"
    )
    warning_label.pack(pady=(15, 5))

    # Pesan
    msg_label = ctk.CTkLabel(
        dialog,
        text=message,
        font=("Segoe UI", 14),
        text_color="#ecf0f1",
        wraplength=350
    )
    msg_label.pack(pady=(0, 15))

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=(0, 15))

    def on_confirm():
        dialog.destroy()
        log_output(f"✅ Pengguna mengkonfirmasi {action_type}.")
        result = action_fn()
        speak(result)

    def on_cancel():
        dialog.destroy()
        log_output(f"❌ {action_type.capitalize()} dibatalkan oleh pengguna.")
        speak(f"Oke, {action_type} dibatalkan.")

    confirm_btn = ctk.CTkButton(
        btn_frame,
        text="Ya, Lanjutkan",
        font=("Segoe UI", 13, "bold"),
        width=140,
        height=40,
        corner_radius=20,
        fg_color="#e74c3c",
        hover_color="#c0392b",
        text_color="#ffffff",
        command=on_confirm
    )
    confirm_btn.pack(side="left", padx=10)

    cancel_btn = ctk.CTkButton(
        btn_frame,
        text="Batalkan",
        font=("Segoe UI", 13, "bold"),
        width=140,
        height=40,
        corner_radius=20,
        fg_color="#2c3e50",
        hover_color="#34495e",
        text_color="#ecf0f1",
        command=on_cancel
    )
    cancel_btn.pack(side="left", padx=10)


# =============================================
# PIPELINE UTAMA
# =============================================

def run_command(command: str):
    """
    Memproses perintah pengguna dengan arsitektur Hybrid:
    1. Cek perintah kritis (exit/sleep) → eksekusi langsung.
    2. Smart Router mendeteksi intent aksi → eksekusi langsung + AI buat respons.
    3. Jika tidak ada aksi → kirim ke AI untuk percakapan biasa.
    """
    command_lower = command.lower().strip()

    # STEP 1: Cek perintah kritis (harus bisa jalan tanpa Ollama)
    for keyword, action in CRITICAL_COMMANDS.items():
        if keyword in command_lower:
            action()
            return

    # STEP 2: Smart Router — deteksi aksi
    action_result = detect_action(command)

    if action_result:
        action_name, result = action_result

        # Handle aksi yang butuh konfirmasi GUI
        if result == "__CONFIRM_SHUTDOWN__":
            speak("Rofid, kamu yakin mau matikan komputer?")
            if gui_state.window:
                gui_state.window.after(0, _show_confirmation_dialog, "shutdown", "")
            return

        if result == "__CONFIRM_RESTART__":
            speak("Rofid, kamu yakin mau restart komputer?")
            if gui_state.window:
                gui_state.window.after(0, _show_confirmation_dialog, "restart", "")
            return

        # Aksi sudah dieksekusi — minta AI buat respons natural
        log_output(f"✅ Aksi '{action_name}' berhasil dijalankan.")

        try:
            # === HANDLING AKSI BIASA ===
            context_msg = (
                f"[KONTEKS SISTEM: Kamu baru saja menjalankan aksi '{action_name}' "
                f"atas permintaan pengguna: '{command}'. "
                f"Hasil aksinya: {result}. "
                f"Berikan konfirmasi singkat dan natural kepada pengguna (1-2 kalimat). "
                f"JANGAN bilang kamu akan melakukannya, karena SUDAH dilakukan.]"
            )
            ai_reply = ask_ai_simple(context_msg)
            speak(ai_reply)
        except Exception:
            # Fallback jika AI tidak bisa merespons
            speak(result)
        return

    # STEP 3: Tidak ada aksi terdeteksi → kirim ke AI untuk percakapan biasa
    log_output("🧠 Milicia sedang berpikir...")

    try:
        ai_reply = ask_ai(command)
        speak(ai_reply)
    except Exception as e:
        speak(f"Maaf, terjadi kesalahan: {str(e)}")
