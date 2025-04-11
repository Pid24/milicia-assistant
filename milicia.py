import customtkinter as ctk
import json
import os
import gui_state  # harus duluan untuk inject window
from utils import speak

USER_DATA_FILE = "user_data.json"

def get_user_name():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("name", "pengguna")
    else:
        return "pengguna"

def set_user_name(name):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({"name": name}, f)

# === Setup UI Theme ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Set username (hanya sekali)
set_user_name("Rofid")

# === Main Window ===
window = ctk.CTk()
window.title("Milicia Assistant")
window.geometry("720x540")
window.resizable(False, False)

# ⬅️ Simpan window ke gui_state sebelum import voice
gui_state.window = window

# Sekarang baru boleh import voice (setelah window sudah tersedia)
from voice import listen_and_process

# === Get user info ===
user = get_user_name()

# === Main Frame ===
main_frame = ctk.CTkFrame(window, corner_radius=15)
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# === Header ===
header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
header_frame.pack(fill="x", padx=10, pady=(15, 5))

title_label = ctk.CTkLabel(
    header_frame,
    text=f"🧠 Halo {user}, Milicia siap membantu",
    font=("Segoe UI", 20, "bold")
)
title_label.pack(side="left")

def toggle_theme():
    mode = ctk.get_appearance_mode()
    new_mode = "light" if mode == "Dark" else "dark"
    ctk.set_appearance_mode(new_mode)
    theme_btn.configure(text="🌙" if new_mode == "dark" else "🌞")

theme_btn = ctk.CTkButton(header_frame, text="🌞", width=40, command=toggle_theme)
theme_btn.pack(side="right", padx=5)

# === Status / Loader ===
status_var = ctk.StringVar(value="🔵 Menunggu perintah...")
status_label = ctk.CTkLabel(main_frame, textvariable=status_var, font=("Segoe UI", 12, "italic"))
status_label.pack(pady=(0, 5))

# === Listen Button ===
listen_button = ctk.CTkButton(
    main_frame,
    text="🎙️ Mulai Mendengarkan",
    font=("Segoe UI", 14),
    width=220,
    height=40,
    command=listen_and_process
)
listen_button.pack(pady=15)

# === Output Area ===
output_area = ctk.CTkTextbox(main_frame, width=640, height=280, font=("Consolas", 12), corner_radius=12)
output_area.pack(pady=10)

# Simpan komponen penting ke gui_state agar bisa diakses dari file lain
gui_state.output_area = output_area
gui_state.status_var = status_var

# === Initial Greeting ===
speak(f"Halo {user}! Saya Milicia. Senang bisa membantu kamu hari ini.")

# === Start the App ===
window.mainloop()
