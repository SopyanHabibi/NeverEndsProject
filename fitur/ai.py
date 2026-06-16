import json
import os
import requests
import sys
from fitur import utilitas


# ============================================================
# SYSTEM PROMPT NEIRA (dibaca sekali, dipakai di semua request)
# Pendek & padat — tidak perlu panjang, model sudah ngerti
# ============================================================

SYSTEM_PROMPT = (
    "Kamu adalah Neira, asisten pribadi sekaligus teman ngobrol Ian. "
    "Ngomong santai kayak WA-an: pakai 'aku', 'iya', 'oke', 'nggak', 'hehe'. "
    "Panggil 'Ian' langsung, jangan 'Kak'. "
    "Jawab singkat dan ekspresif. "
    "Jangan pakai tanda bintang ganda (**)."
)

SYSTEM_PROMPT_ANALISIS = (
    "Kamu adalah Neira, asisten produktivitas Ian. "
    "Analisis data yang diberikan, rekomendasikan tugas dari yang paling penting, beri alasan singkat. "
    "Panggil 'Ian' langsung, jangan 'Kak'. "
    "Jawaban rapi, tanpa tanda bintang ganda (**)."
)


# ============================================================
# KEYWORD INTENT DETECTION
# ============================================================

KEYWORD_TUGAS = [
    "tugas", "todo", "kerjaan", "prioritas", "deadline", "selesai",
    "belum kelar", "list tugas", "apa aja yang", "yang harus"
]

KEYWORD_JADWAL = [
    "jadwal", "agenda", "besok", "hari ini", "minggu ini", "kapan",
    "jam berapa", "event", "kegiatan", "acara"
]

KEYWORD_PROFIL = [
    "profil", "memori", "tentang aku", "data aku", "siapa aku",
    "ingat ga", "kamu tau ga", "info aku"
]


def deteksi_intent(perintah_user: str) -> dict:
    """Deteksi intent dari input user tanpa load database atau panggil AI."""
    teks = perintah_user.lower()

    butuh_tugas  = any(k in teks for k in KEYWORD_TUGAS)
    butuh_jadwal = any(k in teks for k in KEYWORD_JADWAL)
    butuh_profil = any(k in teks for k in KEYWORD_PROFIL)
    butuh_db     = butuh_tugas or butuh_jadwal or butuh_profil

    return {
        "butuh_db"    : butuh_db,
        "butuh_tugas" : butuh_tugas,
        "butuh_jadwal": butuh_jadwal,
        "butuh_profil": butuh_profil,
    }


# ============================================================
# DATABASE LOADER (SELECTIVE)
# ============================================================

def muat_database_lokal(intent: dict) -> str:
    """Load hanya file JSON yang dibutuhkan berdasarkan intent."""
    konteks = {}

    if intent.get("butuh_tugas") and os.path.exists("database/todo_list.json"):
        with open("database/todo_list.json", "r") as f:
            konteks["tugas"] = json.load(f)

    if intent.get("butuh_jadwal") and os.path.exists("database/jadwal.json"):
        with open("database/jadwal.json", "r") as f:
            konteks["jadwal"] = json.load(f)

    if intent.get("butuh_profil") and os.path.exists("database/memori.json"):
        with open("database/memori.json", "r") as f:
            konteks["profil"] = json.load(f)

    return json.dumps(konteks, indent=2) if konteks else ""


# ============================================================
# OLLAMA CORE
# ============================================================

def warmup_neira():
    """Pre-load model ke RAM saat startup biar response pertama langsung cepat."""
    url = "http://localhost:11434/api/generate"
    try:
        print("Neira lagi bangun tidur sebentar... ☕")
        requests.post(url, json={
            "model"     : "qwen3:4b",
            "system"    : SYSTEM_PROMPT,
            "prompt"    : "",
            "keep_alive": -1,
            "think"     : False
        }, timeout=120)
        print("Neira siap!")
    except Exception:
        pass


def panggil_ollama_api(system: str, prompt: str) -> str:
    """
    Fungsi core untuk request ke Ollama.
    - system: instruksi karakter Neira (pendek, tidak berubah)
    - prompt: data konteks + pertanyaan user (berubah tiap request)
    """
    url = "http://localhost:11434/api/generate"

    payload = {
        "model"     : "qwen3:4b",
        "system"    : system,   # instruksi karakter → field terpisah, lebih efisien
        "prompt"    : prompt,   # hanya data + pertanyaan user
        "stream"    : True,
        "keep_alive": -1,
        "think"     : False
    }

    try:
        response = requests.post(url, json=payload, stream=True, timeout=None)

        if response.status_code == 200:
            teks_lengkap = ""
            for line in response.iter_lines():
                if line:
                    data_json = json.loads(line.decode("utf-8"))
                    token = data_json.get("response", "")
                    teks_lengkap += token
                    sys.stdout.write(token)
                    sys.stdout.flush()
            return teks_lengkap
        else:
            return f"Neira: Waduh, server Ollama error: {response.status_code}"

    except requests.exceptions.ConnectionError:
        return "Neira: Ian, Ollama-nya belum dinyalain tuh. Buka dulu ya!"
    except Exception as e:
        return f"Neira: Ada kendala teknis: {e}"


# ============================================================
# FITUR NEIRA
# ============================================================

def analisis_prioritas(perintah_user: str) -> str:
    """Rekomendasi tugas — load hanya data tugas & profil."""
    intent = {"butuh_tugas": True, "butuh_jadwal": False, "butuh_profil": True}
    data_sekarang = muat_database_lokal(intent)

    prompt = f"Data Ian:\n{data_sekarang}\n\nPerintah: {perintah_user}"
    return panggil_ollama_api(SYSTEM_PROMPT_ANALISIS, prompt)


def ngobrol_santai(perintah_user: str) -> str:
    """Ngobrol santai — load database hanya kalau dibutuhkan."""
    intent = deteksi_intent(perintah_user)
    data_sekarang = muat_database_lokal(intent)

    if data_sekarang:
        prompt = f"Konteks:\n{data_sekarang}\n\nIan: {perintah_user}"
    else:
        prompt = perintah_user  # ngobrol biasa → prompt seminimal mungkin

    return panggil_ollama_api(SYSTEM_PROMPT, prompt)


def tanya_neira(perintah_user: str) -> str:
    """
    Gateway utama dari neira.py.
    Otomatis pilih mode berdasarkan intent.
    """
    intent = deteksi_intent(perintah_user)

    if intent["butuh_db"]:
        return analisis_prioritas(perintah_user)
    else:
        return ngobrol_santai(perintah_user)