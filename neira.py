import datetime
import time
import sys
import os
import webbrowser
import ollama
import wikipediaapi
import threading
import subprocess
import base64
import tempfile
from typing import Optional
from fitur import sistem, profil
from tools import tools_neira, monitor, dokumen

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

# ==================== TOOLS / FUNCTION CALLING ====================

TOOLS_SCHEMA = [
    {
        'type': 'function',
        'function': {
            'name': 'buka_aplikasi',
            'description': "Open/launch an app or website (VS Code, Chrome, Spotify, YouTube, etc).",
            'parameters': {
                'type': 'object',
                'properties': {'nama_aplikasi': {'type': 'string', 'description': "App name, e.g. 'vscode', 'chrome', 'spotify'."}},
                'required': ['nama_aplikasi']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'tambah_tugas',
            'description': "Add a new task/to-do for Ian.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'deskripsi': {'type': 'string', 'description': 'Task description.'},
                    'deadline': {'type': 'string', 'description': "Optional deadline, free text. Empty if unmentioned."}
                },
                'required': ['deskripsi']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'lihat_tugas',
            'description': "Show Ian's pending tasks.",
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'selesaikan_tugas',
            'description': "Mark a task done by ID.",
            'parameters': {
                'type': 'object',
                'properties': {'id_tugas': {'type': 'integer', 'description': 'Task ID.'}},
                'required': ['id_tugas']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'update_tugas',
            'description': "Update the deadline or description of an EXISTING task by its ID. Use this — NOT tambah_tugas — when Ian gives more detail (like a deadline) about a task already mentioned earlier in the conversation.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'id_tugas': {'type': 'integer', 'description': 'ID of the existing task to update.'},
                    'deadline': {'type': 'string', 'description': 'New deadline, free text. Optional.'},
                    'deskripsi': {'type': 'string', 'description': 'New description. Optional.'}
                },
                'required': ['id_tugas']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'tambah_jadwal',
            'description': "Add an event to Ian's schedule with a time.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'aktivitas': {'type': 'string', 'description': 'Activity description.'},
                    'waktu': {'type': 'string', 'description': "Time/date, free text e.g. 'today 3pm', '2026-06-23 14:00'."}
                },
                'required': ['aktivitas', 'waktu']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'lihat_jadwal',
            'description': "Show Ian's schedule.",
            'parameters': {'type': 'object', 'properties': {}}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'analisa_produktivitas',
            'description': "Analyze Ian's usage pattern for an app (e.g. VS Code) — compares today's activity to his historical average to detect productivity changes.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'nama_aplikasi': {'type': 'string', 'description': "App name, e.g. 'VS Code', 'Chrome'."}
                },
                'required': ['nama_aplikasi']
            }
        }
    },
]

def _format_tugas(daftar):
    if not daftar:
        return "No pending tasks, Ian. You're all clear!"
    baris = [f"#{t['id']} - {t['deskripsi']}" + (f" (deadline: {t['deadline']})" if t['deadline'] else "") for t in daftar]
    return "Here's your task list:\n" + "\n".join(baris)

def _format_jadwal(daftar):
    if not daftar:
        return "Your schedule's empty, Ian."
    baris = [f"{j['waktu']} - {j['aktivitas']}" for j in daftar]
    return "Here's your schedule:\n" + "\n".join(baris)

