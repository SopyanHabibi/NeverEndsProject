import datetime
import json
import os
import time
import webbrowser
from playsound import playsound

# Meng-import fitur-fitur modular Neira
from fitur import utilitas, profil, produktivitas, jadwal, fokus, sistem

# ==================== FITUR KELOLA TERMINAL & REMINDER ====================
def bersihkan_terminal():
    """Membersihkan layar terminal biar rapi."""
    os.system('cls' if os.name == 'nt' else 'clear')

def sapa_user():
    """Fungsi untuk menyapa pengguna berdasarkan waktu saat ini."""
    try:
        data = profil.baca_memori()  
        nama_user = data.get("nama", "kamu")
    except Exception:
        nama_user = "kamu"

    jam = datetime.datetime.now().hour
    if jam < 12:
        print(f"Neira: Halo {nama_user}! Semangat produktifnya hari ini.")
    elif 12 <= jam < 18:
        print(f"Neira: Halo {nama_user}! Ada yang bisa aku bantu?")
    else:
        print(f"Neira: Halo {nama_user}! Jangan lupa istirahat yang cukup ya.")


def set_reminder(menit):
    """Fungsi untuk menahan program dan memunculkan pengingat suara."""
    detik = menit * 60
    print(f"Neira: Baik, aku akan mengingatkanmu dalam {menit} menit.")
    time.sleep(detik)

    print(f"Neira: WAKTU HABIS!!!")
    try:
        playsound('alarm.wav')
    except Exception as e:
        print(f"Neira: Maaf, aku tidak dapat memainkan suara alarm. Error: {e}")


