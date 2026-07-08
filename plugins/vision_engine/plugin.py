import ollama
from database import db
from core.plugin_manager import BasePlugin

class VisionEnginePlugin(BasePlugin):
    def execute(self, session_id_raw: str, pertanyaan: str, filedata_b64: str, nama_file: str) -> dict:
        """Memproses gambar via Moondream, mencatat riwayat chat, dan mengembalikan deskripsi."""
        try:
            if not session_id_raw:
                session_id = db.buat_sesi_baru(judul=f"📷 {nama_file[:15]}")
            else:
                session_id = int(session_id_raw)

            # 1. Simpan pesan user ke history chat database
            db.simpan_chat(session_id, "user", f"[Uploaded image: {nama_file}] {pertanyaan}")

            # 2. Panggil model vision (Moondream) via Ollama
            print(f"[PLUGIN VISION] Analyzing image '{nama_file}' with Moondream...")
            hasil_vision = ollama.chat(
                model='moondream',
                messages=[{
                    'role': 'user',
                    'content': pertanyaan,
                    'images': [filedata_b64]
                }]
            )
            deskripsi = hasil_vision['message']['content']

            # 3. Simpan respons asisten ke database
            db.simpan_chat(session_id, "assistant", deskripsi)

            return {
                "status": "success",
                "session_id": session_id,
                "deskripsi": deskripsi
            }
        except Exception as e:
            print(f"[PLUGIN VISION ERROR] {e}")
            return {"status": "error", "message": str(e)}