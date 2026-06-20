import datetime
import sys
import os
import webbrowser
import ollama
import wikipediaapi
import threading
from typing import Optional

# Kita kunci path absolut agar db_neira selalu sinkron di satu tempat
DIR_NEIRA = os.path.dirname(os.path.abspath(__file__))
PATH_DB_ABSOLUT = os.path.join(DIR_NEIRA, "neira_data.db")

from database import db
db.DB_FILE = PATH_DB_ABSOLUT

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
def proses_perintah_backend(perintah, session_id):
    """Sistem Backend Neira dengan dukungan penuh Session-ID database."""
    try:
        # Inisialisasi database di awal
        db.inisialisasi_db()
        
        # 1. KELUAR / DADAH
        if "goodbye" in perintah or "bye" in perintah or "exit" in perintah:
            yield "Catch you later, Ian! Stay productive! 🚀"
            return

        # 2. PENCEGATAN TYPO NAMA
        elif "niera" in perintah.lower() or "nera" in perintah.lower():
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

        # 4. JALUR UTAMA LLM + DYNAMIC MULTI-SESSION CONTEXT
        else:
            # FIX BUG 1: Langsung simpan chat user sekarang juga ke dalam session_id aktif
            db.simpan_chat(session_id, "user", perintah)
            
            # Ambil memori profil jangka panjang (Profil Ian)
            data_profil_ian = db.ambil_semua_profil()
            str_konteks_profil = ", ".join([f"{k}: {v}" for k, v in data_profil_ian.items()])
            
            dynamic_system_prompt = system_prompt
            if str_konteks_profil:
                dynamic_system_prompt += f" For your context, here is what you know about Ian: {str_konteks_profil}."
            
            messages_payload = [{'role': 'system', 'content': dynamic_system_prompt}]
            
            # Deteksi Pencarian Web
            if perlu_akses_internet(perintah):
                yield "🌐 *Neira is searching the live web...*\n\n"
                data_internet = ambil_info_internet(perintah)
                yield f"💡 *[Live Web Info]* Found some updates! Let me process this for you...\n\n"
                messages_payload.append({'role': 'user', 'content': f"Here is the real-time web data for your reference:\n{data_internet}"})
            
            # FIX BUG 2: Hanya ambil 20 chat terakhir khusus dari session_id yang aktif!
            riwayat_chat_sqlite = db.ambil_riwayat_terakhir(session_id, limit=20)
            messages_payload.extend(riwayat_chat_sqlite)
            
            # Panggil Ollama
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
                
            # Simpan balasan asisten ke db session terkait
            db.simpan_chat(session_id, "assistant", respons_lengkap_neira)
            
            # FIX BUG 3: Jalankan auto remember di Thread terpisah agar UI gak "Processing" kelamaan
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
        
        raw_json = response['message']['content'].strip().replace("```json", "").replace("```", "")
        fakta_baru = json.loads(raw_json)
        
        for kunci, nilai in fakta_baru.items():
            if nilai: 
                print(f"[SQLITE AUTO-REMEMBER] Saved -> {kunci}: {nilai}")
                db.simpan_profil(kunci, nilai)
                
    except Exception as e:
        print(f"[DEBUG AUTO-REMEMBER ERROR]: {e}")
        
# Tambahkan logika ini di neira.py kamu saat sesi baru terdeteksi
# def buat_ringkasan_judul_ai(teks_user, teks_neira):
#     prompt = f"Ringkas percakapan ini menjadi judul maksimal 3 kata tanpa tanda kutip. User: '{teks_user}' AI: '{teks_neira}'"
#     # Panggil model Qwen kamu secara instan tanpa streaming khusus untuk baris ini
#     judul_singkat = model.generate(prompt)
#     return judul_singkat


if __name__ == "__main__":
    print("🚀 Triggering Neira with PyQt6 Engine... Let's Go!")
    import gui.pyqt_dashboard
    gui.pyqt_dashboard.main()