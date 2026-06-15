import datetime
import json
import os
from config import FILE_TASKS
from config import FILE_SESI_FOKUS

def load_tasks():
    """Membuat file tasks.json default jika belum ada."""
    if not os.path.exists(FILE_TASKS):
        with open(FILE_TASKS, "w") as file:
            json.dump([], file, indent=4)


def read_tasks():
    """Membaca daftar tugas dari file JSON."""
    load_tasks()
    with open(FILE_TASKS, "r") as file:
        return json.load(file)


def save_tasks(daftar_tugas):
    """Menulis ulang seluruh daftar tugas ke file JSON."""
    with open(FILE_TASKS, "w") as file:
        json.dump(daftar_tugas, file, indent=4)


def add_tasks(nama_tugas):
    """Menambahkan tugas baru dengan metadata waktu buat."""
    daftar = read_tasks()
    id_baru = len(daftar) + 1

    # Membuat ID otomatis berdasarkan jumlah tugas yang ada
    waktu_sekarang = datetime.datetime.now()
    waktu_24j = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
    waktu_ampm = waktu_sekarang.strftime("%Y-%m-%d %I:%M %p")

    tugas_baru = {
        "id": id_baru,
        "tugas": nama_tugas,
        "status": "belum selesai",
        "waktu_dibuat": waktu_24j,
        "waktu_selesai": None,
    }
    daftar.append(tugas_baru)
    save_tasks(daftar)
    print(
        f"Siap! '{nama_tugas}' dimasukkan ke daftar pada {waktu_ampm}."
    )


def view_tasks():
    """Menampilkan tugas yang belum selesai maupun yang sudah."""
    daftar = read_tasks()

    if not daftar:
        print("Daftar tugas kamu masih kosong!")
        return

    print("\n📋 DAFTAR TUGAS KAMU:")
    for t in daftar:
        status_simbol = "[ ]" if t["status"] == "belum selesai" else "[SELESAI]"
        print(f"{t['id']}. {status_simbol} {t['tugas']}")


def mark_done(nomor):
    """Menandai selesai dan mencatat waktu selesainya."""
    daftar = read_tasks()
    ditemukan = False

    for t in daftar:
        if t["id"] == nomor:
            ditemukan = True
            if t["status"] == "belum selesai":
                t["status"] = "selesai"
                t["waktu_selesai"] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                save_tasks(daftar)
                print(f"Bagus! Tugas nomor {nomor} ditandai selesai.")
            else:
                print("Tugas itu memang sudah selesai sebelumnya.")
            break

    if not ditemukan:
        print("Nomor tugas tidak ditemukan.")


def delete_tasks(nomor):
    """Menghapus tugas dan menyusun ulang ID-nya agar tetap berurutan."""
    daftar = read_tasks()
    tugas_baru = [t for t in daftar if t["id"] != nomor]

    if len(daftar) == len(tugas_baru):
        print("Nomor tugas tidak valid.")
        return

    # Susun ulang ID agar rapi (1, 2, 3...)
    for indeks, t in enumerate(tugas_baru):
        t["id"] = indeks + 1

    save_tasks(tugas_baru)
    print(f"Tugas nomor {nomor} berhasil dihapus.")


# def load_sesi():
#     """Membuat file sesi_fokus.json default jika belum ada."""
#     if not os.path.exists(FILE_SESI_FOKUS):
#         with open(FILE_SESI_FOKUS, "w") as file:
#             json.dump([], file, indent=4)


# def simpan_sesi_fokus(durasi_menit):
#     """Menyimpan data mentah sesi fokus ke dalam database JSON."""
#     # membaca data
#     try:
#         with open(FILE_TASKS, "r") as file:
#             data = json.load(file)
#     except (FileNotFoundError, json.JSONDecodeError):
#         data = {"tugas": [], "sesi_fokus": []}

#     # kunci "sesi_fokus" ada di dalam dict
#     if "sesi_fokus" not in data:
#         data["sesi_fokus"] = []

#     now = datetime.datetime.now()
#     start_time = now - datetime.timedelta(minutes=durasi_menit)

