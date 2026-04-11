"""Test script - bicara 'milicia' dan lihat apakah Vosk mendengarnya."""
import json
import vosk
import pyaudio
import os
import sys

# Fix unicode output di Windows console
sys.stdout.reconfigure(encoding='utf-8')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")  # ke root project

WAKE_WORDS = [
    "militia", "milicia", "melissa", "malicia",
    "mili", "milia", "million", "melee",
    "police", "felicia",
]

GRAMMAR = json.dumps(WAKE_WORDS + ["[unk]"])

print("Loading Vosk model...")
vosk.SetLogLevel(-1)  # suppress vosk logs
model = vosk.Model("vosk_model")
print("Model loaded!\n")

pa = pyaudio.PyAudio()
default_input = pa.get_default_input_device_info()
print(f"Default mic: [{default_input['index']}] {default_input['name']}\n")

# Test DENGAN grammar (constrained)
print("=" * 50)
print("Bicara 'milicia' beberapa kali...")
print("Tekan Ctrl+C untuk selesai")
print("=" * 50 + "\n")

stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
rec = vosk.KaldiRecognizer(model, 16000, GRAMMAR)

count = 0
try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "")
            if text and text.strip() != "[unk]":
                count += 1
                is_wake = any(w in text.lower() for w in WAKE_WORDS)
                marker = ">> WAKE WORD DETECTED! <<" if is_wake else "(not wake)"
                print(f"  #{count} [GRAMMAR] Heard: '{text}' {marker}")
            # Uncomment below to also see [unk] detections:
            # elif text:
            #     print(f"  (background noise)")
        else:
            partial = json.loads(rec.PartialResult())
            pt = partial.get("partial", "")
            if pt and pt.strip() != "[unk]" and pt.strip():
                print(f"  ... partial: '{pt}'", end="\r")

except KeyboardInterrupt:
    pass

stream.stop_stream()
stream.close()
pa.terminate()
print(f"\n\nTotal detections: {count}")
