# 🧠 Milicia

Milicia adalah **Asisten Virtual Pribadi** berbasis suara (Voice Assistant) yang digerakkan oleh **Kecerdasan Buatan Lokal (Local LLM)** menggunakan **Ollama**. 

Berbeda dengan asisten lawas yang mengandalkan aturan kaku (*rule-based*), Milicia memiliki "otak" sejati yang memungkinkannya mengobrol secara natural, mengingat konteks percakapan, memberikan saran cerdas, hingga mengontrol komputer Anda — dan semuanya berjalan **100% Offline** di laptop Anda tanpa membutuhkan kunci API internet!

Sistem dibangun menggunakan bahasa Python dengan antarmuka grafis (GUI) bertema gelap premium *(Glassmorphism - Tokyo Night)* berkat `customtkinter`.

---

## 🚀 Fitur Unggulan

- 🧠 **Cerdas & Fleksibel (Ollama Brain)**: Dapat diajak berdiskusi, tanya-jawab, atau bercanda seperti manusia berkat integrasi model Local LLM (default: `qwen2.5:1.5b`).
- 💾 **Memori Kontekstual**: Milicia mampu mengingat runutan percakapan Anda layaknya asisten pribadi sungguhan.
- 🎙️ **Kontrol Suara**: Anda cukup berbicara melalui mikrofon (Speech Recognition) dan Milicia akan merespons menggunakan suara (Text-to-Speech).
- ⚡ **Perintah Sistem Hibrida (Hybrid Commands)**: Untuk tugas-tugas pengelolaan komputer, Milicia bekerja secepat kilat tanpa perlu proses pikir AI yang lama.
- 🎨 **GUI Premium**: Antarmuka visual kustom yang elegan, lengkap dengan indikator status server AI.
- 🔒 **Privasi 100%**: Tidak ada data percakapan Anda yang dikirim ke *cloud* atau server perusahaan lain. Murni berjalan di komputer lokal.

---

## 🛠️ Persyaratan Sistem

- **Python 3.10** atau lebih baru
- Sistem Operasi **Windows**
- Mikrofon aktif
- **[Ollama](https://ollama.com/)** terinstall di komputer (Wajib untuk mengaktifkan "Brain")

---

## ⚙️ Cara Instalasi & Menjalankan

### Langkah 1: Persiapan Otak AI (Ollama)
1. Download dan instal **Ollama** untuk Windows dari situs resminya.
2. Buka Command Prompt/Terminal Windows dan jalankan perintah penarikan model (ukuran sekitar 1GB) lalu biarkan berjalan di latar belakang:
   ```bash
   ollama run qwen2.5:1.5b
   ```
   *(Catatan: Biarkan terminal Ollama tetap terbuka/berjalan agar Milicia bisa terhubung).*

### Langkah 2: Persiapan Library Python
Buka folder **milicia-assistant** melalui Terminal dan eksekusi perintah berikut untuk menyiapkan *Virtual Environment*:

```bash
# Membuat environment bernama venv
python -m venv venv

# Mengaktifkan environment (Untuk Windows)
.\venv\Scripts\activate

# Menginstal semua dependensi 
pip install -r requirements.txt
```

*(Catatan Khusus Pengguna Windows: Anda mungkin juga perlu memastikan `PyAudio` terpasang dengan baik karena dibutuhkan oleh fitur pengenalan mikrofon).*

### Langkah 3: Menjalankan Milicia
Setelah semuanya siap dan Ollama sudah *standby*, ketik perintah ini:

```bash
python milicia.py
```

Silakan klik tombol **"🎙️ Bicara Sekarang"** pada aplikasi yang muncul, dan mulai sapa asisten pintar Anda!

---

## 🎙️ Daftar Perintah Cepat (Fast Commands)

Selain obrolan natural bebas (yang akan dilempar ke otak LLM), Milicia mengadopsi fitur **Bypass Command** di mana ia akan langsung menjalankan instruksi spesifik komputer tanpa perlu "berpikir" ke Ollama. Ucapkan kalimat-kalimat ini:

| Perintah Suara | Aksi yang Dilakukan Komputer |
| :--- | :--- |
| **"Buka Chrome"** atau **"Buka Browser"** | Langsung membuka Google Chrome |
| **"Buka folder"** atau **"Buka file explorer"** | Langsung membuka File Explorer Windows |
| **"Buka CMD"** atau **"Buka Terminal"** | Membuka jendela Command Prompt baru |
| **"Buka Notepad"** | Meluncurkan aplikasi Notepad |
| **"Keluar"** atau **"Tutup Milicia"** | Menutup program asisten |

> Ingin meminta AI mencarikan informasi atau memberikan saran anime? **Cukup tanyakan saja dengan santai!** (Contoh: *"Milicia, saranin aku anime action yang tokoh utamanya overpower dong."*)

---
*Ditenagai dan dirancang untuk pengalaman asisten desktop mandiri masa depan.*
