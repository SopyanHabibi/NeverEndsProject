import datetime
import sys
import time
import webbrowser
from typing import Optional

from playsound import playsound

# Fitur-fitur modular Neira
from fitur import utilitas, profil, produktivitas, jadwal, fokus, sistem, cuaca, ai

# Komponen GUI
# from gui.pyqt_dashboard import _PrintCapture


# ==================== HELPER ====================
def _ambil_angka(teks: str) -> Optional[int]:
    """Ambil angka pertama dari sebuah string perintah. Return None kalau gak ketemu."""
    digit = "".join(filter(str.isdigit, teks))
    return int(digit) if digit else None


# ==================== FITUR REMINDER & SAPAAN ====================
def sapa_user():
    """Menyapa pengguna berdasarkan waktu saat ini."""
    try:
        data = profil.baca_memori()
        nama_user = data.get("nama", "kamu")
    except Exception:
        nama_user = "kamu"

    jam = datetime.datetime.now().hour
    if jam < 12:
        print(f"Halo {nama_user}! Semangat produktifnya hari ini.")
    elif 12 <= jam < 18:
        print(f"Halo {nama_user}! Ada yang bisa aku bantu?")
    else:
        print(f"Halo {nama_user}! Jangan lupa istirahat yang cukup ya.")


def set_reminder(menit: int):
    """Menahan program lalu memunculkan pengingat suara setelah waktu berlalu."""
    print(f"Baik, aku akan mengingatkanmu dalam {menit} menit.")
    time.sleep(menit * 60)

    print("WAKTU HABIS!!!")
    try:
        playsound("alarm.wav")
    except Exception as e:
        print(f"Maaf, aku tidak dapat memainkan suara alarm. Error: {e}")


