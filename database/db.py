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
    
    # 4. TABEL BARU: Tasks/To-do list
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tugas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deskripsi TEXT NOT NULL,
            deadline TEXT,
            status TEXT DEFAULT 'pending',
            dibuat_pada DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. TABEL BARU: Jadwal harian
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jadwal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aktivitas TEXT NOT NULL,
            waktu TEXT NOT NULL,
            dibuat_pada DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 6. TABEL BARU: Log aktivitas aplikasi (buat deteksi pola produktivitas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aktivitas_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_aplikasi TEXT NOT NULL,
            waktu_mulai DATETIME NOT NULL,
            waktu_selesai DATETIME
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

# ==================== FITUR TASKS / TO-DO ====================

def tambah_tugas(deskripsi: str, deadline: str = None) -> int:
    """Menambahkan tugas baru, mengembalikan ID tugas yang baru dibuat."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tugas (deskripsi, deadline) VALUES (?, ?)", (deskripsi, deadline))
    id_baru = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_baru

def ambil_tugas(hanya_pending: bool = True) -> list:
    """Mengambil daftar tugas. Default cuma yang statusnya 'pending'."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if hanya_pending:
        cursor.execute("SELECT id, deskripsi, deadline FROM tugas WHERE status = 'pending' ORDER BY id")
    else:
        cursor.execute("SELECT id, deskripsi, deadline, status FROM tugas ORDER BY id")
    baris = cursor.fetchall()
    conn.close()
    return [{"id": b[0], "deskripsi": b[1], "deadline": b[2]} for b in baris]

def selesaikan_tugas(id_tugas: int) -> bool:
    """Menandai tugas selesai berdasarkan ID. Return True kalau berhasil."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    berhasil = False
    try:
        cursor.execute("UPDATE tugas SET status = 'done' WHERE id = ?", (id_tugas))
        berhasil = cursor.rowcount > 0
        conn.commit()
    except Exception as e:
        yield f"Gagal menyelesaikan tugas: {e}"
    finally:
        conn.close()
    return berhasil

def update_tugas(id_tugas: int, deskripsi: str = None, deadline: str = None) -> bool:
    """Mengupdate deskripsi dan/atau deadline tugas yang sudah ada, tanpa membuat entry baru."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    berhasil = False
    try:
        if deskripsi is not None and deadline is not None:
            cursor.execute("UPDATE tugas SET deskripsi = ?, deadline = ? WHERE id = ?", (deskripsi, deadline, id_tugas))
        elif deadline is not None:
            cursor.execute("UPDATE tugas SET deadline = ? WHERE id = ?", (deadline, id_tugas))
        elif deskripsi is not None:
            cursor.execute("UPDATE tugas SET deskripsi = ? WHERE id = ?", (deskripsi, id_tugas))
        berhasil = cursor.rowcount > 0
        conn.commit()
    except Exception as e:
        print(f"Gagal update tugas: {e}")
    finally:
        conn.close()
    return berhasil

def hapus_tugas(id_tugas: int) -> bool:
    """Menghapus tugas permanen berdasarkan ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    berhasil = False
    try:
        cursor.execute("DELETE FROM tugas WHERE id = ?", (id_tugas))
        berhasil = cursor.rowcount > 0
        conn.commit()
    except Exception as e:
        yield f"Gagal menghapus tugas: {e}"
    finally:
        conn.close()
    return berhasil

# ==================== FITUR JADWAL HARIAN ====================

def tambah_jadwal(aktivitas: str, waktu: str) -> int:
    """Menambahkan item jadwal baru, mengembalikan ID-nya."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO jadwal (aktivitas, waktu) VALUES (?, ?)", (aktivitas, waktu))
    id_baru = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_baru

def ambil_jadwal() -> list:
    """Mengambil seluruh item jadwal."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, aktivitas, waktu FROM jadwal ORDER BY id")
    baris = cursor.fetchall()
    conn.close()
    return [{"id": b[0], "aktivitas": b[1], "waktu": b[2]} for b in baris]

def hapus_jadwal(id_jadwal: int) -> bool:
    """Menghapus item jadwal berdasarkan ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    berhasil = False
    try:
        cursor.execute("DELETE FROM jadwal WHERE id = ?", (id_jadwal,))
        berhasil = cursor.rowcount > 0
        conn.commit()
    except Exception as e:
        print(f"Gagal menghapus jadwal: {e}")
    finally:
        conn.close()
    return berhasil

# ==================== FITUR MONITORING AKTIVITAS ====================

def mulai_sesi_aktivitas(nama_aplikasi: str) -> int:
    """Mencatat aplikasi mulai terdeteksi jalan. Dipanggil sama background monitor."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO aktivitas_log (nama_aplikasi, waktu_mulai) VALUES (?, CURRENT_TIMESTAMP)",
        (nama_aplikasi,)
    )
    id_baru = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_baru

def selesaikan_sesi_aktivitas(nama_aplikasi: str):
    """Menutup sesi aktivitas terbuka terakhir untuk aplikasi tertentu (waktu_selesai diisi sekarang)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE aktivitas_log
            SET waktu_selesai = CURRENT_TIMESTAMP
            WHERE id = (
                SELECT id FROM aktivitas_log
                WHERE nama_aplikasi = ? AND waktu_selesai IS NULL
                ORDER BY id DESC LIMIT 1
            )
        ''', (nama_aplikasi,))
        conn.commit()
    except Exception as e:
        print(f"Gagal menutup sesi aktivitas: {e}")
    finally:
        conn.close()

def tutup_semua_sesi_aktif():
    """Menutup SEMUA sesi yang masih kebuka (waktu_selesai NULL). Dipanggil pas Neira ditutup,
    biar gak ada sesi 'menggantung' selamanya kalau app dimatiin paksa."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE aktivitas_log SET waktu_selesai = CURRENT_TIMESTAMP WHERE waktu_selesai IS NULL")
        conn.commit()
    except Exception as e:
        print(f"Gagal menutup sesi aktif: {e}")
    finally:
        conn.close()

def ambil_riwayat_aktivitas(nama_aplikasi: str, hari: int = 14) -> list:
    """Ambil riwayat sesi (mulai, selesai) untuk sebuah app dalam N hari terakhir, sesi yang udah selesai aja."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT waktu_mulai, waktu_selesai FROM aktivitas_log
        WHERE nama_aplikasi = ?
          AND waktu_selesai IS NOT NULL
          AND waktu_mulai >= datetime('now', ?)
        ORDER BY waktu_mulai ASC
    ''', (nama_aplikasi, f'-{hari} days'))
    baris = cursor.fetchall()
    conn.close()
    return [{"mulai": b[0], "selesai": b[1]} for b in baris]

def ambil_sesi_terbuka() -> list:
    """Ambil semua sesi yang masih 'menggantung' (waktu_selesai NULL) — biasanya sisa dari restart sebelumnya."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama_aplikasi, waktu_mulai FROM aktivitas_log WHERE waktu_selesai IS NULL")
    baris = cursor.fetchall()
    conn.close()
    return [{"id": b[0], "nama_aplikasi": b[1], "waktu_mulai": b[2]} for b in baris]

def tutup_sesi_by_id(id_sesi: int):
    """Tutup 1 sesi spesifik berdasarkan ID-nya."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE aktivitas_log SET waktu_selesai = CURRENT_TIMESTAMP WHERE id = ?", (id_sesi,))
    conn.commit()
    conn.close()