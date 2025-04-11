import gui_state

def log_output(message):
    area = gui_state.output_area
    area.configure(state="normal")
    area.insert("end", f"{message}\n")
    area.configure(state="disabled")
    area.see("end")