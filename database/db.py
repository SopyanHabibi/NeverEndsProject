import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "neira_data.db")

def inisialisasi_db():
    """Membuat database dengan tabel profil, sesi_chat, dan riwayat_chat."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Tabel Profil (Tetap aman seperti kemarin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profil (
            kunci TEXT PRIMARY KEY,
            nilai TEXT
        )
    ''')
    
    # 2. TABEL BARU: Untuk menyimpan daftar sesi chat di Sidebar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesi_chat (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. TABEL UPDATE: Riwayat chat sekarang punya kolom session_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sesi_chat(session_id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# ==================== FITUR PROFIL ====================

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

# ==================== FITUR MULTI-SESSION CHAT ====================

def buat_sesi_baru(judul="Chat Baru") -> int:
    """Membuat sesi chat baru di tabel sesi_chat dan mengembalikan session_id-nya."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sesi_chat (judul) VALUES (?)", (judul,))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def ambil_semua_sesi() -> list:
    """Mengambil semua daftar sesi untuk ditampilkan di Sidebar PyQt."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, judul FROM sesi_chat ORDER BY updated_at DESC")
    baris = cursor.fetchall()
    conn.close()
    return [{"session_id": b[0], "judul": b[1]} for b in baris]

def update_judul_sesi(session_id: int, pesan_pertama: str):
    """Otomatis memotong 25 karakter pesan pertama user untuk dijadikan judul di sidebar."""
    judul = pesan_pertama[:25] + "..." if len(pesan_pertama) > 25 else pesan_pertama
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE sesi_chat SET judul = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (judul, session_id))
    conn.commit()
    conn.close()

def hapus_sesi(session_id):
    """Menghapus sesi beserta seluruh riwayat chat di dalamnya."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Hapus riwayat chat-nya dulu (Foreign Key friendly)
        cursor.execute("DELETE FROM riwayat_chat WHERE session_id = ?", (session_id,))
        # Hapus sesinya
        cursor.execute("DELETE FROM sesi_chat WHERE session_id = ?", (session_id,))
        conn.commit()
    except Exception as e:
        print(f"Gagal menghapus sesi: {e}")
    finally:
        conn.close()

def ubah_judul_sesi(session_id, judul_baru):
    """Fitur rename manual untuk judul sesi chat."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE sesi_chat SET judul = ? WHERE session_id = ?", (judul_baru, session_id))
        conn.commit()
    except Exception as e:
        print(f"Gagal mengubah judul: {e}")
    finally:
        conn.close()

def simpan_chat(session_id: int, role: str, content: str):
    """Menyimpan chat berdasarkan session_id yang sedang aktif."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Jika ini adalah chat pertama dari user di sesi tersebut, otomatis update judul sidbarnya!
    if role == "user":
        cursor.execute("SELECT COUNT(*) FROM riwayat_chat WHERE session_id = ?", (session_id,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            update_judul_sesi(session_id, content)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

    cursor.execute("INSERT INTO riwayat_chat (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    # Update timestamp di sesi_chat agar sesi naik ke paling atas di sidebar
    cursor.execute("UPDATE sesi_chat SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
    
    conn.commit()
    conn.close()

def ambil_riwayat_terakhir(session_id: int, limit=20) -> list:
    """Mengambil riwayat chat spesifik berdasarkan session_id tertentu saja."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content FROM (
            SELECT id, role, content FROM riwayat_chat WHERE session_id = ? ORDER BY id DESC LIMIT ?
        ) ORDER BY id ASC
    """, (session_id, limit))
    baris = cursor.fetchall()
    conn.close()
    return [{"role": r, "content": c} for r, c in baris]