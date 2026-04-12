"""
commands.py — Sistem Perintah AI-First (Agentic Pipeline)
Modul ini memproses perintah pengguna. Semua perintah dikirim ke otak AI Ollama
yang akan memutuskan sendiri apakah perlu menjalankan tool (aksi) atau menjawab teks biasa.
Hanya perintah kritis (exit, sleep) yang tetap diproses langsung tanpa AI.
"""

import os
import threading
import customtkinter as ctk

from utils import speak, speak_natural
from gui_utils import log_output
from gui_state import window
import gui_state
from ollama_brain import ask_ollama
from actions import _execute_shutdown, _execute_restart


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
    Memproses perintah pengguna dengan arsitektur AI-First:
    1. Cek apakah perintah adalah perintah kritis (exit/sleep) → eksekusi langsung.
    2. Kirim semua perintah lain ke Ollama → AI memutuskan apakah perlu tool atau teks.
    3. Jika AI mengembalikan marker konfirmasi, tampilkan dialog GUI.
    """
    command_lower = command.lower().strip()

    # STEP 1: Cek perintah kritis (harus bisa jalan tanpa Ollama)
    for keyword, action in CRITICAL_COMMANDS.items():
        if keyword in command_lower:
            action()
            return

    # STEP 2: Kirim ke AI (Ollama akan memutuskan: tool call atau jawab biasa)
    log_output("🧠 Milicia sedang berpikir...")

    try:
        ai_reply = ask_ollama(command)

        # STEP 3: Cek apakah ada marker konfirmasi dari aksi berbahaya
        if ai_reply.startswith("__CONFIRM_SHUTDOWN__|"):
            message = ai_reply.split("|", 1)[1]
            speak(message)
            # Tampilkan dialog konfirmasi di main thread
            if gui_state.window:
                gui_state.window.after(0, _show_confirmation_dialog, "shutdown", message)
            return

        if ai_reply.startswith("__CONFIRM_RESTART__|"):
            message = ai_reply.split("|", 1)[1]
            speak(message)
            # Tampilkan dialog konfirmasi di main thread
            if gui_state.window:
                gui_state.window.after(0, _show_confirmation_dialog, "restart", message)
            return

        # Respons biasa — ucapkan via TTS
        speak(ai_reply)

    except Exception as e:
        speak(f"Maaf, terjadi kesalahan: {str(e)}")
