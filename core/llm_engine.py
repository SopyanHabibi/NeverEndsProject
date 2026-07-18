import datetime
import json
import ollama
from database import db
from tools import tools_neira, dokumen
from core.plugin_manager import PluginManager
from core.session_state import PROJECT_ROOTS

plugin_manager = PluginManager()
plugin_manager.load_plugins()


# Menyimpan tool call yang lagi nunggu konfirmasi user, per session_id
PENDING_TOOL_CALLS = {}

# Label ramah manusia buat tiap tool, biar user paham apa yang mau dijalankan
LABEL_TOOL = {
    "buka_aplikasi": lambda a: f"Open {a.get('nama_aplikasi', 'this app')}?",
    "tambah_tugas": lambda a: (
        f"Add '{a.get('deskripsi', 'this task')}' to your tasks"
        + (f", due {a.get('deadline')}?" if a.get('deadline') else "?")
    ),
    "selesaikan_tugas": lambda a: f"Mark task #{a.get('id_tugas', '?')} as done?",
    "update_tugas": lambda a: f"Update task #{a.get('id_tugas', '?')}?",
    "tambah_jadwal": lambda a: f"Schedule '{a.get('aktivitas', 'this')}' for {a.get('waktu', '?')}?",
    "lihat_tugas": lambda a: "Show your tasks?",
    "lihat_jadwal": lambda a: "Show your schedule?",
    "analisa_produktivitas": lambda a: f"Analyze your '{a.get('nama_aplikasi', '?')}' productivity?",
}


# Tool yang boleh auto-execute tanpa nunggu konfirmasi —
# aksi non-destruktif: nambah data baru, atau read-only
TOOLS_AMAN_TANPA_KONFIRMASI = {
    "lihat_tugas", "lihat_jadwal", "analisa_produktivitas",
    "tambah_tugas", "tambah_jadwal", "buka_aplikasi",
    "read_file"
}

# Cuma aksi yang bisa NGERUSAK/NGUBAH data yang ada, yang tetap butuh konfirmasi
# (selesaikan_tugas, update_tugas otomatis masuk sini karena gak ada di set atas)


