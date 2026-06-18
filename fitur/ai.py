import json
import os
import requests

def muat_nama_user():
    """Hanya mengambil nama user dari memori lokal agar prompt ringan"""
    if os.path.exists("database/memori.json"):
        try:
            with open("database/memori.json", "r") as f:
                data = json.load(f)
                return data.get("nama", "Ian")
        except:
            return "Ian"
    return "Ian"

def panggil_ollama_endpoint(prompt_lengkap):
    """Fungsi inti untuk berkomunikasi dengan aplikasi Ollama di laptopmu dengan kontrol emosi AI"""
    url = "http://localhost:11434/api/generate"
    
    # KUNCI PENJINAK: Menambahkan pengaturan parameter kontrol (options) agar teks waras & teratur
    payload = {
        "model": "qwen2.5:7b-instruct-q4_K_M",  # Menggunakan model andalanmu!
        "prompt": prompt_lengkap,
        "stream": True,
        "options": {
            "temperature": 0.5,     # Menurunkan keacakan kata (Biar bahasanya waras dan teratur)
            "top_p": 0.85,          # Membatasi pilihan variasi token agar tetap logis
            "repeat_penalty": 1.25  # Rem tangan otomatis biar ga terjadi glitch repetisi kata ga jelas
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30, stream=True)
        if response.status_code == 200:
            # Baca respons baris demi baris saat Ollama mengirimkannya
            for line in response.iter_lines():
                if line:
                    data_json = json.loads(line.decode('utf-8'))
                    token = data_json.get("response", "")
                    yield token  # Kirim token/kata ini langsung ke GUI saat itu juga
        else:
            yield f"Waduh, server Ollama error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        yield f"Ian, aplikasi Ollama belum dinyalain tuh!"
    except Exception as e:
        yield f"Ada kendala teknis: {e}"

def ngobrol_santai(perintah_user):
    """Fungsi ngobrol kasual yang ramah dan berempati via Qwen2.5"""
    nama_ian = muat_nama_user()
    
    prompt = f"""
    Kamu adalah Neira, asisten pribadi sekaligus sahabat dekat Ian yang pintar, seru, dan suportif.
    
    Aturan Gayamu Berbicara:
    1. JANGAN GUNAKAN BAHASA BAKU (seperti 'Anda', 'mengapa', 'tetapi'). Itu terlalu kaku!
    2. Gunakan bahasa chat sehari-hari Indonesia yang santai, kasual, dan akrab. Gunakan kata: 'aku', 'kamu', 'iya', 'oke', 'nggak', 'udah', 'lagi apa', 'hehe', 'siap'.
    3. Panggil nama lawan bicaramu langsung dengan 'Ian'. JANGAN PERNAH gunakan kata 'Kak' atau 'Kak Ian'.
    4. JANGAN gunakan tanda bintang ganda (**) untuk menebalkan teks karena GUI tidak mendukungnya.
    5. Jawab dengan ekspresif, cerdas, dan nyambung. Jika Ian sedang mengeluh, pusing, atau sedih, berikan perhatian hangat dan empati layaknya teman dekat yang peduli. Tetap jaga jawaban agar padat dan tidak terlalu bertele-tele.

    Nama Temanmu: {nama_ian}
    Chat dari Ian: "{perintah_user}"
    
    Respons Anda:
    """
    yield from panggil_ollama_endpoint(prompt)

def analisis_prioritas(perintah_user):
    """Fungsi analisis tugas khusus menggunakan kecerdasan Qwen2.5"""
    nama_ian = muat_nama_user()
    
    # Ambil data tugas mentah jika ada untuk dijadikan konteks sederhana
    tugas_mentah = ""
    if os.path.exists("database/todo_list.json"):
        try:
            with open("database/todo_list.json", "r") as f:
                tugas_mentah = f.read()
        except:
            pass

    prompt = f"""
    Kamu adalah Neira, asisten produktivitas. Analisis daftar tugas berikut untuk Ian.
    
    Data Tugas Saat Ini:
    {tugas_mentah if tugas_mentah else "Tidak ada tugas terdaftar."}
    
    Pertanyaan Ian: "{perintah_user}"
    
    Tugas Anda:
    1. Sapa Ian dengan akrab (JANGAN panggil 'Kak').
    2. Berikan rekomendasi urutan mana tugas yang harus dikerjakan duluan beserta alasan singkatnya.
    3. Gunakan format teks biasa yang rapi tanpa tanda bintang ganda (**).
    
    Respons Anda:
    """
    return panggil_ollama_endpoint(prompt)

def warmup_neira():
    """Fungsi opsional untuk memicu loading awal model ke RAM"""
    try:
        requests.post("http://localhost:11434/api/generate", 
                      json={"model": "qwen2.5:7b-instruct-q4_K_M", "prompt": "hi", "stream": False}, 
                      timeout=5)
    except:
        pass