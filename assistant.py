import datetime
import json
import os
import time
import webbrowser
from playsound import playsound


FILE_TASKS = "tasks.json"
FILE_MEMORI = "memory.json"

# ==================== FITUR BARU: MEMORI ASISTEN ====================
def inisialisasi_memori():
    """Membuat file memori default jika belum ada di komputer."""
    if not os.path.exists(FILE_MEMORI):
        data_default = {"nama": "kamu", "hobi": "belum diatur", "umur": "belum diatur"}
        with open(FILE_MEMORI, "w") as file:
            json.dump(data_default, file, indent=4)


def baca_memori():
    """Membaca data dari file JSON."""
    inisialisasi_memori()
    with open(FILE_MEMORI, "r") as file:
        return json.load(file)


def simpan_memori(kunci, nilai):
    """Mengubah data spesifik di dalam memori."""
    data = baca_memori()
    data[kunci] = nilai  # Mengubah nilai berdasarkan kuncinya (misal: data['nama'] = 'ian')

    with open(FILE_MEMORI, "w") as file:
        json.dump(data, file, indent=4)


def cek_typo_nama(perintah_user):
    """fungsi untuk mendeteksi apakah user salah mengetik nama Neira."""
    # daftar variasi typo yang paling sering terjadi untuk nama 'Neira'
    daftar_typo = [
        "neria",
        "niera",
        "neyra",
        "nera",
        "nira",
        "neirra",
        "najra",
        "neisa",
    ]

    # memecah perintah menjadi kata-kata tunggal
    kata_kata = perintah_user.split()

    for kata in kata_kata:
        kata_bersih = kata.strip(",.?!\"'")

        if kata_bersih in daftar_typo:
            return True
        
    return False


# ===================================================================

def sapa_user():
    """Fungsi untuk menyapa pengguna berdasarkan waktu saat ini."""
    data = baca_memori()  # Memuat memori untuk mendapatkan nama pengguna
    nama_user = data["nama"]  # Ambil nama dari memori


    jam = datetime.datetime.now().hour
    if jam < 12:
        print(f"Neira: Selamat pagi, {nama_user}! Ada yang bisa saya bantu?")
    elif 12 <= jam < 18:
        print(
            f"Neira: Selamat siang/sore, {nama_user}! Ada yang bisa saya bantu?"
        )
    else:
        print(f"Neira: Selamat malam, {nama_user}! Ada yang bisa saya bantu?")


def set_reminder(menit):
    """Fungsi untuk menahan program dan memunculkan pengingat."""
    # konversi menit ke detik
    detik = menit * 60
    print(f"Neira: Baik, saya akan mengingatkanmu dalam {menit} menit.")
    time.sleep(detik)

    # setelah waktu habis, tampilkan pengingat
    print(f"Neira: WAKTU HABIS!!!")

    try:
        # Memainkan suara alarm (pastikan file 'alarm.wav' ada di direktori yang sama)
        playsound('alarm.wav')
    except Exception as e:
        print(f"Neira: Maaf, saya tidak dapat memainkan suara alarm. Error: {e}")

# ==================== FITUR BARU: TO-DO LIST & STATISTIK (JSON) ====================
def load_tasks():
    """Membuat file todo_list.json default jika belum ada."""
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

    # Membuat ID otomatis berdasarkan jumlah tugas yang ada
    id_baru = len(daftar) + 1
    waktu_sekarang = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tugas_baru = {
        "id": id_baru,
        "tugas": nama_tugas,
        "status": "belum selesai",
        "waktu_dibuat": waktu_sekarang,
        "waktu_selesai": None,
    }

    daftar.append(tugas_baru)
    save_tasks(daftar)
    print(
        f"Neira: Siap! '{nama_tugas}' dimasukkan ke daftar pada {waktu_sekarang}."
    )


def view_tasks():
    """Menampilkan tugas yang belum selesai maupun yang sudah."""
    daftar = read_tasks()

    if not daftar:
        print("Neira: Daftar tugas kamu masih kosong!")
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
                print(f"Neira: Bagus! Tugas nomor {nomor} ditandai selesai.")
            else:
                print("Neira: Tugas itu memang sudah selesai sebelumnya.")
            break

    if not ditemukan:
        print("Neira: Nomor tugas tidak ditemukan.")


