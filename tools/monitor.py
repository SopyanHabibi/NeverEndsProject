import psutil
import time
import threading
import datetime
from database import db

# Mapping nama proses (exe) -> nama aplikasi yang konsisten dipakai di database
PETA_PROSES = {
    "code.exe": "VS Code",
    "chrome.exe": "Chrome",
    "msedge.exe": "Edge",
    "spotify.exe": "Spotify",
    "notepad.exe": "Notepad",
    "winword.exe": "Word",
    "excel.exe": "Excel",
    "discord.exe": "Discord",
    "steam.exe": "Steam",
}

INTERVAL_DETIK = 300

_sesi_aktif = {}
_lock = threading.Lock()

def _ambil_proses_yang_jalan() -> set:
    """Cek semua proses window yang lagi jalan, balikin set nama_aplikasi (sesuai PETA_PROSES) yang match."""
    nama_terdeteksi = set()
    for proc in psutil.process_iter(['name']):
        try:
            nama_proses = proc.info['nama']
            if nama_proses:
                nama_lower = nama_proses.lower()
                if nama_lower in PETA_PROSES:
                    nama_terdeteksi.add(PETA_PROSES[nama_lower])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return nama_terdeteksi

def _siklus_monitoring():
    """Satu putaran cek: bandingkan app yang jalan sekarang vs status tercatat, update DB kalau ada perubahan."""
    with _lock:
        jalan_sekarang = _ambil_proses_yang_jalan()

        # App baru mulai jalan -> buka sesi baru
        for app in jalan_sekarang:
            if app not in _sesi_aktif:
                db.mulai_sesi_aktivitas(app)
                _sesi_aktif[app] = True
                print(f"[MONITOR] {app} mulai terdeteksi jalan.")

        # App yang tadinya jalan, sekarang udah ga ada -> tutup sesi
        app_yang_berhenti = [app for app in _sesi_aktif if app not in jalan_sekarang]
        for app in app_yang_berhenti:
            db.selesaikan_sesi_aktivitas(app)
            del _sesi_aktif[app]
            print(f"[MONITOR] {app} terdeteksi berhenti.")

def _loop_monitoring():
    while True:
        try:
            _siklus_monitoring()
        except Exception as e:
            print(f"[MONITOR ERROR] {e}")
        time.sleep(INTERVAL_DETIK)

def mulai_monitoring():
    """Jalankan background monitor di thread terpisah, daemon biar otomatis mati pas app ditutup."""
    thread = threading.Thread(target=_loop_monitoring, daemon=True)
    thread.start()
    print("[MONITOR] Activity monitoring started, checking every 5 minutes.")