"""voice.py — Modul pengenalan suara untuk Milicia AI Assistant."""

import speech_recognition as sr
import threading
import gui_state
from commands import run_command
from utils import speak, speak_natural
from gui_utils import log_output
import time
import json
import vosk
import pyaudio

recognizer = sr.Recognizer()


# Kalibrasi noise awal sekali saja agar tidak lag saat dipanggil
def init_calibration():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
    except Exception:
        pass

threading.Thread(target=init_calibration, daemon=True).start()

def listen_and_process():
    """Memulai thread baru untuk menangkap input suara."""
    # Cegah double-click saat AI sedang berpikir
    if gui_state.is_processing:
        return
    gui_state.is_processing = True
    threading.Thread(target=handle_voice_input, daemon=True).start()


def handle_voice_input():
    """Menangkap suara dari mikrofon, konversi ke teks, dan proses."""
    gui_state.is_processing = True
    gui_state.status_var.set("🎙️ Mendengarkan...")
    
    try:
        with sr.Microphone() as source:
            log_output("─" * 40)
            log_output("🎙️ Mendengarkan... (bicara sekarang)")

            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
            gui_state.status_var.set("🧠 Sedang memproses...")
            command = recognizer.recognize_google(audio, language='id-ID')
            log_output(f"🗣️ Rofid: {command}")
            run_command(command.lower())

    except sr.WaitTimeoutError:
        speak("Hmm, aku nggak dengar apa-apa. Coba tekan tombol lagi ya.")
    except sr.UnknownValueError:
        speak_natural([
            "Maaf, aku nggak menangkap itu.",
            "Bisa diulangi lagi?",
            "Sepertinya suaranya kurang jelas.",
        ])
    except sr.RequestError:
        speak("Gagal terhubung ke layanan pengenalan suara. Cek koneksi internet kamu ya.")
    except Exception as e:
        log_output(f"⚠️ Error: {e}")
    finally:
        gui_state.is_processing = False
        gui_state.status_var.set("🔵 Siap mendengarkan...")


# =============================================
# WAKE WORD (Hands-Free Mode) — Vosk Engine
# =============================================

# Daftar variasi fonetik wake word yang bisa dikenali Vosk English model.
# Karena kita pakai model EN, kita perlu mencocokkan bagaimana Vosk
# mendengar kata "Milicia" dalam bahasa Inggris.
WAKE_WORDS = [
    "militia", "milicia", "melissa", "malicia",
    "mili", "milia", "million", "melee",
    "police", "felicia",  # variasi fonetik mirip
]

# Grammar list untuk Vosk — memaksa recognizer HANYA mencocokkan
# kata-kata ini, bukan seluruh vocabulary. Ini jauh lebih akurat
# karena model kecil tidak punya "militia" di open vocabulary-nya.
# "[unk]" menangkap semua suara yang bukan wake word.
VOSK_GRAMMAR = json.dumps(
    WAKE_WORDS + ["[unk]"]
)


def _is_wake_word(text: str) -> bool:
    """Cek apakah teks mengandung wake word. Case-insensitive."""
    text = text.lower().strip()
    if not text:
        return False
    # Abaikan jika hanya "[unk]" atau kosong
    if text == "[unk]":
        return False
    for word in WAKE_WORDS:
        if word in text:
            return True
    return False


def start_wake_word_listener():
    """Menjalankan engine Vosk di background untuk menunggu kata sakti."""
    threading.Thread(target=_wake_word_loop, daemon=True).start()


def _wake_word_loop():
    """Loop utama wake word detection. Mengelola lifecycle PyAudio dengan benar."""
    
    # Load Vosk model sekali saja
    try:
        model = vosk.Model("vosk_model")
        log_output("✅ Vosk wake word engine berhasil dimuat.")
    except Exception as e:
        log_output(f"⚠️ Gagal memuat Vosk model: {e}")
        log_output("   Pastikan folder 'vosk_model' ada dan berisi model yang valid.")
        log_output("   Jalankan: python download_vosk.py")
        return

    while True:
        # Tunggu sampai handsfree mode diaktifkan
        if not gui_state.handsfree_mode:
            time.sleep(0.5)
            continue
            
        # Tunggu sampai AI selesai memproses
        if gui_state.is_processing:
            time.sleep(0.5)
            continue

        # Buat PyAudio instance baru setiap siklus untuk menghindari resource leak
        pa = None
        stream = None
        try:
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4000
            )
            rec = vosk.KaldiRecognizer(model, 16000, VOSK_GRAMMAR)

            # Loop mendengarkan sampai wake word terdeteksi atau mode dimatikan
            while gui_state.handsfree_mode and not gui_state.is_processing:
                data = stream.read(4000, exception_on_overflow=False)
                
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    
                    if text:
                        log_output(f"🔍 Vosk heard: '{text}'")
                    
                    if _is_wake_word(text):
                        log_output("🔔 Wake word 'Milicia' terdeteksi!")
                        
                        # Tutup stream SEBELUM speak & listen 
                        # agar tidak conflict dengan microphone
                        stream.stop_stream()
                        stream.close()
                        stream = None
                        pa.terminate()
                        pa = None
                        
                        # Respons ke user
                        speak("Ya Rofid?")
                        
                        # Tunggu sebentar agar speak selesai
                        time.sleep(0.3)
                        
                        # Aktifkan mode dengar
                        listen_and_process()
                        
                        # Tunggu sampai processing selesai sebelum restart loop
                        while gui_state.is_processing:
                            time.sleep(0.5)
                        
                        break  # Keluar dari inner loop, akan restart dari outer loop
                        
                else:
                    # Partial result — cek juga untuk responsivitas lebih cepat
                    partial = json.loads(rec.PartialResult())
                    partial_text = partial.get("partial", "")
                    if _is_wake_word(partial_text):
                        log_output(f"🔔 Wake word terdeteksi (partial): '{partial_text}'")
                        
                        stream.stop_stream()
                        stream.close()
                        stream = None
                        pa.terminate()
                        pa = None
                        
                        speak("Ya Rofid?")
                        time.sleep(0.3)
                        listen_and_process()
                        
                        while gui_state.is_processing:
                            time.sleep(0.5)
                        
                        break

        except OSError as e:
            log_output(f"⚠️ Audio device error: {e}")
            time.sleep(2)
        except Exception as e:
            log_output(f"⚠️ Wake word error: {e}")
            time.sleep(1)
        finally:
            # Pastikan stream dan PyAudio selalu di-cleanup
            try:
                if stream is not None:
                    if stream.is_active():
                        stream.stop_stream()
                    stream.close()
            except Exception:
                pass
            try:
                if pa is not None:
                    pa.terminate()
            except Exception:
                pass
