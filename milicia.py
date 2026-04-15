"""
Milicia — Sci-Fi JARVIS GUI
Tampilan holografik dengan visualizer arc JARVIS yang animasi
sesuai status: idle, mendengarkan, atau berbicara.
"""

import customtkinter as ctk
import json
import math
import os
import random
import sys
import threading
import time
import tkinter as tk
import pystray
from PIL import Image, ImageDraw

# Fix untuk Autostart
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Prevent multiple instances
try:
    import ctypes as _ctypes
    _hwnd = _ctypes.windll.user32.FindWindowW(None, "Milicia")
    if _hwnd:
        _ctypes.windll.user32.ShowWindow(_hwnd, 5)
        _ctypes.windll.user32.SetForegroundWindow(_hwnd)
        sys.exit(0)
except Exception:
    pass

import gui_state
from brain import is_ai_running, reset_history
from utils import speak, get_time_greeting

USER_DATA_FILE = "user_data.json"

def get_user_name():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("name", "pengguna")
    return "pengguna"

def set_user_name(name):
    data = {}
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
    data["name"] = name
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

set_user_name("Rofid")
user = get_user_name()

# ─────────────────────────────────────────────
# WARNA & TEMA SCI-FI
# ─────────────────────────────────────────────
BG_COLOR      = "#070b14"          # Midnight deep space
PANEL_COLOR   = "#0d1117"          # Card dark
BORDER_COLOR  = "#1a2740"          # Subtle blue border
ACCENT_CYAN   = "#00d4ff"          # Primary cyan (JARVIS blue)
ACCENT_GREEN  = "#00ff88"          # Speaking / active green
ACCENT_DIM    = "#0a6b8a"          # Dim cyan for idle rings
TEXT_PRIMARY  = "#c8d8e8"          # Soft white-blue
TEXT_MUTED    = "#4a6080"          # Muted gray-blue
TEXT_USER     = "#00d4ff"          # User message color
TEXT_AI       = "#00ff88"          # AI message color
TEXT_SYSTEM   = "#4a6080"          # System log color
GLOW_CYAN     = "#004466"          # Glow behind arc

# ─────────────────────────────────────────────
# CTk THEME SETUP
# ─────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────
window = ctk.CTk()
window.title("Milicia")
window.geometry("1000x700")
window.minsize(900, 620)
window.resizable(True, True)
window.configure(fg_color=BG_COLOR)
gui_state.window = window

# ─────────────────────────────────────────────
# SYSTEM TRAY
# ─────────────────────────────────────────────
tray_icon = None

def create_tray_image():
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Draw glowing M circle
    d.ellipse([4, 4, 60, 60], outline=(0, 212, 255, 200), width=3)
    d.text((18, 14), "M", fill=(0, 212, 255, 255))
    return img

def show_window(icon, item):
    icon.stop()
    window.deiconify()

def quit_app(icon=None, item=None):
    if icon:
        icon.stop()
    window.quit()
    sys.exit(0)

gui_state.hard_quit = quit_app

