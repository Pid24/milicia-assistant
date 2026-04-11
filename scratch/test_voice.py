"""
test_voice.py — Script untuk test wake word (Vosk) secara isolated.
Jalankan dari folder milicia-assistant:
    python scratch/test_voice.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import vosk
import pyaudio

WAKE_WORDS = [
    "militia", "milicia", "melissa", "malicia",
    "mili", "milia", "million", "melee",
    "hey mili", "hey militia", "hey melissa",
    "police", "felicia",
]

def is_wake_word(text: str) -> bool:
    text = text.lower().strip()
    for word in WAKE_WORDS:
        if word in text:
            return True
    return False

print("🔄 Memuat Vosk model...")
try:
    model = vosk.Model("vosk_model")
    print("✅ Vosk model berhasil dimuat!")
except Exception as e:
    print(f"❌ Gagal muat model: {e}")
    sys.exit(1)

pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
rec = vosk.KaldiRecognizer(model, 16000)

print("\n🎙️  Microphone aktif. Ucapkan 'Milicia' (atau variasi apapun).")
print("    Ctrl+C untuk berhenti.\n")

try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "")
            if text:
                hit = "✅ WAKE WORD!" if is_wake_word(text) else "   (bukan wake word)"
                print(f"🔍 Vosk heard: '{text}'  {hit}")
        else:
            partial = json.loads(rec.PartialResult()).get("partial", "")
            if partial:
                print(f"   [partial] '{partial}'", end="\r")
except KeyboardInterrupt:
    print("\n\n🛑 Test dihentikan.")
finally:
    stream.stop_stream()
    stream.close()
    pa.terminate()
