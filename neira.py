import datetime
import json
import os
import time
import webbrowser
import sys 
from playsound import playsound

# Meng-import fitur-fitur modular Neira
from fitur import utilitas, profil, produktivitas, jadwal, fokus, sistem, cuaca, ai
# PERBAIKAN: Import fungsi chatbot Gemini yang baru
from fitur.ai import ngobrol_santai, analisis_prioritas
# Import komponen GUI dari folder gui
from gui.dashboard import NeiraDashboard, _PrintCapture

# ==================== FITUR REMINDER & SAPAAN ====================
def sapa_user():
    """Fungsi untuk menyapa pengguna berdasarkan waktu saat ini."""
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

def set_reminder(menit):
    """Fungsi untuk menahan program dan memunculkan pengingat suara."""
    detik = menit * 60
    print(f"Baik, aku akan mengingatkanmu dalam {menit} menit.")
    time.sleep(detik)

    print(f"WAKTU HABIS!!!")
    try:
        playsound('alarm.wav')
    except Exception as e:
        print(f"Maaf, aku tidak dapat memainkan suara alarm. Error: {e}")


# ==================== CORE UTAMA BACKEND NEIRA ====================
def proses_perintah_backend(perintah: str) -> str:
    """
    Fungsi ini menggantikan loop 'while True'. 
    Setiap kali kamu klik tombol Kirim di GUI, fungsi ini akan dipanggil sekali.
    """
    perintah_asli = perintah
    perintah = perintah.lower().strip()

    if perintah == "":
        return ""

    # Trik membajak print() agar outputnya dialihkan ke chat bubble GUI
    capture_io = _PrintCapture(None)  # buffer mode, tidak pakai callback
    sys.stdout = capture_io

    try:
        keyword_dikenali = False
        
        if "keluar" in perintah or "dadah" in perintah or "exit" in perintah:
            print("Sampai jumpa lagi! Semangat produktifnya ya.")
            sys.stdout = sys.__stdout__
            return capture_io.get_result()

        # 1. PENCEGATAN TYPO NAMA
        if utilitas.cek_typo_nama(perintah):
            print("Hmm... Mungkin maksudmu 'Neira'? Typo sedikit tuh, hehe.")
            keyword_dikenali = True

        # # 2. FITUR FAVORIT: MENYAPA & MENANYAKAN KABAR
        # elif any(x in perintah for x in ["halo", "hai", "hi", "pagi", "siang", "sore", "malam"]):
        #     sapa_user()
        #     keyword_dikenali = True
            
        elif any(x in perintah for x in ["apa kabar", "bagaimana kabarmu", "kamu apa kabar", "gimana kabarmu"]):
            print("Aku baik-baik aja, kalo kamu gimana?")
            keyword_dikenali = True

        # 3. FITUR UTENSIL: CEK JAM UTAMA & BUKA BROWSER
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
            try:
                menit = int("".join(filter(str.isdigit, perintah)))
                sistem.atur_shutdown_timer(menit)
            except ValueError:
                print("Tolong sebutkan menitnya dengan jelas. Contoh: 'matikan laptop dalam 30 menit'")
            keyword_dikenali = True
        
        elif "batal matikan" in perintah or "batalkan shutdown" in perintah:
            sistem.batalkan_shutdown()
            keyword_dikenali = True

        # 4. SEKTOR PROFIL & MEMORI (DINAMIS)
        elif any(x in perintah for x in ["siapa aku", "ringkas tentangku", "profilku"]):
            profil.ringkas_profil()
            keyword_dikenali = True

        elif perintah.split()[0].endswith("ku"):
            try:
                ABAIKAN = ["aku", "kalau", "waktu", "atau", "buku", "ragu"]
                bagian_depan, isi_data = perintah.split(" ", 1)
                if bagian_depan.endswith("ku") and bagian_depan not in ABAIKAN:
                    kategori = bagian_depan[:-2]
                    if isi_data.strip():
                        profil.simpan_memori(kategori, isi_data.strip())
                        print(f"Sipp! Informasi '{kategori}' kamu berhasil diperbarui menjadi: {isi_data}.")
                        keyword_dikenali = True
                else:
                    # PERBAIKAN: Menggunakan ngobrol_santai bawaan Gemini Flash
                    respons_ai = ngobrol_santai(perintah_asli)
                    print(respons_ai)
                    keyword_dikenali = True
            except ValueError:
                pass

        # 5. SEKTOR TO-DO LIST (PRODUKTIVITAS) - LEBIH LUAS & FLEKSIBEL
        elif "tambah tugas" in perintah:
            tugas_baru = perintah.replace("tambah tugas", "").strip()
            produktivitas.add_tasks(tugas_baru)
            keyword_dikenali = True

        elif any(x in perintah for x in ["lihat tugas", "lihat tugasku", "tugas hari ini"]):
            produktivitas.view_tasks()
            keyword_dikenali = True

        elif "selesai tugas" in perintah or "selesai no" in perintah:
            try:
                nomor = int("".join(filter(str.isdigit, perintah)))
                produktivitas.mark_done(nomor)
            except ValueError:
                print("Tolong masukkan nomor tugas yang valid. Contoh: 'selesai tugas 1'")
            keyword_dikenali = True

        elif "hapus tugas" in perintah or "hapus no" in perintah:
            try:
                nomor = int("".join(filter(str.isdigit, perintah)))
                produktivitas.delete_tasks(nomor)
            except ValueError:
                print("Tolong masukkan nomor tugas yang valid. Contoh: 'hapus tugas 1'")
            keyword_dikenali = True

        # SEKTOR SESI FOKUS (AUTOMATED MULTI-THREADING)
        elif "mulai sesi fokus" in perintah:
            try:
                menit = int("".join(filter(str.isdigit, perintah)))
                fokus.mulai_sesi(menit)
            except ValueError:
                print("Masukkan angka menit yang jelas. Contoh: 'mulai sesi fokus 45 menit'")
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

        # 6. SEKTOR JADWAL HARIAN (QUEST LOG)
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
        
        # SEKTOR INFORMASI INTERNET (CUACA, DLL)
        elif "cuaca hari ini" in perintah or "laporan cuaca kota" in perintah:
            cuaca.cek_cuaca()
            keyword_dikenali = True
        
        # 9. SEKTOR KONSULTASI JADWAL (AI CONTEXT-AWARE)
        elif "rekomendasi tugas" in perintah or "prioritas" in perintah or "analisis jadwal" in perintah:
            # PERBAIKAN: Menggunakan fungsi prioritas Gemini Flash dan mencetaknya langsung
            respons_prioritas = analisis_prioritas(perintah_asli)
            print(respons_prioritas)
            keyword_dikenali = True

        # 10. JALUR AKHIR: CHATBOT UMUM (Jika tidak ada keyword lokal yang cocok)
        else:
            # PERBAIKAN: Menggunakan ngobrol_santai bawaan Gemini Flash
            respons_ai = ngobrol_santai(perintah_asli)
            print(respons_ai)
            keyword_dikenali = True

    except Exception as e:
        print(f"⚠️ Error di sistem backend: {e}")
    finally:
        sys.stdout = sys.__stdout__

    # Mengembalikan semua teks yang di-print tadi ke GUI untuk dijadikan animasi ketik
    return capture_io.get_result()


# ==================== SEKTOR RUNNER UTAMA APLIKASI ====================
if __name__ == "__main__":
    print("🤖 Neira Engine v2.0: Online.")
    print("⚡ Memulai Neira AI Dashboard System...")

    # PERBAIKAN: Hapus baris warmup_neira() karena Gemini Flash tidak butuh loading lokal
    
    app = NeiraDashboard(processor_callback=proses_perintah_backend)
    app.mainloop()