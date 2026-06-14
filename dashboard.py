"""
Neira AI Dashboard
==================
Letakkan file ini sejajar dengan Neira.py di root project kamu.

Struktur folder:
    project_kamu/
    ├── Neira.py
    ├── neira_dashboard.py   ← file ini
    ├── fitur/
    └── ...

Requirements:
    pip install customtkinter
"""

import customtkinter as ctk
import tkinter as tk
import threading
import datetime
import sys
import io
import os
from PIL import Image, ImageTk

# ─────────────────────────────────────────────────────────────────────────────
#  REDIRECT print() → GUI
# ─────────────────────────────────────────────────────────────────────────────
class _PrintCapture(io.StringIO):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback
        self._original = sys.stdout

    def write(self, text):
        self._original.write(text)
        if text.strip():
            self._callback(text.strip())

    def flush(self):
        self._original.flush()


# ─────────────────────────────────────────────────────────────────────────────
#  PROSESOR PERINTAH NEIRA
# ─────────────────────────────────────────────────────────────────────────────
def proses_perintah_neira(perintah: str) -> str:
    import datetime
    import webbrowser

    try:
        from fitur import utilitas, profil, produktivitas, jadwal, fokus, sistem, cuaca, ai
    except ImportError as e:
        return f"⚠️ Gagal import modul fitur: {e}\nPastikan neira_dashboard.py ada di folder root project."

    perintah_asli = perintah
    perintah = perintah.lower().strip()

    if perintah == "":
        return ""

    captured = []
    capture_io = _PrintCapture(lambda t: captured.append(t))
    sys.stdout = capture_io

    try:
        keyword_dikenali = False

        if utilitas.cek_typo_nama(perintah):
            print("Hmm... Mungkin maksudmu 'Neira'? Typo sedikit tuh, hehe.")
            keyword_dikenali = True

        elif any(x in perintah for x in ["halo", "hai", "hi", "pagi", "siang", "sore", "malam"]):
            try:
                data = profil.baca_memori()
                nama_user = data.get("nama", "kamu")
            except Exception:
                nama_user = "kamu"
            jam = datetime.datetime.now().hour
            if jam < 12:
                print(f"Halo {nama_user}! Semangat produktifnya hari ini.")
            elif jam < 18:
                print(f"Halo {nama_user}! Ada yang bisa aku bantu?")
            else:
                print(f"Halo {nama_user}! Jangan lupa istirahat yang cukup ya.")
            keyword_dikenali = True

        elif any(x in perintah for x in ["apa kabar", "bagaimana kabarmu", "gimana kabarmu"]):
            print("Aku baik-baik aja, kalo kamu gimana?")
            keyword_dikenali = True

        elif "jam berapa" in perintah or "cek jam" in perintah:
            waktu = datetime.datetime.now().strftime("%I:%M %p")
            print(f"Sekarang jam {waktu}.")
            keyword_dikenali = True

        elif "buka google" in perintah:
            webbrowser.open("https://www.google.com")
            print("Okeyy, membuka Google di browsermu...")
            keyword_dikenali = True

        elif "buka youtube" in perintah:
            webbrowser.open("https://www.youtube.com")
            print("Okeyy, membuka YouTube...")
            keyword_dikenali = True

        elif "buka instagram" in perintah or "buka ig" in perintah:
            webbrowser.open("https://www.instagram.com")
            print("Okeyy, membuka Instagram...")
            keyword_dikenali = True

        elif "buka chrome" in perintah:
            sistem.buka_aplikasi("chrome")
            keyword_dikenali = True

        elif "buka vscode" in perintah or "buka vs code" in perintah:
            sistem.buka_aplikasi("vscode")
            keyword_dikenali = True

        elif "buka notepad" in perintah:
            sistem.buka_aplikasi("notepad")
            keyword_dikenali = True

        elif "buka kalkulator" in perintah:
            sistem.buka_aplikasi("calc")
            keyword_dikenali = True

        elif "mode ngoding" in perintah or "waktunya ngoding" in perintah:
            sistem.buka_workspace("ngoding")
            keyword_dikenali = True

        elif "mode kuliah" in perintah or "waktunya belajar" in perintah:
            sistem.buka_workspace("kuliah")
            keyword_dikenali = True

        elif "buka folder" in perintah:
            target = perintah.replace("buka folder", "").strip()
            if target:
                sistem.buka_folder(target)
            else:
                print("Folder apa yang mau dibuka? Contoh: 'buka folder kuliah'")
            keyword_dikenali = True

        elif "matikan laptop dalam" in perintah or "matikan pc dalam" in perintah:
            try:
                menit = int("".join(filter(str.isdigit, perintah)))
                sistem.atur_shutdown_timer(menit)
            except ValueError:
                print("Tolong sebutkan menitnya. Contoh: 'matikan laptop dalam 30 menit'")
            keyword_dikenali = True

        elif "batal matikan" in perintah or "batalkan shutdown" in perintah:
            sistem.batalkan_shutdown()
            keyword_dikenali = True

        elif any(x in perintah for x in ["siapa aku", "ringkas tentangku", "profilku"]):
            profil.ringkas_profil()
            keyword_dikenali = True

        elif "ku " in perintah:
            try:
                bagian_depan, isi_data = perintah.split(" ", 1)
                if bagian_depan.endswith("ku"):
                    kategori = bagian_depan[:-2]
                    if isi_data.strip():
                        profil.simpan_memori(kategori, isi_data.strip())
                        print(f"Sipp! Informasi '{kategori}' kamu berhasil diperbarui.")
                        keyword_dikenali = True
            except ValueError:
                pass

        if "tambah tugas" in perintah:
            produktivitas.add_tasks(perintah.replace("tambah tugas", "").strip())
            keyword_dikenali = True
        elif "lihat tugas" in perintah:
            produktivitas.view_tasks()
            keyword_dikenali = True
        elif "selesai tugas" in perintah or "selesai no" in perintah:
            try:
                produktivitas.mark_done(int("".join(filter(str.isdigit, perintah))))
            except ValueError:
                print("Contoh: 'selesai tugas 1'")
            keyword_dikenali = True
        elif "hapus tugas" in perintah or "hapus no" in perintah:
            try:
                produktivitas.delete_tasks(int("".join(filter(str.isdigit, perintah))))
            except ValueError:
                print("Contoh: 'hapus tugas 1'")
            keyword_dikenali = True

        if "mulai sesi fokus" in perintah:
            try:
                fokus.mulai_sesi(int("".join(filter(str.isdigit, perintah))))
            except ValueError:
                print("Contoh: 'mulai sesi fokus 45 menit'")
            keyword_dikenali = True
        elif "batalkan sesi" in perintah or "stop sesi" in perintah:
            fokus.batalkan_sesi()
            keyword_dikenali = True
        elif "laporan sesi fokus" in perintah or "lihat laporan sesi fokus" in perintah:
            fokus.lihat_statistik_fokus()
            keyword_dikenali = True
        elif "lihat statistik" in perintah or "statistik" in perintah:
            produktivitas.view_statistics()
            keyword_dikenali = True

        if "tambah jadwal" in perintah or ("jadwal jam" in perintah and "agenda" in perintah):
            try:
                bagian_jam = perintah.split("jam ")[1].split("agenda ")[0].strip()
                bagian_agenda = perintah.split("agenda ")[1].strip()
                jadwal.add_jadwal(bagian_jam, bagian_agenda)
            except IndexError:
                print("Contoh: 'jadwal jam 01:00 siang agenda ngoding'")
            keyword_dikenali = True
        elif any(x in perintah for x in ["apa kegiatan nanti", "jadwal nanti"]):
            jadwal.cek_agenda_mendatang()
            keyword_dikenali = True
        elif "lihat jadwal" in perintah:
            jadwal.lihat_semua_jadwal()
            keyword_dikenali = True

        if "cuaca hari ini" in perintah or "laporan cuaca kota" in perintah:
            cuaca.cek_cuaca()
            keyword_dikenali = True
        # Ganti bagian penanganan AI di dalam proses_perintah_neira menjadi seperti ini:
        elif "rekomendasi tugas" in perintah or "prioritas" in perintah or "analisis jadwal" in perintah:
            hasil_ai = ai.analisis_prioritas(perintah)
            print(hasil_ai) # Print utuh agar ditangkap sempurna oleh _PrintCapture
            keyword_dikenali = True
            
        elif "tanya neira" in perintah or perintah.startswith("neira,"):
            pertanyaan = perintah.replace("tanya neira", "").replace("neira,", "").strip()
            if pertanyaan:
                hasil_ai = ai.tanya_neira(pertanyaan)
                print(hasil_ai) # Print utuh agar ditangkap sempurna oleh _PrintCapture
            else:
                print("Iya? Mau nanya apa ke aku?")
            keyword_dikenali = True

        if not keyword_dikenali:
            print("Aku belum ngerti perintah itu. Coba ketik 'tanya neira, ...' untuk nanya bebas!")

    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        sys.stdout = sys.__stdout__

    return "\n".join(captured) if captured else ""


