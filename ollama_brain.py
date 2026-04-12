"""
ollama_brain.py — Otak AI Milicia menggunakan Ollama (Local LLM)
Modul ini menangani komunikasi dengan server Ollama yang berjalan di localhost.
Milicia mengirimkan teks ke sini, dan menerima balasan cerdas dari AI.

UPGRADE: Sekarang mendukung Tool Calling (Function Calling) agar Milicia
bisa mengeksekusi aksi nyata di komputer, bukan hanya menjawab teks.
"""

import requests
import json
import datetime
import prayer_times
from actions import TOOL_DEFINITIONS, execute_action
from gui_utils import log_output

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"

# System prompt — kepribadian Milicia + instruksi agentic
SYSTEM_PROMPT = """Kamu adalah Milicia, asisten virtual pribadi milik Rofid. 
Kamu berbicara dalam Bahasa Indonesia yang santai, hangat, dan ramah.
Kamu pintar, lucu, dan suka membantu.
Kamu bisa membantu menjawab pertanyaan, memberikan saran, mengobrol santai, 
memberikan rekomendasi anime, membantu perhitungan matematika, dan banyak lagi.

Kamu JUGA memiliki kemampuan untuk MENGENDALIKAN KOMPUTER Rofid melalui tools yang tersedia.
Kamu bisa membuka aplikasi, membuka website, mengecek baterai, mengontrol volume, 
mengambil screenshot, mencari file, mencari informasi di internet, dan lainnya.

Aturan penting:
- Selalu jawab dengan ringkas dan jelas (maksimal 3-4 kalimat) kecuali diminta detail.
- Gunakan emoji sesekali untuk membuat percakapan lebih hidup.
- Jika pengguna meminta kamu melakukan sesuatu yang bisa dilakukan dengan tools, GUNAKAN TOOLS YANG TERSEDIA. Jangan hanya bilang kamu akan melakukannya, LAKUKAN langsung.
- Jika pengguna meminta membuka aplikasi atau website, gunakan tool yang sesuai.
- Panggil pengguna dengan nama "Rofid" atau "kak" sesekali.
- Kamu BUKAN chatbot biasa. Kamu adalah asisten pribadi seperti Jarvis dari Iron Man.
- Setelah menjalankan tool, berikan konfirmasi singkat dan natural kepada pengguna.
"""

# Riwayat percakapan (memori jangka pendek)
conversation_history = []

# Batasan memori (menyimpan N pesan terakhir agar tidak membebani RAM)
MAX_HISTORY = 20


def reset_history():
    """Menghapus seluruh riwayat percakapan."""
    global conversation_history
    conversation_history = []