def delete_tasks(nomor):
    """Menghapus tugas dan menyusun ulang ID-nya agar tetap berurutan."""
    daftar = read_tasks()
    tugas_baru = [t for t in daftar if t["id"] != nomor]

    if len(daftar) == len(tugas_baru):
        print("Neira: Nomor tugas tidak valid.")
        return

    # Susun ulang ID agar rapi (1, 2, 3...)
    for indeks, t in enumerate(tugas_baru):
        t["id"] = indeks + 1

    save_tasks(tugas_baru)
    print(f"Neira: Tugas nomor {nomor} berhasil dihapus.")


def view_statistics():
    """Fungsi statistik yang dilengkapi detektor dan pembersih error data."""
    daftar = read_tasks()
    waktu_sekarang = datetime.datetime.now()

    # --- PROTEKSI TAMBAHAN: Mencegah tipe data rusak ---
    # Jika ternyata yang terbaca bukan sebuah List, kita paksa reset jadi list kosong
    if not isinstance(daftar, list):
        print(
            "Neira: Waduh, struktur data todo_list.json rusak. Saya sedang meresetnya..."
        )
        save_tasks([])
        daftar = []

    if not daftar:
        print(
            "Neira: Belum ada data tugas yang bisa dihitung untuk statistik hari ini."
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


def ringkas_profil():
    """Fungsi untuk menampilkan ringkasan semua hal yang Neira ketahui tentang user"""
    data = baca_memori()

    print("\n===========================================")
    print(f"   👤 PROFIL PENGGUNA (DIINGAT OLEH NEIRA)  ")
    print("===========================================")

    # Menghitung berapa banyak informasi yang sudah diketahui Neira
    total_informasi = 0

    # melakukan looping untuk membaca semua key dan value di dalam file JSON
    for kunci, nilai in data.items():
        kunci_rapi = kunci.upper()

        if nilai == "kamu" or nilai == "belum diatur":
            status_nilai = "❌ Belum kamu ceritakan"
        else:
            status_nilai = nilai
            total_informasi += 1

        print(f"➤ {kunci_rapi} : {status_nilai}")

    print("-------------------------------------------")
    if total_informasi == 0:
        print("Neira : Saya belum tahu banyak tentangmu. Yuk, ceritakan sesuatu!")
    else:
        print(f"Neira: Total ada {total_informasi} hal penting tentangmu yang saya kunci di memori")
    print("===========================================")



def neira():
    sapa_user()

    data = baca_memori()  # Memuat memori untuk mendapatkan nama pengguna
    nama_user = data["nama"]  # Ambil nama dari memori
    while True:


        perintah = input("\nKamu: ").lower()

        if "keluar" in perintah or "stop" in perintah or "dadah" in perintah:
            print(
                "Neira: Sampai jumpa! Neira akan terus menunggu kamu."
            )
            break

        keyword_dikenali = False

        # --- FITUR BARU: DETEKSI TYPO NAMA (CEK PALING AWAL) ---
        if cek_typo_nama(perintah):
            print("Neira: Hmm... Mungkin maksudmu 'Neira'? Typo dikit tuh, hehe. Ada yang bisa saya bantu?")
            keyword_dikenali = True
            continue


        # ==================== LOGIKA MEMORI BARU (DENGAN RINGKASAN) ====================

        # 1. Perintah Ringkasan Profil (Menu Status Player)
        if (
            "siapa aku" in perintah
            or "ringkas tentangku" in perintah
            or "profilku" in perintah
            or "biodataku" in perintah
        ):
            ringkas_profil()  # Memanggil fungsi ringkasan baru
            keyword_dikenali = True

        # 2. Kelompok Mengatur Nama
        elif "namaku" in perintah:
            nama_baru = perintah.replace("namaku", "").strip()
            if nama_baru:
                simpan_memori("nama", nama_baru)
                print(f"Neira: Catat! Mulai sekarang saya panggil kamu {nama_baru}.")
            else:
                print("Neira: Siapa namamu? Contoh: 'namaku Budi'")
            keyword_dikenali = True

        # 3. Kelompok Mengatur Hobi
        elif "hobiku" in perintah:
            hobi_baru = perintah.replace("hobiku", "").strip()
            if hobi_baru:
                simpan_memori("hobi", hobi_baru)
                print(f"Neira: Oh, jadi kamu suka {hobi_baru}. Keren!")
            else:
                print("Neira: Apa hobimu? Contoh: 'hobiku coding'")
            keyword_dikenali = True

        # 4. Kelompok Menanyakan Hobi Secara Spesifik
        elif "apa hobiku" in perintah:
            data = baca_memori()
            if data["hobi"] != "belum diatur":
                print(f"Neira: Setahu saya, hobi kamu itu {data['hobi']}.")
            else:
                print(
                    "Neira: Kamu belum cerita hobimu apa. Ketik 'hobiku [Hobi kamu]'"
                )
            keyword_dikenali = True

        # ============================================================================

        # ==================== LOGIKA LAMA (TETAP DIJAGA) ====================
        if "halo" in perintah or "hai" in perintah or "hi" in perintah:
            print(f"Neira: Halo juga {nama_user}!")
            keyword_dikenali = True

        if "apa kabar" in perintah or "bagaimana kabarmu" in perintah:
            print(
                "Neira: Saya baik-baik saja, terima kasih sudah bertanya! Bagaimana dengan kamu?"
            )
            keyword_dikenali = True

        if "jam" in perintah or "waktu" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"Neira: Sekarang jam {waktu_sekarang}.")
            keyword_dikenali = True

        if "buka google" in perintah:
            print("Neira: Membuka Google di browser kamu...")
            webbrowser.open("https://www.google.com")
            keyword_dikenali = True

        if "buka youtube" in perintah or "buka yt" in perintah:
            print("Neira: Membuka YouTube di browser kamu...")
            webbrowser.open("https://www.youtube.com")
            keyword_dikenali = True

        if "buka instagram" in perintah or "buka ig" in perintah:
            print("Neira: Membuka Instagram di browser kamu...")
            webbrowser.open("https://www.instagram.com")
            keyword_dikenali = True

        if "ingatkan aku 1 menit lagi" in perintah:
            set_reminder(1)
            keyword_dikenali = True
        if "ingatkan aku 5 menit lagi" in perintah:
            set_reminder(5)
            keyword_dikenali = True

        if "tambah tugas" in perintah:
            nama_tugas = perintah.replace("tambah tugas", "").strip()
            if nama_tugas:
                add_tasks(nama_tugas)
            else:
                print("Neira: Tugasnya apa? Tulis contoh: 'tambah tugas belajar'")
            keyword_dikenali = True

                # Tambahkan logika ini di dalam while True pada fungsi infinite_assistant()
        if (
            "lihat statistik" in perintah
            or "cek produktivitas" in perintah
            or "statistik" in perintah
        ):
            view_statistics()
            keyword_dikenali = True


        if "lihat tugas" in perintah or "list tugas" in perintah:
            view_tasks()
            keyword_dikenali = True

        if "selesai tugas" in perintah:
            try:
                nomor = int(perintah.replace("selesai tugas", "").strip())
                mark_done(nomor)
            except ValueError:
                print(
                    "Neira: Tolong masukkan nomor tugasnya. Contoh: 'selesai tugas 1'"
                )
            keyword_dikenali = True

        if "hapus tugas" in perintah:
            try:
                nomor = int(perintah.replace("hapus tugas", "").strip())
                delete_tasks(nomor)
            except ValueError:
                print(
                    "Neira: Tolong masukkan nomor tugasnya. Contoh: 'hapus tugas 2'"
                )
            keyword_dikenali = True

        if not keyword_dikenali:
            print(
                "Neira: Maaf, saya belum memahami perintah itu. Maklum, saya masih versi basic!"
            )


# Menjalankan assistant
if __name__ == "__main__":
    neira()