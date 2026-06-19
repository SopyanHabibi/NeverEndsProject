# fitur/profil.py
# import json
import os
# from config import FILE_MEMORI
from database import db


def ringkas_profil():
    """Menampilkan seluruh informasi database memori dengan format Markdown Premium via SQLite."""
    # Ambil data langsung dari SQLite
    data = db.ambil_semua_profil()
    
    yield "### 👤 User Profile Summary\n"
    yield "*Here is everything I remember about you, Ian:*\n\n---\n"
    
    if not data:
        yield "No profile data has been stored in SQLite yet."
        return

    for kunci, nilai in data.items():
        kunci_rapi = kunci.replace("_", " ").upper()
        yield f"• **{kunci_rapi}**: {nilai}\n"

    yield "\n---\n"
    yield f"*Total: {len(data)} dynamic information vectors saved in SQLite database.*"