def ask_ollama(user_message: str) -> str:
    """
    Mengirimkan pesan pengguna ke Ollama dan mengembalikan balasan AI.
    Mendukung Tool Calling: jika model memutuskan perlu menjalankan aksi,
    fungsi ini akan mengeksekusi aksi tersebut dan mengirimkan hasilnya
    kembali ke model untuk respons final.
    
    Returns:
        str: Respons AI (bisa berupa teks biasa atau konfirmasi aksi).
              Jika respons mengandung "__CONFIRM_SHUTDOWN__" atau "__CONFIRM_RESTART__",
              caller (commands.py) harus menampilkan dialog konfirmasi.
    """
    global conversation_history

    # Tambahkan pesan user ke riwayat
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Potong riwayat jika terlalu panjang
    if len(conversation_history) > MAX_HISTORY:
        conversation_history = conversation_history[-MAX_HISTORY:]

    now = datetime.datetime.now()
    informasi_tambahan = f"\n\n[INFO SISTEM: Saat ini tanggal {now.strftime('%d-%m-%Y')} dan waktu menunjukkan tepat jam {now.strftime('%H:%M')}."

    if prayer_times.cached_prayer_times:
        prayer_info = ", ".join(f"{k}: {v}" for k, v in prayer_times.cached_prayer_times.items())
        city = prayer_times.user_location.get('city', 'wilayah mu')
        informasi_tambahan += f" Jadwal waktu sholat hari ini untuk {city}: {prayer_info}.]"
    else:
        informasi_tambahan += "]"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + informasi_tambahan}
    ] + conversation_history
    
    # Prepend Contextual Time to the current user's message to avoid memory hallucination
    messages[-1]["content"] = f"[Konteks Waktu: {now.strftime('%H:%M')}]\n{user_message}"

    try:
        # === STEP 1: Kirim pesan ke Ollama DENGAN tool definitions ===
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "tools": TOOL_DEFINITIONS,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 512,
                }
            },
            timeout=120  # Timeout lebih lama untuk model 3b + tool processing
        )

        if response.status_code != 200:
            return f"Maaf, terjadi kesalahan saat menghubungi otak AI ku. (Status: {response.status_code})"

        data = response.json()
        assistant_message = data.get("message", {})

        # === STEP 2: Cek apakah model ingin memanggil tool ===
        tool_calls = assistant_message.get("tool_calls")

        if tool_calls:
            # Model ingin menjalankan satu atau lebih aksi
            log_output(f"🔧 AI memilih {len(tool_calls)} aksi untuk dijalankan...")

            # Simpan response assistant (yang berisi tool_calls) ke history
            conversation_history.append(assistant_message)

            # Eksekusi setiap tool call dan kumpulkan hasilnya
            confirm_action = None  # Track jika ada aksi yang butuh konfirmasi
            
            for tc in tool_calls:
                func_name = tc.get("function", {}).get("name", "")
                func_args = tc.get("function", {}).get("arguments", {})

                # Eksekusi aksi
                result = execute_action(func_name, func_args)

                # Cek apakah ini aksi yang butuh konfirmasi GUI
                if result == "__CONFIRM_SHUTDOWN__":
                    confirm_action = "shutdown"
                    result = "Menunggu konfirmasi pengguna untuk mematikan komputer."
                elif result == "__CONFIRM_RESTART__":
                    confirm_action = "restart"
                    result = "Menunggu konfirmasi pengguna untuk restart komputer."

                # Kirim hasil eksekusi kembali ke model sebagai role "tool"
                tool_result_message = {
                    "role": "tool",
                    "content": result
                }
                conversation_history.append(tool_result_message)

            # === STEP 3: Kirim hasil tool kembali ke model untuk respons natural ===
            followup_messages = [
                {"role": "system", "content": SYSTEM_PROMPT + informasi_tambahan}
            ] + conversation_history

            followup_response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": followup_messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 256,
                    }
                },
                timeout=120
            )

            if followup_response.status_code == 200:
                followup_data = followup_response.json()
                ai_reply = followup_data.get("message", {}).get("content", "").strip()

                if not ai_reply:
                    ai_reply = "Sudah ku-jalankan perintahmu, Rofid."

                # Simpan respons final ke riwayat
                conversation_history.append({
                    "role": "assistant",
                    "content": ai_reply
                })

                # Jika ada aksi yang butuh konfirmasi, prepend marker
                if confirm_action:
                    return f"__CONFIRM_{confirm_action.upper()}__|{ai_reply}"

                return ai_reply
            else:
                return "Aksinya sudah ku-jalankan, tapi aku gagal merangkai kalimat konfirmasi."

        else:
            # === Tidak ada tool call — respons teks biasa ===
            ai_reply = assistant_message.get("content", "").strip()

            if not ai_reply:
                ai_reply = "Hmm, aku tidak bisa berpikir sekarang. Coba lagi ya."

            # Simpan balasan AI ke riwayat
            conversation_history.append({
                "role": "assistant",
                "content": ai_reply
            })

            return ai_reply

    except requests.exceptions.ConnectionError:
        return "Aku tidak bisa terhubung ke otak AI. Pastikan Ollama sudah berjalan di komputer kamu ya! (jalankan: ollama serve)"
    except requests.exceptions.Timeout:
        return "Otak AI ku butuh waktu terlalu lama untuk berpikir. Coba tanya yang lebih singkat ya."
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}"


def is_ollama_running() -> bool:
    """Mengecek apakah server Ollama sedang berjalan."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False
