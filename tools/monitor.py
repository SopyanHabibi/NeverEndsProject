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
            nama_proses = proc.info['name']
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

def _sinkronisasi_saat_mulai():
    """Dipanggil sekali pas Neira start. Cek sesi 'menggantung' dari sesi sebelumnya."""
    sesi_menggantung = db.ambil_sesi_terbuka()
    if not sesi_menggantung:
        return

    jalan_sekarang = _ambil_proses_yang_jalan()
    hari_ini_str = datetime.date.today().isoformat()

    for sesi in sesi_menggantung:
        app = sesi["nama_aplikasi"]
        waktu_mulai_sesi = sesi.get("waktu_mulai", "")

        # Cek apakah sesi ini udah lewat hari (dimulai BUKAN hari ini)
        sudah_beda_hari = waktu_mulai_sesi and not waktu_mulai_sesi.startswith(hari_ini_str)

        if app in jalan_sekarang and not sudah_beda_hari:
            # App masih jalan DAN sesinya dari hari ini juga -> lanjutin
            _sesi_aktif[app] = True
            print(f"[MONITOR] Melanjutkan sesi {app} yang masih berjalan dari sebelumnya.")
        else:
            # App udah gak jalan, ATAU sesinya udah ganti hari -> tutup paksa sesi lama
            db.tutup_sesi_by_id(sesi["id"])
            print(f"[MONITOR] Menutup sesi {app} (alasan: {'ganti hari' if sudah_beda_hari else 'app sudah tidak berjalan'}).")
            # Kalau app-nya MASIH jalan tapi sesinya beda hari, mulai sesi BARU buat hari ini
            if app in jalan_sekarang:
                db.mulai_sesi_aktivitas(app)
                _sesi_aktif[app] = True
                print(f"[MONITOR] Memulai sesi baru untuk {app} di hari ini.")

def mulai_monitoring():
    """Jalankan background monitor di thread terpisah, daemon biar otomatis mati pas app ditutup."""
    _sinkronisasi_saat_mulai()
    thread = threading.Thread(target=_loop_monitoring, daemon=True)
    thread.start()
    print("[MONITOR] Activity monitoring started, checking every 5 minutes.")