def hide_window():
    window.withdraw()
    global tray_icon
    image = create_tray_image()
    menu = (
        pystray.MenuItem('Tampilkan', show_window, default=True),
        pystray.MenuItem('Matikan Sepenuhnya', quit_app)
    )
    tray_icon = pystray.Icon("milicia", image, "Milicia", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

window.protocol('WM_DELETE_WINDOW', hide_window)

# ─────────────────────────────────────────────
# IMPORT VOICE & PRAYER
# ─────────────────────────────────────────────
from voice import listen_and_process, start_wake_word_listener
from gui_utils import log_output
from prayer_times import start_prayer_reminder

start_wake_word_listener()
start_prayer_reminder()

# ═══════════════════════════════════════════════════════
#  ROOT LAYOUT — 2 COLUMN: LEFT (visualizer) | RIGHT (chat)
# ═══════════════════════════════════════════════════════
root_frame = tk.Frame(window, bg=BG_COLOR)
root_frame.pack(fill="both", expand=True, padx=0, pady=0)

root_frame.columnconfigure(0, weight=0)   # Left panel fixed
root_frame.columnconfigure(1, weight=1)   # Right panel expands
root_frame.rowconfigure(0, weight=1)

# ─── LEFT PANEL ────────────────────────────────────────
left_panel = tk.Frame(root_frame, bg=BG_COLOR, width=320)
left_panel.grid(row=0, column=0, sticky="nsew", padx=(18, 0), pady=18)
left_panel.pack_propagate(False)

# App title at top of left panel
title_frame = tk.Frame(left_panel, bg=BG_COLOR)
title_frame.pack(fill="x", pady=(0, 10))

tk.Label(
    title_frame, text="MILICIA", bg=BG_COLOR, fg=ACCENT_CYAN,
    font=("Courier New", 22, "bold")
).pack()

# ─────────────────────────────────────────────
# JARVIS ARC VISUALIZER CANVAS
# ─────────────────────────────────────────────
VIZ_SIZE = 280
viz_canvas = tk.Canvas(
    left_panel,
    width=VIZ_SIZE, height=VIZ_SIZE,
    bg=BG_COLOR, highlightthickness=0
)
viz_canvas.pack(pady=(0, 12))

# ── Visualizer State ──────────────────────────
_viz_angle      = 0.0        # Rotation of outer ring
_viz_phase      = 0.0        # Wave phase
_viz_bars       = [0.0] * 32 # Waveform bar heights
_viz_particles  = []         # Floating particle dots

def _init_particles(n=18):
    global _viz_particles
    cx, cy = VIZ_SIZE / 2, VIZ_SIZE / 2
    _viz_particles = []
    for _ in range(n):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(90, 130)
        _viz_particles.append({
            "angle": angle,
            "radius": radius,
            "speed": random.uniform(0.003, 0.012),
            "size":  random.uniform(1.5, 3.5),
            "alpha": random.uniform(0.3, 1.0),
        })

_init_particles()

def _hex_to_rgb(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _blend_color(c1_hex, c2_hex, t):
    """Lerp between two hex colors."""
    r1, g1, b1 = _hex_to_rgb(c1_hex)
    r2, g2, b2 = _hex_to_rgb(c2_hex)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

def _draw_arc_ring(cx, cy, r, start_ang, span, width, color, dash=None):
    """Draw an arc ring on viz_canvas using line segments."""
    steps = max(int(abs(span) / 3), 30)
    points = []
    for i in range(steps + 1):
        a = math.radians(start_ang + span * i / steps)
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        viz_canvas.create_line(x0, y0, x1, y1, fill=color, width=width, smooth=True)

def _update_visualizer():
    global _viz_angle, _viz_phase, _viz_bars

    # Determine current AI state
    speaking  = gui_state.is_speaking
    listening = gui_state.is_listening
    processing= gui_state.is_processing

    # ── Tick rates ──────────────────────────────
    if speaking:
        angle_speed = 2.5
        phase_speed = 0.25
    elif listening:
        angle_speed = 1.2
        phase_speed = 0.10
    elif processing:
        angle_speed = 1.8
        phase_speed = 0.14
    else:
        angle_speed = 0.4
        phase_speed = 0.03

    _viz_angle = (_viz_angle + angle_speed) % 360
    _viz_phase += phase_speed

    # ── Color theme per state ───────────────────
    if speaking:
        ring_color   = ACCENT_GREEN
        mid_color    = "#00cc77"
        glow_color   = "#003322"
        core_color   = ACCENT_GREEN
    elif listening:
        ring_color   = "#ffcc00"
        mid_color    = "#ffaa00"
        glow_color   = "#332200"
        core_color   = "#ffcc00"
    elif processing:
        ring_color   = "#aa66ff"
        mid_color    = "#8844dd"
        glow_color   = "#220033"
        core_color   = "#bb77ff"
    else:
        ring_color   = ACCENT_CYAN
        mid_color    = ACCENT_DIM
        glow_color   = GLOW_CYAN
        core_color   = ACCENT_CYAN

    # ── Update waveform bars ────────────────────
    for i in range(len(_viz_bars)):
        if speaking:
            target = abs(math.sin(_viz_phase * 3 + i * 0.6)) * 38 + \
                     abs(math.sin(_viz_phase * 5 + i * 1.1)) * 20 + \
                     random.uniform(0, 8)
        elif listening:
            target = abs(math.sin(_viz_phase * 2 + i * 0.4)) * 25 + random.uniform(0, 5)
        elif processing:
            target = abs(math.sin(_viz_phase * 4 + i * 0.8)) * 28 + random.uniform(0, 6)
        else:
            target = abs(math.sin(_viz_phase + i * 0.3)) * 8 + 2
        _viz_bars[i] += (target - _viz_bars[i]) * 0.3

    # ── Update particle positions ───────────────
    for p in _viz_particles:
        p["angle"] = (p["angle"] + p["speed"] * (2.5 if speaking else 0.8)) % (2 * math.pi)

    # ════════════════════════════════════════════
    # DRAW
    # ════════════════════════════════════════════
    viz_canvas.delete("all")
    cx, cy = VIZ_SIZE / 2, VIZ_SIZE / 2

    # ── Background glow circle ──────────────────
    for r_off, alpha_factor in [(60, 0.12), (52, 0.18), (42, 0.25)]:
        r = 100 + r_off
        viz_canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=glow_color, outline=""
        )

    # ── Hex grid background lines (subtle) ─────
    hex_color = "#0d1f33"
    for ring_r in [50, 80, 110, 140]:
        viz_canvas.create_oval(
            cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
            outline=hex_color, width=1
        )
    for angle_deg in range(0, 360, 30):
        a = math.radians(angle_deg)
        viz_canvas.create_line(
            cx, cy,
            cx + 140 * math.cos(a), cy + 140 * math.sin(a),
            fill=hex_color, width=1
        )

    # ── Outer rotating dashed arc segments ─────
    num_arc_segments = 8
    gap_degrees = 8
    segment_span = (360 / num_arc_segments) - gap_degrees
    for i in range(num_arc_segments):
        start = _viz_angle + i * (360 / num_arc_segments)
        brightness = 0.4 + 0.6 * abs(math.sin(math.radians(start * 2)))
        color = _blend_color(glow_color, ring_color, brightness)
        _draw_arc_ring(cx, cy, 128, start, segment_span, 2, color)

    # Outer ring slow counter-rotate
    for i in range(num_arc_segments):
        start = -_viz_angle * 0.5 + i * (360 / num_arc_segments) + 15
        _draw_arc_ring(cx, cy, 118, start, segment_span * 0.6, 1, mid_color)

    # ── Waveform bars (radial) ──────────────────
    n_bars = len(_viz_bars)
    base_r = 70
    for i, bar_h in enumerate(_viz_bars):
        a = math.radians(i * 360 / n_bars - 90)
        inner = base_r
        outer = base_r + bar_h
        x0 = cx + inner * math.cos(a)
        y0 = cy + inner * math.sin(a)
        x1 = cx + outer * math.cos(a)
        y1 = cy + outer * math.sin(a)
        # Color gradient from dim to bright based on height
        t = min(bar_h / 60, 1.0)
        bar_col = _blend_color(mid_color, ring_color, t)
        viz_canvas.create_line(x0, y0, x1, y1, fill=bar_col, width=2, capstyle="round")

    # ── Middle ring ─────────────────────────────
    _draw_arc_ring(cx, cy, 62, _viz_angle * -0.7, 340, 1, mid_color)

    # ── Inner core circle ────────────────────────
    pulse = 0.85 + 0.15 * math.sin(_viz_phase * 6)
    core_r = int(22 * pulse)
    viz_canvas.create_oval(
        cx - core_r - 6, cy - core_r - 6, cx + core_r + 6, cy + core_r + 6,
        fill=glow_color, outline=""
    )
    viz_canvas.create_oval(
        cx - core_r, cy - core_r, cx + core_r, cy + core_r,
        fill=BG_COLOR, outline=core_color, width=2
    )
    # Core dot
    dot_r = int(8 * pulse)
    viz_canvas.create_oval(
        cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r,
        fill=core_color, outline=""
    )

    # ── Floating particles ──────────────────────
    for p in _viz_particles:
        px = cx + p["radius"] * math.cos(p["angle"])
        py = cy + p["radius"] * math.sin(p["angle"])
        pr = p["size"]
        alpha_color = _blend_color(BG_COLOR, ring_color, p["alpha"] * (0.7 if not speaking else 1.0))
        viz_canvas.create_oval(
            px - pr, py - pr, px + pr, py + pr,
            fill=alpha_color, outline=""
        )

    # ── Status text below core ──────────────────
    if speaking:
        status_text = "● SPEAKING"
        status_col = ACCENT_GREEN
    elif listening:
        status_text = "◉ LISTENING"
        status_col = "#ffcc00"
    elif processing:
        status_text = "⟳ PROCESSING"
        status_col = "#aa66ff"
    else:
        status_text = "○ STANDBY"
        status_col = TEXT_MUTED

    viz_canvas.create_text(
        cx, cy + 108,
        text=status_text,
        fill=status_col,
        font=("Courier New", 9, "bold")
    )

    # Schedule next frame (50ms = ~20fps, smooth but light on CPU)
    window.after(50, _update_visualizer)

# ─────────────────────────────────────────────
# STATUS BADGES (below visualizer)
# ─────────────────────────────────────────────
ai_active = is_ai_running()

badge_frame = tk.Frame(left_panel, bg=BG_COLOR)
badge_frame.pack(fill="x", pady=(0, 8))

_status_dot_color = "#2ecc71" if ai_active else "#e74c3c"
_status_text      = "ONLINE" if ai_active else "OFFLINE"

tk.Label(
    badge_frame,
    text=f"◉ GEMINI: {_status_text}",
    bg=BG_COLOR, fg=_status_dot_color,
    font=("Courier New", 9, "bold")
).pack(side="left", padx=4)

tk.Label(
    badge_frame,
    text="⚡ gemini-2.0-flash",
    bg=BG_COLOR, fg=TEXT_MUTED,
    font=("Courier New", 9)
).pack(side="right", padx=4)

# ─────────────────────────────────────────────
# USER INFO + CLOCK CLOCK IN LEFT PANEL
# ─────────────────────────────────────────────
info_frame = tk.Frame(left_panel, bg=BG_COLOR)
info_frame.pack(fill="x", pady=(2, 4))

tk.Label(
    info_frame,
    text=f"USER // {user.upper()}",
    bg=BG_COLOR, fg=TEXT_MUTED,
    font=("Courier New", 9)
).pack(side="left", padx=4)

clock_label = tk.Label(
    info_frame,
    text="",
    bg=BG_COLOR, fg=ACCENT_CYAN,
    font=("Courier New", 9, "bold")
)
clock_label.pack(side="right", padx=4)

def _update_clock():
    import datetime
    now = datetime.datetime.now()
    clock_label.config(text=now.strftime("%H:%M:%S"))
    window.after(1000, _update_clock)

_update_clock()

# ─────────────────────────────────────────────
# LEFT PANEL DIVIDER LINE
# ─────────────────────────────────────────────
tk.Frame(left_panel, bg=BORDER_COLOR, height=1).pack(fill="x", pady=6)

# ─────────────────────────────────────────────
# VOICE CONTROLS (LEFT PANEL BOTTOM)
# ─────────────────────────────────────────────
ctrl_frame = tk.Frame(left_panel, bg=BG_COLOR)
ctrl_frame.pack(fill="x", pady=(4, 8))

def _on_speak_btn_hover(e):
    speak_btn.config(bg="#003344")

def _on_speak_btn_leave(e):
    speak_btn.config(bg=BG_COLOR)

speak_btn = tk.Button(
    ctrl_frame,
    text="  🎙  BICARA",
    bg=BG_COLOR,
    fg=ACCENT_CYAN,
    activebackground="#003344",
    activeforeground=ACCENT_CYAN,
    font=("Courier New", 11, "bold"),
    relief="flat",
    bd=0,
    cursor="hand2",
    command=listen_and_process,
    highlightthickness=1,
    highlightbackground=ACCENT_DIM,
    padx=8,
    pady=6
)
speak_btn.pack(fill="x", pady=(0, 6), ipady=2)
speak_btn.bind("<Enter>", _on_speak_btn_hover)
speak_btn.bind("<Leave>", _on_speak_btn_leave)

def _on_reset_btn():
    reset_history()
    output_text.config(state="normal")
    output_text.delete("1.0", "end")
    output_text.config(state="disabled")
    log_output("🔄 Memori dihapus. Percakapan baru dimulai!")

reset_btn = tk.Button(
    ctrl_frame,
    text="  🗑  RESET CHAT",
    bg=BG_COLOR,
    fg=TEXT_MUTED,
    activebackground="#1a1a1a",
    activeforeground=TEXT_PRIMARY,
    font=("Courier New", 10),
    relief="flat",
    bd=0,
    cursor="hand2",
    command=_on_reset_btn,
    highlightthickness=1,
    highlightbackground=BORDER_COLOR,
    padx=8,
    pady=4
)
reset_btn.pack(fill="x", pady=(0, 4))

# ─────────────────────────────────────────────
# HANDS-FREE TOGGLE
# ─────────────────────────────────────────────
hf_var = tk.BooleanVar(value=False)

def toggle_handsfree():
    mode = hf_var.get()
    gui_state.handsfree_mode = mode
    if mode:
        hf_btn.config(
            text="  ◉  HANDS-FREE: ON",
            fg=ACCENT_GREEN,
            highlightbackground=ACCENT_GREEN
        )
        log_output("✅ Hands-Free AKTIF. Ucapkan 'Milicia' kapan saja.")
        if not os.path.exists("vosk_model"):
            log_output("⚠️ Vosk model belum terinstall. Jalankan download_vosk.py")
    else:
        hf_btn.config(
            text="  ○  HANDS-FREE: OFF",
            fg=TEXT_MUTED,
            highlightbackground=BORDER_COLOR
        )
        log_output("🚫 Hands-Free MATI.")

hf_btn = tk.Checkbutton(
    ctrl_frame,
    text="  ○  HANDS-FREE: OFF",
    variable=hf_var,
    onvalue=True,
    offvalue=False,
    bg=BG_COLOR,
    fg=TEXT_MUTED,
    activebackground=BG_COLOR,
    activeforeground=ACCENT_GREEN,
    selectcolor=BG_COLOR,
    font=("Courier New", 10),
    relief="flat",
    bd=0,
    cursor="hand2",
    command=toggle_handsfree,
    highlightthickness=1,
    highlightbackground=BORDER_COLOR,
    padx=8,
    pady=4,
    anchor="w"
)
hf_btn.pack(fill="x")

# Store reference to handsfree switch (for compatibility with voice.py)
gui_state.handsfree_switch = hf_btn

# Patch: handsfree_switch compatibility (voice.py calls .get() and .deselect())
class _HFSwitchCompat:
    def get(self): return hf_var.get()
    def deselect(self):
        hf_var.set(False)
        toggle_handsfree()
    def select(self):
        hf_var.set(True)
        toggle_handsfree()

gui_state.handsfree_switch = _HFSwitchCompat()

# ─── RIGHT PANEL ───────────────────────────────────────
right_panel = tk.Frame(root_frame, bg=BG_COLOR)
right_panel.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
right_panel.pack_propagate(True)

# ─────────────────────────────────────────────
# CHAT HEADER
# ─────────────────────────────────────────────
chat_header = tk.Frame(right_panel, bg=PANEL_COLOR, height=44)
chat_header.pack(fill="x", pady=(0, 8))
chat_header.pack_propagate(False)

tk.Label(
    chat_header,
    text="◈  NEURAL INTERFACE  //  CHAT LOG",
    bg=PANEL_COLOR, fg=ACCENT_CYAN,
    font=("Courier New", 10, "bold")
).pack(side="left", padx=12, pady=10)

tk.Label(
    chat_header,
    text=f"AGENT: MILICIA v2.0",
    bg=PANEL_COLOR, fg=TEXT_MUTED,
    font=("Courier New", 9)
).pack(side="right", padx=12, pady=10)

# ─────────────────────────────────────────────
# CHAT OUTPUT AREA
# ─────────────────────────────────────────────
chat_frame = tk.Frame(right_panel, bg=PANEL_COLOR, bd=0)
chat_frame.pack(fill="both", expand=True, pady=(0, 8))

output_text = tk.Text(
    chat_frame,
    bg=PANEL_COLOR,
    fg=TEXT_PRIMARY,
    insertbackground=ACCENT_CYAN,
    selectbackground="#1a3a55",
    font=("Consolas", 12),
    relief="flat",
    bd=0,
    wrap="word",
    spacing1=4,
    spacing3=6,
    padx=14,
    pady=10,
    cursor="arrow",
    state="disabled"
)
output_text.pack(side="left", fill="both", expand=True)

# Scrollbar (styled)
scrollbar = tk.Scrollbar(chat_frame, bg=PANEL_COLOR, troughcolor=BG_COLOR,
                          activebackground=ACCENT_DIM, relief="flat", bd=0, width=6)
scrollbar.pack(side="right", fill="y")
output_text.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=output_text.yview)

