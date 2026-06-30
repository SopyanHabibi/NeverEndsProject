import subprocess
import webbrowser
import shutil
import os
import datetime
from database import db

PETA_APLIKASI = {
    "vscode": "code", "vs code": "code", "visual studio code": "code",
    "spotify": "spotify",
    "notepad": "notepad",
    "calculator": "calc",
    "explorer": "explorer", "file explorer": "explorer",
    "terminal": "wt", "cmd": "cmd",
    "word": "winword", "excel": "excel",
    "instagram": "instagram",
}

# Browser butuh perlakuan khusus karena sering gak ke-register di PATH
PETA_BROWSER = {
    "chrome": {
        "command": "chrome",
        "fallback_paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    },
    "edge": {
        "command": "msedge",
        "fallback_paths": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]
    },
    "browser": {  # default kalau Ian cuma bilang "browser" tanpa spesifik
        "command": "chrome",
        "fallback_paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    },
}

SITUS_WEB = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "instagram": "https://instagram.com/_sop.ayam/",
}

def _cari_executable(nama_command: str, daftar_fallback: list) -> str | None:
    """Cari executable: cek PATH dulu via shutil.which, baru cek lokasi instalasi umum."""
    path_dari_sistem = shutil.which(nama_command)
    if path_dari_sistem:
        return path_dari_sistem
    for path in daftar_fallback:
        if os.path.exists(path):
            return path
    return None

def buka_aplikasi(nama_aplikasi: str) -> str:
    kunci = nama_aplikasi.lower().strip()

    # 1. Cek apakah ini browser spesifik
    if kunci in PETA_BROWSER:
        info = PETA_BROWSER[kunci]
        path_ditemukan = _cari_executable(info["command"], info["fallback_paths"])
        if path_ditemukan:
            subprocess.Popen([path_ditemukan])
            return f"Launched {nama_aplikasi} for you, Ian."
        return f"Couldn't find {nama_aplikasi} installed on this PC, Ian. Is it actually installed?"

    # 2. Cek apakah ini situs web (dibuka via browser default)
    if kunci in SITUS_WEB:
        webbrowser.open(SITUS_WEB[kunci])
        return f"Opened {nama_aplikasi} in your browser, Ian."

    # 3. Cek aplikasi desktop lainnya
    perintah = PETA_APLIKASI.get(kunci, kunci)
    path_ditemukan = shutil.which(perintah)
    if path_ditemukan:
        subprocess.Popen([path_ditemukan])
        return f"Launched {nama_aplikasi} for you, Ian."

    return f"Couldn't find '{nama_aplikasi}' on this PC, Ian — it might not be installed, or it's not registered in PATH."

def tampilkan_task_list():
    """
    Mengambil dan menampilkan daftar tugas (To-Do List) aktif milik Ian langsung dari SQLite.
    """
    try:
        # Menarik data secara dinamis dari database kamu
        if hasattr(db, 'ambil_semua_tugas'):
            tugas_db = db.ambil_semua_tugas()
        else:
            # Fallback jika nama fungsi di database.py berbeda, sesuaikan di sini
            return "⚠️ Fungsi 'ambil_semua_tugas' belum terdeteksi di database.py kamu, Ian."

        if not tugas_db:
            return "📝 **Daftar Tugas:**\n\nWah, kosong Ian! Semua tugas kamu sudah beres atau belum ada yang dicatat."

        res = "📝 **Daftar Tugas Aktif Kamu, Ian:**\n\n"
        for i, t in enumerate(tugas_db, 1):
            # Sesuaikan dengan nama kolom di tabel database kamu (misal: 'status', 'nama_tugas')
            status = t.get('status', 'Belum')
            nama_tugas = t.get('nama_tugas', t.get('tugas', 'Tugas Tanpa Nama'))
            
            ikon_status = "✅" if status.lower() in ["selesai", "done", "1"] else "⏳"
            res += f"{i}. {ikon_status} **{nama_tugas}**\n"
            
        return res

    except Exception as e:
        return f"Waduh Ian, gagal mengambil daftar tugas dari SQLite. Error: {str(e)}"


def tampilkan_jadwal_harian():
    """
    Melihat jadwal harian, agenda kuliah, atau kegiatan Ian berdasarkan hari ini dari SQLite.
    """
    try:
        # Mendapatkan nama hari ini dalam bahasa Indonesia
        hari_ini = datetime.datetime.now().strftime("%A")
        kamus_hari = {
            "Monday": "senin", "Tuesday": "selasa", "Wednesday": "rabu",
            "Thursday": "kamis", "Friday": "jumat", "Saturday": "sabtu", "Sunday": "minggu"
        }
        hari_lowercase = kamus_hari.get(hari_ini, hari_ini.lower())
        hari_display = hari_lowercase.capitalize()

        if hasattr(db, 'ambil_jadwal_hari'):
            jadwal_db = db.ambil_jadwal_hari(hari_lowercase)
        elif hasattr(db, 'ambil_jadwal_harian'):
            jadwal_db = db.ambil_jadwal_harian(hari_lowercase)
        else:
            return "⚠️ Fungsi untuk mengambil jadwal berdasarkan hari belum terdeteksi di database.py kamu."

        if not jadwal_db:
            return f"📅 **Jadwal Hari {hari_display}:**\n\nHari ini tidak ada agenda tetap atau kuliah yang tercatat di SQLite, Ian. Bebas santai!"

        res = f"📅 **Jadwal & Agenda Kamu Hari Ini ({hari_display}):**\n\n"
        for item in jadwal_db:
            # Sesuaikan dengan nama kolom tabel jadwal kamu (misal: 'jam', 'kegiatan')
            jam = item.get('jam', item.get('waktu', '--:--'))
            kegiatan = item.get('kegiatan', item.get('matkul', 'Kegiatan'))
            res += f"• **{jam}** ➔ {kegiatan}\n"
            
        return res

    except Exception as e:
        return f"Waduh Ian, gagal memuat jadwal harian dari SQLite. Error: {str(e)}"