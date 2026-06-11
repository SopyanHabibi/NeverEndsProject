# fitur/profil.py
import json
import os
from config import FILE_MEMORI

def inisialisasi_memori():
    """Membuat file memori dengan struktur default jika belum ada."""
    if not os.path.exists(FILE_MEMORI):
        # Kita mulai dengan kamus (dictionary) kosong agar dinamis
        default_data = {}
        with open(FILE_MEMORI, "w") as file:
            json.dump(default_data, file, indent=4)

def baca_memori():
    inisialisasi_memori()
    with open(FILE_MEMORI, "r") as file:
        return json.load(file)

def simpan_memori(kunci, nilai):
    """Menyimpan atau memperbarui informasi apa pun berdasarkan kunci dan nilai."""
    data = baca_memori()
    data[kunci] = nilai  # Mengisi kunci secara dinamis (bisa nama, umur, hobi, dll)
    with open(FILE_MEMORI, "w") as file:
        json.dump(data, file, indent=4)

def ringkas_profil():
    """Menampilkan seluruh informasi yang ada di dalam database memori."""
    data = baca_memori()
    
    print("\n===========================================")
    print("  👤 PROFIL PENGGUNA (DIINGAT OLEH NEIRA)  ")
    print("===========================================")
    
    if not data:
        print("Neira: Belum ada data profil yang tersimpan.")
        print("===========================================")
        return

    # Looping ini akan otomatis mencetak apa pun yang ada di file JSON
    for kunci, nilai in data.items():
        # Mengubah format kunci agar rapi (misal: "makanan_favorit" -> "MAKANAN FAVORIT")
        kunci_rapi = kunci.replace("_", " ").upper()
        print(f"➤  {kunci_rapi} : {nilai}")

    print("-------------------------------------------")
    # print(f"Neira: Total ada {len(data)} informasi tentangmu yang tersimpan.")
    print("===========================================")