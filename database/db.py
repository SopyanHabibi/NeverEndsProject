import sqlite3
import os

# KUNCI BARU: Karena neira_data.db sekarang satu folder dengan db.py,
# kita cukup ambil folder tempat file db.py ini berada.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "neira_data.db")

def inisialisasi_db():
    """Membuat database dengan kolom id AUTOINCREMENT jika belum ada."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profil (
            kunci TEXT PRIMARY KEY,
            nilai TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def simpan_profil(kunci: str, nilai: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO profil (kunci, nilai) VALUES (?, ?)", (kunci.lower(), nilai))
    conn.commit()
    conn.close()

def ambil_semua_profil() -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT kunci, nilai FROM profil")
    baris = cursor.fetchall()
    conn.close()
    return {kunci: nilai for kunci, nilai in baris}

def simpan_chat(role: str, content: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO riwayat_chat (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def ambil_riwayat_terakhir(limit=20) -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Query yang sudah fix anti-error kemarin
    cursor.execute("""
        SELECT role, content FROM (
            SELECT id, role, content FROM riwayat_chat ORDER BY id DESC LIMIT ?
        ) ORDER BY id ASC
    """, (limit,))
    baris = cursor.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in baris]