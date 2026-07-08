import os
import webbrowser
from tools import monitor

# 1. Kunci konfigurasi database paling awal sebelum modul lain meluncur
DIR_NEIRA = os.path.dirname(os.path.abspath(__file__))
PATH_DB_ABSOLUT = os.path.join(DIR_NEIRA, "neira_data.db")

from database import db
db.DB_FILE = PATH_DB_ABSOLUT

# 2. Impor engine setelah DB terdefinisi dengan aman
from core.server import jalankan_server_neira

if __name__ == "__main__":
    print("⚡ [STARTING] Initializing Neira AI Core System...")
    
    # Inisialisasi struktur database
    db.inisialisasi_db()
    print("📁 [DATABASE] Securely locked at:", db.DB_FILE)
    
    # Aktifkan background monitoring pelacak aplikasi PC bawaan sistem Ian
    monitor.mulai_monitoring()
    print("📊 [MONITOR] Application activity tracker background thread started.")
    
    # Buka UI lewat localhost server internal
    webbrowser.open("http://localhost:5000")
    
    # Luncurkan server
    jalankan_server_neira()