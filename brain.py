"""
brain.py — Otak Utama AI Milicia menggunakan Google Gemini API (Cloud LLM)
Modul ini menggantikan Ollama dan menggunakan Gemini untuk percakapan
serta Tool Calling (Agentic Actions).
"""

import os
import json
import datetime
import google.generativeai as genai
from google.generativeai.types import content_types

import prayer_times
from prayer_times import get_prayer_schedule
from gui_utils import log_output

# Import semua fungsi nyata (tools) dari actions.py
from actions import (
    open_website, open_application, shutdown_computer, restart_computer,
    lock_screen, set_volume, get_battery_status, get_system_info,
    take_screenshot, search_files, search_web, search_news, open_file, analyze_screen,
    execute_action
)

# Kumpulkan semua function untuk diumpan ke Gemini
MILICIA_TOOLS = [
    open_website, open_application, shutdown_computer, restart_computer,
    lock_screen, set_volume, get_battery_status, get_system_info,
    take_screenshot, search_files, search_web, search_news, open_file, analyze_screen
]

MODEL_NAME = "gemini-flash-latest"

# =========================================================
# SYSTEM PROMPT
# =========================================================
SYSTEM_PROMPT = """Kamu adalah Milicia, asisten virtual pribadi milik Rofid. 
Kamu berbicara dalam Bahasa Indonesia yang santai, hangat, dan ramah.
Kamu pintar, lucu, dan suka membantu.
Kamu bisa membantu menjawab pertanyaan, memberikan saran, mengobrol santai, 
memberikan rekomendasi anime, membantu perhitungan matematika, dan banyak lagi.

Kamu JUGA memiliki kemampuan untuk MENGENDALIKAN KOMPUTER Rofid melalui tools yang tersedia.
Kamu bisa membuka aplikasi, membuka website, mengecek baterai, mengontrol volume, 
mengambil screenshot, mencari file, mencari informasi di internet, menganalisa isi layar, dan lainnya.

Kamu SEKARANG BISA MELIHAT LAYAR. Jika Rofid memintamu menjelaskan sesuatu di layar, memperbaiki kode yang error di layar, atau bertanya "apa yang kamu lihat?", "lihat layar", kamu WAJIB menggunakan perintah analyze_screen. Mata kamu terhubung ke Cloud (Gemini) sehingga kamu bisa menganalisa detail gambar dengan sangat sempurna. Minta pengguna menunjukkan gambar di layar terlebih dahulu.

Aturan penting:
- Selalu jawab dengan ringkas dan jelas (maksimal 3-4 kalimat) kecuali diminta detail.
- Gunakan emoji sesekali untuk membuat percakapan lebih hidup.
- Jika pengguna meminta kamu melakukan sesuatu yang bisa dilakukan dengan tools, GUNAKAN TOOLS YANG TERSEDIA.
- Jika pengguna meminta membuka aplikasi atau website, gunakan tool yang sesuai.
- Panggil pengguna dengan nama "Rofid" atau "kak" sesekali.
- Kamu BUKAN chatbot biasa. Kamu adalah asisten pribadi seperti Jarvis dari Iron Man.
- Setelah menjalankan tool, berikan konfirmasi singkat dan natural kepada pengguna.
- DILARANG KERAS menggunakan kata-kata kasar, vulgar, tidak sopan, atau kata makian.
- Kamu paham tentang jadwal sholat Islam. Ada 5 waktu sholat wajib: Subuh, Dzuhur, Ashar, Maghrib, dan Isya.
- Pada hari JUMAT, sholat Dzuhur digantikan oleh SHOLAT JUMAT.
"""

# =========================================================
# STATE & INITIALIZATION
# =========================================================
_api_key_loaded = False
_chat_session = None

def _load_api_key():
    global _api_key_loaded
    if _api_key_loaded:
        return True

    api_key = None
    if os.path.exists("user_data.json"):
        try:
            with open("user_data.json", "r") as f:
                data = json.load(f)
                api_key = data.get("gemini_api_key")
        except Exception:
            pass
            
    if api_key:
        genai.configure(api_key=api_key)
        _api_key_loaded = True
        return True
    return False

def _get_system_context() -> str:
    now = datetime.datetime.now()
    informasi_tambahan = f"\n\n[INFO SISTEM: Saat ini tanggal {now.strftime('%d-%m-%Y')} dan waktu menunjukkan tepat jam {now.strftime('%H:%M')}."

    schedule = get_prayer_schedule()
    if schedule:
        prayer_info = ", ".join(f"{k}: {v}" for k, v in schedule.items())
        city = prayer_times.user_location.get('city', 'wilayah mu')
        day_name = now.strftime("%A")
        hari_map = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}
        hari = hari_map.get(day_name, day_name)
        informasi_tambahan += f" Hari ini hari {hari}. Jadwal waktu sholat hari ini untuk {city}: {prayer_info}."
        if hari == "Jumat":
            informasi_tambahan += " CATATAN: Hari ini JUMAT, sholat Dzuhur digantikan oleh Sholat Jumat yang wajib berjamaah di masjid."
    
    informasi_tambahan += "]"
    return SYSTEM_PROMPT + informasi_tambahan

