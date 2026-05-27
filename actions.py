"""
actions.py — Kemampuan Fisik Milicia (Agentic Actions)
Modul ini berisi semua aksi nyata yang bisa dilakukan Milicia di komputer.
Setiap fungsi menjalankan satu aksi dan mengembalikan string hasil.
Gemini akan memanggil fungsi-fungsi ini melalui mekanisme Tool Calling.
"""

import os
import re
import subprocess
import datetime
import glob
import json
import ctypes
import html as html_lib
import xml.etree.ElementTree as ET
import requests
from urllib.parse import quote as url_quote

from gui_utils import log_output


# =========================================================
# TOOL DEFINITIONS — Schema JSON untuk LLM tool calling
# =========================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Membuka sebuah website atau URL di browser default. Gunakan ini ketika pengguna ingin membuka situs web seperti YouTube, Google, GitHub, dll.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL lengkap website yang akan dibuka. Contoh: 'https://youtube.com', 'https://google.com'. Jika user hanya bilang nama situs, tambahkan https:// dan .com secara otomatis."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Membuka aplikasi di komputer Windows. Gunakan ini ketika pengguna ingin membuka aplikasi seperti Chrome, Brave, VS Code, Notepad, Spotify, Discord, Telegram, CMD/Terminal, File Explorer, dll.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Nama aplikasi yang ingin dibuka (lowercase). Contoh: 'chrome', 'brave', 'vscode', 'notepad', 'spotify', 'discord', 'telegram', 'cmd', 'explorer', 'calculator', 'paint', 'obs'."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_computer",
            "description": "Mematikan komputer. Gunakan HANYA jika pengguna secara eksplisit meminta untuk mematikan/shutdown komputer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_computer",
            "description": "Me-restart komputer. Gunakan HANYA jika pengguna secara eksplisit meminta untuk restart komputer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lock_screen",
            "description": "Mengunci layar komputer (lock screen). Gunakan ketika pengguna ingin mengunci PC.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Mengatur volume suara komputer. Gunakan ketika pengguna ingin menaikkan, menurunkan, atau mematikan volume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Level volume dari 0 (mute) sampai 100 (maksimum)."
                    }
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Mengecek status baterai laptop (persentase dan status charging). Gunakan ketika pengguna bertanya tentang baterai.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Mendapatkan informasi sistem komputer seperti RAM yang terpakai, CPU usage, disk space, dll. Gunakan ketika pengguna bertanya tentang spesifikasi atau kondisi komputernya.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Mengambil screenshot layar dan menyimpannya. Gunakan ketika pengguna meminta untuk mengambil tangkapan layar.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Mencari file di folder pengguna (Desktop, Documents, Downloads). Gunakan ketika pengguna ingin mencari file tertentu di komputernya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nama file atau pola pencarian. Contoh: 'tugas', 'proposal.docx', '*.pdf'."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Mencari informasi di internet. Gunakan ketika pengguna bertanya tentang berita terbaru, informasi real-time, atau hal yang membutuhkan data terkini yang tidak kamu ketahui.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query pencarian dalam Bahasa Indonesia atau Inggris."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_file",
            "description": "Membuka file tertentu dengan aplikasi default. Gunakan ketika pengguna ingin membuka file spesifik.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path lengkap ke file yang ingin dibuka."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_screen",
            "description": "Menganalisis isi layar di komputer. Gunakan alat ini JIKA pengguna menyuruhmu melihat layar, memperbaiki error kode di layar, atau menjelaskan apa yang ada di layar/screenshot komputernya saat ini.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Pertanyaan atau instruksi pengguna tentang gambar di layar."
                    }
                },
                "required": ["query"]
            }
        }
    },
]


# =========================================================
# PETA APLIKASI — Mapping nama aplikasi ke path executable
# =========================================================

