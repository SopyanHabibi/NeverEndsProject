# fitur/cuaca.py
import urllib.request
import json
import urllib.parse
from fitur import profil

def cek_cuaca():
    """Mengambil data lokasi dan menyajikan kondisi saat ini serta prediksi cuaca."""
    try:
        data_user = profil.baca_memori()
        kota = data_user.get("lokasi", data_user.get("kota", "Medan"))
    except Exception:
        kota = "Medan"
        
    print(f"✨ Mengambil laporan dan prediksi cuaca untuk Kota {kota.capitalize()}...")
    
    url = f"https://wttr.in/{urllib.parse.quote(kota)}?format=j1"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            # Kamus terjemahan cuaca
            kamus_cuaca = {
                "Sunny": "Cerah Penuh☀️", "Clear": "Cerah Penuh☀️",
                "Partly cloudy": "Berawan Sebagian⛅", "Cloudy": "Berawan☁️",
                "Overcast": "Mendung Gelap☁️", "Mist": "Berkabut Tipis🌫️",
                "Fog": "Kabut🌫️", "Light rain": "Hujan Ringan🌧️",
                "Light drizzle": "Gerimis Ringan",
                "Moderate rain": "Hujan Sedang🌧️", "Heavy rain": "Hujan Lebat⛈️",
                "Patchy rain nearby": "Gerimis di Sekitar🌧️",
                "Thundery outbreaks possible": "Potensi Hujan Badai⚡"
            }
            
            # ==================== 1. KONDISI SEKARANG ====================
            kondisi_saat_ini = data['current_condition'][0]
            suhu_sekarang = kondisi_saat_ini['temp_C']
            kelembapan = kondisi_saat_ini['humidity']
            desc_sekarang = kondisi_saat_ini['weatherDesc'][0]['value']
            langit_sekarang = kamus_cuaca.get(desc_sekarang, desc_sekarang)
            
            # ==================== 2. ANALISIS HUJAN HARI INI ====================
            # Mengambil data hari pertama (hari ini)
            cuaca_hari_ini = data['weather'][0]
            
            # wttr.in membagi hari jadi beberapa segmen waktu (hourly). 
            # Kita ambil rata-rata peluang hujan (chanceofrain) terbesar dari segmen yang ada.
            peluang_hujan_maks = 0
            for segmen in cuaca_hari_ini['hourly']:
                peluang = int(segmen['chanceofrain'])
                if peluang > peluang_hujan_maks:
                    peluang_hujan_maks = peluang
            
            # Tentukan kesimpulan prediksi hari ini berdasarkan persentase
            if peluang_hujan_maks >= 70:
                kesimpulan_hujan = f"⚠️  Kemungkinan BESAR akan hujan ({peluang_hujan_maks}%). Sedia payung, Ian!"
            elif 30 <= peluang_hujan_maks < 70:
                kesimpulan_hujan = f"⛅  Ada potensi hujan ringan/gerimis ({peluang_hujan_maks}%)."
            else:
                kesimpulan_hujan = f"✅  Aman ({peluang_hujan_maks}%). Kemungkinan kecil terjadi hujan hari ini."

            # ==================== 3. PREDIKSI CUACA BESOK ====================
            # Mengambil data hari kedua (besok)
            cuaca_besok = data['weather'][1]
            suhu_min_besok = cuaca_besok['mintempC']
            suhu_max_besok = cuaca_besok['maxtempC']
            
            # Mengambil gambaran cuaca besok pagi (segmen jam 9 pagi biasanya indeks ke-3)
            desc_besok = cuaca_besok['hourly'][3]['weatherDesc'][0]['value']
            langit_besok = kamus_cuaca.get(desc_besok, desc_besok)

            # ==================== OUTPUT LAPORAN LENGKAP ====================
            print("\n===========================================")
            print(f"🌦️     LAPORAN CUACA KOTA {kota.upper()}     ")
            print("===========================================")
            print(f"📍 KONDISI SAAT INI:")
            print(f"   ➤  Langit       : {langit_sekarang}")
            print(f"   ➤  Suhu Udara   : {suhu_sekarang}°C")
            print(f"   ➤  Kelembapan   : {kelembapan}%")
            print("-------------------------------------------")
            print(f"🔮 ANALISIS HUJAN HARI INI:")
            print(f"   ➤  Status       : {kesimpulan_hujan}")
            print("-------------------------------------------")
            print(f"📅 PREDIKSI CUACA BESOK:")
            print(f"   ➤  Langit       : {langit_besok}")
            print(f"   ➤  Rentang Suhu : {suhu_min_besok}°C - {suhu_max_besok}°C")
            print("===========================================")
            
    except urllib.error.URLError:
        print("❌ Gagal terhubung ke server cuaca. Coba cek koneksi internetmu.")
    except Exception as e:
        print(f"❌ Gagal memproses prediksi cuaca. Error: {e}")