# ─────────────────────────────────────────────────────────────────────────────
#  PALET WARNA
# ─────────────────────────────────────────────────────────────────────────────
BG_DEEP      = "#0D0F14"
BG_PANEL     = "#13161E"
BG_CARD      = "#1A1D27"
BG_INPUT     = "#1F2330"
ACCENT       = "#7C6DEB"
ACCENT_DIM   = "#3D3570"
TEXT_PRI     = "#E8E9F0"
TEXT_SEC     = "#6B7080"
USER_BUBBLE  = "#232640"
NEIRA_BUBBLE = "#181B27"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
class NeiraDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Neira — AI Dashboard")
        self.geometry("900x680")
        self.minsize(720, 520)
        self.configure(fg_color=BG_DEEP)
        self._thinking = False
        self._build_layout()
        self._bind_keys()

        try:
            from fitur import profil
            data = profil.baca_memori()
            nama = data.get("nama", "kamu")
        except Exception:
            nama = "kamu"

        jam = datetime.datetime.now().hour
        if jam < 12:
            salam = f"Halo {nama}! Semangat produktifnya hari ini. 🌤️"
        elif jam < 18:
            salam = f"Halo {nama}! Ada yang bisa aku bantu? ☀️"
        else:
            salam = f"Halo {nama}! Jangan lupa istirahat yang cukup ya. 🌙"

        self.after(300, lambda: self._add_neira_bubble(salam))
        self.after(700, lambda: self._add_neira_bubble(
            "Ketik perintah seperti biasa ya — semua fitur Neira bisa kamu pakai di sini.\n"
            "Contoh: lihat tugas · cuaca hari ini · tanya neira, ..."
        ))

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Header
        header = ctk.CTkFrame(self, height=58, fg_color=BG_PANEL, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        logo = ctk.CTkFrame(header, fg_color="transparent")
        logo.pack(side="left", padx=20, pady=8)
        ctk.CTkFrame(logo, width=10, height=10, fg_color=ACCENT,
                     corner_radius=5).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(logo, text="Neira", font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=TEXT_PRI).pack(side="left")
        ctk.CTkLabel(logo, text="", font=ctk.CTkFont("Segoe UI", 11),
                     text_color=TEXT_SEC).pack(side="left", padx=(8, 0))

        self.status_label = ctk.CTkLabel(header, text="● Online",
                                          font=ctk.CTkFont("Segoe UI", 11),
                                          text_color="#4ADE80")
        self.status_label.pack(side="right", padx=20)

        ctk.CTkButton(header, text="Bersihkan", width=90, height=30,
                      font=ctk.CTkFont("Segoe UI", 11),
                      fg_color=BG_INPUT, hover_color=ACCENT_DIM,
                      text_color=TEXT_SEC, corner_radius=6,
                      command=self._clear_chat).pack(side="right", padx=(0, 8), pady=14)

        # Input bar
        input_bar = ctk.CTkFrame(self, height=76, fg_color=BG_PANEL, corner_radius=0)
        input_bar.pack(fill="x", side="bottom")
        input_bar.pack_propagate(False)

        input_inner = ctk.CTkFrame(input_bar, fg_color=BG_INPUT, corner_radius=14)
        input_inner.pack(fill="x", padx=16, pady=14, ipady=2)

        self.input_box = ctk.CTkTextbox(
            input_inner, height=40, fg_color="transparent",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=TEXT_PRI, wrap="word",
            border_width=0, activate_scrollbars=False)
        self.input_box.pack(side="left", fill="both", expand=True, padx=(14, 4), pady=6)

        self.send_btn = ctk.CTkButton(
            input_inner, text="Kirim ↵", width=84, height=36,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_DIM,
            text_color="#FFFFFF", corner_radius=10,
            command=self._on_send)
        self.send_btn.pack(side="right", padx=(4, 10), pady=6)

        # ── Chat area: Canvas + Scrollbar (manual, bukan CTkScrollableFrame) ──
        chat_outer = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        chat_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(chat_outer, bg=BG_CARD, bd=0,
                                  highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(chat_outer, command=self._canvas.yview,
                                      button_color=ACCENT_DIM,
                                      button_hover_color=ACCENT)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Frame di dalam canvas — ini yang jadi container bubble
        self._chat_frame = tk.Frame(self._canvas, bg=BG_CARD)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._chat_frame, anchor="nw")

        # Update scroll region & lebar frame saat resize
        self._chat_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Scroll dengan mouse wheel
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _on_frame_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Paksa frame selebar canvas — ini kunci wrapping yang benar
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    # ── Key bindings ──────────────────────────────────────────────────────────
    def _bind_keys(self):
        self.input_box.bind("<Return>", self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)

    def _on_enter(self, event):
        if not (event.state & 0x1):
            self._on_send()
            return "break"

    # ── Chat logic ────────────────────────────────────────────────────────────
    def _on_send(self):
        if self._thinking:
            return
        text = self.input_box.get("1.0", "end-1c").strip()
        if not text:
            return
        self.input_box.delete("1.0", "end")
        self._add_user_bubble(text)
        self._set_thinking(True)
        threading.Thread(target=self._run_neira, args=(text,), daemon=True).start()

    def _run_neira(self, text):
        try:
            reply = proses_perintah_neira(text)
        except Exception as e:
            reply = f"⚠️ Error: {e}"
        self.after(0, lambda: self._finish_response(reply))

    def _finish_response(self, reply):
        self._set_thinking(False)
        if reply:
            self._add_neira_bubble(reply)

    def _set_thinking(self, state: bool):
        self._thinking = state
        if state:
            self.status_label.configure(text="● Berpikir...", text_color=ACCENT)
            self.send_btn.configure(state="disabled", text="...")
            self._show_typing()
        else:
            self.status_label.configure(text="● Online", text_color="#4ADE80")
            self.send_btn.configure(state="normal", text="Kirim ↵")
            self._hide_typing()

    # ── Bubble builder ────────────────────────────────────────────────────────
    def _add_user_bubble(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M")
        outer = tk.Frame(self._chat_frame, bg=BG_CARD)
        outer.pack(fill="x", pady=(8, 0), padx=12)

        # Bubble rata kanan
        bubble_wrap = tk.Frame(outer, bg=BG_CARD)
        bubble_wrap.pack(side="right")

        # UBAH KE CTkFrame agar bubble bisa melengkung cantik (tidak ngotak)
        bubble = ctk.CTkFrame(bubble_wrap, fg_color=USER_BUBBLE, corner_radius=16)
        bubble.pack(side="right")

        # justify="left" dan anchor="w" memaksa teks rata kiri di dalam bubble
        msg = tk.Message(bubble, text=text,
                         bg=USER_BUBBLE, fg=TEXT_PRI,
                         font=("Segoe UI", 11),
                         width=520, justify="left", anchor="w")
        msg.pack(padx=14, pady=10)

        # Timestamp
        ts_frame = tk.Frame(self._chat_frame, bg=BG_CARD)
        ts_frame.pack(fill="x", padx=16, pady=(2, 8))
        tk.Label(ts_frame, text=f"Kamu  {ts}",
                 bg=BG_CARD, fg=TEXT_SEC,
                 font=("Segoe UI", 9)).pack(side="right")

        self._scroll_bottom()

    def _add_neira_bubble(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M")
        outer = tk.Frame(self._chat_frame, bg=BG_CARD)
        outer.pack(fill="x", pady=(8, 0), padx=12)

        avatar_opsi = self._get_avatar_config()
        
        # 1. LOGIKA PENANGANAN AVATAR
        padx_text = 4 # Default padding jika ada avatar
        
        if avatar_opsi == "none":
            # Jika 'none', jangan buat komponen avatar sama sekali
            padx_text = 40 # Geser teks sedikit agar sejajar rapi
        else:
            avatar_frame = tk.Frame(outer, bg=BG_CARD)
            avatar_frame.pack(side="left", anchor="n", pady=4)
            
            if avatar_opsi == "default" or not os.path.exists(avatar_opsi):
                # Avatar Huruf N Bulat Bawaan
                avatar = ctk.CTkLabel(avatar_frame, text="N", width=28, height=28,
                                      fg_color=ACCENT, text_color="white",
                                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                      corner_radius=14)
                avatar.pack()
            else:
                # Avatar Foto Custom
                try:
                    img = Image.open(avatar_opsi).resize((28, 28), Image.Resampling.LANCZOS)
                    img_tk = ImageTk.PhotoImage(img)
                    avatar = tk.Label(avatar_frame, image=img_tk, bg=BG_CARD)
                    avatar.image = img_tk # Jaga objek agar tidak dihapus garbage collector
                    avatar.pack()
                except Exception:
                    # Fallback jika gambar error/rusak
                    avatar = ctk.CTkLabel(avatar_frame, text="N", width=28, height=28,
                                          fg_color=ACCENT, text_color="white",
                                          corner_radius=14)
                    avatar.pack()

        # 2. KOMPONEN BUBBLE TEXT (Tetap tanpa garis tepi/background kotak)
        bubble = tk.Frame(outer, bg=BG_CARD, highlightthickness=0)
        bubble.pack(side="left", fill="x", expand=True, padx=(12, 60))

        msg = tk.Message(bubble, text="",
                         bg=BG_CARD, fg=TEXT_PRI,
                         font=("Segoe UI", 11),
                         width=520, justify="left", anchor="w")
        msg.pack(padx=padx_text, pady=6, fill="x")

        # 3. TIMESTAMP
        ts_frame = tk.Frame(self._chat_frame, bg=BG_CARD)
        ts_frame.pack(fill="x", padx=16, pady=(2, 8))
        tk.Label(ts_frame, text=f"Neira  {ts}",
                 bg=BG_CARD, fg=TEXT_SEC,
                 font=("Segoe UI", 9)).pack(side="left", padx=(40, 0))

        self._scroll_bottom()

        def _update_msg_width(e, m=msg):
            new_w = max(300, e.width - 160)
            m.configure(width=new_w)
        self._canvas.bind("<Configure>", _update_msg_width, add="+")

        def ketik_horizontal(indeks=0):
            if indeks < len(text):
                teks_sekarang = text[:indeks+1]
                msg.configure(text=teks_sekarang)
                self._scroll_bottom()
                self.after(10, lambda: ketik_horizontal(indeks + 1))

        ketik_horizontal()

    # ── Typing indicator ──────────────────────────────────────────────────────
    def _show_typing(self):
        self._typing_outer = tk.Frame(self._chat_frame, bg=BG_CARD)
        self._typing_outer.pack(fill="x", pady=(4, 8), padx=12)

        avatar_opsi = self._get_avatar_config()
        padx_text = 4
        
        # SINKRONISASI AVATAR DI INDIKATOR TYPING
        if avatar_opsi != "none":
            avatar_frame = tk.Frame(self._typing_outer, bg=BG_CARD)
            avatar_frame.pack(side="left", anchor="n", pady=6)
            
            if avatar_opsi == "default" or not os.path.exists(avatar_opsi):
                avatar = ctk.CTkLabel(avatar_frame, text="N", width=28, height=28,
                                      fg_color=ACCENT, text_color="white",
                                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                      corner_radius=14)
                avatar.pack()
            else:
                try:
                    img = Image.open(avatar_opsi).resize((28, 28), Image.Resampling.LANCZOS)
                    img_tk = ImageTk.PhotoImage(img)
                    avatar = tk.Label(avatar_frame, image=img_tk, bg=BG_CARD)
                    avatar.image = img_tk
                    avatar.pack()
                except Exception:
                    avatar = ctk.CTkLabel(avatar_frame, text="N", width=28, height=28, fg_color=ACCENT, corner_radius=14)
                    avatar.pack()
        else:
            padx_text = 40

        # Hilangkan border kotak kaku pada bubble typing (samakan dengan BG_CARD)
        bubble = tk.Frame(self._typing_outer, bg=BG_CARD, highlightthickness=0)
        bubble.pack(side="left", padx=(12, 0))

        self._typing_lbl = tk.Label(bubble, text="Neira sedang memproses ●",
                                     bg=BG_CARD, fg=TEXT_SEC,
                                     font=("Segoe UI", 11, "italic"))
        self._typing_lbl.pack(padx=padx_text, pady=10)
        self._animate_typing()
        self._scroll_bottom()

    def _animate_typing(self):
        if not self._thinking:
            return
        t = self._typing_lbl.cget("text")
        dots = t.count("●")
        self._typing_lbl.configure(text="Neira sedang memproses " + "●" * ((dots % 3) + 1))
        self.after(400, self._animate_typing)

    def _hide_typing(self):
        if hasattr(self, "_typing_outer"):
            self._typing_outer.destroy()

    # ── Utilities ─────────────────────────────────────────────────────────────
    def _scroll_bottom(self):
        self.after(80, lambda: self._canvas.yview_moveto(1.0))

    def _clear_chat(self):
        for w in self._chat_frame.winfo_children():
            w.destroy()
        self.after(200, lambda: self._add_neira_bubble("Chat dibersihkan. Mau ngapain sekarang? ✨"))
        
    def _get_avatar_config(self):
        """Membaca profil.json untuk menentukan jenis avatar Neira saat ini."""
        try:
            from fitur import profil
            data = profil.baca_memori()
            opsi = data.get("avatar_neira", "none")
        except Exception:
            opsi = "none"
            
        return opsi


if __name__ == "__main__":
    app = NeiraDashboard()
    app.mainloop()