def _init_chat_session():
    global _chat_session
    if not _load_api_key():
        return False
        
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=_get_system_context(),
            tools=MILICIA_TOOLS
        )
        _chat_session = model.start_chat()
        return True
    # Fallback to gemini-1.5-flash if 2.0 is not avaiable for the user's API key yet
    except Exception as e:
        if "is not found for API version" in str(e) or "models/gemini-2.0-flash" in str(e):
             model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                system_instruction=_get_system_context(),
                tools=MILICIA_TOOLS
            )
             _chat_session = model.start_chat()
             return True
        else:
             return False


def is_ai_running() -> bool:
    """Mengecek apakah API Key ada dan sistem cloud siap."""
    return _load_api_key()

def add_to_history(user_text: str, assistant_text: str):
    """Menambahkan konteks ke memori tanpa meminta balasan."""
    global _chat_session
    if _chat_session is None:
        _init_chat_session()
    if _chat_session:
        _chat_session.history.append(genai.protos.Content(role="user", parts=[genai.protos.Part(text=user_text)]))
        _chat_session.history.append(genai.protos.Content(role="model", parts=[genai.protos.Part(text=assistant_text)]))

def reset_history():
    """Mengosongkan riwayat percakapan."""
    global _chat_session
    _chat_session = None

def ask_ai(user_message: str) -> str:
    """
    Kirim pesan ke Gemini. Mendukung Tool Calling (Function Calling).
    Jika Gemini memanggil fungsi (tool execution), kita eksekusi lokal dan kirim balik hasilnya.
    """
    global _chat_session
    
    if not _load_api_key():
        return "Aku belum terhubung ke otak Cloud-ku. Tolong periksa gemini_api_key di user_data.json ya!"
        
    if _chat_session is None:
        success = _init_chat_session()
        if not success:
            return "Maaf, aku gagal inisialisasi sesi ngobrol baruku."

    now = datetime.datetime.now()
    time_context = f"[INFO: Waktu saat ini adalah {now.strftime('%H:%M')}]\n{user_message}"

    try:
        response = _chat_session.send_message(time_context)
        
        confirm_action = None
        
        # Mengecek apakah model ingin menjalankan fungsi berulang (chained tools)
        iteration_limit = 5
        iteration = 0
        while response.parts and any(part.function_call for part in response.parts) and iteration < iteration_limit:
            iteration += 1
            log_output("🔧 Gemini memilih untuk menjalankan aksi otomatis...")
            
            function_responses = []
            for part in response.parts:
                if fn := part.function_call:
                    func_name = fn.name
                    args = {k: v for k, v in fn.args.items()}
                    
                    try:
                        result = execute_action(func_name, args)
                    except Exception as e:
                        result = str(e)
                        
                    if result == "__CONFIRM_SHUTDOWN__":
                        confirm_action = "shutdown"
                        result = "Menunggu konfirmasi pengguna."
                    elif result == "__CONFIRM_RESTART__":
                        confirm_action = "restart"
                        result = "Menunggu konfirmasi pengguna."
                        
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=func_name,
                                response={"result": result}
                            )
                        )
                    )
                    
            if function_responses:
                response = _chat_session.send_message(function_responses)
            else:
                break
                
        # Setelah loop selesai (atau tidak memanggil fungsi), baca teks balasannya
        try:
            ai_reply = response.text.strip()
            if not ai_reply:
                ai_reply = "Aksi sudah kulaksanakan!"
        except ValueError:
            ai_reply = "Aksi sudah kulaksanakan!"
            
        if confirm_action:
            return f"__CONFIRM_{confirm_action.upper()}__|{ai_reply}"
        return ai_reply

    except Exception as e:
        log_output(f"⚠️ Error Gemini API: {str(e)}")
        return "Maaf, kepalaku agak pusing karena koneksi ke Cloud terputus sementara. Coba ulang lagi."


def ask_ai_simple(message: str) -> str:
    """
    Versi ringan, tidak menggunakan riwayat percakapan utama, digunakan saat merespon 
    konfirmasi singkat bahwa suatu aksi (yang ditentukan via smart router regex) sudah dilakukan.
    """
    if not _load_api_key():
        return "Sudah kujalankan!"
        
    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest", 
            system_instruction=_get_system_context()
        )
        response = model.generate_content(message)
        return response.text.strip()
    except Exception:
        return "Aksinya sudah dikoordinasikan."


def ask_ai_detailed(message: str) -> str:
    """
    Versi detail, tidak menggunakan riwayat karena context sudah dicakup, digunakan untuk 
    menjelaskan berita, dsb.
    """
    if not _load_api_key():
        return "Maaf, aku butuh otak cloud-ku aktif untuk detail ini."
        
    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest", 
            system_instruction=_get_system_context()
        )
        response = model.generate_content(message)
        return response.text.strip()
    except Exception:
        return "Penjelasan detail gagal diambil dari Cloud."
