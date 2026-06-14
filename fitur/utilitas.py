import datetime
import sys
import time



def cek_typo_nama(perintah_user):
    """fungsi untuk mendeteksi apakah user salah mengetik nama Neira."""
    # daftar variasi typo yang paling sering terjadi untuk nama 'Neira'
    daftar_typo = [
        "neria",
        "neriaa",
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


def penerjemah_waktu_manusia(teks_jam_mentah):
    """Mengubah format waktu manusia menjadi format 24 Jam dengan toleransi tinggi."""
    try:
        komponen = teks_jam_mentah.lower().strip().split()
        if not komponen:
            return None

        waktu_angka = komponen[0]  # "01:00"
        keterangan = komponen[1] if len(komponen) > 1 else ""  # "siang"

        # Memisahkan jam dan menit
        if ":" not in waktu_angka:
            return None

        jam_teks, menit_teks = waktu_angka.split(":")
        jam = int(jam_teks)
        minut = int(menit_teks)

        # Logika konversi berdasarkan kata keterangan
        if jam <= 12:
            if "siang" in keterangan:
                if jam != 12:
                    jam += 12
            elif "sore" in keterangan:
                if jam != 12:
                    jam += 12
            elif "malam" in keterangan:
                if jam == 12:
                    jam = 0
                else:
                    jam += 12
            elif "pagi" in keterangan or "subuh" in keterangan:
                if jam == 12:
                    jam = 0

        # Kembalikan string 24 jam rapi
        return f"{jam:02d}:{minut:02d}"

    except Exception as e:
        # Jika ada error internal, kita bisa intip lewat sini (bisa dihapus kalau sudah lancar)
        # print(f"[DEBUG ERROR]: {e}")
        return None
    
    
def cetak_animasi(teks, kecepatan=0.01):
    """Mencetak teks ke terminal huruf demi huruf seperti efek mengetik."""
    for huruf in teks:
        # Cetak huruf tanpa baris baru
        sys.stdout.write(huruf)
        # Paksa terminal untuk langsung memunculkan huruf tersebut saat itu juga
        sys.stdout.flush()
        # Jeda waktu per huruf (semakin kecil angkanya, semakin cepat)
        time.sleep(kecepatan)
    print()