def _analisa_pola(nama_aplikasi: str) -> str:
    """Hitung rata-rata jam mulai & durasi historis, bandingin sama hari ini."""
    import datetime
    print(f"[DEBUG ANALISA] Fungsi dipanggil dengan nama_aplikasi='{nama_aplikasi}'")
    riwayat = db.ambil_riwayat_aktivitas(nama_aplikasi, hari=14)

    if len(riwayat) < 3:
        return f"Not enough history yet for {nama_aplikasi} to spot a pattern, Ian. Keep using it and ask me again in a few days!"

    BATAS_MENIT_WAJAR = 960  # 16 jam, di atas ini dianggap data corrupt (sisa restart/sleep, dll)

    def durasi_valid(s):
        try:
            mulai = datetime.datetime.fromisoformat(s['mulai'])
            selesai = datetime.datetime.fromisoformat(s['selesai'])
            return (selesai - mulai).total_seconds() / 60 <= BATAS_MENIT_WAJAR
        except Exception:
            return False

    riwayat = [r for r in riwayat if durasi_valid(r)]

    hari_ini = datetime.date.today().isoformat()
    sesi_hari_ini = [r for r in riwayat if r['mulai'].startswith(hari_ini)]
    sesi_historis = [r for r in riwayat if not r['mulai'].startswith(hari_ini)]

    # Tambahin sesi yang LAGI BERJALAN sekarang (belum 'selesai'), biar kehitung real-time
    sesi_aktif_sekarang = db.ambil_sesi_terbuka()
    for sesi in sesi_aktif_sekarang:
        if sesi["nama_aplikasi"] == nama_aplikasi:
            conn_temp = __import__('sqlite3').connect(db.DB_FILE)
            cur_temp = conn_temp.cursor()
            cur_temp.execute("SELECT waktu_mulai FROM aktivitas_log WHERE id = ?", (sesi["id"],))
            waktu_mulai_aktif = cur_temp.fetchone()[0]
            conn_temp.close()
            # PENTING: cuma masukin kalau sesi ini BENERAN mulai hari ini.
            # Kalau sesi ini udah berumur lebih dari hari ini (sisa nyangkut), JANGAN dihitung sebagai "hari ini".
            if waktu_mulai_aktif.startswith(hari_ini):
                sesi_hari_ini.append({"mulai": waktu_mulai_aktif, "selesai": datetime.datetime.now().isoformat()})

    def hitung_durasi_menit(sesi):
        total = 0
        for s in sesi:
            mulai = datetime.datetime.fromisoformat(s['mulai'])
            selesai = datetime.datetime.fromisoformat(s['selesai'])
            total += (selesai - mulai).total_seconds() / 60
        return total

    def rata_jam_mulai(sesi):
        jam_list = [datetime.datetime.fromisoformat(s['mulai']).hour + datetime.datetime.fromisoformat(s['mulai']).minute / 60 for s in sesi]
        return sum(jam_list) / len(jam_list) if jam_list else None

    if not sesi_historis:
        return f"Today's your first tracked day with {nama_aplikasi}, Ian. Check back tomorrow for a real comparison!"

    durasi_historis_per_hari = hitung_durasi_menit(sesi_historis) / max(1, len(set(s['mulai'][:10] for s in sesi_historis)))
    durasi_hari_ini = hitung_durasi_menit(sesi_hari_ini)
    jam_mulai_historis = rata_jam_mulai(sesi_historis)
    jam_mulai_hari_ini = rata_jam_mulai(sesi_hari_ini)

    persen_perubahan = ((durasi_hari_ini - durasi_historis_per_hari) / durasi_historis_per_hari * 100) if durasi_historis_per_hari > 0 else 0

    hasil = (
        f"Historical average for {nama_aplikasi}: starts around {jam_mulai_historis:.1f}h, "
        f"~{durasi_historis_per_hari:.0f} min/day. "
    )
    if sesi_hari_ini:
        hasil += (
            f"Today: started around {jam_mulai_hari_ini:.1f}h, {durasi_hari_ini:.0f} min so far. "
            f"That's {abs(persen_perubahan):.0f}% {'lower' if persen_perubahan < 0 else 'higher'} than usual."
        )
    else:
        hasil += f"No {nama_aplikasi} activity detected yet today."

    print(f"[DEBUG ANALISA] sesi_hari_ini={len(sesi_hari_ini)} sesi_historis={len(sesi_historis)} | hasil_mentah: {hasil}")
    return hasil