# Tag colors for different message types
output_text.tag_config("user",   foreground=TEXT_USER,   font=("Consolas", 12, "bold"))
output_text.tag_config("ai",     foreground=TEXT_AI,     font=("Consolas", 12))
output_text.tag_config("system", foreground=TEXT_SYSTEM, font=("Consolas", 11))
output_text.tag_config("warn",   foreground="#ffaa00",   font=("Consolas", 11))
output_text.tag_config("prefix", foreground=ACCENT_DIM,  font=("Consolas", 12, "bold"))

# ─────────────────────────────────────────────
# HOOK: gui_state.output_area → use custom log
# ─────────────────────────────────────────────
# We wrap a fake "area" object that gui_utils can call .insert() on
class _FakeTextArea:
    """Duck-typed proxy that routes log_output calls into our styled output_text."""
    def configure(self, **kw): pass
    def insert(self, pos, content):
        self._write_styled(content)

    def _write_styled(self, content: str):
        content = content.rstrip("\n")
        if not content:
            return

        def _do():
            output_text.config(state="normal")
            # Detect line type
            if content.startswith("⌨️"):
                parts = content.split(":", 1)
                output_text.insert("end", parts[0] + ":", "prefix")
                if len(parts) > 1:
                    output_text.insert("end", parts[1], "user")
            elif content.startswith("🤖"):
                parts = content.split(":", 1)
                output_text.insert("end", parts[0] + ":", "prefix")
                if len(parts) > 1:
                    output_text.insert("end", parts[1], "ai")
            elif "⚠️" in content or "❌" in content:
                output_text.insert("end", content, "warn")
            elif content.startswith("✅") or content.startswith("🔍") or \
                 content.startswith("📰") or content.startswith("⚡"):
                output_text.insert("end", content, "system")
            else:
                output_text.insert("end", content, "system")
            output_text.insert("end", "\n")
            output_text.config(state="disabled")
            output_text.see("end")

        try:
            if gui_state.window:
                gui_state.window.after(0, _do)
            else:
                _do()
        except Exception:
            pass

    def see(self, pos): pass

