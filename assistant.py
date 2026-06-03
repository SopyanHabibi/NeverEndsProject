import datetime
import os
import time
import webbrowser
from playsound import playsound


FILE_TUGAS = "todo_list.txt"


def sapa_user():
    """Fungsi untuk menyapa pengguna berdasarkan waktu saat ini."""
    jam = datetime.datetime.now().hour
    if jam < 12:
        print("Hai! Selamat pagi! Aku Neira, asisten virtualmu. Ada yang bisa saya bantu?")
    elif 12 <= jam <= 18:
        print("Hai! Selamat siang! Aku Neira, asisten virtualmu. Ada yang bisa saya bantu?")
    else:
        print("Hai! Selamat malam! Aku Neira, asisten virtualmu. Ada yang bisa saya bantu?")


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


def assistant():
    sapa_user()

    while True:
        # Mengambil input dari user dan mengubah nya menjadi huruf kecil semua
        perintah = input("\nKamu: ").lower()

        # Fitur: Menyapa kembali
        if "halo" in perintah or "hi" in perintah:
            print("Neira: Halo! Senang bertemu denganmu.")
        
        # Fitur: Menanyakan kabar
        elif "apa kabar" in perintah or "gimana kabar" in perintah:
            print("Neira: Aku baik, terima kasih! Bagaimana denganmu?")

        # fitur: reminder sederhana
        elif "ingatkan aku 1 menit lagi" in perintah:
            set_reminder(1)

        # LOGIKA PERINTAH TO-DO LIST
        elif "tambah tugas" in perintah or "bikin tugas" in perintah:
            # Mengambil nama tugas setelah kata 'tambah tugas '
            # Contoh: "tambah tugas belajar python" -> nama tugasnya: "belajar python"
            nama_tugas = perintah.replace("bikin tugas", "").strip()
            if nama_tugas:
                tambah_tugas(nama_tugas)
            else:
                print("Neira: Tugasnya apa? Tulis contoh: 'tambah tugas belajar'")

        elif "lihat tugas" in perintah or "list tugas" in perintah or "liat tugas" in perintah:
            lihat_tugas()

        elif "selesai tugas" in perintah or "tandai selesai" in perintah:
            # Contoh perintah: "selesai tugas 1"
            try:
                nomor = int(perintah.replace("selesai tugas", "").strip())
                tandai_selesai(nomor)
            except ValueError:
                print(
                    "Neira: Tolong masukkan nomor tugasnya. Contoh: 'selesai tugas 1'"
                )

        elif "hapus tugas" in perintah:
            # Contoh perintah: "hapus tugas 2"
            try:
                nomor = int(perintah.replace("hapus tugas", "").strip())
                hapus_tugas(nomor)
            except ValueError:
                print(
                    "Neira: Tolong masukkan nomor tugasnya. Contoh: 'hapus tugas 2'"
                )

        # Fitur: Cek waktu/jam
        elif "jam" in perintah or "waktu" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"Neira: Saat ini jam ({waktu_sekarang})")

        # fitur: membuka google (automasi browser sederhana)
        elif "buka google" in perintah:
            print("Neira: Membuka Google...")
            webbrowser.open("https://www.google.com")

        # fitur: membuka instagram (automasi browser sederhana)
        elif "buka instagram" in perintah or "buka ig" in perintah:
            print("Neira: Membuka Instagram...")
            webbrowser.open("https://www.instagram.com/_sop.ayam/")

        # fitur: membuka youtube (automasi browser sederhana)
        elif "buka youtube" in perintah or "buka yt" in perintah:
            print("Neira: Membuka YouTube...")
            webbrowser.open("https://www.youtube.com")

        # fitur: exit program
        elif "keluar" in perintah or "exit" in perintah:
            print("Neira: Sampai jumpa! Semoga harimu menyenangkan.")
            break

        # jika perintah tidak dikenali
        else:
            print("Neira: Maaf, saya tidak mengerti perintah itu. Coba perintah lain atau ketik 'keluar' untuk keluar.")


# Menjalankan assistant
if __name__ == "__main__":
    assistant()