APP_REGISTRY = {
    "chrome": {
        "paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "command": "start chrome",
        "display_name": "Google Chrome"
    },
    "brave": {
        "paths": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
        "command": "start brave",
        "display_name": "Brave Browser"
    },
    "vscode": {
        "paths": [],
        "command": "code",
        "display_name": "Visual Studio Code"
    },
    "notepad": {
        "paths": [],
        "command": "notepad",
        "display_name": "Notepad"
    },
    "cmd": {
        "paths": [],
        "command": "start cmd",
        "display_name": "Command Prompt"
    },
    "terminal": {
        "paths": [],
        "command": "start cmd",
        "display_name": "Terminal"
    },
    "powershell": {
        "paths": [],
        "command": "start powershell",
        "display_name": "PowerShell"
    },
    "explorer": {
        "paths": [],
        "command": "explorer",
        "display_name": "File Explorer"
    },
    "calculator": {
        "paths": [],
        "command": "calc",
        "display_name": "Calculator"
    },
    "paint": {
        "paths": [],
        "command": "mspaint",
        "display_name": "Microsoft Paint"
    },
    "spotify": {
        "paths": [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
        ],
        "command": "start spotify:",
        "display_name": "Spotify"
    },
    "discord": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
        ],
        "command": None,
        "display_name": "Discord"
    },
    "telegram": {
        "paths": [
            os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe"),
        ],
        "command": None,
        "display_name": "Telegram"
    },
    "obs": {
        "paths": [
            r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        ],
        "command": None,
        "display_name": "OBS Studio"
    },
    "word": {
        "paths": [],
        "command": "start winword",
        "display_name": "Microsoft Word"
    },
    "excel": {
        "paths": [],
        "command": "start excel",
        "display_name": "Microsoft Excel"
    },
    "settings": {
        "paths": [],
        "command": "start ms-settings:",
        "display_name": "Windows Settings"
    },
    "task manager": {
        "paths": [],
        "command": "taskmgr",
        "display_name": "Task Manager"
    },
    "taskmgr": {
        "paths": [],
        "command": "taskmgr",
        "display_name": "Task Manager"
    },
}


# =========================================================
# IMPLEMENTASI AKSI
# =========================================================

def open_website(url: str) -> str:
    """Membuka website di browser default."""
    # Pastikan URL punya scheme
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        os.startfile(url)
        log_output(f"🌐 Membuka: {url}")
        return f"Berhasil membuka website {url} di browser."
    except Exception as e:
        return f"Gagal membuka website {url}: {str(e)}"


def open_application(app_name: str) -> str:
    """Membuka aplikasi berdasarkan nama."""
    app_key = app_name.lower().strip()

    # Cari di registry
    app_info = APP_REGISTRY.get(app_key)

    if app_info:
        display_name = app_info["display_name"]

        # Coba buka via path terlebih dahulu
        for path in app_info.get("paths", []):
            if os.path.exists(path):
                try:
                    os.startfile(path)
                    log_output(f"📂 Membuka {display_name}")
                    return f"Berhasil membuka {display_name}."
                except Exception:
                    continue

        # Fallback ke command
        if app_info.get("command"):
            try:
                subprocess.Popen(app_info["command"], shell=True)
                log_output(f"📂 Membuka {display_name}")
                return f"Berhasil membuka {display_name}."
            except Exception as e:
                return f"Gagal membuka {display_name}: {str(e)}"

        return f"Aplikasi {display_name} ditemukan di registry tapi tidak bisa dibuka. Mungkin belum terinstall."

    # Jika tidak ada di registry, coba jalankan langsung sebagai command
    try:
        subprocess.Popen(f"start {app_key}", shell=True)
        log_output(f"📂 Mencoba membuka: {app_key}")
        return f"Mencoba membuka aplikasi '{app_name}'. Jika tidak berhasil, mungkin aplikasi tersebut belum terinstall."
    except Exception as e:
        return f"Tidak dapat menemukan atau membuka aplikasi '{app_name}': {str(e)}"


def shutdown_computer() -> str:
    """
    Mematikan komputer. Membutuhkan konfirmasi GUI.
    Return string untuk memberitahu brain bahwa konfirmasi sedang ditunggu.
    """
    log_output("⚠️ Permintaan SHUTDOWN diterima — menunggu konfirmasi pengguna...")
    return "__CONFIRM_SHUTDOWN__"


def restart_computer() -> str:
    """
    Me-restart komputer. Membutuhkan konfirmasi GUI.
    Return string untuk memberitahu brain bahwa konfirmasi sedang ditunggu.
    """
    log_output("⚠️ Permintaan RESTART diterima — menunggu konfirmasi pengguna...")
    return "__CONFIRM_RESTART__"


def _execute_shutdown():
    """Eksekusi shutdown sesungguhnya (dipanggil setelah konfirmasi GUI)."""
    os.system("shutdown /s /t 30")
    return "Komputer akan mati dalam 30 detik. Ketik 'shutdown /a' di CMD untuk membatalkan."


