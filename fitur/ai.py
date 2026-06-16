import json
import os
import google.generativeai as genai

# ==========================================
# 🔑 ATUR API KEY GEMINI FLASH KAMU DI SINI
# ==========================================
GOOGLE_API_KEY = "AQ.Ab8RN6KDpDGlnStotDCTZ1FJS7HnHWlUBZk3rusgaAQTVqfUvw"
genai.configure(api_key=GOOGLE_API_KEY)

# PERBAIKAN: Set konfigurasi biar Gemini merespons pendek, padat, dan cepat!
konfigurasi_cepat = genai.types.GenerationConfig(
    # max_output_tokens=250,  # Dibatasi ~2 kalimat pendek biar hemat bandwidth & cepat kirimnya
    temperature=0.7
)

model = genai.GenerativeModel('gemini-3.5-flash')


def muat_database_lokal(hanya_profil=False):
    """Fungsi dinamis untuk mengambil data database berdasarkan kebutuhan"""
    konteks = {}
    
    # Profil selalu dimuat agar Neira tahu nama Ian
    if os.path.exists("database/memori.json"):
        with open("database/memori.json", "r") as f:
            konteks["profil"] = json.load(f)
            
    # Jika hanya_profil=True, abaikan tugas dan jadwal demi menghemat speed chat santai
    if not hanya_profil:
        if os.path.exists("database/todo_list.json"): 
            with open("database/todo_list.json", "r") as f:
                konteks["tugas"] = json.load(f)
                
        if os.path.exists("database/jadwal.json"):
            with open("database/jadwal.json", "r") as f:
                konteks["jadwal"] = json.load(f)
                
    return json.dumps(konteks, indent=2)


def analisis_prioritas(perintah_user):
    """Rekomendasi tugas (Membutuhkan data full tugas & jadwal)"""
    data_sekarang = muat_database_lokal(hanya_profil=False)
    
    prompt = f"""
    Kamu adalah Neira, asisten produktivitas pintar. Berikut adalah data real-time dari database pengguna saat ini:
    {data_sekarang}
    
    Pertanyaan/Perintah Pengguna: "{perintah_user}"
    
    Tugas Anda:
    1. Ambil nama asli pengguna dari data profil. JANGAN PERNAH memanggil dengan sebutan "Kak", panggil langsung 'Ian' dengan akrab!
    2. Analisis tugas yang BELUM selesai.
    3. Berikan rekomendasi urutan mana yang harus dikerjakan duluan beserta alasan singkatnya.
    4. JANGAN gunakan tanda bintang ganda (**) untuk menebalkan teks karena GUI tidak mendukungnya. Gunakan format teks biasa yang rapi.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Neira: Duh Ian, gagal terkoneksi ke Gemini nih. Cek internet atau API Key kamu ya! Error: {e}"


def ngobrol_santai(perintah_user):
    """Fungsi ngobrol kasual SUPER CEPAT (Hanya memuat data profil)"""
    # OPTIMASI: Set True agar tidak perlu membaca & mengirim data todo list/jadwal yang berat
    data_profil = muat_database_lokal(hanya_profil=True)
    
    prompt = f"""
    Kamu adalah Neira, asisten pribadi sekaligus teman ngobrol yang pintar, seru, dan suportif untuk Ian.
    
    Karakter Gayamu Berbicara:
    1. JANGAN GUNAKAN BAHASA BAKU (seperti 'Anda', 'mengapa', 'tetapi'). Itu terlalu kaku!
    2. Gunakan bahasa chat sehari-hari Indonesia yang santai, kasual, dan akrab. Gunakan kata: 'aku', 'kamu', 'iya', 'oke', 'nggak', 'udah', 'lagi apa', 'hehe', 'siap'.
    3. Panggil nama lawan bicaramu langsung dengan 'Ian' (JANGAN PERNAH gunakan kata 'Kak' atau 'Kak Ian').
    4. JANGAN gunakan tanda bintang ganda (**) untuk menebalkan teks.
    5. Jawab dengan ekspresif, asyik, dan nyambung. Tetap jaga respons agar tidak terlalu panjang, TAPI jika Ian sedang mengeluh, sedih, atau pusing, berikan empati dan perhatian yang hangat layaknya teman dekat yang peduli!

    Konteks Profil Pengguna:
    {data_profil}

    Pertanyaan/Obrolan dari Ian: "{perintah_user}"
    
    Respons Anda:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Neira: Duh Ian, koneksiku ke server Gemini keganggu nih. Error: {e}"