import datetime
import sys
import time
import webbrowser
import ollama
from typing import Optional

from playsound import playsound

# Fitur-fitur modular Neira
from fitur import utilitas, profil, produktivitas, jadwal, fokus, sistem, cuaca, ai

# Komponen GUI
# from gui.pyqt_dashboard import _PrintCapture

# Di dalam neira.py, pastikan system prompt-nya kayak gini:
# Contoh kalau mau Neira mode bilingual yang santai tapi tetep keren
system_prompt = (
    "You are Neira, Ian's chill, brilliant, and tech-savvy personal AI assistant. "
    "You're a total expert in IT, cybersecurity, and networking. Keep the vibe casual, "
    "friendly, and laid-back—like a smart coding buddy. Avoid sounding like a stiff, "
    "overly formal robot or a generic corporate AI. Speak strictly and exclusively in English, "
    "and always keep your answers punchy, natural, and highly efficient. Always address him as 'Ian'."
)

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
    yield f"Baik, aku akan mengingatkanmu dalam {menit} menit."
    time.sleep(menit * 60)

    yield "WAKTU HABIS!!!"
    try:
        playsound("alarm.wav")
    except Exception as e:
        yield f"Maaf, aku tidak dapat memainkan suara alarm. Error: {e}"



# ==================== CORE UTAMA BACKEND NEIRA ====================
# ==================== CORE UTAMA BACKEND NEIRA ====================
def proses_perintah_backend(perintah):
    # Pastikan variabel teks asli aman untuk AI umum
    perintah_asli = perintah 
    
    try:
        # 1. KELUAR / DADAH
        if "keluar" in perintah or "dadah" in perintah or "exit" in perintah:
            yield "Sampai jumpa lagi! Semangat produktifnya ya."
            return

        # 2. PENCEGATAN TYPO NAMA
        elif utilitas.cek_typo_nama(perintah):
            yield "Hmm... Mungkin maksudmu 'Neira'? Typo sedikit tuh, hehe."
            return

        elif any(x in perintah for x in ["apa kabar", "bagaimana kabarmu", "kamu apa kabar", "gimana kabarmu"]):
            yield "Aku baik-baik aja, kalo kamu gimana?"
            return

        # 4. UTILITAS: JAM & SHORTCUT APLIKASI/BROWSER
        elif "jam berapa" in perintah or "cek jam" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            yield f"Sekarang jam {waktu_sekarang}."
            return

        elif "buka google" in perintah:
            yield "Okeyy, membuka Google di browsermu..."
            webbrowser.open("https://www.google.com")
            return

        elif "buka youtube" in perintah:
            yield "Okeyy, membuka YouTube..."
            webbrowser.open("https://www.youtube.com")
            return

        elif "buka instagram" in perintah or "buka ig" in perintah:
            yield "Okeyy, membuka Instagram..."
            webbrowser.open("https://www.Instagram.com/_sop.ayam")
            return

        elif "buka chrome" in perintah:
            sistem.buka_aplikasi("chrome")
            return

        elif "buka vscode" in perintah or "buka vs code" in perintah:
            sistem.buka_aplikasi("vscode")
            return

        elif "buka notepad" in perintah:
            sistem.buka_aplikasi("notepad")
            return

        elif "buka kalkulator" in perintah:
            sistem.buka_aplikasi("calc")
            return

        elif "mode ngoding" in perintah or "waktunya ngoding" in perintah:
            sistem.buka_workspace("ngoding")
            return

        elif "mode kuliah" in perintah or "waktunya belajar" in perintah:
            sistem.buka_workspace("kuliah")
            return

        elif "buka folder" in perintah:
            target_folder = perintah.replace("buka folder", "").strip()
            if target_folder:
                sistem.buka_folder(target_folder)
            else:
                yield "Folder apa yang mau dibuka? Contoh: 'buka folder kuliah' atau 'buka folder project'."
            return

        elif "matikan laptop dalam" in perintah or "matikan pc dalam" in perintah:
            menit = _ambil_angka(perintah)
            if menit is None:
                yield "Tolong sebutkan menitnya dengan jelas. Contoh: 'matikan laptop dalam 30 menit'"
            else:
                sistem.atur_shutdown_timer(menit)
            return

        elif "batal matikan" in perintah or "batalkan shutdown" in perintah:
            sistem.batalkan_shutdown()
            return

        # 5. PROFIL & MEMORI (DINAMIS)
        elif any(x in perintah for x in ["siapa aku", "ringkas tentangku", "profilku"]):
            # Jika profil.ringkas_profil() dulu pakai print, ganti fungsinya atau tampung teksnya ke yield
            yield "Menampilkan ringkasan profilmu..."
            profil.ringkas_profil()
            return

        elif perintah.split()[0].endswith("ku"):
            ABAIKAN = ["aku", "kalau", "waktu", "atau", "buku", "ragu"]
            try:
                bagian_depan, isi_data = perintah.split(" ", 1)
            except ValueError:
                bagian_depan, isi_data = perintah, ""

            if bagian_depan.endswith("ku") and bagian_depan not in ABAIKAN and isi_data.strip():
                kategori = bagian_depan[:-2]
                profil.simpan_memori(kategori, isi_data.strip())
                yield f"Sipp! Informasi '{kategori}' kamu berhasil diperbarui menjadi: {isi_data}."
                return

        # 6. TO-DO LIST (PRODUKTIVITAS)
        elif "tambah tugas" in perintah:
            tugas_baru = perintah.replace("tambah tugas", "").strip()
            produktivitas.add_tasks(tugas_baru)
            return

        elif any(x in perintah for x in ["lihat tugas", "lihat tugasku", "tugas hari ini"]):
            produktivitas.view_tasks()
            return

        elif "selesai tugas" in perintah or "selesai no" in perintah:
            nomor = _ambil_angka(perintah)
            if nomor is None:
                yield "Tolong masukkan nomor tugas yang valid. Contoh: 'selesai tugas 1'"
            else:
                produktivitas.mark_done(nomor)
            return

        elif "hapus tugas" in perintah or "hapus no" in perintah:
            nomor = _ambil_angka(perintah)
            if nomor is None:
                yield "Tolong masukkan nomor tugas yang valid. Contoh: 'hapus tugas 1'"
            else:
                produktivitas.delete_tasks(nomor)
            return

        # 7. SESI FOKUS
        elif "mulai sesi fokus" in perintah:
            menit = _ambil_angka(perintah)
            if menit is None:
                yield "Masukkan angka menit yang jelas. Contoh: 'mulai sesi fokus 45 menit'"
            else:
                fokus.mulai_sesi(menit)
            return

        elif "batalkan sesi" in perintah or "stop sesi" in perintah:
            fokus.batalkan_sesi()
            return

        elif "laporan sesi fokus" in perintah or "lihat laporan sesi fokus" in perintah:
            fokus.lihat_statistik_fokus()
            return

        elif "lihat statistik" in perintah or "statistik" in perintah:
            produktivitas.view_statistics()
            return

        # 8. JADWAL HARIAN
        elif "tambah jadwal" in perintah or ("jadwal jam" in perintah and "agenda" in perintah):
            try:
                bagian_jam = perintah.split("jam ")[1].split("agenda ")[0].strip()
                bagian_agenda = perintah.split("agenda ")[1].strip()
                jadwal.add_jadwal(bagian_jam, bagian_agenda)
            except IndexError:
                yield "Pola salah. Contoh: 'jadwal jam 01:00 siang agenda ngoding'"
            return

        elif any(x in perintah for x in ["apa kegiatan nanti", "jadwal nanti"]):
            jadwal.cek_agenda_mendatang()
            return

        elif "lihat jadwal" in perintah:
            jadwal.lihat_semua_jadwal()
            return

        # 9. INFORMASI INTERNET
        elif "cuaca hari ini" in perintah or "laporan cuaca kota" in perintah:
            cuaca.cek_cuaca()
            return

        # 10. KONSULTASI JADWAL
        elif "rekomendasi tugas" in perintah or "prioritas" in perintah or "analisis jadwal" in perintah:
            for token in ai.analisis_prioritas(perintah_asli):
                yield token
            return

        # 11. JALUR AKHIR: JIKA TIDAK ADA KEYWORD NYANGKUT -> OPER KE LLM LOKAL OLLAMA (DENGAN SYSTEM PROMPT)
        else:
            import ollama
            response = ollama.chat(
                model='qwen2.5:7b-instruct-q4_K_M',
                messages=[
                    {'role': 'system', 'content': system_prompt}, # Memanggil variabel system_prompt atas
                    {'role': 'user', 'content': perintah}
                ],
                stream=True
            )
            for chunk in response:
                yield chunk['message']['content']

    except Exception as e:
        yield f"⚠️ Error di sistem backend: {e}"
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