def _execute_restart():
    """Eksekusi restart sesungguhnya (dipanggil setelah konfirmasi GUI)."""
    os.system("shutdown /r /t 30")
    return "Komputer akan restart dalam 30 detik. Ketik 'shutdown /a' di CMD untuk membatalkan."


def lock_screen() -> str:
    """Mengunci layar komputer."""
    try:
        ctypes.windll.user32.LockWorkStation()
        log_output("🔒 Layar dikunci.")
        return "Layar komputer berhasil dikunci."
    except Exception as e:
        return f"Gagal mengunci layar: {str(e)}"


def set_volume(level: int) -> str:
    """Mengatur volume sistem Windows."""
    try:
        import comtypes
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        # COM harus diinisialisasi di setiap thread yang menggunakannya
        comtypes.CoInitialize()

        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            # Konversi level (0-100) ke scalar (0.0-1.0)
            clamped = max(0, min(100, level))
            scalar = clamped / 100.0
            volume.SetMasterVolumeLevelScalar(scalar, None)

            log_output(f"🔊 Volume diatur ke {clamped}%")
            return f"Volume berhasil diatur ke {clamped}%."
        finally:
            comtypes.CoUninitialize()
    except ImportError:
        return "Library pycaw belum terinstall. Jalankan: pip install pycaw comtypes"
    except Exception as e:
        log_output(f"⚠️ Error set_volume: {e}")
        return f"Gagal mengatur volume: {str(e)}"


def get_battery_status() -> str:
    """Mengecek status baterai laptop."""
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "Komputer ini tidak memiliki baterai (kemungkinan PC desktop)."

        percent = battery.percent
        plugged = "sedang di-charge" if battery.power_plugged else "tidak di-charge (menggunakan baterai)"
        secs_left = battery.secsleft

        if secs_left == psutil.POWER_TIME_UNLIMITED:
            time_info = "terhubung ke charger"
        elif secs_left == psutil.POWER_TIME_UNKNOWN:
            time_info = "sisa waktu tidak diketahui"
        else:
            hours = secs_left // 3600
            mins = (secs_left % 3600) // 60
            time_info = f"estimasi sisa {hours} jam {mins} menit"

        log_output(f"🔋 Baterai: {percent}% — {plugged}")
        return f"Baterai saat ini {percent}%, status: {plugged}. {time_info}."
    except ImportError:
        return "Library psutil belum terinstall. Jalankan: pip install psutil"
    except Exception as e:
        return f"Gagal cek baterai: {str(e)}"


def get_system_info() -> str:
    """Mendapatkan informasi sistem (CPU, RAM, Disk)."""
    try:
        import psutil

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # RAM
        ram = psutil.virtual_memory()
        ram_total_gb = round(ram.total / (1024**3), 1)
        ram_used_gb = round(ram.used / (1024**3), 1)
        ram_percent = ram.percent

        # Disk
        disk = psutil.disk_usage('C:\\')
        disk_total_gb = round(disk.total / (1024**3), 1)
        disk_free_gb = round(disk.free / (1024**3), 1)

        info = (
            f"CPU: {cpu_percent}% terpakai ({cpu_count} core). "
            f"RAM: {ram_used_gb}/{ram_total_gb} GB ({ram_percent}% terpakai). "
            f"Disk C: {disk_free_gb}/{disk_total_gb} GB tersisa."
        )
        log_output(f"💻 System Info: {info}")
        return info
    except ImportError:
        return "Library psutil belum terinstall. Jalankan: pip install psutil"
    except Exception as e:
        return f"Gagal mendapatkan info sistem: {str(e)}"


def take_screenshot() -> str:
    """Mengambil screenshot layar dan menyimpannya di Desktop."""
    try:
        from PIL import ImageGrab

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop, f"screenshot_{timestamp}.png")

        screenshot = ImageGrab.grab()
        screenshot.save(filepath)

        log_output(f"📸 Screenshot disimpan: {filepath}")
        return f"Screenshot berhasil disimpan di Desktop dengan nama screenshot_{timestamp}.png"
    except Exception as e:
        return f"Gagal mengambil screenshot: {str(e)}"