# ==================== CORE UTAMA BACKEND NEIRA ====================
def proses_perintah_backend(perintah: str):
    """
    Menggantikan loop 'while True'.
    Setiap kali tombol Kirim di GUI diklik, fungsi ini dipanggil sekali.

    Generator: untuk fitur lokal (print-based) hasilnya dikumpulkan lalu
    di-yield satu kali di akhir. Untuk respons AI (ngobrol_santai /
    analisis_prioritas), token di-relay langsung dari fitur/ai.py — jadi
    kalau ada masalah spasi pada balasan AI, sumbernya ada di sana, bukan
    di file ini.
    """
    perintah_asli = perintah
    perintah = perintah.lower().strip()

    if perintah == "":
        return

    # Membajak print() agar outputnya dialihkan ke chat bubble GUI
    # capture_io = _PrintCapture(None)  # buffer mode, tidak pakai callback
    # sys.stdout = capture_io

    try:
        keyword_dikenali = False

        # 1. KELUAR / DADAH
        if "keluar" in perintah or "dadah" in perintah or "exit" in perintah:
            print("Sampai jumpa lagi! Semangat produktifnya ya.")
            keyword_dikenali = True

        # 2. PENCEGATAN TYPO NAMA
        elif utilitas.cek_typo_nama(perintah):
            print("Hmm... Mungkin maksudmu 'Neira'? Typo sedikit tuh, hehe.")
            keyword_dikenali = True

        # # 3. MENYAPA & MENANYAKAN KABAR (nonaktif sementara)
        # elif any(x in perintah for x in ["halo", "hai", "hi", "pagi", "siang", "sore", "malam"]):
        #     sapa_user()
        #     keyword_dikenali = True

        elif any(x in perintah for x in ["apa kabar", "bagaimana kabarmu", "kamu apa kabar", "gimana kabarmu"]):
            print("Aku baik-baik aja, kalo kamu gimana?")
            keyword_dikenali = True

        # 4. UTILITAS: JAM & SHORTCUT APLIKASI/BROWSER
        elif "jam berapa" in perintah or "cek jam" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            print(f"Sekarang jam {waktu_sekarang}.")
            keyword_dikenali = True

        elif "buka google" in perintah:
            print("Okeyy, membuka Google di browsermu...")
            webbrowser.open("https://www.google.com")
            keyword_dikenali = True

        elif "buka youtube" in perintah:
            print("Okeyy, membuka YouTube...")
            webbrowser.open("https://www.youtube.com")
            keyword_dikenali = True

        elif "buka instagram" in perintah or "buka ig" in perintah:
            print("Okeyy, membuka Instagram...")
            webbrowser.open("https://www.Instagram.com/_sop.ayam")
            keyword_dikenali = True

        elif "buka chrome" in perintah:
            sistem.buka_aplikasi("chrome")
            keyword_dikenali = True

        elif "buka vscode" in perintah or "buka vs code" in perintah:
            sistem.buka_aplikasi("vscode")
            keyword_dikenali = True

        elif "buka notepad" in perintah:
            sistem.buka_aplikasi("notepad")
            keyword_dikenali = True

        elif "buka kalkulator" in perintah:
            sistem.buka_aplikasi("calc")
            keyword_dikenali = True

        elif "mode ngoding" in perintah or "waktunya ngoding" in perintah:
            sistem.buka_workspace("ngoding")
            keyword_dikenali = True

        elif "mode kuliah" in perintah or "waktunya belajar" in perintah:
            sistem.buka_workspace("kuliah")
            keyword_dikenali = True

        elif "buka folder" in perintah:
            target_folder = perintah.replace("buka folder", "").strip()
            if target_folder:
                sistem.buka_folder(target_folder)
            else:
                print("Folder apa yang mau dibuka? Contoh: 'buka folder kuliah' atau 'buka folder project'.")
            keyword_dikenali = True

        elif "matikan laptop dalam" in perintah or "matikan pc dalam" in perintah:
            menit = _ambil_angka(perintah)
            if menit is None:
                print("Tolong sebutkan menitnya dengan jelas. Contoh: 'matikan laptop dalam 30 menit'")
            else:
                sistem.atur_shutdown_timer(menit)
            keyword_dikenali = True

        elif "batal matikan" in perintah or "batalkan shutdown" in perintah:
            sistem.batalkan_shutdown()
            keyword_dikenali = True

        # 5. PROFIL & MEMORI (DINAMIS)
        elif any(x in perintah for x in ["siapa aku", "ringkas tentangku", "profilku"]):
            profil.ringkas_profil()
            keyword_dikenali = True

        elif perintah.split()[0].endswith("ku"):
            ABAIKAN = ["aku", "kalau", "waktu", "atau", "buku", "ragu"]
            try:
                bagian_depan, isi_data = perintah.split(" ", 1)
            except ValueError:
                bagian_depan, isi_data = perintah, ""

            if bagian_depan.endswith("ku") and bagian_depan not in ABAIKAN and isi_data.strip():
                kategori = bagian_depan[:-2]
                profil.simpan_memori(kategori, isi_data.strip())
                print(f"Sipp! Informasi '{kategori}' kamu berhasil diperbarui menjadi: {isi_data}.")
                keyword_dikenali = True
            else:
                for token in ai.ngobrol_santai(perintah_asli):
                    yield token
                keyword_dikenali = True

        # 6. TO-DO LIST (PRODUKTIVITAS)
        elif "tambah tugas" in perintah:
            tugas_baru = perintah.replace("tambah tugas", "").strip()
            produktivitas.add_tasks(tugas_baru)
            keyword_dikenali = True

        elif any(x in perintah for x in ["lihat tugas", "lihat tugasku", "tugas hari ini"]):
            produktivitas.view_tasks()
            keyword_dikenali = True

        elif "selesai tugas" in perintah or "selesai no" in perintah:
            nomor = _ambil_angka(perintah)
            if nomor is None:
                print("Tolong masukkan nomor tugas yang valid. Contoh: 'selesai tugas 1'")
            else:
                produktivitas.mark_done(nomor)
            keyword_dikenali = True

        elif "hapus tugas" in perintah or "hapus no" in perintah:
            nomor = _ambil_angka(perintah)
            if nomor is None:
                print("Tolong masukkan nomor tugas yang valid. Contoh: 'hapus tugas 1'")
            else:
                produktivitas.delete_tasks(nomor)
            keyword_dikenali = True

        # 7. SESI FOKUS (MULTI-THREADING)
        elif "mulai sesi fokus" in perintah:
            menit = _ambil_angka(perintah)
            if menit is None:
                print("Masukkan angka menit yang jelas. Contoh: 'mulai sesi fokus 45 menit'")
            else:
                fokus.mulai_sesi(menit)
            keyword_dikenali = True

        elif "batalkan sesi" in perintah or "stop sesi" in perintah:
            fokus.batalkan_sesi()
            keyword_dikenali = True

        elif "laporan sesi fokus" in perintah or "lihat laporan sesi fokus" in perintah:
            fokus.lihat_statistik_fokus()
            keyword_dikenali = True

        elif "lihat statistik" in perintah or "statistik" in perintah:
            produktivitas.view_statistics()
            keyword_dikenali = True

        # 8. JADWAL HARIAN (QUEST LOG)
        elif "tambah jadwal" in perintah or ("jadwal jam" in perintah and "agenda" in perintah):
            try:
                bagian_jam = perintah.split("jam ")[1].split("agenda ")[0].strip()
                bagian_agenda = perintah.split("agenda ")[1].strip()
                jadwal.add_jadwal(bagian_jam, bagian_agenda)
            except IndexError:
                print("Pola salah. Contoh: 'jadwal jam 01:00 siang agenda ngoding'")
            keyword_dikenali = True

        elif any(x in perintah for x in ["apa kegiatan nanti", "jadwal nanti"]):
            jadwal.cek_agenda_mendatang()
            keyword_dikenali = True

        elif "lihat jadwal" in perintah:
            jadwal.lihat_semua_jadwal()
            keyword_dikenali = True

        # 9. INFORMASI INTERNET (CUACA, DLL)
        elif "cuaca hari ini" in perintah or "laporan cuaca kota" in perintah:
            cuaca.cek_cuaca()
            keyword_dikenali = True

        # 10. KONSULTASI JADWAL (AI CONTEXT-AWARE)
        elif "rekomendasi tugas" in perintah or "prioritas" in perintah or "analisis jadwal" in perintah:
            # analisis_prioritas menghasilkan generator, alirkan langsung tokennya
            for token in ai.analisis_prioritas(perintah_asli):
                yield token
            keyword_dikenali = True

        # 11. JALUR AKHIR: CHATBOT UMUM
        else:
            for token in ai.ngobrol_santai(perintah_asli):
                yield token
            keyword_dikenali = True

    except Exception as e:
        print(f"⚠️ Error di sistem backend: {e}")
    finally:
        sys.stdout = sys.__stdout__

    # Kembalikan semua teks yang di-print tadi ke GUI untuk dijadikan animasi ketik
    # if keyword_dikenali and capture_io.get_result():
    #     yield capture_io.get_result()


# ==================== RUNNER UTAMA APLIKASI ====================
if __name__ == "__main__":
    print("🚀 Memicu Neira dengan Engine PyQt6... Let's Go!")

    import gui.pyqt_dashboard
    gui.pyqt_dashboard.main()