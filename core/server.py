import json
import threading
import time
import os
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from database import db
from core.llm_engine import proses_perintah_backend, plugin_manager

_pending_vscode = {"data": None}
_pending_lock = threading.Lock()

class NeiraServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 1. STREAMING API ENDPOINT (SSE) -> Sinkron dengan Chat.js asli
        if parsed_url.path == '/api/chat-stream':
            pesan_user = query_params.get('pesan', [''])[0]
            session_id_raw = query_params.get('session_id', [''])[0]

            if not session_id_raw or session_id_raw == 'null' or session_id_raw == 'undefined':
                session_id = db.buat_sesi_baru(judul="Chat Baru")
                sesi_baru = True
            else:
                try:
                    session_id = int(session_id_raw)
                    sesi_baru = False
                except:
                    session_id = db.buat_sesi_baru(judul="Chat Baru")
                    sesi_baru = True

            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()

            # Format identitas sesi baru untuk UI
            self.wfile.write(f"data: [SESSION_ID_ASSIGNED:{session_id}]\n\n".encode('utf-8'))
            self.wfile.flush()

            try:
                generator = proses_perintah_backend(pesan_user, session_id)
                respons_lengkap = ""
                for token in generator:
                    if token:
                        respons_lengkap += token
                        token_aman = token.replace("\n", "[NEWLINE]")
                        payload = json.dumps({"text": token_aman})
                        self.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                        self.wfile.flush()

                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()

                if sesi_baru:
                    def _generate_judul_background():
                        from core.llm_engine import generate_judul_sesi
                        judul_baru = generate_judul_sesi(pesan_user, respons_lengkap)
                        db.ubah_judul_sesi(session_id, judul_baru)
                    threading.Thread(target=_generate_judul_background, daemon=True).start()

            except Exception as e:
                print(f"Error streaming: {e}")
                try:
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                except:
                    pass
            return

        # 2. AMBIL DAFTAR HISTORI CHAT BERDASARKAN KATEGORI
        elif parsed_url.path == '/api/sessions':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                kat = query_params.get('kategori', ['general'])[0]
                sesi_db = db.ambil_semua_sesi_by_kategori(kat)
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
            
        elif parsed_url.path == '/api/vscode/pending':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            with _pending_lock:
                pending = _pending_vscode["data"]
                _pending_vscode["data"] = None
            self.wfile.write(json.dumps(pending or {}).encode('utf-8'))
            return
        
        elif parsed_url.path == '/api/workflows':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                data = db.ambil_semua_workflow()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            except Exception as e:
                print(f"Gagal ambil workflow: {e}")
                self.wfile.write(json.dumps([]).encode('utf-8'))
            return
        
        elif parsed_url.path == '/api/tool-confirm-stream':
            session_id_raw = query_params.get('session_id', [''])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            try:
                session_id = int(session_id_raw)
                from core.llm_engine import eksekusi_tool_terkonfirmasi
                generator = eksekusi_tool_terkonfirmasi(session_id)
                for token in generator:
                    if token:
                        token_aman = token.replace("\n", "[NEWLINE]")
                        payload = json.dumps({"text": token_aman})
                        self.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                        self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except Exception as e:
                print(f"Error tool-confirm-stream: {e}")
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            return
            
        else:
            # Tetap layani asset statis (HTML/JS/CSS) jika diakses langsung lewat localhost:5000
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8')) if content_length > 0 else {}
        
        # 1. VS CODE INTEGRATION ENTRY POINT
        if self.path == '/api/vscode/ask':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                nama_project = data.get('projectName', 'Unknown Project')
                nama_file = data.get('fileName', 'Unknown File')
                kode_error = data.get('errorMessage', '')
                kode_diblok = data.get('selectedCode', '')

                session_id = db.cek_project_eksis(nama_project)
                if not session_id:
                    judul_baru = f"🛠️ Project: {nama_project}"
                    session_id = db.buat_sesi_project_baru(nama_project, judul=judul_baru)

                with _pending_lock:
                    _pending_vscode["data"] = {
                        "session_id": session_id,
                        "fileName": nama_file,
                        "selectedCode": kode_diblok,
                        "errorMessage": kode_error
                    }

                self.wfile.write(json.dumps({"status": "success", "session_id": session_id}).encode('utf-8'))
            except Exception as e:
                print(f"[VS CODE API ERROR] {e}")
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return
        
        # 2. UPLOAD DOKUMEN PLUGIN
        elif self.path == '/api/upload-document':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                hasil = plugin_manager.execute_plugin(
                    "document_analyzer", int(data.get('session_id')), data.get('filename'), data.get('filedata')
                )
                self.wfile.write(json.dumps(hasil or {"status": "error"}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return
        
        # 3. UPLOAD IMAGE VISION PLUGIN
        elif self.path == '/api/upload-image':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                hasil = plugin_manager.execute_plugin(
                    "vision_engine", data.get('session_id'), data.get('pertanyaan'), data.get('filedata'), data.get('filename')
                )
                self.wfile.write(json.dumps(hasil or {"status": "error"}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        # 4. RE-NAME HISTORI CHAT
        elif self.path == '/api/session/rename':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                id_sesi = int(data.get('id'))
                judul_baru = data.get('title')
                db.ubah_judul_sesi(id_sesi, judul_baru)
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                print(f"Error rename: {e}")
            return

        # 5. HAPUS HISTORI CHAT
        elif self.path == '/api/session/delete':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                id_sesi = int(data.get('id'))
                db.hapus_sesi(id_sesi)
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                print(f"Error delete: {e}")
            return

        # 6. SHUTDOWN BEACON VIA CLOSE TAB (DINONAKTIFKAN SEMENTARA - dev mode)
        elif self.path == '/api/shutdown':
            self.send_response(200)
            self.end_headers()
            print("\n⚠️  Shutdown request diterima tapi diabaikan (dev mode aktif).")
            # def kill():
            #     time.sleep(0.5)
            #     os._exit(0)
            # threading.Thread(target=kill).start()
            return
        
        # 7. WORKFLOW CRUD
        elif self.path == '/api/workflow/create':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                id_baru = db.tambah_workflow(
                    data.get('nama'),
                    data.get('trigger_type'),
                    json.dumps(data.get('trigger_config')),
                    json.dumps(data.get('actions'))
                )
                self.wfile.write(json.dumps({"status": "success", "id": id_baru}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return
        
        # 8. BATALKAN TOOL CALL YANG PENDING
        elif self.path == '/api/tool-cancel':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                from core.llm_engine import batalkan_tool_pending
                batalkan_tool_pending(int(data.get('session_id')))
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        elif self.path == '/api/workflow/toggle':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                db.update_status_workflow(int(data.get('id')), bool(data.get('enabled')))
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        elif self.path == '/api/workflow/delete':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                db.hapus_workflow(int(data.get('id')))
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return


def _workflow_scheduler_loop():
    """Cek workflow time-based tiap 30 detik."""
    import time as time_module
    from core.llm_engine import plugin_manager as pm

    while True:
        try:
            pm.execute_plugin("workflow_engine", mode="check_time_triggers")
        except Exception as e:
            print(f"[Scheduler] Error: {e}")
        time_module.sleep(30)


def jalankan_server_neira():
    server_address = ('', 5000)
    httpd = ThreadingHTTPServer(server_address, NeiraServerHandler)

    scheduler_thread = threading.Thread(target=_workflow_scheduler_loop, daemon=True)
    scheduler_thread.start()

    print("🌍 Neira Premium Server Sync running on http://localhost:5000")
    httpd.serve_forever()
