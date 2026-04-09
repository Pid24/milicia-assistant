"""gui_utils.py — Utilitas untuk menampilkan output ke area teks GUI."""

import gui_state


def log_output(message):
    """Menampilkan pesan ke area output di GUI secara thread-safe."""
    area = gui_state.output_area
    if area is None:
        print(message)  # Fallback ke terminal jika GUI belum siap
        return

    try:
        area.configure(state="normal")
        area.insert("end", f"{message}\n")
        area.configure(state="disabled")
        area.see("end")
    except Exception:
        print(message)