def analyze_screen(query: str) -> str:
    """Mengambil screenshot dan mengirimkannya ke API Gemini untuk dianalisis."""
    try:
        import json
        import os
        from PIL import ImageGrab
        import google.generativeai as genai
        
        # Ambil API key
        api_key = None
        if os.path.exists("user_data.json"):
            with open("user_data.json", "r") as f:
                data = json.load(f)
                api_key = data.get("gemini_api_key")
                
        if not api_key:
            return "Kunci API Gemini (gemini_api_key) tidak ditemukan di user_data.json. Mohon tambahkan terlebih dahulu agar fitur Vision berfungsi."
            
        # Konfigurasi Gemini
        genai.configure(api_key=api_key)
        # Gunakan model terbaru untuk Vision cepat
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Ambil gambar
        log_output("📸 Mengambil *screenshot* untuk dianalisa...")
        screenshot = ImageGrab.grab()
        
        # Kirim ke Gemini
        log_output("👁️ Mata cloud sedang menganalisis layar...")
        response = model.generate_content([query, screenshot])
        
        result_text = response.text.replace('\n', ' ')
        log_output(f"✅ Analisis selesai!")
        return "Insight dari layar: " + response.text
        
    except ImportError:
         return "Library google-generativeai belum terinstall."
    except Exception as e:
         return f"Terjadi kesalahan saat menganalisa layar: {str(e)}"


def search_files(query: str) -> str:
    """Mencari file di folder pengguna (Desktop, Documents, Downloads)."""
    try:
        home = os.path.expanduser("~")
        search_dirs = [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
        ]

        import re
        query = re.sub(r'\b(folder|file|dokumen|direktori)\b', '', query, flags=re.IGNORECASE).strip()

        # Jika query belum punya wildcard, tambahkan
        if "*" not in query:
            pattern = f"*{query}*"
        else:
            pattern = query

        results = []
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                matches = glob.glob(os.path.join(search_dir, "**", pattern), recursive=True)
                results.extend(matches[:10])  # Batasi 10 per folder

        if not results:
            return f"Tidak ditemukan file yang cocok dengan '{query}' di Desktop, Documents, atau Downloads."

        # Batasi total 15 hasil
        results = results[:15]
        file_list = "\n".join(f"- {r}" for r in results)
        log_output(f"🔍 Ditemukan {len(results)} file untuk '{query}'")
        return f"Ditemukan {len(results)} file:\n{file_list}"
    except Exception as e:
        return f"Gagal mencari file: {str(e)}"


def search_web(query: str) -> str:
    """Mencari informasi di internet menggunakan DuckDuckGo."""
    try:
        from ddgs import DDGS

        ddgs = DDGS()

        # Deteksi apakah user mencari berita
        news_keywords = ["berita", "kabar", "headline", "terbaru", "terkini", "update", "news"]
        is_news = any(kw in query.lower() for kw in news_keywords)

        if is_news:
            # Gunakan endpoint news untuk hasil berita yang lebih akurat
            try:
                results = list(ddgs.news(query, region="id-id", max_results=5))
                search_type = "berita"
            except Exception:
                # Fallback ke text search jika news endpoint gagal
                results = list(ddgs.text(query, region="id-id", max_results=5))
                search_type = "pencarian"
        else:
            results = list(ddgs.text(query, max_results=5))
            search_type = "pencarian"

        if not results:
            return f"Tidak ditemukan hasil {search_type} untuk '{query}'."

        summary_parts = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            body = r.get("body", r.get("excerpt", ""))
            href = r.get("href", r.get("url", ""))
            date = r.get("date", "")
            source = r.get("source", "")

            entry = f"{i}. {title}: {body}"
            if date:
                entry += f" ({date})"
            if source:
                entry += f" [Sumber: {source}]"
            elif href:
                entry += f" (Sumber: {href})"
            summary_parts.append(entry)

        summary = "\n".join(summary_parts)
        log_output(f"🔍 Web {search_type}: '{query}' — {len(results)} hasil")
        return f"Hasil {search_type} untuk '{query}':\n{summary}"
    except ImportError:
        return "Library ddgs belum terinstall. Jalankan: pip install ddgs"
    except Exception as e:
        log_output(f"⚠️ Error search_web: {e}")
        return f"Gagal mencari di web: {str(e)}"