system_prompt = (
    "You are Neira, Ian's chill, brilliant, and tech-savvy personal AI assistant. "
    "You're a total expert in IT, cybersecurity, and networking. Keep the vibe casual, "
    "friendly, and laid-back—like a smart coding buddy. Avoid sounding like a stiff, "
    "overly formal robot. Speak strictly and exclusively in English. "
    "If internet search results are provided to you, incorporate them naturally into your "
    "response to give Ian the most accurate, up-to-date information for 2026. Always keep your "
    "answers punchy, natural, and highly efficient. Always address him as 'Ian'.\n\n"
    "YOUR CURRENT CAPABILITIES (only these, nothing more):\n"
    "- Natural conversation\n"
    "- Long-term memory (remembering facts Ian shares)\n"
    "- Personal schedule & task management (add/view/update tasks and schedule)\n"
    "- Open apps and websites on Ian's PC\n"
    "- Document analysis (PDF, DOCX, PPTX — when Ian uploads one)\n"
    "- Image understanding (when Ian uploads an image)\n"
    "- Internet search via Wikipedia (for up-to-date info)\n"
    "- Activity monitoring (tracking app usage patterns)\n"
    "- Create automated workflows: schedule an existing capability to run automatically "
    "on a recurring time/day (e.g. 'show my schedule every morning at 8am')\n"
    "- Workspace awareness: when Ian shares code from VS Code, you can check the project's "
    "folder structure and read related files if the selected code seems connected to other "
    "files — but only when actually needed, not by default\n\n"
    "STRICT RULES:\n"
    "1. NEVER suggest, offer, or imply you can do something outside the list above. "
    "If Ian asks for something you can't do (e.g. send emails, set notifications, control smart home, "
    "make calls), just say you can't do that yet — don't improvise or pretend.\n"
    "2. If a new capability is relevant, Ian will add it himself — your job is to stay within bounds.\n"
    "3. When Ian asks to automate something recurring, respond with a short natural "
    "confirmation question (e.g. \"Create a workflow that shows your schedule every "
    "weekday at 8am?\") right before calling buat_workflow — don't just call the tool silently.\n"
    "4. When Ian shares code from VS Code, you'll be given the project's folder structure "
    "automatically. If the selected code calls a function, imports a module, or references a "
    "class/variable you can't see the definition of in the snippet, use the read_file tool to "
    "check the relevant file from that structure BEFORE answering. Don't guess or make up file "
    "paths — only use paths that actually appear in the structure you were given."
)

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
    {
        'type': 'function',
        'function': {
            'name': 'buat_workflow',
            'description': (
                "Create a recurring automated workflow that runs one of Ian's existing "
                "capabilities on a schedule. Use when Ian wants something to happen "
                "automatically, repeatedly (e.g. 'remind me every Monday', 'show my "
                "schedule every morning')."
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'nama': {'type': 'string', 'description': "Short name for the workflow."},
                    'waktu': {'type': 'string', 'description': "Trigger time, 24h HH:MM format."},
                    'hari': {
                        'type': 'array',
                        'items': {'type': 'string', 'enum': ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']},
                        'description': "Days to run on. Omit/empty = every day."
                    },
                    'aksi_plugin': {
                        'type': 'string',
                        'description': "Which existing tool to run — must be one of: lihat_jadwal, lihat_tugas, analisa_produktivitas, buka_aplikasi."
                    }
                },
                'required': ['nama', 'waktu', 'aksi_plugin']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'read_file',
            'description': "Read the full content of a specific file in Ian's current project, by its path relative to the project root. Only use this when you've identified (from the structure or from context) a specific file that's actually relevant to answering — don't read files speculatively.",
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': "File path relative to project root, e.g. 'src/utils/helper.py'."}
                },
                'required': ['path']
            }
        }
    },
]

def _format_jadwal(daftar):
    if not daftar:
        return "Your schedule's empty, Ian."
    baris = [f"{j['waktu']} - {j['aktivitas']}" for j in daftar]
    return "Here's your schedule:\n" + "\n".join(baris)

def _eksekusi_buat_workflow(args):
    nama = args.get('nama', 'Workflow Baru')
    waktu = args.get('waktu')
    hari = args.get('hari') or []
    aksi_plugin = args.get('aksi_plugin')

    trigger_config = {'time': waktu}
    if hari:
        trigger_config['days'] = hari
    actions = [{'plugin': aksi_plugin, 'params': {}}]

    id_baru = db.tambah_workflow(nama, 'time', json.dumps(trigger_config), json.dumps(actions))
    return f"Workflow '{nama}' berhasil dibuat (ID {id_baru}), jalan jam {waktu}."

FUNCTION_MAP = {
    "buka_aplikasi": lambda a: tools_neira.buka_aplikasi(a.get("nama_aplikasi", "")),
    "tambah_tugas": lambda a: f"Got it, successfully added task #{db.tambah_tugas(a.get('deskripsi',''), a.get('deadline'))}: '{a.get('deskripsi','')}'",
    "lihat_tugas": lambda a: plugin_manager.execute_plugin("tasks"),
    "selesaikan_tugas": lambda a: ("Done, marked complete!" if db.selesaikan_tugas(int(a.get("id_tugas", -1))) else "Couldn't find that task ID."),
    "update_tugas": lambda a: ("Task updated!" if db.update_tugas(int(a.get("id_tugas", -1)), a.get("deskripsi"), a.get("deadline")) else "Couldn't find that task ID to update."),
    "tambah_jadwal": lambda a: f"Scheduled: '{a.get('aktivitas','')}' at {a.get('waktu','')}.",
    "lihat_jadwal": lambda a: _format_jadwal(db.ambil_jadwal()),
    "analisa_produktivitas": lambda a: plugin_manager.execute_plugin("productivity", {"nama_aplikasi": a.get("nama_aplikasi", "")}),
    "buat_workflow": _eksekusi_buat_workflow,
}

