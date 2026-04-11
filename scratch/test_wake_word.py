"""
Diagnostic: Cari tahu kata apa yang Vosk dengar saat kamu bilang 'milicia'.
Pakai open vocabulary (tanpa grammar) agar kita bisa lihat raw output.
Bicara 'milicia' berkali-kali dengan cara berbeda, lalu Ctrl+C untuk selesai.
"""
import json
import vosk
import pyaudio
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

vosk.SetLogLevel(-1)
print("Loading model...")
model = vosk.Model("vosk_model")
print("Model loaded!\n")
print("=" * 55)
print("Coba ucapkan 'milicia' dengan berbagai cara:")
print("  - 'milicia' (normal)")
print("  - 'milisia' (eja per suku kata)")
print("  - 'militia' (aksen inggris)")
print("  - 'hey milicia'")
print("  - 'hei milicia'")
print()
print("Semua yang Vosk dengar akan tercetak di sini.")
print("Tekan Ctrl+C untuk selesai.")
print("=" * 55 + "\n")

pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
# Open vocabulary — tanpa grammar, biar kita lihat apa yang Vosk map-kan
rec = vosk.KaldiRecognizer(model, 16000)

heard = []
try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").strip()
            if text:
                heard.append(text)
                print(f"  Vosk: '{text}'")
        else:
            partial = json.loads(rec.PartialResult()).get("partial", "").strip()
            if partial:
                print(f"  ... '{partial}'", end="\r")
except KeyboardInterrupt:
    pass

stream.stop_stream()
stream.close()
pa.terminate()

print(f"\n\nSemua yang didengar:")
for i, t in enumerate(heard, 1):
    print(f"  {i}. '{t}'")
print(f"\nTambahkan kata-kata di atas ke WAKE_WORDS di voice.py")