# ==================== FIX FUNCTION MAP (ANTI-TYPO) ====================
FUNCTION_MAP = {
    "buka_aplikasi": lambda a: tools_neira.buka_aplikasi(a.get("nama_aplikasi", "")),
    "tambah_tugas": lambda a: f"Got it, successfully added task #{db.tambah_tugas(a.get('deskripsi',''), a.get('deadline'))}: '{a.get('deskripsi','')}'",
    "lihat_tugas": lambda a: _format_tugas(db.ambil_tugas()),
    "selesaikan_tugas": lambda a: ("Done, marked complete!" if db.selesaikan_tugas(int(a.get("id_tugas", -1))) else "Couldn't find that task ID."),
    "update_tugas": lambda a: ("Task updated!" if db.update_tugas(int(a.get("id_tugas", -1)), a.get("deskripsi"), a.get("deadline")) else "Couldn't find that task ID to update."),
    "tambah_jadwal": lambda a: f"Scheduled: '{a.get('aktivitas','')}' at {a.get('waktu','')}.",
    "lihat_jadwal": lambda a: _format_jadwal(db.ambil_jadwal()),
    "analisa_produktivitas": lambda a: _analisa_pola(a.get("nama_aplikasi", "")),
}

# Tools yang outputnya udah final & natural -> gak perlu dinarasiin ulang sama LLM (hemat 1x inference)
TOOLS_INSTANT = {
    "buka_aplikasi",
    "selesaikan_tugas",
    "update_tugas",
    "lihat_tugas",   # Disamakan dengan nama fungsi di TOOLS_SCHEMA
    "lihat_jadwal"   # Disamakan dengan nama fungsi di TOOLS_SCHEMA
}

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

def perlu_tool_check(teks: str) -> bool:
    """Mengecek longgar apakah kalimat user berpotensi butuh tool (app/task/jadwal),
    biar tools schema cuma dikirim ke Qwen kalau emang relevan -> hemat token & lebih cepat."""
    teks_lower = teks.lower()
    kata_kunci = [
        # buka aplikasi
        "open", "launch", "run", "start", "buka", "jalankan",
        "code", "coding", "vscode", "vs code", "chrome", "browser",
        "spotify", "youtube", "github", "gmail", "notepad", "calculator",
        "explorer", "terminal", "cmd", "app", "application", "program",
        # tasks
        "task", "tugas", "todo", "to-do", "to do", "list", "kerjaan", "pekerjaan",
        # jadwal
        "schedule", "jadwal", "agenda", "deadline", "remind", "ingatkan", "hari ini", "today", "calendar",
        # produktivitas
        "productivity", "productive", "produktivitas", "produktif",
        "pattern", "pola", "activity", "aktivitas",
    ]
    return any(kata in teks_lower for kata in kata_kunci)

# ==================== HELPER ====================
def _ambil_angka(teks: str) -> Optional[int]:
    """Ambil angka pertama dari sebuah string perintah."""
    digit = "".join(filter(str.isdigit, teks))
    return int(digit) if digit else None