def search_news(query: str = None) -> str:
    """
    Mencari berita terbaru menggunakan Google News RSS.
    Mengambil artikel nyata dengan judul, sumber, tanggal, dan link.
    Juga mencoba mengekstrak isi konten artikel utama agar AI bisa menjelaskan.
    """
    try:
        # Build Google News RSS URL
        if query and query.strip():
            # Bersihkan query dari kata-kata trigger yang redundan
            clean_query = re.sub(
                r'\b(carikan|cari|tolong|dong|ya|hari ini|terbaru|terkini|update)\b',
                '', query, flags=re.IGNORECASE
            ).strip()
            if not clean_query:
                clean_query = "Indonesia"
            encoded = url_quote(clean_query)
            rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=id&gl=ID&ceid=ID:id"
        else:
            # Headline utama Indonesia
            rss_url = "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(rss_url, timeout=15, headers=headers)

        if response.status_code != 200:
            log_output(f"⚠️ Google News RSS gagal (status {response.status_code}), fallback ke DuckDuckGo...")
            return _search_news_ddg(query or "berita terbaru Indonesia")

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        if not items:
            log_output("⚠️ Google News RSS kosong, fallback ke DuckDuckGo...")
            return _search_news_ddg(query or "berita terbaru Indonesia")

        # Ambil 3 artikel teratas
        articles = []
        for item in items[:3]:
            title_el = item.find('title')
            link_el = item.find('link')
            pub_date_el = item.find('pubDate')
            source_el = item.find('source')
            desc_el = item.find('description')

            title = title_el.text if title_el is not None else "Tanpa judul"
            google_link = link_el.text if link_el is not None else ""
            pub_date = pub_date_el.text if pub_date_el is not None else ""
            source = source_el.text if source_el is not None else ""
            description = desc_el.text if desc_el is not None else ""

            # Ambil URL sumber asli dari atribut <source url="...">
            source_url = ""
            if source_el is not None:
                source_url = source_el.get('url', '')

            # Bersihkan HTML dari description RSS
            if description:
                description = re.sub(r'<[^>]+>', '', description)
                description = html_lib.unescape(description)

            # Gunakan source_url jika ada, otherwise google_link
            article_link = source_url if source_url else google_link

            articles.append({
                'title': title,
                'link': article_link,
                'google_link': google_link,
                'date': pub_date,
                'source': source,
                'description': description
            })

        # Coba scrape isi konten dari artikel pertama agar AI bisa menjelaskan
        article_content = ""
        if articles and articles[0].get('google_link'):
            # Coba scrape via Google redirect link (bisa resolve ke artikel asli)
            article_content, resolved_url = _try_extract_article(articles[0]['google_link'])
            if resolved_url and 'news.google.com' not in resolved_url:
                # Berhasil resolve ke URL artikel asli
                articles[0]['link'] = resolved_url

        # Format hasil untuk dikirim ke AI
        result_parts = []
        for i, art in enumerate(articles, 1):
            entry = f"=== BERITA {i} ===\n"
            entry += f"Judul: {art['title']}\n"
            if art['source']:
                entry += f"Sumber: {art['source']}\n"
            if art['date']:
                entry += f"Tanggal: {art['date']}\n"
            entry += f"Link: {art['link']}\n"
            if art['description']:
                entry += f"Ringkasan: {art['description']}\n"

            # Tambahkan isi lengkap hanya untuk artikel pertama
            if i == 1 and article_content:
                entry += f"\nISI ARTIKEL LENGKAP:\n{article_content}\n"

            result_parts.append(entry)

        result = "\n".join(result_parts)
        log_output(f"📰 Berita ditemukan: {len(articles)} artikel")
        return f"BERITA TERBARU ({len(articles)} artikel):\n\n{result}"

    except Exception as e:
        log_output(f"⚠️ Error search_news: {e}")
        # Fallback ke DuckDuckGo
        try:
            return _search_news_ddg(query or "berita terbaru Indonesia")
        except Exception:
            return f"Gagal mencari berita: {str(e)}"


