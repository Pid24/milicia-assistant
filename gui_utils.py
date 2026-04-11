"""gui_utils.py — Utilitas untuk menampilkan output ke area teks GUI."""

import gui_state


def log_output(message):
    """Menampilkan pesan ke area output di GUI secara thread-safe."""
    area = gui_state.output_area
    window = gui_state.window

    if area is None:
        print(message)  # Fallback ke terminal jika GUI belum siap
        return

    def _update():
        try:
            area.configure(state="normal")
            area.insert("end", f"{message}\n")
            area.configure(state="disabled")
            area.see("end")
        except Exception:
            print(message)

    # Schedule UI update ke main thread agar thread-safe
    try:
        if window is not None:
            window.after(0, _update)
        else:
            # Fallback jika window belum di-set
            _update()
    except Exception:
        print(message)