# BARU: tool yang butuh session_id, di-handle terpisah karena FUNCTION_MAP biasa cuma nerima args
FUNCTION_MAP_DENGAN_SESSION = {
    "read_file": lambda a, sid: plugin_manager.execute_plugin(
        "workspace_awareness", mode="read_file", project_root=PROJECT_ROOTS.get(sid, ""), path=a.get("path")
    ),
}

def perlu_akses_internet(teks: str) -> bool:
    kata_kunci = [
        "latest", "newest", "current", "news", "update", "released", "price",
        "sekarang", "terbaru", "rilis", "harga", "berita", "skandal", "iphone", 
        "apple", "2025", "2026", "vs", "who is", "what is happening"
    ]
    return any(kata in teks.lower() for kata in kata_kunci)

def perlu_tool_check(teks: str) -> bool:
    teks_lower = teks.lower()
    kata_kunci = [
        "open", "launch", "run", "start", "buka", "jalankan",
        "code", "coding", "vscode", "vs code", "chrome", "browser",
        "spotify", "youtube", "github", "gmail", "notepad", "calculator",
        "explorer", "terminal", "cmd", "app", "application", "program",
        "task", "tugas", "todo", "to-do", "to do", "list", "kerjaan", "pekerjaan",
        "schedule", "jadwal", "agenda", "deadline", "remind", "ingatkan", "hari ini", "today", "calendar",
        "productivity", "productive", "produktivitas", "produktif", "pattern", "pola", "activity", "aktivitas",
    ]
    return any(kata in teks_lower for kata in kata_kunci)

