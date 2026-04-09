# gui_state.py — Variabel global yang dibagikan antar modul
# Diinisialisasi oleh milicia.py, diakses oleh voice.py, commands.py, dll.

output_area = None
status_var = None
window = None
is_processing = False  # Flag untuk mencegah double-click saat AI sedang berpikir
