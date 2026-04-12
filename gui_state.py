# gui_state.py — Variabel global yang dibagikan antar modul
# Diinisialisasi oleh milicia.py, diakses oleh voice.py, commands.py, dll.

output_area = None
status_var = None
window = None
is_processing = False  # Flag untuk mencegah double-click saat AI sedang berpikir
hard_quit = None       # Fungsi untuk mematikan aplikasi secara total (termasuk Tray)
handsfree_mode = False # Mode Vosk Wake Word
handsfree_switch = None # Objek switch UI
is_speaking = False    # Flag: True saat Milicia sedang berbicara (untuk visualizer)
is_listening = False   # Flag: True saat sedang mendengarkan input suara user

