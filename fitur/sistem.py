# fitur sistem.py

import subprocess
import os

def buka_aplikasi(nama_aplikasi):
    """Membuka aplikasi desktop berdasarkan kata kunci perintah user."""
    

    # Peta alamat aplikasi
    username_pc = os.getlogin()
    peta_aplikasi = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "vscode": r"C:\Users\sopya\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "notepad": "notepad.exe", # Notepad bawaan Windows bisa langsung dipanggil namanya
        "calc": "calc.exe",
    }
    
    # ambil path asli berdasarkan username laptop Windows secara dinamis
    # user_pc = os.getlogin()
    # if nama_aplikasi == "vscode": 
    #     peta_aplikasi["vscode"] = f"C:\\Users\\{Neira}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
        
    if nama_aplikasi in peta_aplikasi:
        path_aplikasi = peta_aplikasi[nama_aplikasi]

        try:
            print(f"Neira: Okeyy, membuka {nama_aplikasi.upper()}...")
            # popen digunakan agar Neira tidak ikutan membeku saat aplikasi dibuka
            subprocess.Popen(path_aplikasi)
        except FileNotFoundError:
            print(f"❌ Neira: Waduh, saya tidak menemukan file {nama_aplikasi} di alamat tersebut.")
            print("💡 Tips: Coba cek alamat instalasi aplikasi tersebut di laptopmu lalu sesuaikan di 'fitur/sistem.py'.")
        except Exception as e:
            print(f"❌ Neira: Gagal membuka aplikasi. Error: {e}")
    else:
        print(f"Neira: Maaf, aplikasi '{nama_aplikasi}' belum terdaftar di sistem saya.")
        

def buka_workspace(nama_workspace):
    """Membuka sekelompok aplikasi sekaligus berdasarkan tema aktivitas."""

    # kumpulan profil workspace
    peta_workspace = {
        "ngoding": ["vscode", "chrome"],               # Membuka VS Code + Chrome sekaligus
        "kuliah": ["chrome", "notepad", "calc"],       # Membuka Chrome + Notepad + Kalkulator sekaligus
        "santai": ["chrome"]
    }
    
    if nama_workspace in peta_workspace:
        daftar_aplikasi = peta_workspace[nama_workspace]
        print(f"Neira: Membuka workspace [{nama_workspace.upper()}]...")

        # lakukan perulangan untuk membuka aplikasi satu per satu secara asinkron
        for aplikasi in daftar_aplikasi:
            print(f"➔ Membuka {aplikasi}...")
            buka_aplikasi(aplikasi)

        print(f"Neira: Workspace {nama_workspace} berhasil dibuka!")
    else:
        print(f"Neira: Workspace '{nama_workspace}' tidak ditemukan. Coba 'ngoding' atau 'kuliah'.")
        
def buka_folder(nama_folder):
    """Membuka folder spesifik di File Explorer berdasarkan shortcut dari user."""
    username_pc = os.getlogin()

    # Peta alamat folder
    peta_folder = {
        "kuliah": rf"D:\Kuliah",
        "project": rf"D:\Kuliah\NeverEndProjects",
        "download": f"C:\\Users\\{username_pc}\\Downloads",
        "documents": f"C:\\Users\\{username_pc}\\Documents"
    }
    
    if nama_folder in peta_folder:
        path_target = peta_folder[nama_folder]

        # pastikan folder ada di dalam laptop
        if os.path.exists(path_target):
            print(f"Neira: Okeyy, membuka folder {nama_folder.upper()}...")
            # memanggil explorer.exe diikuti dengan alamat folder target
            subprocess.Popen(f'explorer "{path_target}"')
        else:
            print(f"❌ Neira: Folder '{nama_folder}' tidak ditemukan di jalur: {path_target}")
            print("💡 Tips: SINKRONKAN alamat foldermu terlebih dahulu di 'fitur/sistem.py'.")
    else:
        print(f"Neira: Folder '{nama_folder}' belum terdaftar. Kamu bisa mendaftarkannya di fitur/sistem.py.")
        
def atur_shutdown_timer(menit):
    """Mengatur waktu hitung mundur untuk mematikan laptop otomatis."""
    # konversi menit ke detik karena argumen windows menggunakan satuan detik
    detik = menit * 60
    
    try:
        # /s = shutdown, /t = waktu tunggu dalam detik
        subprocess.Popen(f"shutdown /s /t {detik}", shell=True)
        print(f"⚠️ Neira: SISTEM AKAN MATI OTOMATIS DALAM {menit} MENIT!")
        print("💡 Tips: Jika ingin membatalkan, ketik perintah 'batal matikan laptop'.")
    except Exception as e:
        print(f"❌ Neira: Gagal mengatur timer shutdown. Error: {e}")
        
def batalkan_shutdown():
    """Membatalkan perintah shutdown yang sedang berjalan."""
    try:
        # /a = abort (batalkan perintah shutdown)
        subprocess.Popen("shutdown /a", shell=True)
        print("✅ Neira: Perintah otomatisasi shutdown BERHASIL DIBATALKAN. Laptop aman!")
    except Exception:
        print("❌ Neira: Gagal membatalkan. Mungkin memang tidak ada timer yang aktif saat ini.")