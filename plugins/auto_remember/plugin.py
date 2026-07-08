import json
import ollama
from database import db
from core.plugin_manager import BasePlugin

class AutoRememberPlugin(BasePlugin):
    def execute(self, perintah_user: str, jawaban_neira: str):
        """Menyuruh Qwen mendeteksi informasi penting secara otomatis untuk disimpan ke SQLite."""
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
                    # Kalau modelnya ngasih list (misal hobbies: [...]), gabungin jadi string
                    if isinstance(nilai, list):
                        nilai = ", ".join(str(v) for v in nilai)
                    elif not isinstance(nilai, str):
                        nilai = str(nilai)
                    
                    print(f"[PLUGIN AUTO-REMEMBER] Saved -> {kunci}: {nilai}")
                    db.simpan_profil(kunci, nilai)
                    
        except Exception as e:
            print(f"[PLUGIN AUTO-REMEMBER ERROR]: {e}")