# ==================== CORE UTAMA NEIRA ====================
def neira():
    bersihkan_terminal()
    # Ambil nama user untuk sapaan pembuka pertama kali
    try:
        data_user = profil.baca_memori()
        nama_ksatria = data_user.get("nama", "kamu")
    except Exception:
        nama_ksatria = "kamu"

    # --- OUTPUT BARU SAAT PERTAMA KALI DIJALANKAN ---
    print(f"🤖 Neira Engine v2.0: Online.")
    print(f"⚙️  Systems: Semua fitur modular berhasil dimuat, {nama_ksatria}.")
    print("------------------------------------------------------------------")

    while True:
        perintah = input("\nKamu: ").lower().strip()

        if "keluar" in perintah or "dadah" in perintah or "exit" in perintah:
            print("Neira: Sampai jumpa lagi! Semangat produktifnya ya.")
            break
        if perintah == "":
            continue

        keyword_dikenali = False

        # 1. PENCEGATAN TYPO NAMA
        if utilitas.cek_typo_nama(perintah):
            print("Neira: Hmm... Mungkin maksudmu 'Neira'? Typo sedikit tuh, hehe.")
            keyword_dikenali = True
            continue

        # 2. FITUR FAVORIT: MENYAPA & MENANYAKAN KABAR
        if any(x in perintah for x in ["halo", "hai", "hi", "pagi", "siang", "sore", "malam"]):
            sapa_user()
            keyword_dikenali = True
            continue
            
        elif any(x in perintah for x in ["apa kabar", "bagaimana kabarmu", "kamu apa kabar", "gimana kabarmu"]):
            print("Neira: Aku baik-baik aja, kalo kamu gimana?")
            keyword_dikenali = True
            continue

        # 3. FITUR UTENSIL: CEK JAM UTAMA & BUKA BROWSER
        elif "jam berapa" in perintah or "cek jam" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            print(f"Neira: Sekarang jam {waktu_sekarang}.")
            keyword_dikenali = True
            continue
            
        elif "buka google" in perintah:
            print("Neira: Okeyy, membuka Google di browsermu...")
            webbrowser.open("https://www.google.com")
            keyword_dikenali = True
            continue
            
        elif "buka youtube" in perintah:
            print("Neira: Okeyy, membuka YouTube...")
            webbrowser.open("https://www.youtube.com")
            keyword_dikenali = True

        elif "buka instagram" in perintah or "buka ig" in perintah:
            print("Neira: Okeyy, membuka Instagram...")
            webbrowser.open("https://www.Instagram.com/_sop.ayam")
            keyword_dikenali = True
            continue
        
        elif "buka chrome" in perintah:
            sistem.buka_aplikasi("chrome")
            keyword_dikenali = True
            continue
        
        elif "buka vscode" in perintah or "buka vs code" in perintah:
            sistem.buka_aplikasi("vscode")
            keyword_dikenali = True
            continue
        
        elif "buka notepad" in perintah:
            sistem.buka_aplikasi("notepad")
            keyword_dikenali = True
            continue
            
        elif "buka kalkulator" in perintah:
            sistem.buka_aplikasi("calc")
            keyword_dikenali = True
            continue
        
        elif "mode ngoding" in perintah or "waktunya ngoding" in perintah:
            sistem.buka_workspace("ngoding")
            keyword_dikenali = True
            continue

        elif "mode kuliah" in perintah or "waktunya belajar" in perintah:
            sistem.buka_workspace("kuliah")
            keyword_dikenali = True
            continue
        
        elif "buka folder" in perintah:
            # mengambil kata setelah "buka folder"
            # Contoh: "buka folder kuliah" -> "kuliah"
            target_folder = perintah.replace("buka folder", "").strip()

            if target_folder:
                sistem.buka_folder(target_folder)
            else:
                print("Neira: Folder apa yang mau dibuka? Contoh: 'buka folder kuliah' atau 'buka folder project'.")
                keyword_dikenali = True
                continue

        # 4. SEKTOR PROFIL & MEMORI (DINAMIS)
        if any(x in perintah for x in ["siapa aku", "ringkas tentangku", "profilku"]):
            profil.ringkas_profil()
            keyword_dikenali = True
            continue
        elif "ku " in perintah:
            try:
                bagian_depan, isi_data = perintah.split(" ", 1)
                if bagian_depan.endswith("ku"):
                    kategori = bagian_depan[:-2] 
                    if isi_data.strip():
                        profil.simpan_memori(kategori, isi_data.strip())
                        print(f"Neira: Sipp! Informasi '{kategori}' kamu berhasil diperbarui menjadi: {isi_data}.")
                        keyword_dikenali = True
                        continue
            except ValueError:
                pass

        # 5. SEKTOR TO-DO LIST (PRODUKTIVITAS)
        if "tambah tugas" in perintah:
            tugas_baru = perintah.replace("tambah tugas", "").strip()
            produktivitas.add_tasks(tugas_baru)
            keyword_dikenali = True
            continue
        elif "lihat tugas" in perintah:
            produktivitas.view_tasks()
            keyword_dikenali = True
            continue
        elif "selesai tugas" in perintah or "selesai no" in perintah:
            try:
                # Mengambil nomor tugas (misal: "selesai tugas 2" -> "2")
                nomor = int("".join(filter(str.isdigit, perintah)))
                produktivitas.mark_done(nomor)
            except ValueError:
                print("Neira: Tolong masukkan nomor tugas yang valid. Contoh: 'selesai tugas 1'")
            keyword_dikenali = True
            continue
        elif "hapus tugas" in perintah or "hapus no" in perintah:
            try:
                # Mengambil nomor tugas (misal: "hapus tugas 1" -> "1")
                nomor = int("".join(filter(str.isdigit, perintah)))
                produktivitas.hapus_tugas(nomor)
            except ValueError:
                print("Neira: Tolong masukkan nomor tugas yang valid. Contoh: 'hapus tugas 1'")
            keyword_dikenali = True
            continue
        # SEKTOR SESI FOKUS (AUTOMATED MULTI-THREADING)
        if "mulai sesi fokus" in perintah:
            try:
                menit = int("".join(filter(str.isdigit, perintah)))
                fokus.mulai_sesi(menit)
            except ValueError:
                print("Neira: Masukkan angka menit yang jelas. Contoh: 'mulai sesi fokus 45 menit'")
            keyword_dikenali = True
            continue
            
        elif "batalkan sesi" in perintah or "stop sesi" in perintah:
            fokus.batalkan_sesi()
            keyword_dikenali = True
            continue
            
        elif "laporan sesi fokus" in perintah or "lihat laporan sesi fokus" in perintah:
            fokus.lihat_statistik_fokus()
            keyword_dikenali = True
            continue
        
        elif "lihat statistik" in perintah or "statistik" in perintah:
            produktivitas.view_statistics()
            keyword_dikenali = True
            continue

        # 6. SEKTOR JADWAL HARIAN (QUEST LOG)
        if "tambah jadwal" in perintah or ("jadwal jam" in perintah and "agenda" in perintah):
            try:
                bagian_jam = perintah.split("jam ")[1].split("agenda ")[0].strip()
                bagian_agenda = perintah.split("agenda ")[1].strip()
                jadwal.add_jadwal(bagian_jam, bagian_agenda)
            except IndexError:
                print("Neira: Pola salah. Contoh: 'jadwal jam 01:00 siang agenda ngoding'")
            keyword_dikenali = True
            continue
        elif any(x in perintah for x in ["apa kegiatan nanti", "jadwal nanti"]):
            jadwal.cek_agenda_mendatang()
            keyword_dikenali = True
            continue
        elif "lihat jadwal" in perintah:
            jadwal.lihat_semua_jadwal()
            keyword_dikenali = True
            continue



# Menjalankan assistant
if __name__ == "__main__":
    neira()