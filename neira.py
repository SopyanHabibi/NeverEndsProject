import datetime
import time
import sys
import os
import webbrowser
import ollama
import wikipediaapi
import threading
import subprocess
from typing import Optional
from fitur import sistem, profil
from tools import tools_neira, monitor

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
    riwayat = db.ambil_riwayat_aktivitas(nama_aplikasi, hari=14)

    if len(riwayat) < 3:
        return f"Not enough history yet for {nama_aplikasi} to spot a pattern, Ian. Keep using it and ask me again in a few days!"

    hari_ini = datetime.date.today().isoformat()
    sesi_hari_ini = [r for r in riwayat if r['mulai'].startswith(hari_ini)]
    sesi_historis = [r for r in riwayat if not r['mulai'].startswith(hari_ini)]

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

    return hasil

FUNCTION_MAP = {
    "buka_aplikasi": lambda a: tools_neira.buka_aplikasi(a.get("nama_aplikasi", "")),
    "tambah_tugas": lambda a: f"Got it, added task #{db.tambah_tugas(a.get('deskripsi',''), a.get('deadline'))}: '{a.get('deskripsi','')}'.",
    "lihat_tugas": lambda a: _format_tugas(db.ambil_tugas()),
    "selesaikan_tugas": lambda a: ("Done, marked complete!" if db.selesaikan_tugas(int(a.get("id_tugas", -1))) else "Couldn't find that task ID."),
    "update_tugas": lambda a: ("Task updated!" if db.update_tugas(int(a.get("id_tugas", -1)), a.get("deskripsi"), a.get("deadline")) else "Couldn't find that task ID to update."),
    "tambah_jadwal": lambda a: (db.tambah_jadwal(a.get('aktivitas',''), a.get('waktu','')), f"Scheduled: '{a.get('aktivitas','')}' at {a.get('waktu','')}.")[1],
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
        "schedule", "jadwal", "agenda", "deadline", "remind", "ingatkan", "hari ini", "today", "calendar"
    ]
    return any(kata in teks_lower for kata in kata_kunci)

# ==================== HELPER ====================
def _ambil_angka(teks: str) -> Optional[int]:
    """Ambil angka pertama dari sebuah string perintah."""
    digit = "".join(filter(str.isdigit, teks))
    return int(digit) if digit else None

