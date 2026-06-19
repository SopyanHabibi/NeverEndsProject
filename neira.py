import datetime
import sys
import os
import webbrowser
import ollama
import wikipediaapi
from typing import Optional
from playsound import playsound
from database import db

# Fitur-fitur modular Neira
from fitur import utilitas, profil, produktivitas, jadwal, fokus, sistem, cuaca, ai

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

# Memori jangka pendek (Short-term Chat History)
riwayat_obrolan = []

# ==================== FITUR BROWSER HYBRID ====================

def ambil_info_internet(kueri: str) -> str:
    """Mengambil data valid dan terbaru dari Wikipedia untuk bypass pemblokiran Google."""
    try:
        wiki = wikipediaapi.Wikipedia(
            user_agent="NeiraAI_Bot/1.0 (contact: ian@example.com)",
            language="en"
        )
        
        halaman = wiki.page("List of iPhone models")
        print(f"\n[DEBUG] Menembak Wikipedia: {halaman.fullurl}")
        
        if not halaman.exists():
            return "Format data global tidak ditemukan."
            
        teks_wiki = halaman.summary
        potongan_info = teks_wiki[:2000] 
        
        print(f"DEBUG WIKI [1]: {potongan_info[:300]}...") 
        
        blob_teks = "\n--- LIVE WIKIPEDIA KNOWLEDGE DATABASE (YEAR: 2026) ---\n"
        blob_teks += f"Context: {potongan_info}\n"
        blob_teks += (
            "\nCRITICAL SYSTEM INSTRUCTION:\n"
            "1. You are currently operating in the year 2026.\n"
            "2. Your original September 2024 information cutoff is no longer the limit; use the live Wikipedia data provided above to answer any contemporary questions.\n"
            "3. Answer Ian's question directly, clearly, and concisely in English based on this real-time context.\n"
            "4. Maintain a supportive, adaptive, and slightly witty AI personality while ensuring technical accuracy."
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
    global riwayat_obrolan
    
    try:
        # Masukkan chat user saat ini ke riwayat memori
        riwayat_obrolan.append({"role": "user", "content": perintah})
        
        # Batasi memori agar tidak overcapacity (Ingat 20 chat terakhir)
        if len(riwayat_obrolan) > 20:
            riwayat_obrolan = riwayat_obrolan[-20:]
        
        # 1. KELUAR / DADAH
        if "goodbye" in perintah or "bye" in perintah or "exit" in perintah:
            yield "Catch you later, Ian! Stay productive! 🚀"
            return

        # 2. PENCEGATAN TYPO NAMA
        elif utilitas.cek_typo_nama(perintah):
            yield "Hmm... Pretty sure you meant 'Neira'. Just a tiny typo right there, haha."
            return

        elif any(x in perintah for x in ["how are you", "how are you doing", "what's up", "how's it going"]):
            yield "I'm doing great, Ian! How about you? Ready to crush some code?"
            return

        # 3. JAM & SHORTCUT APLIKASI
        elif "what time is it" in perintah or "check time" in perintah or "what time" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            yield f"It's currently {waktu_sekarang}, Ian."
            return

        elif "open google" in perintah:
            yield "Alright, opening Google for you..."
            webbrowser.open("https://www.google.com")
            return

        elif "open youtube" in perintah:
            yield "Sure thing, spinning up YouTube..."
            webbrowser.open("https://www.youtube.com")
            return

        elif "open instagram" in perintah or "open ig" in perintah:
            yield "Opening Instagram... don't get too distracted, haha!"
            webbrowser.open("https://www.Instagram.com/_sop.ayam")
            return

        elif "open chrome" in perintah:
            sistem.buka_aplikasi("chrome")
            return

        elif "open vscode" in perintah or "open vs code" in perintah:
            sistem.buka_aplikasi("vscode")
            return

        elif "open notepad" in perintah:
            sistem.buka_aplikasi("notepad")
            return

        elif "open calculator" in perintah:
            sistem.buka_aplikasi("calc")
            return

        elif "coding mode" in perintah or "time to code" in perintah:
            sistem.buka_workspace("ngoding")
            return

        elif "study mode" in perintah or "time to study" in perintah:
            sistem.buka_workspace("kuliah")
            return

        elif "open folder" in perintah:
            target_folder = perintah.replace("open folder", "").strip()
            if target_folder:
                sistem.buka_folder(target_folder)
            else:
                yield "Which folder do you want to open? Example: 'open folder kuliah'."
            return

        # 4. PROFIL & MEMORI
        elif any(x in perintah for x in ["who am i", "summarize my profile", "my profile"]):
            yield "Fetching your profile summary..."
            yield from profil.ringkas_profil()
            return

        # 5. TO-DO LIST (PRODUKTIVITAS)
        elif "add task" in perintah:
            tugas_baru = perintah.replace("add task", "").strip()
            produktivitas.add_tasks(tugas_baru)
            return

        elif any(x in perintah for x in ["view tasks", "view my tasks", "today's tasks"]):
            produktivitas.view_tasks()
            return

        elif "complete task" in perintah or "complete no" in perintah:
            nomor = _ambil_angka(perintah)
            if nomor is None:
                yield "Please enter a valid task number. Example: 'complete task 1'"
            else:
                produktivitas.mark_done(nomor)
            return

        elif "delete task" in perintah or "delete no" in perintah:
            nomor = _ambil_angka(perintah)
            if nomor is None:
                yield "Please enter a valid task number. Example: 'delete task 1'"
            else:
                produktivitas.delete_tasks(nomor)
            return

        # 6. SESI FOKUS
        elif "start focus session" in perintah:
            menit = _ambil_angka(perintah)
            if menit is None:
                yield "Please enter a clear number of minutes. Example: 'start focus session 45 minutes'"
            else:
                fokus.mulai_sesi(menit)
            return

        elif "cancel session" in perintah or "stop session" in perintah:
            fokus.batalkan_sesi()
            return

        elif "focus session report" in perintah or "view focus session report" in perintah:
            fokus.lihat_statistik_fokus()
            return

        elif "view statistics" in perintah or "statistics" in perintah:
            produktivitas.view_statistics()
            return

        # 7. JADWAL HARIAN
        elif "add schedule" in perintah or ("schedule at" in perintah and "for" in perintah):
            try:
                bagian_jam = perintah.split("at ")[1].split("for ")[0].strip()
                bagian_agenda = perintah.split("for ")[1].strip()
                jadwal.add_jadwal(bagian_jam, bagian_agenda)
            except IndexError:
                yield "Wrong pattern. Example: 'schedule at 01:00 pm for coding'"
            return

        elif any(x in perintah for x in ["what's next", "upcoming schedule"]):
            jadwal.cek_agenda_mendatang()
            return

        elif "view schedule" in perintah:
            yield jadwal.lihat_semua_jadwal()
            return

        # 8. INFORMASI LAINNYA
        elif "weather today" in perintah or "weather report city" in perintah:
            cuaca.cek_cuaca()
            return

        elif "task recommendation" in perintah or "priority" in perintah or "schedule analysis" in perintah:
            for token in ai.analisis_prioritas(perintah):
                yield token
            return
        
        # 9. JALUR UTAMA LLM + DYNAMIC SQLITE CONTEXT INTEGRATION
        else:
            # A. PASTIKAN DATABASE DIINISIALISASI
            db.inisialisasi_db()
            
            # B. KUNCI UTAMA: SIMPAN CHAT USER SEKARANG JUGA (Jangan ditunda!)
            db.simpan_chat("user", perintah)
            
            # Ambil data profil dari SQLite
            data_profil_ian = db.ambil_semua_profil()
            str_konteks_profil = ", ".join([f"{k}: {v}" for k, v in data_profil_ian.items()])
            
            dynamic_system_prompt = system_prompt
            if str_konteks_profil:
                dynamic_system_prompt += f" For your context, here is what you know about Ian: {str_konteks_profil}."
            
            messages_payload = [{'role': 'system', 'content': dynamic_system_prompt}]
            
            # Jalur Cek Internet
            if perlu_akses_internet(perintah):
                yield "🌐 *Neira is searching the live web...*\n\n"
                data_internet = ambil_info_internet(perintah)
                yield f"💡 *[Live Web Info]* Found some updates! Let me process this for you...\n\n"
                messages_payload.append({'role': 'user', 'content': f"Here is the real-time web data for your reference:\n{data_internet}"})
            
            # C. AMBIL RIWAYAT CHAT TERAKHIR (Termasuk chat user yang barusan disimpan!)
            riwayat_chat_sqlite = db.ambil_riwayat_terakhir(limit=20)
            messages_payload.extend(riwayat_chat_sqlite)
            
            # Panggil Ollama Qwen
            response = ollama.chat(
                model='qwen2.5:7b-instruct-q4_K_M',
                messages=messages_payload,
                stream=True
            )
            
            respons_lengkap_neira = ""
            for chunk in response:
                token = chunk['message']['content']
                respons_lengkap_neira += token
                yield token
                
            # Simpan chat asisten ke database
            db.simpan_chat("assistant", respons_lengkap_neira)
            
            # AKALIN DI SINI: Suruh proses pengingat otomatis jalan di "jalur bayangan"
            import threading
            threading.Thread(
                target=neira_auto_remember, 
                args=(perintah, respons_lengkap_neira), 
                daemon=True
            ).start()

    except Exception as e:
        yield f"⚠️ Backend system error: {e}"

def neira_auto_remember(perintah_user: str, jawaban_neira: str):
    """Menyuruh Qwen mendeteksi informasi penting secara otomatis untuk disimpan ke SQLite."""
    import json
    try:
        # Prompt khusus agar Qwen mengekstrak fakta penting dari obrolan dalam format JSON
        prompt_memori = (
            f"Analyze this conversation turn between Ian and you.\n"
            f"Ian said: '{perintah_user}'\n"
            f"You replied: '{jawaban_neira}'\n\n"
            f"CRITICAL: If Ian shared a new personal fact about himself (e.g., his name, age, current project, girlfriend, location, hobby, or bike), "
            f"extract it into a flat JSON object where keys are the specific topics (use underscores for spaces) and values are the facts. "
            f"Example output if Ian says 'I live in Medan': {{\"lokasi\": \"Medan\"}}\n"
            f"If NO new personal information was shared by Ian, strictly reply with an empty object: {{}}\n"
            f"Output ONLY the valid raw JSON object, no extra text, no markdown block."
        )
        
        response = ollama.chat(
            model='qwen2.5:7b-instruct-q4_K_M',
            messages=[{'role': 'user', 'content': prompt_memori}]
        )
        
        # FIX BARIS INI: Menghapus sisa block markdown dengan benar
        raw_json = response['message']['content'].strip().replace("```json", "").replace("```", "")
        fakta_baru = json.loads(raw_json)
        
        # Jika ditemukan ada fakta baru, langsung masukkan ke SQLite!
        for kunci, nilai in fakta_baru.items():
            if nilai: # Pastikan nilainya tidak kosong
                print(f"[SQLITE AUTO-REMEMBER] Saved -> {kunci}: {nilai}")
                db.simpan_profil(kunci, nilai)
                
    except Exception as e:
        print(f"[DEBUG AUTO-REMEMBER ERROR]: {e}")


if __name__ == "__main__":
    print("🚀 Triggering Neira with PyQt6 Engine... Let's Go!")
    import gui.pyqt_dashboard
    gui.pyqt_dashboard.main()