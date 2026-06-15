import datetime
import os
import json
import threading
import time
import winsound
import keyboard
from playsound import playsound

FILE_SESI_FOKUS = "database/sesi_fokus.json"

sesi_sedang_berjalan = False
waktu_mulai_session = None
durasi_target = 0

def hitung_mundur_otomatis(menit):
    """Fungsi latar belakang dengan deteksi tombol spasi global (Bisa di mana saja)."""
    global sesi_sedang_berjalan, waktu_mulai_session
    
    # Jalankan hitung mundur sesuai durasi sesi
    time.sleep(menit * 60)
    
    if sesi_sedang_berjalan:
        waktu_sekarang = datetime.datetime.now()
        
        print(f"\n🚨 [ALARM NEIRA]: WAKTU SESI FOKUS {menit} MENIT HABIS!!!")
        print("⌨️  [INFO]: Tekan tombol SPASI untuk mematikan alarm...")
        print("Kamu: ", end="", flush=True)
        
        try:
            # Nyalakan alarm looping di background
            winsound.PlaySound('alarm.wav', winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC)
        except Exception:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            
        # --- DETEKSI TOMBOL GLOBAL (SOLUTION) ---
        # Program akan 'menunggu' sampai tombol space ditekan, di mana pun kursor berada
        keyboard.wait('space')
        
        # Matikan suara seketika setelah spasi ditekan
        winsound.PlaySound(None, winsound.SND_PURGE)
        print("\n🔊 Alarm dimatikan via Global Hotkey.")
        print("Kamu: ", end="", flush=True)
            
        # Amankan Data ke JSON
        simpan_ke_database(waktu_mulai_session, waktu_sekarang, menit)
        
        # Reset Status Sesi
        sesi_sedang_berjalan = False
        waktu_mulai_session = None

def mulai_sesi(menit):
    """Memulai sesi fokus tanpa mengunci terminal menggunakan bantuan threading."""
    global sesi_sedang_berjalan, waktu_mulai_session, durasi_target
    
    if sesi_sedang_berjalan:
        print("Kamu masih berada dalam sesi fokus aktif! Selesaikan dulu sesi ini atau tunggu sampai alarm berbunyi.")
        return
        
    sesi_sedang_berjalan = True
    waktu_mulai_session = datetime.datetime.now()
    durasi_target = menit
    
    jam_mulai_str = waktu_mulai_session.strftime("%I:%M %p")
    estimasi_selesai = waktu_mulai_session + datetime.timedelta(minutes=menit)
    
    print(f"Sesi fokus selama {menit} menit DIMULAI pada {jam_mulai_str}.")
    print(f"📌 Alarm otomatis diatur ke jam {estimasi_selesai.strftime('%I:%M %p')}. Selamat belajar, Ian!")
    
    # MEMBUAT JALUR BARU (THREAD): Menjalankan hitung mundur di balik layar
    thread_kacamata = threading.Thread(target=hitung_mundur_otomatis, args=(menit,), daemon=True)
    thread_kacamata.start()

def batalkan_sesi():
    """Fitur opsional jika di tengah jalan kamu ingin menyerah atau membatalkan sesi."""
    global sesi_sedang_berjalan, waktu_mulai_session
    
    if not sesi_sedang_berjalan:
        print("Tidak ada sesi fokus yang sedang berjalan untuk dibatalkan.")
        return
        
    sesi_sedang_berjalan = False
    waktu_mulai_session = None
    print("❌ Sesi fokus berhasil dibatalkan. Data tidak akan disimpan ke statistik.")

def simpan_ke_database(mulai, selesai, durasi):
    """Fungsi internal untuk menyimpan data mentah ke JSON."""
    if not os.path.exists(FILE_SESI_FOKUS):
        data = {"sesi_fokus": []}
    else:
        try:
            with open(FILE_SESI_FOKUS, "r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = {"sesi_fokus": []}
            
    sesi_baru = {
        "tanggal": mulai.strftime("%Y-%m-%d"),
        "mulai": mulai.strftime("%H:%M:%S"),
        "selesai": selesai.strftime("%H:%M:%S"),
        "durasi_menit": durasi
    }
    
    data["sesi_fokus"].append(sesi_baru)
    with open(FILE_SESI_FOKUS, "w") as file:
        json.dump(data, file, indent=4)

def lihat_statistik_fokus():
    """Menampilkan ringkasan statistik harian dan mingguan dari JSON (Sama seperti kemarin)."""
    # ... (Isi fungsi lihat_statistik_fokus kamu yang kemarin tetap sama, tidak perlu diubah) ...
    if not os.path.exists(FILE_SESI_FOKUS):
        print("Belum ada riwayat sesi fokus.")
        return
    with open(FILE_SESI_FOKUS, "r") as file:
        data = json.load(file)
    sesi_list = data.get("sesi_fokus", [])
    hari_ini_str = datetime.datetime.now().strftime("%Y-%m-%d")
    tujuh_hari_lalu = datetime.datetime.now() - datetime.timedelta(days=7)
    sesi_hari_ini = [s for s in sesi_list if s["tanggal"] == hari_ini_str]
    total_durasi_minggu = sum(s["durasi_menit"] for s in sesi_list if datetime.datetime.strptime(s["tanggal"], "%Y-%m-%d") >= tujuh_hari_lalu)
    
    print("\n===========================================")
    print("      ⏱️  RIWAYAT SESI FOKUS (POMODORO)     ")
    print("===========================================")
    print(f"📆  HARI INI ({datetime.datetime.now().strftime('%d %B %Y')}):")
    if not sesi_hari_ini:
        print("   (Belum ada sesi fokus harian)")
    else:
        total_durasi_hari = 0
        for indeks, s in enumerate(sesi_hari_ini, 1):
            jam_m = datetime.datetime.strptime(s["mulai"], "%H:%M:%S").strftime("%I:%M %p")
            jam_s = datetime.datetime.strptime(s["selesai"], "%H:%M:%S").strftime("%I:%M %p")
            print(f"   [Sesi {indeks}] -> 🕒 {jam_m} - {jam_s} | ⏳ {s['durasi_menit']} mnt")
            total_durasi_hari += s["durasi_menit"]
        print(f"➔  Total Hari Ini: {len(sesi_hari_ini)} Sesi ({total_durasi_hari} menit)")
    print("-------------------------------------------")
    print(f"📅  RINGKASAN MINGGUAN (7 Hari Terakhir):")
    print(f"➤   Total Waktu Fokus: {total_durasi_minggu} menit (~{round(total_durasi_minggu/60, 1)} jam)")
    print("===========================================")