def _try_extract_article(url: str) -> tuple:
    """
    Mencoba mengekstrak isi artikel dari URL berita.
    Google News RSS link akan di-redirect ke URL asli artikel.
    Returns: (content_text, actual_url)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8'
        }
        resp = requests.get(url, timeout=12, headers=headers, allow_redirects=True)
        actual_url = resp.url  # URL setelah redirect (URL asli artikel)
        page_html = resp.text

        content_parts = []

        # 1. Coba ambil og:description (biasanya ringkasan bagus)
        og_match = re.search(
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\'>]*)["\']',
            page_html, re.IGNORECASE
        )
        if not og_match:
            # Coba format alternatif (content sebelum property)
            og_match = re.search(
                r'<meta[^>]*content=["\']([^"\'>]*)["\'][^>]*property=["\']og:description["\']',
                page_html, re.IGNORECASE
            )
        if og_match:
            og_desc = html_lib.unescape(og_match.group(1).strip())
            if len(og_desc) > 30:
                content_parts.append(og_desc)

        # 2. Ambil meta description sebagai fallback
        if not content_parts:
            meta_match = re.search(
                r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\'>]*)["\']',
                page_html, re.IGNORECASE
            )
            if meta_match:
                meta_desc = html_lib.unescape(meta_match.group(1).strip())
                if len(meta_desc) > 30:
                    content_parts.append(meta_desc)

        # 3. Ekstraksi paragraf <p> dari artikel
        #    Hanya ambil paragraf yang cukup panjang (isi artikel, bukan navigasi)
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', page_html, re.DOTALL)
        para_count = 0
        for p in paragraphs:
            clean = re.sub(r'<[^>]+>', '', p).strip()
            clean = html_lib.unescape(clean)
            # Filter: hanya paragraf substansial (>80 karakter, bukan menu/nav)
            if len(clean) > 80 and not re.match(r'^(Baca juga|BACA JUGA|Lihat juga|Tags?:|Sumber:)', clean):
                content_parts.append(clean)
                para_count += 1
                if para_count >= 8:  # Maks 8 paragraf
                    break

        if content_parts:
            return '\n\n'.join(content_parts), actual_url
        return "", actual_url

    except Exception as e:
        log_output(f"⚠️ Gagal scrape artikel: {e}")
        return "", ""


def _search_news_ddg(query: str) -> str:
    """Fallback: Mencari berita menggunakan DuckDuckGo News."""
    try:
        from ddgs import DDGS
        ddgs = DDGS()

        try:
            results = list(ddgs.news(query, region="id-id", max_results=5))
        except Exception:
            results = list(ddgs.text(query, region="id-id", max_results=5))

        if not results:
            return f"Tidak ditemukan berita untuk '{query}'."

        summary_parts = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            body = r.get("body", r.get("excerpt", ""))
            href = r.get("href", r.get("url", ""))
            date = r.get("date", "")
            source = r.get("source", "")

            entry = f"{i}. {title}: {body}"
            if date:
                entry += f" ({date})"
            if source:
                entry += f" [Sumber: {source}]"
            elif href:
                entry += f" (Link: {href})"
            summary_parts.append(entry)

        return f"Berita terbaru:\n" + "\n".join(summary_parts)
    except Exception as e:
        return f"Gagal mencari berita: {str(e)}"


def open_file(file_path: str) -> str:
    """Membuka file dengan aplikasi default."""
    if os.path.exists(file_path):
        try:
            os.startfile(file_path)
            log_output(f"📄 Membuka file: {file_path}")
            return f"Berhasil membuka file {os.path.basename(file_path)}."
        except Exception as e:
            return f"Gagal membuka file: {str(e)}"
    else:
        return f"File tidak ditemukan: {file_path}"


# =========================================================
# DISPATCHER — Menjalankan aksi berdasarkan nama fungsi
# =========================================================

# Mapping nama fungsi ke implementasi Python
ACTION_MAP = {
    "open_website": open_website,
    "open_application": open_application,
    "shutdown_computer": shutdown_computer,
    "restart_computer": restart_computer,
    "lock_screen": lock_screen,
    "set_volume": set_volume,
    "get_battery_status": get_battery_status,
    "get_system_info": get_system_info,
    "take_screenshot": take_screenshot,
    "search_files": search_files,
    "search_web": search_web,
    "search_news": search_news,
    "open_file": open_file,
    "analyze_screen": analyze_screen,
}


def execute_action(function_name: str, arguments: dict) -> str:
    """
    Dispatcher utama: Menjalankan aksi berdasarkan nama fungsi dan argumen
    yang diberikan oleh LLM tool calls.
    Returns: String hasil eksekusi.
    """
    action_fn = ACTION_MAP.get(function_name)

    if action_fn is None:
        return f"Aksi '{function_name}' tidak dikenali oleh sistem Milicia."

    try:
        log_output(f"⚡ Menjalankan aksi: {function_name}({arguments})")
        result = action_fn(**arguments)
        return result
    except TypeError as e:
        log_output(f"⚠️ TypeError pada {function_name}: {e}")
        return f"Argumen tidak valid untuk aksi '{function_name}': {str(e)}"
    except Exception as e:
        log_output(f"⚠️ Exception pada {function_name}: {e}")
        return f"Gagal menjalankan aksi '{function_name}': {str(e)}"
