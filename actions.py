"""
actions.py — Kemampuan Fisik Milicia (Agentic Actions)
Modul ini berisi semua aksi nyata yang bisa dilakukan Milicia di komputer.
Setiap fungsi menjalankan satu aksi dan mengembalikan string hasil.
Ollama akan memanggil fungsi-fungsi ini melalui mekanisme Tool Calling.
"""

import os
import subprocess
import datetime
import glob
import json
import ctypes

from gui_utils import log_output


# =========================================================
# TOOL DEFINITIONS — Schema JSON untuk Ollama API
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
    Return string untuk memberitahu Ollama bahwa konfirmasi sedang ditunggu.
    """
    log_output("⚠️ Permintaan SHUTDOWN diterima — menunggu konfirmasi pengguna...")
    return "__CONFIRM_SHUTDOWN__"


def restart_computer() -> str:
    """
    Me-restart komputer. Membutuhkan konfirmasi GUI.
    Return string untuk memberitahu Ollama bahwa konfirmasi sedang ditunggu.
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
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)

        # Konversi level (0-100) ke scalar (0.0-1.0)
        clamped = max(0, min(100, level))
        scalar = clamped / 100.0
        volume.SetMasterVolumeLevelScalar(scalar, None)

        log_output(f"🔊 Volume diatur ke {clamped}%")
        return f"Volume berhasil diatur ke {clamped}%."
    except ImportError:
        return "Library pycaw belum terinstall. Jalankan: pip install pycaw comtypes"
    except Exception as e:
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


def search_files(query: str) -> str:
    """Mencari file di folder pengguna (Desktop, Documents, Downloads)."""
    try:
        home = os.path.expanduser("~")
        search_dirs = [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
        ]

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
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return f"Tidak ditemukan hasil pencarian untuk '{query}'."

        summary_parts = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            summary_parts.append(f"{i}. {title}: {body} (Sumber: {href})")

        summary = "\n".join(summary_parts)
        log_output(f"🔍 Web search: '{query}' — {len(results)} hasil")
        return f"Hasil pencarian untuk '{query}':\n{summary}"
    except ImportError:
        return "Library duckduckgo-search belum terinstall. Jalankan: pip install duckduckgo-search"
    except Exception as e:
        return f"Gagal mencari di web: {str(e)}"


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
    "open_file": open_file,
}


def execute_action(function_name: str, arguments: dict) -> str:
    """
    Dispatcher utama: Menjalankan aksi berdasarkan nama fungsi dan argumen
    yang diberikan oleh Ollama tool_calls.
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
        return f"Argumen tidak valid untuk aksi '{function_name}': {str(e)}"
    except Exception as e:
        return f"Gagal menjalankan aksi '{function_name}': {str(e)}"
