import subprocess
import webbrowser

PETA_APLIKASI = {
    "vscode": "code", "vs code": "code", "visual studio code": "code",
    "chrome": "chrome", "browser": "chrome",
    "spotify": "spotify",
    "notepad": "notepad",
    "calculator": "calc",
    "explorer": "explorer", "file explorer": "explorer",
    "terminal": "wt", "cmd": "cmd",
    "word": "winword", "excel": "excel",
}

SITUS_WEB = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
}

def buka_aplikasi(nama_aplikasi: str) -> str:
    kunci = nama_aplikasi.lower().strip()

    if kunci in SITUS_WEB:
        webbrowser.open(SITUS_WEB[kunci])
        return f"Opened {nama_aplikasi} in your browser, Ian."

    perintah = PETA_APLIKASI.get(kunci, kunci)
    try:
        subprocess.Popen(perintah, shell=True)
        return f"Launched {nama_aplikasi} for you, Ian."
    except Exception as e:
        return f"Couldn't open {nama_aplikasi}: {e}"