# ==================== CORE INTEGRATED BACKEND (FIXED MEMORY & TOOLS) ====================
def proses_perintah_backend(perintah, session_id):
    try:
        db.inisialisasi_db()
        if "goodbye" in perintah.lower() or "bye" in perintah.lower():
            yield "Catch you later, Ian! Stay productive! 🚀"
            return
        
        # Shortcut waktu — jawab langsung dari sistem, jangan biarin Qwen "nebak" jam
        perintah_lower_cek = perintah.lower()
        if "what time" in perintah_lower_cek or "jam berapa" in perintah_lower_cek or "current time" in perintah_lower_cek:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            yield f"It's currently {waktu_sekarang} in Medan, Ian."
            return
        
        # 1. Simpan pesan user ke SQLite
        db.simpan_chat(session_id, "user", perintah)
        
        # 2. Ambil data profil konteks Ian
        data_profil_ian = db.ambil_semua_profil()
        str_konteks_profil = ", ".join([f"{k}: {v}" for k, v in list(data_profil_ian.items())[:10]])
        
        dynamic_prompt = system_prompt
        if str_konteks_profil:
            dynamic_prompt += f" Context about Ian: {str_konteks_profil}."
            
        messages_payload = [{'role': 'system', 'content': dynamic_prompt}]
        
        # 3. Cek kebutuhan Live Web Search
        if perlu_akses_internet(perintah):
            yield "🌐 Neira is searching the live web...\n\n"
            messages_payload.append({'role': 'user', 'content': ambil_info_internet(perintah)})
            
        # 3.5 Cek apakah ada dokumen aktif di sesi ini, suntik konteks relevan kalau ada
        chunks_dokumen = db.ambil_chunks_sesi(session_id)
        if chunks_dokumen:
            perintah_lower = perintah.lower()
            kata_kunci_ringkas = ["summarize", "ringkas", "summary", "rangkum", "quiz", "kuis", "soal"]
            
            if any(k in perintah_lower for k in kata_kunci_ringkas):
                konteks_dokumen = dokumen.pilih_chunks_sample(chunks_dokumen, max_chunks=5)
            else:
                konteks_dokumen = dokumen.pilih_chunks_relevan(chunks_dokumen, perintah, top_n=3)

            nama_file_aktif = chunks_dokumen[0]["nama_file"]
            messages_payload.append({
                'role': 'user',
                'content': (
                    f"Here is relevant content from the document '{nama_file_aktif}' that Ian uploaded:\n\n"
                    f"{konteks_dokumen}\n\n"
                    f"Use this content to answer Ian's question. If asked to summarize, summarize ONLY based on "
                    f"this content. If asked to make a quiz, create quiz questions based ONLY on this content."
                )
            })
            
        # 4. Ambil riwayat obrolan lama agar Neira tidak amnesia masa lalu
        riwayat_chat_sqlite = db.ambil_riwayat_terakhir(session_id, limit=8)
        messages_payload.extend(riwayat_chat_sqlite)
        
        # Setup parameter pemanggilan model Ollama
        kwargs_ollama = {'model': 'qwen2.5:7b-instruct-q4_K_M', 'messages': messages_payload, 'stream': True}
        if perlu_tool_check(perintah):
            kwargs_ollama['tools'] = TOOLS_SCHEMA
            kwargs_ollama['options'] = {'temperature': 0.1, 'num_predict': 300}
            
        # 5. Panggilan Pertama ke Ollama (Mengecek text biasa ATAU penugasan Tool)
        response = ollama.chat(**kwargs_ollama)
        tool_calls_terdeteksi = None
        respons_lengkap_neira = ""

        for chunk in response:
            if 'message' in chunk and 'tool_calls' in chunk['message'] and chunk['message']['tool_calls']:
                tool_calls_terdeteksi = chunk['message']['tool_calls']
                continue
            token = chunk.get('message', {}).get('content', '')
            respons_lengkap_neira += token
            if token and not respons_lengkap_neira.strip().startswith("{"):
                yield token

        # 6. FIX UTAMA: Eksekusi Tool & Umpan Balik Hasilnya ke Model LLM agar Neira Tahu Isinya!
        if tool_calls_terdeteksi:
            # Masukkan respons model yang meminta pemanggilan tool ke payload terlebih dahulu (Wajib bagi Ollama)
            messages_payload.append({
                'role': 'assistant',
                'content': respons_lengkap_neira,
                'tool_calls': tool_calls_terdeteksi
            })

            for panggilan in tool_calls_terdeteksi:
                nama_fungsi = panggilan['function']['name']
                args_fungsi = panggilan['function'].get('arguments', {})
                fungsi = FUNCTION_MAP.get(nama_fungsi)
                
                # Jalankan fungsi database asli (ambil_tugas / tambah_tugas / dll)
                hasil_eksekusi = fungsi(args_fungsi) if fungsi else "Unknown tool"
                
                # Masukkan hasil pembacaan database ke payload pesan dengan role 'tool'
                messages_payload.append({
                    'role': 'tool',
                    'content': str(hasil_eksekusi),
                    'name': nama_fungsi
                })
            
            # Panggil Ollama sekali lagi untuk meramu teks final berdasarkan data database yang sudah valid!
            second_response = ollama.chat(
                model='qwen2.5:7b-instruct-q4_K_M',
                messages=messages_payload,
                stream=True
            )
            
            respons_lengkap_neira = "" # Reset wadah teks
            for chunk in second_response:
                token = chunk.get('message', {}).get('content', '')
                respons_lengkap_neira += token
                if token:
                    yield token

        # 7. Simpan jawaban final asisten ke SQLite database
        db.simpan_chat(session_id, "assistant", respons_lengkap_neira)
        
    except Exception as e:
        print(f"Crash pada proses perintah: {e}")
        yield f"⚠️ Backend system error: {e}"

