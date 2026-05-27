import threading
import time
import requests
import datetime
from config import get_user_name
from utils import speak
from gui_utils import log_output

PRAYER_NAMES_MAP = {
    "Fajr": "Subuh",
    "Dhuhr": "Dzuhur",
    "Asr": "Ashar",
    "Maghrib": "Maghrib",
    "Isha": "Isya"
}

# Menit sebelum Dzuhur untuk pengingat Jumat (persiapan sholat Jumat)
JUMAT_REMINDER_MINUTES_BEFORE = 15

cached_prayer_times = {}
last_fetch_date = None
user_location = {"city": "Unknown", "country": "Unknown"}

def fetch_location():
    """Mendapatkan lokasi pengguna menggunakan ip-api."""
    global user_location
    try:
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            user_location["city"] = data.get("city", "Unknown")
            user_location["country"] = data.get("country", "Unknown")
            log_output(f"🌍 Lokasi terdeteksi: {user_location['city']}, {user_location['country']}")
    except Exception as e:
        log_output(f"⚠️ Gagal mendeteksi lokasi: {e}")

def fetch_prayer_times():
    """Mengambil data waktu sholat dari api.aladhan.com."""
    global cached_prayer_times, last_fetch_date, user_location
    if user_location["city"] == "Unknown":
        fetch_location()

    if user_location["city"] == "Unknown":
        return  # Masih gagal deteksi lokasi

    city = user_location["city"]
    country = user_location["country"]
    
    # Method 20 adalah Kementerian Agama Republik Indonesia, sangat akurat untuk wilayah Indonesia
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=20"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            timings = data["data"]["timings"]
            # Ambil hanya waktu sholat wajib
            cached_prayer_times = {
                PRAYER_NAMES_MAP[key]: value
                for key, value in timings.items()
                if key in PRAYER_NAMES_MAP
            }
            last_fetch_date = datetime.datetime.now().date()
            log_output(f"✅ Berhasil mengambil jadwal sholat untuk {city}")
    except Exception as e:
        log_output(f"⚠️ Gagal mengambil jadwal sholat: {e}")


def _is_friday(date=None):
    """Cek apakah hari ini Jumat (weekday 4)."""
    if date is None:
        date = datetime.datetime.now()
    return date.weekday() == 4


def _get_jumat_reminder_time():
    """
    Hitung waktu pengingat Jumat = waktu Dzuhur - JUMAT_REMINDER_MINUTES_BEFORE menit.
    Memberikan waktu buat persiapan sebelum sholat Jumat.
    """
    dzuhur_str = cached_prayer_times.get("Dzuhur")
    if not dzuhur_str:
        return None
    try:
        h, m = map(int, dzuhur_str.split(":"))
        dzuhur_dt = datetime.datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        reminder_dt = dzuhur_dt - datetime.timedelta(minutes=JUMAT_REMINDER_MINUTES_BEFORE)
        return reminder_dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return None


def get_prayer_schedule():
    """
    Mengembalikan jadwal sholat hari ini dengan awareness hari Jumat.
    Pada hari Jumat, Dzuhur diganti dengan label 'Jumat' dalam output.
    Digunakan oleh ollama_brain.py untuk konteks AI.
    """
    if not cached_prayer_times:
        return {}

    schedule = dict(cached_prayer_times)

    if _is_friday():
        # Pada hari Jumat, ganti label Dzuhur → Jumat
        dzuhur_time = schedule.pop("Dzuhur", None)
        if dzuhur_time:
            schedule["Jumat"] = dzuhur_time

    return schedule


def prayer_time_daemon():
    """Loop utama untuk daemon sholat berjalan di background."""
    global cached_prayer_times, last_fetch_date, user_location
    
    # Tunggu sebentar sampai sistem network siap setelah boot
    time.sleep(5)
    log_output("⏳ Memulai layanan pengingat sholat...")
    fetch_prayer_times()

    # Catat sholat apa yang sudah diingatkan hari ini
    notified_prayers = set()

    while True:
        now = datetime.datetime.now()
        
        # Reset jadwal setiap pergantian hari
        if last_fetch_date != now.date():
            fetch_prayer_times()
            notified_prayers.clear()

        current_hm = now.strftime("%H:%M")
        city = user_location["city"]
        is_jumat = _is_friday(now)

        # === Pengingat Sholat Jumat (khusus hari Jumat) ===
        if is_jumat and "Jumat_reminder" not in notified_prayers:
            jumat_reminder = _get_jumat_reminder_time()
            if jumat_reminder and current_hm == jumat_reminder:
                speak(
                    f"Assalamu'alaikum {get_user_name()}! Sebentar lagi masuk waktu Sholat Jumat "
                    f"untuk wilayah {city} dan sekitarnya. "
                    f"Yuk segera bersiap-siap berangkat ke masjid. "
                    f"Jangan lupa mandi, pakai baju rapi, dan berangkat lebih awal ya!"
                )
                notified_prayers.add("Jumat_reminder")

        # === Pengingat Sholat Wajib Reguler ===
        for sholat, time_str in cached_prayer_times.items():
            if current_hm == time_str and sholat not in notified_prayers:
                # Pada hari Jumat, Dzuhur diganti dengan pesan Jumat
                if is_jumat and sholat == "Dzuhur":
                    speak(
                        f"{get_user_name()}, sudah masuk waktu Sholat Jumat untuk wilayah {city} "
                        f"dan sekitarnya. Semoga khutbah dan sholatnya khusyuk!"
                    )
                    notified_prayers.add(sholat)
                else:
                    speak(
                        f"{get_user_name()}, sudah masuk waktu sholat {sholat} untuk wilayah {city} "
                        f"dan sekitarnya. Jangan lupa untuk sholat."
                    )
                    notified_prayers.add(sholat)
        
        # Cek setiap 30 detik agar tidak lolos 1 menit tersebut
        time.sleep(30)

def start_prayer_reminder():
    """Menjalankan daemon pengingat sholat di background."""
    thread = threading.Thread(target=prayer_time_daemon, daemon=True)
    thread.start()