_fake_area = _FakeTextArea()
gui_state.output_area = _fake_area

# ─────────────────────────────────────────────
# INPUT BAR (bottom of right panel)
# ─────────────────────────────────────────────
input_bg = tk.Frame(right_panel, bg=PANEL_COLOR, bd=0)
input_bg.pack(fill="x", pady=(0, 0))

prompt_label = tk.Label(
    input_bg, text="> ", bg=PANEL_COLOR, fg=ACCENT_CYAN,
    font=("Courier New", 13, "bold")
)
prompt_label.pack(side="left", padx=(10, 0), pady=8)

text_input = tk.Entry(
    input_bg,
    bg=PANEL_COLOR,
    fg=TEXT_PRIMARY,
    insertbackground=ACCENT_CYAN,
    font=("Consolas", 13),
    relief="flat",
    bd=0,
    highlightthickness=0,
)
text_input.pack(side="left", fill="x", expand=True, pady=10, ipady=4)

def _process_text_command(text):
    from commands import run_command
    try:
        run_command(text)
    finally:
        gui_state.is_processing = False
        gui_state.status_var.set("STANDBY")

def _handle_submit(event=None):
    if gui_state.is_processing:
        return
    text = text_input.get().strip()
    if not text:
        return
    text_input.delete(0, "end")
    gui_state.is_processing = True
    gui_state.status_var.set("PROCESSING...")
    log_output(f"⌨️ Rofid: {text}")
    threading.Thread(target=_process_text_command, args=(text,), daemon=True).start()

