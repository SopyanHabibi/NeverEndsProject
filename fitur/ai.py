# fitur/ai.py
import google.generativeai as genai
import json
import os
from fitur import utilitas  # Import modul utilitas untuk memakai fungsi animasi

# Konfigurasi Gemini (Gunakan model 3.5 pilihanmu)
GEMINI_API_KEY = "AQ.Ab8RN6KDpDGlnStotDCTZ1FJS7HnHWlUBZk3rusgaAQTVqfUvw"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash') # Model terupdate yang kamu pakai

def tanya_neira(pertanyaan_user):
    """Fitur Chatbot Umum dengan Efek Mengetik Animasi."""
    print("🧠 Neira sedang berpikir...")
    
    instruksi_kepribadian = (
        "Kamu adalah Neira, sebuah asisten pintar pribadi yang ramah, taktis, dan protektif buatan Ian. "
        "Gunakan bahasa Indonesia yang santai, suportif, kadang panggil dia 'Ian'. Jangan terlalu formal seperti robot. "
        "Jawab pertanyaan berikut dengan jelas dan ringkas:\n\n"
    )
    
    try:
        response = model.generate_content(instruksi_kepribadian + pertanyaan_user)
        
        # --- PERUBAHAN DI SINI: GUNAKAN ANIMASI ---
        print("\n🧠 Neira: ", end="")
        utilitas.cetak_animasi(response.text, kecepatan=0.015)
        print() # Baris baru untuk kerapian prompt berikutnya
        
    except Exception as e:
        print(f"❌ Neira: Gagal terhubung ke otak AI. Error: {e}")

def analisis_prioritas(pertanyaan_user):
    """Fitur Konsultasi RAG dengan Efek Mengetik Animasi untuk output besar."""
    print("🧠 Neira sedang membaca database dan menganalisis jadwalmu...")
    
    FILE_TASKS = "database/tasks.json"
    FILE_JADWAL = "database/jadwal.json"
    
    data_tugas = "Tidak ada tugas tercatat."
    if os.path.exists(FILE_TASKS):
        try:
            with open(FILE_TASKS, "r") as f: data_tugas = json.dumps(json.load(f), indent=2)
        except Exception: pass
            
    data_jadwal = "Tidak ada agenda/jadwal tercatat."
    if os.path.exists(FILE_JADWAL):
        try:
            with open(FILE_JADWAL, "r") as f: data_wal = json.dumps(json.load(f), indent=2)
        except Exception: pass

    prompt_konteks = (
        "Kamu adalah Neira, asisten pribadi Ian. Tugas utamamu adalah membantu Ian mengelola waktu kuliah.\n"
        f"Data tugas:\n{data_tugas}\n\nData jadwal:\n{data_jadwal}\n\n"
        f"Pertanyaan Ian: {pertanyaan_user}\n"
    )
    
    try:
        response = model.generate_content(prompt_konteks)
        
        # --- PERUBAHAN DI SINI: GUNAKAN ANIMASI UNTUK OUTPUT BESAR ---
        print("\n===========================================")
        print("📊 [ANALISIS STRATEGIS NEIRA]:             ")
        print("===========================================")
        utilitas.cetak_animasi(response.text, kecepatan=0.012) # Sedikit lebih cepat untuk teks panjang
        print("===========================================\n")
        
    except Exception as e:
        print(f"❌ Neira: Gagal melakukan analisis cerdas. Error: {e}")