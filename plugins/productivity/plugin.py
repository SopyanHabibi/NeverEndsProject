import datetime
from database import db
from core.plugin_manager import BasePlugin

class ProductivityPlugin(BasePlugin):
    def execute(self, nama_aplikasi: str) -> str:
        """Hitung rata-rata jam mulai & durasi historis, bandingin sama hari ini."""
        print(f"[PLUGIN PRODUCTIVITY] Fungsi dipanggil dengan nama_aplikasi='{nama_aplikasi}'")
        riwayat = db.ambil_riwayat_aktivitas(nama_aplikasi, hari=14)

        if len(riwayat) < 3:
            return f"Not enough history yet for {nama_aplikasi} to spot a pattern, Ian. Keep using it and ask me again in a few days!"

        BATAS_MENIT_WAJAR = 960  # 16 jam, di atas ini dianggap data corrupt (sisa restart/sleep, dll)

        def durasi_valid(s):
            try:
                mulai = datetime.datetime.fromisoformat(s['mulai'])
                selesai = datetime.datetime.fromisoformat(s['selesai'])
                return (selesai - mulai).total_seconds() / 60 <= BATAS_MENIT_WAJAR
            except Exception:
                return False

        riwayat = [r for r in riwayat if durasi_valid(r)]

        hari_ini = datetime.date.today().isoformat()
        sesi_hari_ini = [r for r in riwayat if r['mulai'].startswith(hari_ini)]
        sesi_historis = [r for r in riwayat if not r['mulai'].startswith(hari_ini)]

        # Tambahin sesi yang LAGI BERJALAN sekarang (belum 'selesai')
        sesi_aktif_sekarang = db.ambil_sesi_terbuka()
        for sesi in sesi_aktif_sekarang:
            if sesi["nama_aplikasi"] == nama_aplikasi:
                conn_temp = __import__('sqlite3').connect(db.DB_FILE)
                cur_temp = conn_temp.cursor()
                cur_temp.execute("SELECT waktu_mulai FROM aktivitas_log WHERE id = ?", (sesi["id"],))
                waktu_mulai_aktif = cur_temp.fetchone()[0]
                conn_temp.close()
                if waktu_mulai_aktif.startswith(hari_ini):
                    sesi_hari_ini.append({"mulai": waktu_mulai_aktif, "selesai": datetime.datetime.now().isoformat()})

        def hitung_durasi_menit(sesi):
            total = 0
            for s in sesi:
                mulai = datetime.datetime.fromisoformat(s['mulai'])
                selesai = datetime.datetime.fromisoformat(s['selesai'])
                total += (selesai - mulai).total_seconds() / 60
            return total

        def rata_jam_mulai(sesi):
            jam_list = [datetime.datetime.fromisoformat(s['mulai']).hour + datetime.datetime.fromisoformat(s['mulai']).minute / 60 for s in sesi]
            return sum(jam_list) / len(jam_list) if jam_list else None

        if not sesi_historis:
            return f"Today's your first tracked day with {nama_aplikasi}, Ian. Check back tomorrow for a real comparison!"

        durasi_historis_per_hari = hitung_durasi_menit(sesi_historis) / max(1, len(set(s['mulai'][:10] for s in sesi_historis)))
        durasi_hari_ini = hitung_durasi_menit(sesi_hari_ini)
        jam_mulai_historis = rata_jam_mulai(sesi_historis)
        jam_mulai_hari_ini = rata_jam_mulai(sesi_hari_ini)

        persen_perubahan = ((durasi_hari_ini - durasi_historis_per_hari) / durasi_historis_per_hari * 100) if durasi_historis_per_hari > 0 else 0

        hasil = (
            f"Historical average for {nama_aplikasi}: starts around {jam_mulai_historis:.1f}h, "
            f"~{durasi_historis_per_hari:.0f} min/day. "
        )
        if sesi_hari_ini:
            hasil += (
                f"Today: started around {jam_mulai_hari_ini:.1f}h, {durasi_hari_ini:.0f} min so far. "
                f"That's {abs(persen_perubahan):.0f}% {'lower' if persen_perubahan < 0 else 'higher'} than usual."
            )
        else:
            hasil += f"No {nama_aplikasi} activity detected yet today."

        print(f"[PLUGIN PRODUCTIVITY] sesi_hari_ini={len(sesi_hari_ini)} sesi_historis={len(sesi_historis)}")
        return hasil