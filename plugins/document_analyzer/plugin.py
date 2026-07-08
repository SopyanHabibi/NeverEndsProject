import os
import base64
import tempfile
from database import db
from tools import dokumen
from core.plugin_manager import BasePlugin

class DocumentAnalyzerPlugin(BasePlugin):
    def execute(self, session_id: int, nama_file: str, filedata_b64: str) -> dict:
        """Mengekstrak file dokumen b64, memecah jadi chunks, lalu menyimpannya ke database."""
        try:
            ekstensi = nama_file.split('.')[-1].lower()

            if ekstensi not in ('pdf', 'docx', 'pptx'):
                return {"status": "error", "message": "Format tidak didukung. Cuma PDF, DOCX, PPTX."}

            # Decode Base64 ke bytes
            file_bytes = base64.b64decode(filedata_b64)
            
            # Tulis ke file temporary sementara untuk diproses ekstrak teks
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ekstensi}") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            # Ekstrak teks menggunakan modul tools dokumen asli
            teks = dokumen.ekstrak_teks(tmp_path, ekstensi)
            
            # Hapus file temporary setelah teks diambil
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            if not teks.strip():
                return {"status": "error", "message": "Gagal membaca isi dokumen, atau dokumen kosong."}

            # Pecah teks menjadi chunks
            chunks = dokumen.pecah_jadi_chunks(teks)
            
            # Hapus chunks lama pada sesi ini (hanya 1 dokumen aktif per sesi)
            db.hapus_chunks_sesi(session_id)
            
            # Simpan setiap chunk ke database
            for i, chunk in enumerate(chunks):
                db.simpan_chunk_dokumen(session_id, nama_file, i, chunk)

            return {
                "status": "success",
                "filename": nama_file,
                "chunks": len(chunks)
            }
            
        except Exception as e:
            print(f"[PLUGIN DOCUMENT ANALYZER ERROR] {e}")
            return {"status": "error", "message": str(e)}