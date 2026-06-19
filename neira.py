import datetime
import sys
import time
import webbrowser
import ollama
import requests
import re
import html
import os
import wikipediaapi
from typing import Optional
from playsound import playsound
from googlesearch import search
# Fitur-fitur modular Neira
from fitur import utilitas, profil, produktivitas, jadwal, fokus, sistem, cuaca, ai

# Komponen GUI
# from gui.pyqt_dashboard import _PrintCapture

# System prompt kasual berbahasa Inggris 
system_prompt = (
    "You are Neira, Ian's chill, brilliant, and tech-savvy personal AI assistant. "
    "You're a total expert in IT, cybersecurity, and networking. Keep the vibe casual, "
    "friendly, and laid-back—like a smart coding buddy. Avoid sounding like a stiff, "
    "overly formal robot. Speak strictly and exclusively in English. "
    "If internet search results are provided to you, incorporate them naturally into your "
    "response to give Ian the most accurate, up-to-date information for 2026. Always keep your "
    "answers punchy, natural, and highly efficient. Always address him as 'Ian'."
)


# ==================== FITUR BROWSER HYBRID (DIUPDATE) ====================
# ==================== FITUR BROWSER HYBRID (VERSI PORTAL BERITA) ====================

def ambil_info_internet(kueri: str) -> str:
    """Mengambil data valid dan terbaru dari Wikipedia untuk bypass pemblokiran Google."""
    try:
        # Inisialisasi Wikipedia dengan User-Agent formal agar disetujui server
        wiki = wikipediaapi.Wikipedia(
            user_agent="NeiraAI_Bot/1.0 (contact: ian@example.com)",
            language="en"
        )
        
        # Kita langsung tembak halaman rangkuman sejarah iPhone yang super lengkap
        halaman = wiki.page("List of iPhone models")
        
        print(f"\n[DEBUG] Menembak Wikipedia: {halaman.fullurl}")
        
        if not halaman.exists():
            return "Format data global tidak ditemukan."
            
        # Ambil ringkasan teks dari halaman tersebut
        teks_wiki = halaman.summary
        
        # Ambil juga bagian tabel/paragraf bawah yang biasanya berisi lini masa model terbaru
        # Kita potong teksnya agar pas dengan context window LLM lokal
        potongan_info = teks_wiki[:2000] 
        
        # PRINT KE TERMINAL BIAR IAN BISA LIHAT DATA ASLINYA
        print(f"DEBUG WIKI [1]: {potongan_info[:300]}...") 
        
        blob_teks = "\n--- LIVE WIKIPEDIA KNOWLEDGE DATABASE (YEAR: 2026) ---\n"
        blob_teks += f"Context: {potongan_info}\n"
        blob_teks += (
            "\nCRITICAL INSTRUCTION: You are currently in the year 2026. "
            "Look closely at the iPhone list. iPhone 15 is NOT the latest anymore. "
            "Answer Ian's question using the newer models mentioned in the text above!"
        )
        return blob_teks
        
    except Exception as e:
        print(f"[DEBUG] Wikipedia Error: {e}")
        return f"Failed to fetch Wikipedia data. Error: {e}"

def perlu_akses_internet(teks: str) -> bool:
    """Mengecek apakah perintah membutuhkan info up-to-date atau di atas cutoff."""
    kata_kunci = [
        "latest", "newest", "current", "news", "update", "released", "price",
        "sekarang", "terbaru", "rilis", "harga", "berita", "skandal", "iphone", 
        "apple", "2025", "2026", "vs", "who is", "what is happening"
    ]
    return any(kata in teks.lower() for kata in kata_kunci)



# ==================== HELPER ====================
def _ambil_angka(teks: str) -> Optional[int]:
    """Ambil angka pertama dari sebuah string perintah."""
    digit = "".join(filter(str.isdigit, teks))
    return int(digit) if digit else None

# ==================== CORE UTAMA BACKEND NEIRA ====================
def proses_perintah_backend(perintah):
    perintah_asli = perintah 
    
    try:
        # 1. KELUAR / DADAH
        if "keluar" in perintah or "dadah" in perintah or "exit" in perintah:
            yield "Catch you later, Ian! Stay productive! 🚀"
            return

        # 2. PENCEGATAN TYPO NAMA
        elif utilitas.cek_typo_nama(perintah):
            yield "Hmm... Pretty sure you meant 'Neira'. Just a tiny typo right there, haha."
            return

        elif any(x in perintah for x in ["apa kabar", "bagaimana kabarmu", "kamu apa kabar", "gimana kabarmu"]):
            yield "I'm doing great, Ian! How about you? Ready to crush some code?"
            return

        # 4. UTILITAS: JAM & SHORTCUT APLIKASI/BROWSER
        elif "jam berapa" in perintah or "cek jam" in perintah or "what time" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            yield f"It's currently {waktu_sekarang}, Ian."
            return

        elif "buka google" in perintah:
            yield "Alright, opening Google for you..."
            webbrowser.open("https://www.google.com")
            return

        elif "buka youtube" in perintah:
            yield "Sure thing, spinning up YouTube..."
            webbrowser.open("https://www.youtube.com")
            return

        elif "buka instagram" in perintah or "buka ig" in perintah:
            yield "Opening Instagram... don't get too distracted, haha!"
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
                yield "Which folder do you want to open? Example: 'buka folder kuliah'."
            return

        # 5. PROFIL & MEMORI (DINAMIS)
        elif any(x in perintah for x in ["siapa aku", "ringkas tentangku", "profilku", "who am i"]):
            yield "Fetching your profile summary..."
            profil.ringkas_profil()
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

        # 11. JALUR AKHIR: INTEGRASI HYBRID LLM LOKAL OLLAMA + WEB SEARCH (DI-FORCED)
        else:
            messages_payload = [{'role': 'system', 'content': system_prompt}]
            
            # CEK JALUR HYBRID: Apakah butuh browsing internet?
            if perlu_akses_internet(perintah):
                yield "🌐 *Neira is searching the live web...*\n\n"
                data_internet = ambil_info_internet(perintah)
                
                # JALUR PAKSA: Kita bocorkan ringkasan internet langsung ke bubble chat Ian
                yield f"💡 *[Live Web Info]* Found some updates! Let me process this for you...\n\n"
                
                # Masukkan hasil pencarian internet sebagai data user agar Qwen terpaksa baca
                messages_payload.append({'role': 'user', 'content': f"Here is the real-time web data for your reference:\n{data_internet}"})
            
            # Gabungkan dengan perintah user yang asli
            messages_payload.append({'role': 'user', 'content': perintah})
            
            # Panggil Qwen2.5 secara lokal
            response = ollama.chat(
                model='qwen2.5:7b-instruct-q4_K_M',
                messages=messages_payload,
                stream=True
            )
            for chunk in response:
                yield chunk['message']['content']

    except Exception as e:
        yield f"⚠️ Backend system error: {e}"

if __name__ == "__main__":
    print("🚀 Triggering Neira with PyQt6 Engine... Let's Go!")
    import gui.pyqt_dashboard
    gui.pyqt_dashboard.main()

    # Kembalikan semua teks yang di-print tadi ke GUI untuk dijadikan animasi ketik
    # if keyword_dikenali and capture_io.get_result():
    #     yield capture_io.get_result()


# ==================== RUNNER UTAMA APLIKASI ====================
if __name__ == "__main__":
    print("🚀 Memicu Neira dengan Engine PyQt6... Let's Go!")

    import gui.pyqt_dashboard
    gui.pyqt_dashboard.main()