# ==================== CORE UTAMA BACKEND NEIRA ====================
def proses_perintah_backend(perintah, session_id):
    """Sistem Backend Neira dengan dukungan penuh Session-ID database."""
    waktu_mulai = time.time()
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
        elif "what time is it" in perintah or "check time" in perintah:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            yield f"It's currently {waktu_sekarang}, Ian."
            return

        elif "open youtube" in perintah:
            yield "Sure thing, spinning up YouTube..."
            webbrowser.open("https://www.youtube.com")
            return

        # 4. JALUR UTAMA LLM + DYNAMIC MULTI-SESSION CONTEXT
        else:
            
            # Langsung simpan chat user sekarang juga ke dalam session_id aktif
            db.simpan_chat(session_id, "user", perintah)
            
            # Ambil memori profil jangka panjang (Profil Ian)
            data_profil_ian = db.ambil_semua_profil()
            str_konteks_profil = ", ".join([f"{k}: {v}" for k, v in list(data_profil_ian.items())[:10]])
            
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
            
            # Hanya ambil 20 chat terakhir khusus dari session_id yang aktif!
            riwayat_chat_sqlite = db.ambil_riwayat_terakhir(session_id, limit=8)
            messages_payload.extend(riwayat_chat_sqlite)
            
            # Panggil Ollama — tools cuma dikirim kalau kalimat user ada indikasi relevan
            kwargs_ollama = {
                'model': 'qwen2.5:7b-instruct-q4_K_M',
                'messages': messages_payload,
                'stream': True
            }
            if perlu_tool_check(perintah):
                kwargs_ollama['tools'] = TOOLS_SCHEMA
                messages_payload[0]['content'] += (
                    " IMPORTANT: If Ian asks about his tasks, schedule, or opening an app, "
                    "you MUST use the corresponding tool. Do NOT print raw JSON or code blocks in your chat response. "
                    "Just execute the tool call."
                )
                kwargs_ollama['options'] = {'temperature': 0.1, 'num_predict': 300}
            response = ollama.chat(**kwargs_ollama)

            tool_calls_terdeteksi = None
            respons_lengkap_neira = ""

            for chunk in response:
                # 1. Cek apakah Ollama mendeteksi ini sebagai Tool Calls secara native
                if 'message' in chunk and 'tool_calls' in chunk['message'] and chunk['message']['tool_calls']:
                    tool_calls_terdeteksi = chunk['message']['tool_calls']
                    continue

                # 2. Ambil potongan teks token
                token = chunk.get('message', {}).get('content', '')
                respons_lengkap_neira += token

                # Cegah kebocoran teks JSON mentah ke layar UI
                if respons_lengkap_neira.strip().startswith("{") or "tool_calls" in respons_lengkap_neira:
                    continue

                if token:
                    yield token

            # ==================== SETELAH STREAMING SELESAI ====================

            # FORCE FALLBACK INTERCEPTOR — Qwen gagal manggil tool native, tapi nulis JSON mentah di teks
            if not tool_calls_terdeteksi and ("```json" in respons_lengkap_neira or '"tugas":' in respons_lengkap_neira):
                perintah_lower = perintah.lower()
                if "task" in perintah_lower or "tugas" in perintah_lower or "todo" in perintah_lower:
                    yield "\n\n🤖 *[Neira Auto-Sync]* Syncing directly with SQLite..."
                    hasil_db = FUNCTION_MAP["lihat_tugas"]({})
                    yield f"\n\n{hasil_db}"
                    db.simpan_chat(session_id, "assistant", hasil_db)
                    return
                elif "schedule" in perintah_lower or "jadwal" in perintah_lower or "agenda" in perintah_lower:
                    yield "\n\n🤖 *[Neira Auto-Sync]* Syncing directly with SQLite..."
                    hasil_db = FUNCTION_MAP["lihat_jadwal"]({})
                    yield f"\n\n{hasil_db}"
                    db.simpan_chat(session_id, "assistant", hasil_db)
                    return

            # Kalau Qwen sukses manggil tool lewat jalur native
            if tool_calls_terdeteksi:
                hasil_tools = []
                semua_instant = True

                for panggilan in tool_calls_terdeteksi:
                    nama_fungsi = panggilan['function']['name']
                    args_fungsi = panggilan['function'].get('arguments', {})
                    fungsi = FUNCTION_MAP.get(nama_fungsi)
                    hasil_eksekusi = fungsi(args_fungsi) if fungsi else f"Unknown tool: {nama_fungsi}"
                    hasil_tools.append(str(hasil_eksekusi))

                    if nama_fungsi not in TOOLS_INSTANT:
                        semua_instant = False

                if semua_instant:
                    teks_gabungan = "\n".join(hasil_tools)
                    respons_lengkap_neira += teks_gabungan
                    yield teks_gabungan
                else:
                    payload_ringkas = [
                        {'role': 'system', 'content': dynamic_system_prompt},
                        {'role': 'user', 'content': perintah},
                        {'role': 'assistant', 'content': '', 'tool_calls': tool_calls_terdeteksi},
                    ]
                    for hasil in hasil_tools:
                        payload_ringkas.append({'role': 'tool', 'content': hasil})

                    response_final = ollama.chat(
                        model='qwen2.5:7b-instruct-q4_K_M',
                        messages=payload_ringkas,
                        stream=True,
                        options={'num_predict': 300}
                    )
                    for chunk in response_final:
                        token = chunk['message']['content']
                        respons_lengkap_neira += token
                        yield token

            # Ini SEKARANG jalan SEKALI doang per respons, bukan per token
            print(f"[TIMING] Total durasi: {time.time() - waktu_mulai:.2f} detik | tool_dipakai={perlu_tool_check(perintah)}")
            db.simpan_chat(session_id, "assistant", respons_lengkap_neira)

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


if __name__ == "__main__":
    print("🚀 Triggering Neira with PyQt6 Engine... Let's Go!")
    db.inisialisasi_db()
    monitor.mulai_monitoring()
    import gui.pyqt_dashboard
    gui.pyqt_dashboard.main()