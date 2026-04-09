"""
ollama_brain.py — Otak AI Milicia menggunakan Ollama (Local LLM)
Modul ini menangani komunikasi dengan server Ollama yang berjalan di localhost.
Milicia mengirimkan teks ke sini, dan menerima balasan cerdas dari AI.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b"

# System prompt — kepribadian Milicia
SYSTEM_PROMPT = """Kamu adalah Milicia, asisten virtual pribadi milik Rofid. 
Kamu berbicara dalam Bahasa Indonesia yang santai, hangat, dan ramah.
Kamu pintar, lucu, dan suka membantu.
Kamu bisa membantu menjawab pertanyaan, memberikan saran, mengobrol santai, 
memberikan rekomendasi anime, membantu perhitungan matematika, dan banyak lagi.

Aturan penting:
- Selalu jawab dengan ringkas dan jelas (maksimal 3-4 kalimat) kecuali diminta detail.
- Gunakan emoji sesekali untuk membuat percakapan lebih hidup.
- Jika pengguna meminta membuka aplikasi, beri tahu bahwa kamu akan membukanya.
- Panggil pengguna dengan nama "Rofid" atau "kak" sesekali.
- Kamu BUKAN chatbot biasa. Kamu adalah asisten pribadi seperti Jarvis.
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
    Juga menyimpan riwayat percakapan untuk konteks.
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

    # Susun pesan: system prompt + riwayat percakapan
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + conversation_history

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 256,  # Batasi panjang respons
                }
            },
            timeout=60  # Timeout 60 detik (model kecil cukup cepat)
        )

        if response.status_code == 200:
            data = response.json()
            ai_reply = data.get("message", {}).get("content", "").strip()

            if not ai_reply:
                ai_reply = "Hmm, aku tidak bisa berpikir sekarang. Coba lagi ya."

            # Simpan balasan AI ke riwayat
            conversation_history.append({
                "role": "assistant",
                "content": ai_reply
            })

            return ai_reply
        else:
            return f"Maaf, terjadi kesalahan saat menghubungi otak AI ku. (Status: {response.status_code})"

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
