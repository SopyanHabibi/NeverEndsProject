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
    """Fungsi AI untuk GUI (Mengembalikan string utuh)."""
    instruksi_kepribadian = (
        "Kamu adalah Neira, sebuah asisten pintar pribadi yang ramah, taktis, dan protektif buatan Ian. "
        "Gunakan bahasa Indonesia yang santai, suportif, kadang panggil dia 'Ian'. Jangan terlalu formal seperti robot. "
        "Jawab pertanyaan berikut dengan jelas dan ringkas:\n\n"
    )
    try:
        response = model.generate_content(instruksi_kepribadian + pertanyaan_user)
        # KUNCI UTAMA: Kita langsung kembalikan teks utuhnya tanpa di-print!
        return response.text
    except Exception as e:
        return f"❌ Gagal terhubung ke otak AI. Error: {e}"

def muat_database_lokal():
    """Fungsi helper untuk mengambil semua data Neira untuk konteks AI."""
    konteks = {}

    # 1. Ambil data To-Do List
    if os.path.exists("database/tasks.json"): # Sesuaikan path foldermu
        with open("database/tasks.json", "r") as f:
            konteks["tugas"] = json.load(f)
            
    # 2. Ambil data Jadwal/Agenda
    if os.path.exists("database/jadwal.json"):
        with open("database/jadwal.json", "r") as f:
            konteks["jadwal"] = json.load(f)
            
    # 3. Ambil data Profil / Memori Kamu
    if os.path.exists("database/memori.json"):
        with open("database/memori.json", "r") as f:
            konteks["profil"] = json.load(f)
            
    return json.dumps(konteks, indent=2)

def analisis_prioritas(perintah_user):
    """Memberikan rekomendasi tugas berdasarkan data real-time di database"""
    # Ambil kondisi database saat ini
    data_sekarang = muat_database_lokal()
    
    # Susun prompt sistem yang galak/tegas agar AI fokus menganalisis data tersebut
    prompt = f"""
    Kamu adalah Neira, asisten produktivitas pintar. Berikut adalah data real-time dari database pengguna saat ini:
    {data_sekarang}
    
    Pertanyaan/Perintah Pengguna: "{perintah_user}"
    
    Tugas Anda:
    1. Ambil nama asli pengguna dari data profil yang disediakan di database (JANGAN memanggil dengan sebutan "Kak", panggil langsung namanya dengan akrab atau sesuai nama di database!).
    2. Analisis tugas yang BELUM selesai (status belum kelar).
    3. Berikan rekomendasi urutan mana yang harus dikerjakan duluan (Urutkan dari yang paling krusial/penting).
    4. Berikan alasan singkat dan bersemangat kenapa tugas itu harus didahulukan.
    5. JANGAN tampilkan simbol '**' untuk menebalkan teks jika GUI belum siap, atau gunakan format yang rapi saja.
    """
    
    response_ai = model.generate_content(prompt)

    try:
        return response_ai.text
    except AttributeError:
        return response_ai.candidates[0].content.parts[0].text


    
    