import urllib.request
import json
from fitur import profil

def cek_cuaca():
    """Mengambil data lokasi dari memori dan menarik data cuaca dari wttr.in."""

    # ambil data kota dari database
    try:
        data_user = profil.baca_memori()
        # mengambil info 'lokasi' atau 'kota'. Jika tidak ada, default ke 'Medan'
        kota = data_user.get("lokasi", data_user.get("kota", "Medan"))
    except Exception:
        kota = "Medan"

    print(f"Neira: Mengambil laporan cuaca terbaru untuk kota {kota.capitalize()}...")

    # Tembak API wttr.in dengan format JSON (format=?j1)
    # Jalur URL di-encode agar aman jika nama kota mengandung spasi
    url = f"https://wttr.in/{urllib.parse.quote(kota)}?format=j1"
    
    try:
        # Mengonstruksi request dengan User-Agent agar tidak diblokir server
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            # Parsing (Ekstrak) Data mentah JSON dari wttr.in
            kondisi_saat_ini = data['current_condition'][0]

            suhu = kondisi_saat_ini['temp_C']
            kelembapan = kondisi_saat_ini['humidity']

            # Deskripsi cuaca dalam bahasa Inggris dari API (misal: "Sunny", "Moderate Rain")
            cuaca_desc = kondisi_saat_ini['weatherDesc'][0]['value']

            # Terjemahan sederhana ke Bahasa Indonesia biar Neira makin akrab
            kamus_cuaca = {
                "Sunny": "Cerah Penuh☀️",
                "Clear": "Cerah Penuh☀️",
                "Partly cloudy": "Berawan Sebagian⛅",
                "Cloudy": "Berawan☁️",
                "Overcast": "Mendung Gelap☁️",
                "Mist": "Berkabut Tipis🌫️",
                "Fog": "Kabut🌫️",
                "Light rain": "Hujan Ringan🌧️",
                "Moderate rain": "Hujan Sedang🌧️",
                "Heavy rain": "Hujan Lebat⛈️",
                "Patchy rain nearby": "Gerimis di Sekitar🌧️",
                "Thundery outbreaks possible": "Potensi Hujan Badai⚡"
            }
            
            langit = kamus_cuaca.get(cuaca_desc, cuaca_desc)

            # Cetak output
            print("\n===========================================")
            print(f"🌦️     LAPORAN CUACA KOTA {kota.upper()}     ")
            print("===========================================")
            print(f"  ➤  Kondisi Langit : {langit}")
            print(f"  ➤  Suhu Udara     : {suhu}°C")
            print(f"  ➤  Kelembapan     : {kelembapan}%")
            print("===========================================")
            
    except urllib.error.URLError:
        print("❌ Neira: Gagal terhubung ke server cuaca. Pastikan laptopmu tersambung ke internet ya, Ian!")
    except Exception as e:
        print(f"❌ Neira: Waduh, ada kendala saat membaca data cuaca. Error: {e}")