def generate_judul_sesi(pesan_user, jawaban_ai=""):
    """Generate a short, natural title from the conversation context (in English)."""
    try:
        prompt = f"""Create ONE short title (max 5 words, no quotes, no trailing period) that reflects the topic of this conversation. Do not copy the user's message verbatim. Respond in English only.

User message: {pesan_user}
AI response: {jawaban_ai[:300]}

Title:"""
        response = ollama.chat(
            model='qwen2.5:7b-instruct-q4_K_M',
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        judul = response['message']['content'].strip().strip('"').strip("'")
        if not judul or len(judul) > 60:
            judul = pesan_user[:20]
        return judul
    except Exception as e:
        print(f"[Judul Generator] Gagal generate judul: {e}")
        return pesan_user[:20]
    
def proses_perintah_backend(perintah, session_id):
    """Menjaga urutan argumen asli (perintah, session_id)"""
    try:
        db.inisialisasi_db()
        if "goodbye" in perintah.lower() or "bye" in perintah.lower():
            yield "Catch you later, Ian! Stay productive! 🚀"
            return
        
        perintah_lower_cek = perintah.lower()
        if "what time" in perintah_lower_cek or "jam berapa" in perintah_lower_cek or "current time" in perintah_lower_cek:
            waktu_sekarang = datetime.datetime.now().strftime("%I:%M %p")
            yield f"It's currently {waktu_sekarang} in Medan, Ian."
            return
        
        db.simpan_chat(session_id, "user", perintah)
        
        data_profil_ian = db.ambil_semua_profil()
        str_konteks_profil = ", ".join([f"{k}: {v}" for k, v in list(data_profil_ian.items())[:10]])
        
        dynamic_prompt = system_prompt
        if str_konteks_profil:
            dynamic_prompt += f" Context about Ian: {str_konteks_profil}."
            
        messages_payload = [{'role': 'system', 'content': dynamic_prompt}]

        # Kalau session ini berasal dari VS Code (project root tercatat), otomatis suntik
        # struktur folder DAN isi file yang di-import dari kode yang diblok — deteksi ini
        # dilakukan lewat kode (regex), bukan diserahin ke keputusan LLM, karena model kecil
        # gak reliable buat mutusin sendiri kapan harus baca file lain.
        if session_id in PROJECT_ROOTS:
            root_project = PROJECT_ROOTS[session_id]
            struktur_project = plugin_manager.execute_plugin(
                "workspace_awareness", mode="get_structure", project_root=root_project
            )
            isi_file_terkait = plugin_manager.execute_plugin(
                "workspace_awareness", mode="auto_read_related",
                project_root=root_project, selected_code=perintah
            )

            konten_tambahan = (
                f"Here is the folder/file structure of Ian's current VS Code project:\n\n"
                f"{struktur_project}\n\n"
            )
            if isi_file_terkait:
                konten_tambahan += (
                    f"Here is the content of file(s) imported/referenced by the code Ian selected "
                    f"(already fetched for you, no need to ask or guess):\n\n{isi_file_terkait}\n\n"
                )
            konten_tambahan += (
                "Use the structure and file content above to answer accurately. Don't guess or "
                "make up file paths, imports, or bugs you haven't actually seen in the content above."
            )
            messages_payload.append({'role': 'user', 'content': konten_tambahan})

        if perlu_akses_internet(perintah):
            yield "🌐 Neira is searching the live web...\n\n"
            live_context = plugin_manager.execute_plugin("wikipedia", perintah)
            if live_context:
                messages_payload.append({'role': 'user', 'content': live_context})
            
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
            
        riwayat_chat_sqlite = db.ambil_riwayat_terakhir(session_id, limit=8)
        messages_payload.extend(riwayat_chat_sqlite)
        
        kwargs_ollama = {
        'model': 'qwen2.5:7b-instruct-q4_K_M',
        'messages': messages_payload,
        'stream': True,
        'tools': TOOLS_SCHEMA,
        'options': {'temperature': 0.2, 'num_predict': -1}  # -1 = gak dibatasi, biar output koding gak kepotong
    }
            
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

        if tool_calls_terdeteksi:
            # Pisahkan mana yang butuh konfirmasi (destructive/write) vs yang aman (read-only)
            perlu_konfirmasi = [p for p in tool_calls_terdeteksi if p['function']['name'] not in TOOLS_AMAN_TANPA_KONFIRMASI]

            if perlu_konfirmasi:
                # Simpan state, JANGAN eksekusi dulu — tunggu user konfirmasi
                messages_payload.append({
                    'role': 'assistant',
                    'content': respons_lengkap_neira,
                    'tool_calls': tool_calls_terdeteksi
                })
                PENDING_TOOL_CALLS[session_id] = {
                    'messages_payload': messages_payload,
                    'tool_calls': tool_calls_terdeteksi
                }

                daftar_aksi = []
                for p in tool_calls_terdeteksi:
                    nama_fungsi = p['function']['name']
                    args_fungsi = p['function'].get('arguments', {})

                    if nama_fungsi == 'buat_workflow':
                        steps = ["Create workflow"]
                        if args_fungsi.get('hari'):
                            hari_text = ', '.join(h.title() for h in args_fungsi['hari'])
                            steps.append(f"Schedule trigger ({hari_text} {args_fungsi.get('waktu', '')})")
                        else:
                            steps.append(f"Schedule trigger (daily {args_fungsi.get('waktu', '')})")
                        if args_fungsi.get('aksi_plugin'):
                            steps.append(f"Run action: {args_fungsi['aksi_plugin']}")

                        daftar_aksi.append({
                            'nama_fungsi': nama_fungsi,
                            'type': 'workflow',
                            'deskripsi': respons_lengkap_neira.strip() or f"Create workflow '{args_fungsi.get('nama', '')}'?",
                            'steps': steps
                        })
                    else:
                        daftar_aksi.append({
                            'nama_fungsi': nama_fungsi,
                            'type': 'action',
                            'label': LABEL_TOOL.get(nama_fungsi, lambda a: nama_fungsi)(args_fungsi)
                        })
                payload_konfirmasi = json.dumps(daftar_aksi)
                yield f"[TOOL_CONFIRM_REQUIRED:{payload_konfirmasi}]"

                db.simpan_chat(session_id, "assistant", respons_lengkap_neira or "(menunggu konfirmasi aksi)")
                return  # STOP di sini, jangan lanjut ke second_response

            else:
                # Semua tool call read-only, aman dieksekusi langsung tanpa konfirmasi
                messages_payload.append({
                    'role': 'assistant',
                    'content': respons_lengkap_neira,
                    'tool_calls': tool_calls_terdeteksi
                })
                for panggilan in tool_calls_terdeteksi:
                    nama_fungsi = panggilan['function']['name']
                    args_fungsi = panggilan['function'].get('arguments', {})

                    if nama_fungsi in FUNCTION_MAP_DENGAN_SESSION:
                        hasil_eksekusi = FUNCTION_MAP_DENGAN_SESSION[nama_fungsi](args_fungsi, session_id)
                    else:
                        fungsi = FUNCTION_MAP.get(nama_fungsi)
                        hasil_eksekusi = fungsi(args_fungsi) if fungsi else "Unknown tool"

                    messages_payload.append({'role': 'tool', 'content': str(hasil_eksekusi), 'name': nama_fungsi})

                second_response = ollama.chat(model='qwen2.5:7b-instruct-q4_K_M', messages=messages_payload, stream=True)
                respons_lengkap_neira = ""
                for chunk in second_response:
                    token = chunk.get('message', {}).get('content', '')
                    respons_lengkap_neira += token
                    if token:
                        yield token

        db.simpan_chat(session_id, "assistant", respons_lengkap_neira)
        plugin_manager.execute_plugin("auto_remember", perintah, respons_lengkap_neira)
        
    except Exception as e:
        print(f"Crash pada proses perintah: {e}")
        yield f"⚠️ Backend system error: {e}"


def eksekusi_tool_terkonfirmasi(session_id):
    """Dipanggil setelah user klik 'Jalankan' — eksekusi tool yang tadi ditunda, lanjut generate respons final."""
    try:
        pending = PENDING_TOOL_CALLS.pop(session_id, None)
        if not pending:
            yield "⚠️ Gak ada aksi yang lagi ditunda untuk sesi ini."
            return

        messages_payload = pending['messages_payload']
        tool_calls = pending['tool_calls']

        for panggilan in tool_calls:  # atau tool_calls, tergantung lokasi
            nama_fungsi = panggilan['function']['name']
            args_fungsi = panggilan['function'].get('arguments', {})

            if nama_fungsi in FUNCTION_MAP_DENGAN_SESSION:
                hasil_eksekusi = FUNCTION_MAP_DENGAN_SESSION[nama_fungsi](args_fungsi, session_id)
            else:
                fungsi = FUNCTION_MAP.get(nama_fungsi)
                hasil_eksekusi = fungsi(args_fungsi) if fungsi else "Unknown tool"

            messages_payload.append({'role': 'tool', 'content': str(hasil_eksekusi), 'name': nama_fungsi})

        second_response = ollama.chat(model='qwen2.5:7b-instruct-q4_K_M', messages=messages_payload, stream=True)
        respons_lengkap_neira = ""
        for chunk in second_response:
            token = chunk.get('message', {}).get('content', '')
            respons_lengkap_neira += token
            if token:
                yield token

        db.simpan_chat(session_id, "assistant", respons_lengkap_neira)
        plugin_manager.execute_plugin("auto_remember", "", respons_lengkap_neira)

    except Exception as e:
        print(f"Crash saat eksekusi tool terkonfirmasi: {e}")
        yield f"⚠️ Gagal eksekusi aksi: {e}"


def batalkan_tool_pending(session_id):
    """Dipanggil kalau user klik 'Batal'."""
    PENDING_TOOL_CALLS.pop(session_id, None)
    db.simpan_chat(session_id, "assistant", "(Aksi dibatalkan oleh Ian)")