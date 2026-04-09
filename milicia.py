"""
Milicia AI Assistant — Asisten Virtual Lokal Berbasis Ollama
Ditenagai oleh model qwen2.5:1.5b yang berjalan 100% di laptop kamu.
"""

import customtkinter as ctk
import json
import os
import threading
import gui_state
from ollama_brain import is_ollama_running, reset_history

USER_DATA_FILE = "user_data.json"


def get_user_name():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("name", "pengguna")
    return "pengguna"


def set_user_name(name):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({"name": name}, f)


# === Setup UI Theme ===
ctk.set_appearance_mode("dark")  # Paksa ke mode gelap karena lebih elegan
ctk.set_default_color_theme("blue")

set_user_name("Rofid")

# === Main Window ===
window = ctk.CTk()
window.title("Milicia AI")
window.geometry("850x650")
window.resizable(False, False)

# Palet Warna Modern (Night Owl / Tokyo Night Aesthetic)
BG_COLOR = "#0b0c10"          # Sangat gelap, hampir hitam
FRAME_COLOR = "#1f2833"       # Abu-abu kebiruan gelap
ACCENT_COLOR = "#66fcf1"      # Cyan neon menyala
ACCENT_HOVER = "#45a29e"      # Cyan redup
TEXT_PRIMARY = "#c5c6c7"      # Putih tulang / abu terang
TEXT_MUTED = "#8A909D"        # Abu-abu pudar

window.configure(fg_color=BG_COLOR)

# Simpan window ke gui_state sebelum import voice
gui_state.window = window

# Import setelah window tersedia
from voice import listen_and_process
from utils import speak
from gui_utils import log_output

user = get_user_name()

# =============================================
# GUI LAYOUT
# =============================================

# === Main Frame (Container) ===
main_frame = ctk.CTkFrame(window, corner_radius=20, fg_color=BG_COLOR)
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# === Header Frame ===
header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
header_frame.pack(fill="x", pady=(5, 10))

# Logo / Judul
title_label = ctk.CTkLabel(
    header_frame,
    text=f"✨ Milicia AI",
    font=("Segoe UI", 26, "bold"),
    text_color="#ffffff"
)
title_label.pack(side="left", padx=10)

greeting_label = ctk.CTkLabel(
    header_frame,
    text=f"Welcome back, {user}",
    font=("Segoe UI", 12),
    text_color=TEXT_MUTED
)
greeting_label.pack(side="left", padx=10, pady=(8, 0))

# === Status Panel ===
status_frame = ctk.CTkFrame(main_frame, fg_color=FRAME_COLOR, corner_radius=10, height=40)
status_frame.pack(fill="x", pady=(0, 15))
status_frame.pack_propagate(False)

ollama_active = is_ollama_running()
status_dot = "🟢" if ollama_active else "🔴"
status_text = "Ollama Active" if ollama_active else "Ollama Offline"

ollama_label = ctk.CTkLabel(
    status_frame, 
    text=f"{status_dot} {status_text}",
    font=("Segoe UI", 12, "bold"),
    text_color="#2ecc71" if ollama_active else "#e74c3c"
)
ollama_label.pack(side="left", padx=15, pady=8)

model_label = ctk.CTkLabel(
    status_frame, 
    text="qwen2.5:1.5b",
    font=("Segoe UI", 11, "italic"),
    text_color=TEXT_MUTED
)
model_label.pack(side="right", padx=15, pady=8)

# === Chat / Output Area ===
# Frame sebagai border luar untuk efek panel kaca
chat_container = ctk.CTkFrame(main_frame, fg_color=FRAME_COLOR, corner_radius=15)
chat_container.pack(fill="both", expand=True, pady=(0, 15))

output_area = ctk.CTkTextbox(
    chat_container, 
    width=780, 
    font=("Segoe UI", 14),
    corner_radius=15,
    fg_color=FRAME_COLOR,
    text_color=TEXT_PRIMARY,
    wrap="word",
    spacing3=8 # Jarak antar paragraf
)
output_area.pack(padx=2, pady=2, fill="both", expand=True)

gui_state.output_area = output_area

# === Status perintah suara ===
status_var = ctk.StringVar(value="S i a p   m e n d e n g a r k a n . . .")
status_label = ctk.CTkLabel(
    main_frame, 
    textvariable=status_var,
    font=("Segoe UI", 11, "bold"),
    text_color=ACCENT_COLOR
)
status_label.pack(pady=(0, 10))
gui_state.status_var = status_var

# === Control Buttons ===
button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
button_frame.pack(pady=(0, 5))

# Tombol Mic Besar
listen_button = ctk.CTkButton(
    button_frame,
    text="🎙️ Bicara Sekarang",
    font=("Segoe UI", 15, "bold"),
    width=300, 
    height=55,
    corner_radius=27, # Sangat bulat menyerupai pill
    command=listen_and_process,
    fg_color=ACCENT_COLOR,
    text_color="#0b0c10", # Teks hitam karena background cyan cerah
    hover_color=ACCENT_HOVER
)
listen_button.pack(side="left", padx=10)

def reset_chat():
    reset_history()
    output_area.configure(state="normal")
    output_area.delete("1.0", "end")
    output_area.configure(state="disabled")
    log_output("🔄 Memori dihapus. Milicia siap dengan percakapan baru!")

reset_button = ctk.CTkButton(
    button_frame,
    text="🗑️ Reset Chat",
    font=("Segoe UI", 13, "bold"),
    width=130, 
    height=55,
    corner_radius=27,
    command=reset_chat,
    fg_color=FRAME_COLOR,
    text_color=TEXT_PRIMARY,
    hover_color="#2b3846"
)
reset_button.pack(side="left", padx=10)

# =============================================
# STARTUP LOGIC
# =============================================

output_area.configure(state="normal")
output_area.insert("end", "✨ Inisialisasi Milicia AI...\n\n")
output_area.configure(state="disabled")

if ollama_active:
    log_output("✅ Koneksi ke Otak AI (Ollama Local) Berhasil.")
    log_output("💡 Klik tombol 'Bicara Sekarang' untuk mulai mengobrol.\n")
    threading.Thread(
        target=speak,
        args=(f"Halo {user}! Saya Milicia. Saya sudah siap menemani hari Anda.",),
        daemon=True
    ).start()
else:
    log_output("⚠️ Peringatan: Tidak dapat terhubung ke Ollama.")
    log_output("   Pastikan Ollama berjalan di background sebelum mengobrol.")
    log_output("   Buka command prompt dan ketik: ollama serve\n")

window.mainloop()
