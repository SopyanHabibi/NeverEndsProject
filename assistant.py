import datetime
import json
import os
import time
import webbrowser
from playsound import playsound


FILE_TUGAS = "todo_list.txt"
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


def tambah_tugas(nama_tugas):
    """Menambahkan tugas baru ke dalam file teks."""
    # 'a' berarti append (menambahkan tanpa menghapus isi file yang sudah ada)
    with open(FILE_TUGAS, "a") as file:
        file.write(f"[ ] {nama_tugas}\n")
    print(f"Neira: Siap! '{nama_tugas}' telah ditambahkan ke daftar.")


def lihat_tugas():
    """Membaca dan menampilkan semua tugas."""
    # Cek apakah file sudah ada atau belum
    if not os.path.exists(FILE_TUGAS) or os.path.getsize(FILE_TUGAS) == 0:
        print("Neira: Gada tugas hari ini! Santai aja, nikmati harimu 😊")
        return []

    print("\n📋 DAFTAR TUGAS HARI INI:")
    with open(FILE_TUGAS, "r") as file:
        tugas_list = file.readlines()

    # Menampilkan tugas dengan nomor urut
    for indeks, tugas in enumerate(tugas_list):
        # .strip() digunakan untuk menghilangkan spasi/baris baru di akhir teks
        print(f"{indeks + 1}. {tugas.strip()}")

    return tugas_list


def tandai_selesai(nomor):
    """Mengubah status tugas menjadi selesai berdasarkan nomor urut."""
    if not os.path.exists(FILE_TUGAS):
        print("Neira: Kamu belum punya daftar tugas.")
        return

    with open(FILE_TUGAS, "r") as file:
        tugas_list = file.readlines()

    # Memastikan nomor yang dimasukkan user itu ada di daftar
    if 0 < nomor <= len(tugas_list):
        indeks = nomor - 1
        # Ganti tanda [ ] menjadi [x]
        if "[ ]" in tugas_list[indeks]:
            tugas_list[indeks] = tugas_list[indeks].replace("[ ]", "[x]")
            with open(FILE_TUGAS, "w") as file:  # 'w' untuk menulis ulang file
                file.writelines(tugas_list)
            print(f"Neira: Bagus! Tugas nomor {nomor} ditandai selesai.")
        else:
            print("Neira: Tugas itu memang sudah selesai sebelumnya.")
    else:
        print("Neira: Nomor tugas tidak valid.")


def hapus_tugas(nomor):
    """Menghapus tugas dari file berdasarkan nomor urut."""
    if not os.path.exists(FILE_TUGAS):
        print("Neira: Kamu belum punya daftar tugas.")
        return

    with open(FILE_TUGAS, "r") as file:
        tugas_list = file.readlines()

    if 0 < nomor <= len(tugas_list):
        indeks = nomor - 1
        tugas_dihapus = tugas_list.pop(indeks)  # Hapus tugas dari list
        with open(FILE_TUGAS, "w") as file:
            file.writelines(tugas_list)
        print(
            f"Neira: '{tugas_dihapus.strip()}' telah dihapus dari daftar."
        )
    else:
        print("Neira: Nomor tugas tidak valid.")


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

        # ==================== LOGIKA MEMORI BARU (PERBAIKAN BUG) ====================

        # --- KELOMPOK NAMA (Dibuat Eksklusif dengan if-elif agar tidak tabrakan) ---
        if "siapa aku" in perintah or "ingat namaku" in perintah:
            data = baca_memori()
            if data["nama"] != "kamu":
                print(f"Neira: Kamu adalah {data['nama']}. Saya tidak akan lupa!")
            else:
                print(
                    "Neira: Kamu belum memberi tahu namamu. Ketik 'namaku [Nama kamu]'"
                )
            keyword_dikenali = True


        elif "namaku" in perintah:  # Menggunakan elif agar tidak memicu deteksi ganda
            nama_baru = perintah.replace("namaku", "").strip()
            if nama_baru:
                simpan_memori("nama", nama_baru)
                print(f"Neira: Catat! Mulai sekarang saya panggil kamu {nama_baru}.")
            else:
                print("Neira: Siapa namamu? Contoh: 'namaku ian'")
            keyword_dikenali = True

        if "berapa umurku" in perintah or "ingat umurku" in perintah:
            data = baca_memori()
            if data["umur"] != "belum diatur":
                print(f"Neira: Umur kamu adalah {data['umur']} tahun. Saya tidak akan lupa!")
            else:
                print(
                    "Neira: Kamu belum memberi tahu umurmu. Ketik 'umurku [Umur kamu]'"
                )
            keyword_dikenali = True

        elif "umurku" in perintah:
            umur_baru = perintah.replace("umurku", "").strip()
            if umur_baru:
                simpan_memori("umur", umur_baru)
                print(f"Neira: Oke, umur kamu sekarang tercatat {umur_baru} tahun.")
            else:
                print("Neira: Berapa umurmu? contoh: 'umurku 24'")
                keyword_dikenali = True

        # --- KELOMPOK HOBI (Dibuat Eksklusif dengan if-elif agar tidak tabrakan) ---
        if "apa hobiku" in perintah:  # Kita cek pertanyaan yang lebih panjang dulu
            data = baca_memori()
            if data["hobi"] != "belum diatur":
                print(f"Neira: Setahu saya, hobi kamu itu {data['hobi']}.")
            else:
                print(
                    "Neira: Kamu belum cerita hobimu apa. Ketik 'hobiku [Hobi kamu]'"
                )
            keyword_dikenali = True

        elif "hobiku" in perintah:  # Jika bukan bertanya, berarti user sedang mendaftarkan hobi baru
            hobi_baru = perintah.replace("hobiku", "").strip()
            if hobi_baru:
                simpan_memori("hobi", hobi_baru)
                print(f"Neira: Oh, jadi kamu suka {hobi_baru}. Keren!")
            else:
                print("Neira: Apa hobimu? Contoh: 'hobiku coding'")
            keyword_dikenali = True

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
                tambah_tugas(nama_tugas)
            else:
                print("Neira: Tugasnya apa? Tulis contoh: 'tambah tugas belajar'")
            keyword_dikenali = True

        if "lihat tugas" in perintah or "list tugas" in perintah:
            lihat_tugas()
            keyword_dikenali = True

        if "selesai tugas" in perintah:
            try:
                nomor = int(perintah.replace("selesai tugas", "").strip())
                tandai_selesai(nomor)
            except ValueError:
                print(
                    "Neira: Tolong masukkan nomor tugasnya. Contoh: 'selesai tugas 1'"
                )
            keyword_dikenali = True

        if "hapus tugas" in perintah:
            try:
                nomor = int(perintah.replace("hapus tugas", "").strip())
                hapus_tugas(nomor)
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