text_input.bind("<Return>", _handle_submit)
text_input.focus_set()

send_btn = tk.Button(
    input_bg,
    text="SEND ▶",
    bg=ACCENT_DIM,
    fg=ACCENT_CYAN,
    activebackground=GLOW_CYAN,
    activeforeground=ACCENT_CYAN,
    font=("Courier New", 10, "bold"),
    relief="flat",
    bd=0,
    cursor="hand2",
    command=_handle_submit,
    padx=14,
    pady=2
)
send_btn.pack(side="right", padx=(0, 10), pady=8)

# ─────────────────────────────────────────────
# STATUS BAR (very bottom strip)
# ─────────────────────────────────────────────
status_var = tk.StringVar(value="STANDBY")
gui_state.status_var = status_var

status_strip = tk.Frame(window, bg=BORDER_COLOR, height=22)
status_strip.pack(fill="x", side="bottom")
status_strip.pack_propagate(False)

tk.Label(
    status_strip,
    text="  MILICIA NEURAL INTERFACE  |  SYSTEM ONLINE  ",
    bg=BORDER_COLOR, fg=TEXT_MUTED,
    font=("Courier New", 8)
).pack(side="left", padx=6, pady=3)

status_label = tk.Label(
    status_strip,
    textvariable=status_var,
    bg=BORDER_COLOR, fg=ACCENT_CYAN,
    font=("Courier New", 8, "bold")
)
status_label.pack(side="right", padx=10, pady=3)