def neira_auto_remember(perintah_user: str, jawaban_neira: str):
    """Menyuruh Qwen mendeteksi informasi penting secara otomatis untuk disimpan ke SQLite."""
    import json
    try:
        profil_sekarang = db.ambil_semua_profil()

        prompt_memori = (
            f"Analyze this conversation turn between Ian and you.\n"
            f"Ian said: '{perintah_user}'\n"
            f"You replied: '{jawaban_neira}'\n\n"
            f"Ian's CURRENT saved profile: {json.dumps(profil_sekarang)}\n\n"
            f"CRITICAL RULES:\n"
            f"1. ONLY use these EXACT keys, never invent new ones: name, age, location, occupation, "
            f"motorcycle, hobbies, current_project, relationship_status, hardware_specs.\n"
            f"2. If Ian shares info matching one of these keys, output that key with the UPDATED value "
            f"(overwrite, don't create a variant key).\n"
            f"3. If Ian shares something that doesn't fit any key above, IGNORE it — do not invent a new key.\n"
            f"4. If a key already has a value in his current profile and nothing new was said about it, "
            f"do NOT include it in your output.\n"
            f"5. If NO new personal information was shared, strictly reply with an empty object: {{}}\n"
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


# ==================== WEB SERVER BACKEND (PYQT6 STYLE & CLEAN ROUTING) ====================
from http.server import SimpleHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import json
import urllib.parse
import webbrowser
import os

class NeiraServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 1. STREAMING API ENDPOINT (SSE)
        if parsed_url.path == '/api/chat-stream':
            pesan_user = query_params.get('pesan', [''])[0]
            session_id_raw = query_params.get('session_id', [''])[0]

            # ALUR PYQT6: Jika session_id kosong/null, buat sesi baru dulu di SQLite agar dapat ID Integer
            if not session_id_raw or session_id_raw == 'null' or session_id_raw == 'undefined':
                session_id = db.buat_sesi_baru(judul=pesan_user[:20])
            else:
                try:
                    session_id = int(session_id_raw)
                except:
                    session_id = db.buat_sesi_baru(judul=pesan_user[:20])

            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()

            # Beritahu frontend ID sesi yang asli lewat token pertama khusus jika ini sesi baru
            self.wfile.write(f"data: [SESSION_ID_ASSIGNED:{session_id}]\n\n".encode('utf-8'))
            self.wfile.flush()

            try:
                generator = proses_perintah_backend(pesan_user, session_id)
                for token in generator:
                    if token:
                        # TRICK UTAMA: Ubah enter asli AI jadi string placeholder aman [NEWLINE]
                        token_aman = token.replace("\n", "[NEWLINE]")
                        
                        payload = json.dumps({"text": token_aman})
                        self.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                        self.wfile.flush()
            except Exception as e:
                print(f"Error streaming: {e}")

        # 2. AMBIL DAFTAR HISTORI CHAT
        elif parsed_url.path == '/api/sessions':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                # Memanggil fungsi asli dari db.py kamu
                sesi_db = db.ambil_semua_sesi()
                self.wfile.write(json.dumps(sesi_db).encode('utf-8'))
            except Exception as e:
                print(f"Gagal ambil sesi: {e}")
                self.wfile.write(json.dumps([]).encode('utf-8'))
            return

        # 3. AMBIL ISI PERCAKAPAN LAMA
        elif parsed_url.path == '/api/history':
            session_id_raw = query_params.get('session_id', [''])[0]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            try:
                if session_id_raw and session_id_raw != 'null':
                    session_id = int(session_id_raw)
                    riwayat = db.ambil_riwayat_terakhir(session_id, limit=50)
                    list_chat = [{"role": i['role'], "content": i['content']} for i in riwayat]
                    self.wfile.write(json.dumps(list_chat).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps([]).encode('utf-8'))
            except Exception as e:
                print(f"Gagal ambil history: {e}")
                self.wfile.write(json.dumps([]).encode('utf-8'))
            return
            
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8')) if content_length > 0 else {}
        
        # 0. UPLOAD DOKUMEN (PDF/DOCX/PPTX)
        if self.path == '/api/upload-document':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                session_id = int(data.get('session_id'))
                nama_file = data.get('filename', 'dokumen')
                ekstensi = nama_file.split('.')[-1].lower()
                filedata_b64 = data.get('filedata')

                if ekstensi not in ('pdf', 'docx', 'pptx'):
                    self.wfile.write(json.dumps({"status": "error", "message": "Format tidak didukung. Cuma PDF, DOCX, PPTX."}).encode('utf-8'))
                    return

                file_bytes = base64.b64decode(filedata_b64)
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ekstensi}") as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                teks = dokumen.ekstrak_teks(tmp_path, ekstensi)
                os.remove(tmp_path)

                if not teks.strip():
                    self.wfile.write(json.dumps({"status": "error", "message": "Gagal membaca isi dokumen, atau dokumen kosong."}).encode('utf-8'))
                    return

                chunks = dokumen.pecah_jadi_chunks(teks)
                db.hapus_chunks_sesi(session_id)  # cuma 1 dokumen aktif per sesi
                for i, chunk in enumerate(chunks):
                    db.simpan_chunk_dokumen(session_id, nama_file, i, chunk)

                self.wfile.write(json.dumps({
                    "status": "success",
                    "filename": nama_file,
                    "chunks": len(chunks)
                }).encode('utf-8'))
            except Exception as e:
                print(f"[UPLOAD ERROR] {e}")
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        # SHUTDOWN VIA BEACON TAB CLOSE
        if self.path == '/api/shutdown':
            self.send_response(200)
            self.end_headers()
            print("\n🔌 Tab Browser ditutup oleh Ian. Mematikan Server Neira...")
            def kill():
                time.sleep(0.5)
                os._exit(0)
            import threading
            threading.Thread(target=kill).start()
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        # 4. RE-NAME HISTORI CHAT (FIXED SINKRON DB.PY)
        if self.path == '/api/session/rename':
            try:
                id_sesi = int(data.get('id'))
                judul_baru = data.get('title')
                db.ubah_judul_sesi(id_sesi, judul_baru)
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                print(f"Error rename: {e}")
            return

        # 5. HAPUS HISTORI CHAT (FIXED SINKRON DB.PY)
        elif self.path == '/api/session/delete':
            try:
                id_sesi = int(data.get('id'))
                db.hapus_sesi(id_sesi)
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                print(f"Error delete: {e}")
            return

def jalankan_server_neira():
    server_address = ('', 5000)
    httpd = ThreadingHTTPServer(server_address, NeiraServerHandler)
    print("🌍 Neira Premium Server Sync running on http://localhost:5000")
    webbrowser.open("http://localhost:5000")
    httpd.serve_forever()

if __name__ == "__main__":
    print("🚀 Triggering Neira Core Ecosystem...")
    db.inisialisasi_db()
    monitor.mulai_monitoring()
    jalankan_server_neira()
