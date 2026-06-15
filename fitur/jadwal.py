import datetime
import os
import json
from config import FILE_JADWAL
from .utilitas import penerjemah_waktu_manusia

def load_jadwal():
    """Membuat file jadwal.json default jika belum ada"""
    if not os.path.exists(FILE_JADWAL):
        with open(FILE_JADWAL, "w") as file:
            json.dump([], file, indent=4)


def read_jadwal():
    """Membaca daftar jadwal dari file JSON"""
    load_jadwal()
    with open(FILE_JADWAL, "r") as file:
        return json.load(file)


def save_all_jadwal(daftar_jadwal):
    """Menulis ulang seluruh daftar jadwal ke file JSON."""
    with open(FILE_JADWAL, "w") as file:
        json.dump(daftar_jadwal, file, indent=4)


def add_jadwal(jam_input, nama_agenda):
    """Menambahkan jadwal dengan deteksi otomatis bahasa manusia (pagi/siang/sore/malam)."""

    # Panggil fungsi penerjemah cerdas
    jam_24h = penerjemah_waktu_manusia(jam_input)

    if jam_24h is None:
        print(
            "Format jam membingungkan. Tolong tulis seperti: '01:00 siang' atau '11:23 pagi'."
        )
        return

    daftar = read_jadwal()
    agenda_baru = {"jam": jam_24h, "agenda": nama_agenda, "status": "mendatang"}
    daftar.append(agenda_baru)
    daftar.sort(key=lambda x: x["jam"])
    save_all_jadwal(daftar)

    # Konversi ke AM/PM hanya untuk gaya bicara Neira saat merespon kamu
    jam_objek = datetime.datetime.strptime(jam_24h, "%H:%M")
    jam_ampm = jam_objek.strftime("%I:%M %p")

    print(
        f"Dimengerti! Agenda '{nama_agenda}' di jam {jam_ampm} ({jam_input}) sudah saya kunci."
    )


# 3. Perbaikan Cek Agenda Mendatang (Menampilkan AM/PM ke Layar)
def cek_agenda_mendatang():
    daftar = read_jadwal()
    if not daftar:
        print("Jadwal harianmu hari ini masih kosong.")
        return

    waktu_sekarang = datetime.datetime.now()
    waktu_sekarang_teks = waktu_sekarang.strftime("%H:%M")
    waktu_sekarang_ampm = waktu_sekarang.strftime("%I:%M %p")

    print(f"Sekarang jam {waktu_sekarang_ampm}.")
    ada_agenda_nanti = False
    print("\n📅 AGENDA KAMU BERIKUTNYA HARI INI:")

    for j in daftar:
        if j["jam"] > waktu_sekarang_teks:
            # KONVERSI DI SINI: Jam 24 jam dari JSON diubah ke AM/PM sebelum di-print
            jam_objek = datetime.datetime.strptime(j["jam"], "%H:%M")
            jam_ampm = jam_objek.strftime("%I:%M %p")

            print(f"⏰ Jam {jam_ampm} -> {j['agenda']}")
            ada_agenda_nanti = True

    if not ada_agenda_nanti:
        print(
            "Untuk sisa hari ini, kamu tidak punya agenda lagi. Waktunya santai!"
        )


# 4. Perbaikan Lihat Semua Jadwal (Menampilkan AM/PM ke Layar)
def lihat_semua_jadwal():
    daftar = read_jadwal()
    if not daftar:
        print("Belum ada jadwal harian yang tercatat.")
        return

    print("\n🗓️  SELURUH JADWAL HARIAN KAMU:")
    print("==============================")
    for j in daftar:
        # Mengubah format 24 jam ke AM/PM saat ditampilkan
        jam_objek = datetime.datetime.strptime(j["jam"], "%H:%M")
        jam_ampm = jam_objek.strftime("%I:%M %p")
        print(f"• [{jam_ampm}] {j['agenda']}")