#     # format data mentah yang akan disimpan
#     sesi_baru = {
#         "tanggal": now.strftime("%Y-%m-%d"),
#         "mulai": start_time.strftime("%H:%M:%S"),
#         "selesai": now.strftime("%H:%M:%S"),
#         "durasi_menit": durasi_menit
#     }

#     data["sesi_fokus"].append(sesi_baru)

#     with open(FILE_TASKS, "w") as file:


def view_statistics():
    """Fungsi statistik yang dilengkapi detektor dan pembersih error data."""
    daftar = read_tasks()
    waktu_sekarang = datetime.datetime.now()

    # --- PROTEKSI TAMBAHAN: Mencegah tipe data rusak ---
    # Jika ternyata yang terbaca bukan sebuah List, kita paksa reset jadi list kosong
    if not isinstance(daftar, list):
        print(
            "Waduh, struktur data todo_list.json rusak. Saya sedang meresetnya..."
        )
        save_tasks([])
        daftar = []

    if not daftar:
        print(
            "Belum ada data tugas yang bisa dihitung untuk statistik hari ini."
        )
        return

    total_tugas_dibuat = len(daftar)
    total_selesai = 0
    tugas_seminggu_ini = 0
    selesai_seminggu_ini = 0

    # Hitung total selesai secara manual dan aman
    for t in daftar:
        if isinstance(t, dict) and t.get("status") == "selesai":
            total_selesai += 1

    print("\n📊 STATISTIK PRODUKTIVITAS")
    print("==========================")
    print(f"Total tugas yang pernah dimasukkan : {total_tugas_dibuat}")
    print(f"Total tugas yang sudah selesai     : {total_selesai}")

    print("\n⏱️ Rincian Durasi Pengerjaan:")

    for t in daftar:
        # Pengecekan apakah data 't' beneran sebuah Dictionary (Kamus data)
        if not isinstance(t, dict):
            continue  # Lewati jika ada data 'sampah' yang bukan dictionary

        # Gunakan fungsi .get() agar program tidak crash jika kunci tidak ditemukan
        teks_waktu_buat = t.get("waktu_dibuat")

        if not teks_waktu_buat:
            # Jika tugas tidak punya catatan waktu dibuat, lewati atau beri waktu sekarang
            continue

        try:
            waktu_buat = datetime.datetime.strptime(
                teks_waktu_buat, "%Y-%m-%d %H:%M:%S"
            )
        except (ValueError, TypeError):
            waktu_buat = datetime.datetime.now()

        # Hitung statistik 1 minggu terakhir
        selisih_hari_buat = (waktu_sekarang - waktu_buat).days
        if selisih_hari_buat <= 7:
            tugas_seminggu_ini += 1

        # Jika tugas sudah selesai, hitung durasi pengerjaannya
        if t.get("status") == "selesai":
            teks_waktu_selesai = t.get("waktu_selesai")
            try:
                waktu_beres = datetime.datetime.strptime(
                    teks_waktu_selesai, "%Y-%m-%d %H:%M:%S"
                )
                durasi = waktu_beres - waktu_buat

                # Cek jika selesainya dalam minggu ini
                if (waktu_sekarang - waktu_beres).days <= 7:
                    selesai_seminggu_ini += 1
            except (ValueError, TypeError):
                durasi = datetime.timedelta(seconds=0)

            # Format durasi agar mudah dibaca manusia
            if durasi.days > 0:
                durasi_teks = f"{durasi.days} hari"
            else:
                durasi_teks = f"{durasi.seconds // 3600} jam atau {durasi.seconds // 60} menit"

            print(
                f"- Tugas '{t.get('tugas')}': Masuk ({t.get('waktu_dibuat')}) -> Selesai dalam {durasi_teks}"
            )
        else:
            print(
                f"- Tugas '{t.get('tugas')}': [Belum Selesai] - Masuk ({t.get('waktu_dibuat')})"
            )

    print("--------------------------")
    print(f"Tugas baru dalam 1 minggu ini     : {tugas_seminggu_ini}")
    print(f"Tugas selesai dalam 1 minggu ini  : {selesai_seminggu_ini}")