# ─────────────────────────────────────────────
# STARTUP SEQUENCE
# ─────────────────────────────────────────────
def _startup_log():
    log_output("◈ Inisialisasi MILICIA NEURAL INTERFACE v2.0...")
    time.sleep(0.3)
    log_output("◈ Loading JARVIS core modules... OK")
    time.sleep(0.2)
    log_output("◈ Connecting to Gemini Cloud AI brain...")
    time.sleep(0.2)
    if ai_active:
        log_output("✅ GEMINI AI Engine: ONLINE")
    else:
        log_output("⚠️ GEMINI AI Engine: OFFLINE — periksa API key di user_data.json!")
    time.sleep(0.1)
    log_output("◈ Prayer time daemon: RUNNING")
    log_output("◈ Wake-word listener: ARMED")
    log_output("─" * 50)

threading.Thread(target=_startup_log, daemon=True).start()

# CLI: --background mode
if "--background" in sys.argv:
    window.withdraw()
    hide_window()
    gui_state.handsfree_switch.select()

if ai_active:
    time_greeting = get_time_greeting()
    threading.Thread(
        target=speak,
        args=(f"{time_greeting} {user}! Sistem Milicia sudah online dan siap membantu.",),
        daemon=True
    ).start()

# Start visualizer animation loop
window.after(100, _update_visualizer)

window.mainloop()
