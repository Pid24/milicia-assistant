# Milicia

Milicia adalah asisten virtual pribadi berbasis suara untuk Windows. Aplikasi ini
menggabungkan GUI desktop, wake word lokal dengan Vosk, speech-to-text,
text-to-speech, Gemini Cloud AI, dan tool calling untuk menjalankan aksi di komputer.

Milicia saat ini memakai **Google Gemini** sebagai otak percakapan dan agentic
action. Artinya fitur chat AI, tool calling, vision/screen analysis, serta beberapa
fitur TTS, pencarian, berita, jadwal sholat, dan Gemini membutuhkan koneksi internet
dan API key. Voice command bisa berjalan lokal dengan faster-whisper setelah model
terunduh. Wake word detection tetap berjalan lokal melalui model Vosk di folder
`vosk_model`.

---

## Fitur Utama

- **Gemini AI Brain**: ngobrol natural dalam Bahasa Indonesia, menjawab pertanyaan, dan memilih tool yang sesuai.
- **Hybrid Commands**: perintah cepat seperti membuka aplikasi, website, volume, lock screen, dan screenshot bisa dieksekusi langsung.
- **Voice Assistant**: input suara lokal via faster-whisper dengan fallback Google STT, output suara via Edge TTS dengan fallback gTTS.
- **Hands-Free Mode**: wake word lokal menggunakan Vosk.
- **Screen Analysis**: mengambil screenshot dan meminta Gemini menganalisis isi layar.
- **Prayer Reminder**: mengambil jadwal sholat berdasarkan lokasi dan memberi pengingat otomatis.
- **Desktop GUI**: antarmuka sci-fi/JARVIS style dengan chat log, status AI, tray mode, dan autostart helper.

---

## Persyaratan Sistem

- Python 3.10 atau lebih baru
- Windows
- Mikrofon aktif
- Koneksi internet untuk Gemini, Google STT fallback, Edge TTS/gTTS, pencarian web, berita, dan jadwal sholat
- Gemini API key, disimpan sementara di `user_data.json` dengan key `gemini_api_key`
- Koneksi internet pada pemakaian pertama local STT untuk mengunduh model faster-whisper

Contoh `user_data.json`:

```json
{
  "name": "Nama Kamu",
  "gemini_api_key": "ISI_API_KEY_DI_SINI",
  "local_stt_enabled": true,
  "local_stt_model": "base",
  "local_stt_device": "auto",
  "local_stt_compute_type": "int8"
}
```

Catatan keamanan: jangan commit `user_data.json`. File ini sudah masuk `.gitignore`.

---

## Instalasi

Siapkan virtual environment:

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Jika PyAudio gagal terpasang di Windows, install wheel yang sesuai dengan versi Python
atau gunakan distribusi Python yang sudah kompatibel dengan PyAudio.

Untuk menyiapkan ulang model wake word Vosk:

```bash
python download_vosk.py
```

Local STT menggunakan `faster-whisper`. Model default `base` akan diunduh otomatis
pada pemakaian pertama, lalu bisa dipakai offline setelah cache tersedia. Untuk laptop
dengan GPU terbatas, konfigurasi default `device=auto` dan `compute=int8` dipilih agar
ringan. Jika local STT gagal, Milicia otomatis fallback ke Google STT.

---

## Menjalankan Aplikasi

```bash
python milicia.py
```

Mode background/autostart:

```bash
python setup_autostart.py
```

---

## Contoh Perintah Cepat

| Perintah | Aksi |
| :--- | :--- |
| "Buka Chrome" / "Buka Browser" | Membuka Google Chrome |
| "Buka YouTube" | Membuka YouTube di browser |
| "Buka File Explorer" | Membuka File Explorer |
| "Buka CMD" / "Buka Terminal" | Membuka terminal Windows |
| "Volume 50" | Mengatur volume ke 50% |
| "Ambil screenshot" | Menyimpan screenshot ke Desktop |
| "Cek baterai" | Menampilkan status baterai |
| "Lihat layar" | Mengirim screenshot ke Gemini Vision untuk dianalisis |
| "Keluar" / "Tutup Milicia" | Menutup aplikasi |

---

## Catatan Pengembangan

- Brain utama ada di `brain.py`.
- Action/tool implementation ada di `actions.py`.
- Smart command router ada di `commands.py`.
- Voice input dan wake word ada di `voice.py`.
- GUI utama ada di `milicia.py`.

Project ini tidak lagi sepenuhnya offline. Jika ingin mode offline penuh, integrasi
Ollama lama masih tersimpan sebagai referensi di `ollama_brain.py.bak` dan bisa
dihidupkan kembali sebagai mode alternatif.
