"""
Milicia AI Assistant — Asisten Virtual Lokal Berbasis Ollama
Ditenagai oleh model qwen2.5:1.5b yang berjalan 100% di laptop kamu.
Termasuk integrasi System Tray & Background Daemon berjalan di latar belakang.
"""

import customtkinter as ctk
import json
import os
import sys
import threading
import pystray
from PIL import Image, ImageDraw

# Fix untuk Autostart: Pastikan working directory selalu di folder tempat milicia.py berada
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Prevent multiple instances and bring existing to foreground
try:
    import ctypes
    hwnd = ctypes.windll.user32.FindWindowW(None, "Milicia AI")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        sys.exit(0)
except Exception:
    pass

import gui_state
from ollama_brain import is_ollama_running, reset_history
from utils import speak, get_time_greeting

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
user = get_user_name()

# === Main Window ===
window = ctk.CTk()
window.title("Milicia AI")
window.geometry("850x650")
window.resizable(False, False)

# Palet Warna Modern (Night Owl / Tokyo Night Aesthetic)
BG_COLOR = "#0b0c10"          
FRAME_COLOR = "#1f2833"       
ACCENT_COLOR = "#66fcf1"      
ACCENT_HOVER = "#45a29e"      
TEXT_PRIMARY = "#c5c6c7"      
TEXT_MUTED = "#8A909D"        

window.configure(fg_color=BG_COLOR)
gui_state.window = window

# === System Tray Logic ===
tray_icon = None

def create_tray_image():
    # Membuat icon logo sederhana bermuatan huruf M
    img = Image.new('RGB', (64, 64), color=(31, 40, 51))
    d = ImageDraw.Draw(img)
    d.text((16, 12), "M", fill=(102, 252, 241), font=None)  # Default font is small, but good enough for tray
    return img

def show_window(icon, item):
    icon.stop()
    window.deiconify()  # Tampilkan window

def quit_app(icon=None, item=None):
    if icon:
        icon.stop()
    window.quit()
    sys.exit(0)

# Register hard_quit ke gui_state
gui_state.hard_quit = quit_app

def hide_window():
    window.withdraw()  # Sembunyikan window
    
    # Setup pystray icon
    global tray_icon
    image = create_tray_image()
    menu = (
        pystray.MenuItem('Tampilkan', show_window, default=True),
        pystray.MenuItem('Matikan Sepenuhnya', quit_app)
    )
    tray_icon = pystray.Icon("milicia", image, "Milicia AI", menu)
    
    # Jalankan pystray di thread terpisah
    threading.Thread(target=tray_icon.run, daemon=True).start()

# Timpa default close behavior agar me-minimize ke tray
window.protocol('WM_DELETE_WINDOW', hide_window)

# Import dependencies yang butuh window ter-define
from voice import listen_and_process, start_wake_word_listener
from gui_utils import log_output
from prayer_times import start_prayer_reminder

# =============================================
# START WAKE WORD & PRAYER DAEMON
# =============================================
start_wake_word_listener()
start_prayer_reminder()

# =============================================
# GUI LAYOUT
# =============================================

main_frame = ctk.CTkFrame(window, corner_radius=20, fg_color=BG_COLOR)
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
header_frame.pack(fill="x", pady=(5, 10))

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
    spacing3=8
)
output_area.pack(padx=2, pady=2, fill="both", expand=True)

gui_state.output_area = output_area

status_var = ctk.StringVar(value="S i a p   m e n d e n g a r k a n . . .")
status_label = ctk.CTkLabel(
    main_frame, 
    textvariable=status_var,
    font=("Segoe UI", 11, "bold"),
    text_color=ACCENT_COLOR
)
status_label.pack(pady=(0, 10))
gui_state.status_var = status_var

button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
button_frame.pack(pady=(0, 5))

listen_button = ctk.CTkButton(
    button_frame,
    text="🎙️ Bicara Sekarang",
    font=("Segoe UI", 15, "bold"),
    width=300, 
    height=55,
    corner_radius=27,
    command=listen_and_process,
    fg_color=ACCENT_COLOR,
    text_color="#0b0c10",
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

def toggle_handsfree():
    mode = handsfree_switch.get()
    gui_state.handsfree_mode = mode
    if mode:
        log_output("✅ Mode Hands-Free AKTIF. Ucapkan 'Milicia' kapan saja untuk memanggilku.")
        if not os.path.exists("vosk_model"):
            log_output("⚠️ Peringatan: Telinga Offline (Vosk) belum terinstall. Aplikasi mungkin tidak merespons. Jalankan file download_vosk.py di terminal.")
    else:
        log_output("🚫 Mode Hands-Free MATI. Milicia hanya mendengar jika tombol ditekan.")

handsfree_switch = ctk.CTkSwitch(
    button_frame,
    text="Hands-Free Mode",
    font=("Segoe UI", 13, "bold"),
    text_color="#c5c6c7",
    progress_color=ACCENT_COLOR,
    button_color="#ffffff",
    button_hover_color="#f0f0f0",
    command=toggle_handsfree
)
gui_state.handsfree_switch = handsfree_switch
handsfree_switch.pack(side="left", padx=15)

# =============================================
# STARTUP LOGIC
# =============================================

output_area.configure(state="normal")
output_area.insert("end", "✨ Inisialisasi Milicia AI Desktop Assistant...\n")
output_area.insert("end", "💡 TIP: Tutup jendela ini untuk menyembunyikan Milicia ke System Tray.\n\n")
output_area.configure(state="disabled")

# Cek argumen CLI (Jika dijalankan via --background dari autostart script)
if "--background" in sys.argv:
    # Sembunyikan window dan jalankan tray langsung
    window.withdraw()
    hide_window()
    
    # Otomatis aktifkan Hands-Free Mode kalau jalan di background
    handsfree_switch.select()
    toggle_handsfree()

if ollama_active:
    log_output("✅ Koneksi ke Otak AI (Ollama Local) Berhasil.")
    
    # Ambil sapaan waktu otomatis
    time_greeting = get_time_greeting()
    
    threading.Thread(
        target=speak,
        args=(f"{time_greeting} {user}! Sistem Milicia sudah online dan siap membantu.",),
        daemon=True
    ).start()
else:
    log_output("⚠️ Peringatan: Tidak dapat terhubung ke Ollama.")
    log_output("   Pastikan Ollama berjalan di background sebelum mengobrol.")

window.mainloop()
