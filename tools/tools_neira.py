import subprocess
import webbrowser
import shutil
import os

PETA_APLIKASI = {
    "vscode": "code", "vs code": "code", "visual studio code": "code",
    "spotify": "spotify",
    "notepad": "notepad",
    "calculator": "calc",
    "explorer": "explorer", "file explorer": "explorer",
    "terminal": "wt", "cmd": "cmd",
    "word": "winword", "excel": "excel",
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