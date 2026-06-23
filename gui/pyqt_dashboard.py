import sys
import html
import re
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QStackedWidget, QScrollArea, QGraphicsOpacityEffect,
                             QLineEdit, QMenu, QInputDialog)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QTextCursor

# Perbaikan Impor Database sesuai folder yang kita buat kemarin
from database import db

# ============================================================
# DESIGN TOKENS — terinspirasi dari Gemini (dark mode)
# ============================================================
BG_BASE      = "#131314"   # background utama
BG_SURFACE   = "#1e1f20"   # sidebar / input box
BG_SURFACE_2 = "#2b2c2e"   # hover / border
BORDER_SOFT  = "#2b2c2e"
TEXT_PRIMARY = "#e8eaed"
TEXT_MUTED   = "#9aa0a6"
ACCENT_BLUE   = "#4c8df6"
ACCENT_PURPLE = "#9b72cb"
ACCENT_PINK   = "#d96570"
GRADIENT = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT_BLUE}, stop:0.5 {ACCENT_PURPLE}, stop:1 {ACCENT_PINK})"

FONT_STACK = "'Google Sans', 'Segoe UI', 'Inter', -apple-system, Roboto, sans-serif"
USER_BUBBLE_BG = "#2b2d31"  # Slate Grey premium
USER_TEXT_COLOR = "#aecbfa" # Biru pucat kontras

# ============================================================
# SIDEBAR CONFIG
# ============================================================
SIDEBAR_COLLAPSED_W = 60
SIDEBAR_EXPANDED_W  = 260


class NeiraWorker(QThread):
    token_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, processor_callback, text, session_id):
        super().__init__()
        self.processor_callback = processor_callback
        self.text = text
        self.session_id = session_id

    def run(self):
        # Memanggil fungsi generator backend neira secara dinamis
        for token in self.processor_callback(self.text, self.session_id):
            self.token_received.emit(token)
        self.finished.emit()


class HistoryItemWidget(QWidget):
    clicked = pyqtSignal(int) # mengirim session_id
    refresh_needed = pyqtSignal()

    def __init__(self, session_id, judul, is_active):
        super().__init__()
        self.session_id = session_id
        self.judul = judul
        self.is_active = is_active
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(38)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(4)

        # Tombol Utama isi konten teks judul chat
        self.btn_utama = QPushButton(f"💬  {self.judul}")
        self.btn_utama.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_utama.setSizePolicy(self.btn_utama.sizePolicy().Policy.Expanding, self.btn_utama.sizePolicy().Policy.Preferred)
        
        # Style base item
        if self.is_active:
            self.btn_utama.setStyleSheet(f"text-align: left; background: transparent; color: {TEXT_PRIMARY}; border: none; font-weight: bold; font-size: 13px;")
            self.setStyleSheet(f"background-color: {BG_SURFACE_2}; border-radius: 8px;")
        else:
            self.btn_utama.setStyleSheet(f"text-align: left; background: transparent; color: {TEXT_MUTED}; border: none; font-size: 13px;")
            self.setStyleSheet("background-color: transparent; border-radius: 8px;")

        self.btn_utama.clicked.connect(lambda: self.clicked.emit(self.session_id))
        layout.addWidget(self.btn_utama)

        # Tombol Titik Tiga Menu (Sembunyikan secara default)
        self.btn_menu = QPushButton("•••")
        self.btn_menu.setFixedSize(26, 26)
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menu.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; border: none; border-radius: 4px; font-weight: bold; }} QPushButton:hover {{ background-color: #3c3d40; color: white; }}")
        self.btn_menu.setVisible(False) 
        self.btn_menu.clicked.connect(self.buka_context_menu)
        layout.addWidget(self.btn_menu)

    # Deteksi Cursor Masuk Area Widget (Hover In)
    def enterEvent(self, event):
        self.btn_menu.setVisible(True)
        if not self.is_active:
            self.setStyleSheet(f"background-color: {BG_SURFACE_2}40; border-radius: 8px;")
        super().enterEvent(event)

    # Deteksi Cursor Keluar Area Widget (Hover Out)
    def leaveEvent(self, event):
        self.btn_menu.setVisible(False)
        if not self.is_active:
            self.setStyleSheet("background-color: transparent;")
        super().leaveEvent(event)

    def buka_context_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {BG_SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_SOFT}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {BG_SURFACE_2}; color: white; }}
        """)
        
        aksi_rename = menu.addAction("✏️  Rename")
        aksi_delete = menu.addAction("🗑️  Delete Chat")
        
        pilihan = menu.exec(self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft()))
        
        if pilihan == aksi_rename:
            teks_baru, ok = QInputDialog.getText(self, "Rename Chat", "Masukkan nama baru percakapan:", text=self.judul)
            if ok and teks_baru.strip():
                db.update_judul_sesi(self.session_id, teks_baru.strip())
                self.refresh_needed.emit()
                
        elif pilihan == aksi_delete:
            # Panggil fungsi hapus di module db kamu
            if hasattr(db, 'hapus_sesi'):
                db.hapus_sesi(self.session_id)
            else:
                # Fallback aman jika fungsi hapus belum kamu buat di database.py
                print(f"Fungsi hapus_sesi belum diimplementasi di database.py untuk session: {self.session_id}")
            self.refresh_needed.emit()


class NeiraDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor_callback = None
        self._thinking = False
        self._is_searching = False
        self._has_chatted = False
        self.sidebar_expanded = False
        self.text_buffer = ""
        self.raw_accumulated_text = ""  
        self.current_neira_widget = None  
        self.thinking_dot_count = 0
        self.search_anim_frame = 0
        
        # 1. BUAT UI DULUAN (Biar layout sidebar chat tercipta sempurna)
        self.init_ui()
        
        # 2. SELESAIKAN URUSAN DATABASE
        db.inisialisasi_db()
        semua_sesi = db.ambil_semua_sesi()
        
        if semua_sesi:
            self.current_session_id = semua_sesi[0]["session_id"]
        else:
            self.current_session_id = db.buat_sesi_baru("Chat Baru")
            
        # 3. ISI DATA KE SIDEBAR
        self.muat_daftar_sidebar()
        
        # 4. SOLUSI ESTETIKA: Paksa layar utama balik ke Welcome Page saat aplikasi baru dibuka
        self._has_chatted = False
        self.stack.setCurrentIndex(0) 
        
    def closeEvent(self, event):
        """Dipanggil otomatis Qt pas window ditutup (klik X). Pastikan sesi aktivitas
        yang masih terbuka (misal app yang lagi dimonitor) ditutup rapi di database,
        biar gak ada data 'menggantung' yang ngerusak analisa pola besok."""
        db.tutup_semua_sesi_aktif()
        event.accept()

    def muat_daftar_sidebar(self):
        """Membaca data sesi dari SQLite dan merendernya menggunakan Custom Hover Widget."""
        if not hasattr(self, 'sidebar_chat_layout'):
            return

        while self.sidebar_chat_layout.count():
            item = self.sidebar_chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                
        daftar_sesi = db.ambil_semua_sesi()
        
        for sesi in daftar_sesi:
            sid = sesi["session_id"]
            judul = sesi["judul"]
            is_active = (sid == self.current_session_id)
            
            item_widget = HistoryItemWidget(sid, judul, is_active)
            item_widget.clicked.connect(self.pindah_sesi)
            item_widget.refresh_needed.connect(self.muat_daftar_sidebar)
            item_widget.refresh_needed.connect(self.muat_konten_chat_ke_layar)
            
            self.sidebar_chat_layout.addWidget(item_widget)
            
        self.sidebar_chat_layout.addStretch()

    def pindah_sesi(self, session_id):
        if self._thinking: 
            return 
            
        self.current_session_id = session_id
        self.muat_daftar_sidebar() 
        self.muat_konten_chat_ke_layar() 

    def muat_konten_chat_ke_layar(self):
        """Membersihkan layar utama dengan aman dan memuat ulang history bubble chat dari sesi aktif."""
        # 1. CARA AMAN BERSIHKAN LAYOUT (Mencegah Crash/Segmentation Fault)
        if hasattr(self, 'chat_layout') and self.chat_layout is not None:
            while self.chat_layout.count() > 1:
                item = self.chat_layout.takeAt(0)
                if item is not None:
                    # Jika berupa sub-layout (seperti baris chat user/neira)
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        while sub_layout.count():
                            sub_item = sub_layout.takeAt(0)
                            if sub_item and sub_item.widget():
                                w = sub_item.widget()
                                w.setParent(None)
                                w.deleteLater()
                        sub_layout.deleteLater()
                    
                    # Jika berupa widget langsung
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                        widget.deleteLater()
        
        # 2. AMBIL DATA DARI DATABASE
        riwayat = db.ambil_riwayat_terakhir(self.current_session_id, limit=20)
        
        if riwayat:
            self._has_chatted = True
            self.stack.setCurrentIndex(1) # Pindah ke halaman Chat Area
            
            for chat in riwayat:
                role = chat["role"]
                content = chat["content"]
                if role == "user":
                    self.append_chat_bubble_manual("Ian", content, is_user=True)
                else:
                    self.append_chat_bubble_manual("Neira", content, is_user=False)
        else:
            self._has_chatted = False
            self.stack.setCurrentIndex(0) # Kembali ke Welcome Page jika kosong
            
        # Pemicu refresh layout agar render ulang berjalan mulus
        self.chat_container.adjustSize()
        QTimer.singleShot(50, self._scroll_to_bottom)

    def append_chat_bubble_manual(self, sender, text, is_user):
        row = QHBoxLayout()
        row.setContentsMargins(0, 5, 12, 5)
        
        if is_user:
            row.addStretch()
            bubble = QLabel(text)
            bubble.setWordWrap(True)
            bubble.setMaximumWidth(700)
            bubble.setStyleSheet(f"background-color: {USER_BUBBLE_BG}; color: {USER_TEXT_COLOR}; font-size: 15px; padding: 12px 18px; border-radius: 18px;")
            row.addWidget(bubble)
        else:
            icon = QLabel("✦ ")
            icon.setStyleSheet(f"color: {ACCENT_PURPLE}; font-size: 16px; font-weight: bold; background: transparent;")
            icon.setFixedWidth(20)
            icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            widget = QTextEdit()
            widget.setReadOnly(True)
            widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            widget.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 500; background: transparent; border: none;")
            widget.setHtml(self._parse_markdown_to_html(text))
            
            row.addWidget(icon)
            row.addWidget(widget, stretch=1)
            
            QTimer.singleShot(10, lambda: widget.setFixedHeight(int(widget.document().size().height()) + 10))
            
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, row)

    def init_ui(self):
        self.setWindowTitle("Neira AI")
        self.resize(1100, 700)
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {BG_BASE}; }}
            QWidget {{
                background-color: {BG_BASE};
                color: {TEXT_PRIMARY};
                font-family: {FONT_STACK};
            }}
        """)

        self.typing_timer = QTimer(self)
        self.typing_timer.setInterval(10)  
        self.typing_timer.timeout.connect(self._drain_text_buffer)

        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(400)
        self.anim_timer.timeout.connect(self._update_thinking_animations)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar_widget = self._build_sidebar()
        root_layout.addWidget(self.sidebar_widget)
        root_layout.addWidget(self._build_main_area(), stretch=1)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setMinimumWidth(SIDEBAR_COLLAPSED_W)
        sidebar.setMaximumWidth(SIDEBAR_COLLAPSED_W)

        v = QVBoxLayout(sidebar)
        v.setContentsMargins(8, 12, 8, 12)
        v.setSpacing(6)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.sidebar_toggle_btn = QPushButton("☰")
        self.sidebar_toggle_btn.setFixedSize(36, 36)
        self.sidebar_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_toggle_btn.setStyleSheet(self._icon_btn_style())
        self.sidebar_toggle_btn.clicked.connect(self._toggle_sidebar)
        v.addWidget(self.sidebar_toggle_btn)

        v.addSpacing(8)

        self.new_chat_btn = QPushButton("➕")
        self.new_chat_btn.setFixedHeight(36)
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_btn.setStyleSheet(self._sidebar_btn_style())
        self.new_chat_btn.clicked.connect(self.aksi_tombol_new_chat)
        v.addWidget(self.new_chat_btn)

        self.search_btn = QPushButton("🔍")
        self.search_btn.setFixedHeight(36)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet(self._sidebar_btn_style())
        self.search_btn.clicked.connect(lambda: self._set_sidebar(True))
        v.addWidget(self.search_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari percakapan...")
        self.search_input.setStyleSheet(f"QLineEdit {{ background-color: {BG_SURFACE_2}; border: 1px solid {BORDER_SOFT}; border-radius: 8px; padding: 6px 10px; font-size: 12px; color: {TEXT_PRIMARY}; }} QLineEdit:focus {{ border: 1px solid {ACCENT_PURPLE}; }}")
        self.search_input.textChanged.connect(self._filter_history)
        self.search_input.setVisible(False)
        v.addWidget(self.search_input)

        self.sidebar_chat_layout = QVBoxLayout()
        self.sidebar_chat_layout.setSpacing(4)
        self.sidebar_chat_layout.setContentsMargins(0, 4, 0, 0)

        history_inner = QWidget()
        history_inner.setLayout(self.sidebar_chat_layout)
        history_inner.setStyleSheet("background: transparent;")

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setWidget(history_inner)
        self.history_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.history_scroll.setVisible(False)
        v.addWidget(self.history_scroll, stretch=1)

        self.new_chat_btn.setVisible(False)
        self.search_btn.setVisible(False)

        self.sidebar = sidebar
        self._apply_sidebar_style(expanded=False)
        return sidebar

    def aksi_tombol_new_chat(self):
        if self._thinking: 
            return
        
        id_baru = db.buat_sesi_baru("Chat Baru")
        self.current_session_id = id_baru
        
        self._set_sidebar(False)
        self.muat_daftar_sidebar()
        self.muat_konten_chat_ke_layar()
        
        self.input_box.clear()
        self.input_box.setFocus()

    def _icon_btn_style(self):
        return f"QPushButton {{ background-color: transparent; border: none; border-radius: 8px; font-size: 15px; color: {TEXT_PRIMARY}; }} QPushButton:hover {{ background-color: {BG_SURFACE_2}; }}"

    def _sidebar_btn_style(self):
        return f"QPushButton {{ background-color: transparent; border: none; border-radius: 8px; font-size: 13px; color: {TEXT_PRIMARY}; text-align: left; padding-left: 6px; }} QPushButton:hover {{ background-color: {BG_SURFACE_2}; }}"

    def _apply_sidebar_style(self, expanded):
        if expanded:
            self.sidebar.setStyleSheet(f"background-color: {BG_SURFACE}; border-right: 1px solid {BORDER_SOFT};")
        else:
            self.sidebar.setStyleSheet(f"background-color: {BG_BASE}; border: none;")

    def _toggle_sidebar(self):
        self._set_sidebar(not self.sidebar_expanded)

    def _set_sidebar(self, expand):
        if expand == self.sidebar_expanded:
            if expand: self.search_input.setFocus()
            return

        self.sidebar_expanded = expand
        start_w = self.sidebar.minimumWidth()
        end_w = SIDEBAR_EXPANDED_W if expand else SIDEBAR_COLLAPSED_W

        if expand:
            self.sidebar_toggle_btn.setText("✕")
            self.new_chat_btn.setText("➕  Percakapan Baru")
            self.search_btn.setText("🔍  Telusuri Percakapan")
            self.new_chat_btn.setVisible(True)
            self.search_btn.setVisible(True)
            self._apply_sidebar_style(expanded=True)
        else:
            self.search_input.setVisible(False)
            self.history_scroll.setVisible(False)
            self.new_chat_btn.setVisible(False)
            self.search_btn.setVisible(False)
            self.sidebar_toggle_btn.setText("☰")
            self.new_chat_btn.setText("➕")
            self.search_btn.setText("🔍")
            self._apply_sidebar_style(expanded=False)

        self.sidebar_anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.sidebar_anim.setDuration(200)
        self.sidebar_anim.setStartValue(start_w)
        self.sidebar_anim.setEndValue(end_w)
        self.sidebar_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.sidebar_anim.valueChanged.connect(lambda v: self.sidebar.setMaximumWidth(v))

        if expand:
            def _reveal_expanded_content():
                self.search_input.setVisible(True)
                self.history_scroll.setVisible(True)
                self.search_input.setFocus()
            self.sidebar_anim.finished.connect(_reveal_expanded_content)

        self.sidebar_anim.start()

    def _filter_history(self, query):
        query = query.lower().strip()
        for i in range(self.sidebar_chat_layout.count()):
            item = self.sidebar_chat_layout.itemAt(i)
            if item and item.widget():
                btn = item.widget()
                btn.setVisible(query in btn.text().lower())

    def _build_main_area(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 18, 36, 22)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.addStretch()
        self.status_label = QLabel("●  Online")
        self.status_label.setStyleSheet("color: #23a55a; font-size: 12px; font-weight: 500; background: transparent;")
        header_row.addWidget(self.status_label)
        layout.addLayout(header_row)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_welcome_page())
        self.stack.addWidget(self._build_chat_page())
        layout.addWidget(self.stack, stretch=1)

        self.fade_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.fade_effect)
        self.fade_effect.setOpacity(1.0)

        layout.addLayout(self._build_input_row())
        return container

    def _build_welcome_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(10)

        greeting = QLabel("Halo, Ian")
        greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        greeting.setStyleSheet(f"font-size: 34px; font-weight: 600; color: {ACCENT_PURPLE}; background: transparent;")
        v.addWidget(greeting)

        sub = QLabel("How can I help you today?")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size: 16px; color: {TEXT_MUTED}; background: transparent; margin-bottom: 18px;")
        v.addWidget(sub)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(10)
        chips_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for chip_text in ["Check a model's performance", "Explain the RIP v2 concept", "who am i?"]:
            chips_row.addWidget(self._make_chip(chip_text))
        chip_wrap = QWidget()
        chip_wrap.setLayout(chips_row)
        chip_wrap.setStyleSheet("background: transparent;")
        v.addWidget(chip_wrap)

        return page

    def _make_chip(self, text):
        chip = QPushButton(text)
        chip.setCursor(Qt.CursorShape.PointingHandCursor)
        chip.setFixedHeight(38)
        chip.setStyleSheet(f"QPushButton {{ background-color: {BG_SURFACE}; border: 1px solid {BORDER_SOFT}; border-radius: 19px; padding: 0 16px; font-size: 12px; color: {TEXT_PRIMARY}; }} QPushButton:hover {{ background-color: {BG_SURFACE_2}; border: 1px solid #3c3d40; }}")
        chip.clicked.connect(lambda: self._fill_input(text))
        return chip

    def _fill_input(self, text):
        self.input_box.setPlainText(text)
        self.input_box.setFocus()
        cursor = self.input_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.input_box.setTextCursor(cursor)

    def _build_chat_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ background-color: {BG_BASE}; border: none; }} QScrollBar:vertical {{ border: none; background: {BG_BASE}; width: 8px; margin: 0px; }} QScrollBar::handle:vertical {{ background: {BG_SURFACE_2}; min-height: 20px; border-radius: 4px; }} QScrollBar::handle:vertical:hover {{ background: #3c3d40; }} QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}")

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet(f"background-color: {BG_BASE};")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 10, 24, 10)
        self.chat_layout.setSpacing(20)
        self.chat_layout.addStretch() 

        self.scroll_area.setWidget(self.chat_container)
        v.addWidget(self.scroll_area)
        return page

    def _build_input_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Ask Neira...")
        self.input_box.setFixedHeight(52)
        self.input_box.setStyleSheet(f"QTextEdit {{ background-color: {BG_SURFACE}; border: 1px solid {BORDER_SOFT}; border-radius: 26px; padding: 13px 20px; font-size: 14px; color: {TEXT_PRIMARY}; }} QTextEdit:focus {{ border: 1px solid {ACCENT_PURPLE}; }}")
        self.input_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_box.installEventFilter(self)
        row.addWidget(self.input_box)

        self.send_button = QPushButton("➤")
        self.send_button.setFixedSize(48, 48)
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setStyleSheet(f"QPushButton {{ background: {GRADIENT}; color: white; border-radius: 24px; font-size: 16px; border: none; }} QPushButton:disabled {{ background: {BG_SURFACE_2}; color: {TEXT_MUTED}; }}")
        self.send_button.clicked.connect(self._on_send)
        row.addWidget(self.send_button)

        return row

    def _animate_to_page(self, index):
        self.fade_anim = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setKeyValueAt(0.5, 0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        def change_index():
            self.stack.setCurrentIndex(index)
            
        self.fade_anim.valueChanged.connect(lambda v: change_index() if v < 0.1 else None)
        self.fade_anim.start()

    def _parse_markdown_to_html(self, text):
        escaped = html.escape(text)
        escaped = re.sub(re.compile(r'\*\*(.*?)\*\*'), r'<b>\1</b>', escaped)
        escaped = re.sub(re.compile(r'\*(.*?)\*'), r'<i>\1</i>', escaped)
        escaped = escaped.replace("\n", "<br>")
        return escaped

    def _drain_text_buffer(self):
        if self.text_buffer and self.current_neira_widget:
            if "neira is thinking" in self.text_buffer.lower() or "searching the live web" in self.text_buffer.lower():
                chunk = self.text_buffer
                self.text_buffer = ""
                self.raw_accumulated_text += chunk
            else:
                chunk_size = 3 if len(self.text_buffer) > 15 else 1
                chars_to_print = self.text_buffer[:chunk_size]
                self.text_buffer = self.text_buffer[chunk_size:]
                self.raw_accumulated_text += chars_to_print

            html_content = self._parse_markdown_to_html(self.raw_accumulated_text)
            self.current_neira_widget.setHtml(html_content)
            
            doc_height = self.current_neira_widget.document().size().height()
            self.current_neira_widget.setFixedHeight(int(doc_height) + 10)

            QTimer.singleShot(5, self._scroll_to_bottom)
        elif not self._thinking:
            self.typing_timer.stop()

    def _update_thinking_animations(self):
        if not self._thinking:
            return
            
        frames = ["┤", "┐", "┐", "┶", "┷", "┹"]
        self.search_anim_frame = (self.search_anim_frame + 1) % len(frames)
        self.status_label.setText(f"{frames[self.search_anim_frame]}  Processing...")
        
        if self.current_neira_widget and not self.raw_accumulated_text:
            self.thinking_dot_count = (self.thinking_dot_count % 3) + 1
            dots = "." * self.thinking_dot_count
            
            if getattr(self, '_is_searching', False):
                self.current_neira_widget.setHtml(
                    f"<span style='color:{ACCENT_BLUE}; font-style: italic; font-weight: bold;'>"
                    f"🌐 Tuning into cyber waves & searching the live web{dots}</span>"
                )
            else:
                self.current_neira_widget.setHtml(
                    f"<span style='color:{TEXT_MUTED}; font-style: italic;'>"
                    f"✦ Neira is thinking{dots}</span>"
                )

    def _scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def eventFilter(self, obj, event):
        if obj is self.input_box and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                else:
                    self._on_send()
                    return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        if self._thinking:
            return
        text = self.input_box.toPlainText().strip()
        if not text:
            return

        riwayat_saat_ini = db.ambil_riwayat_terakhir(self.current_session_id, limit=2)
        if not riwayat_saat_ini:
            potongan_judul = " ".join(text.split()[:5])
            if len(potongan_judul) > 25: potongan_judul = potongan_judul[:25] + "..."
            db.update_judul_sesi(self.current_session_id, potongan_judul)

        if not self._has_chatted:
            self._has_chatted = True
            self._animate_to_page(1)

        self.input_box.clear()
        self._set_thinking(True)

        # 1. ADD BUBBLE USER 
        user_row = QHBoxLayout()
        user_row.setContentsMargins(0, 0, 12, 0)
        user_row.addStretch()

        user_bubble = QLabel(text)
        user_bubble.setWordWrap(True)
        user_bubble.setMaximumWidth(700) 
        user_bubble.setStyleSheet(f"QLabel {{ background-color: {USER_BUBBLE_BG}; color: {USER_TEXT_COLOR}; font-size: 15px; padding: 12px 18px; border-radius: 18px; }}")
        user_row.addWidget(user_bubble)
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, user_row)

        # 2. ADD RESPONSE NEIRA
        neira_row = QHBoxLayout()
        neira_row.setContentsMargins(0, 5, 12, 5)
        
        neira_icon = QLabel("✦ ")
        neira_icon.setStyleSheet(f"color: {ACCENT_PURPLE}; font-size: 16px; font-weight: bold; background: transparent;")
        neira_icon.setFixedWidth(20)
        neira_icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.current_neira_widget = QTextEdit()
        self.current_neira_widget.setReadOnly(True)
        self.current_neira_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.current_neira_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.current_neira_widget.setStyleSheet(f"QTextEdit {{ color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 500; background: transparent; border: none; }}")
        self.current_neira_widget.setFixedHeight(30) 
        
        neira_row.addWidget(neira_icon)
        neira_row.addWidget(self.current_neira_widget, stretch=1)
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, neira_row)

        self.text_buffer = ""
        self.raw_accumulated_text = ""
        
        self.typing_timer.start()
        self.anim_timer.start()

        self.worker = NeiraWorker(self.processor_callback, text, self.current_session_id)
        self.worker.token_received.connect(self._on_token_received)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.finished.connect(self.muat_daftar_sidebar) 
        self.worker.start()
        
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _on_token_received(self, token):
        if "searching the live web" in token.lower() or "searching the live" in token.lower():
            self._is_searching = True
            return

        if "[live web info]" in token.lower() or "found some updates" in token.lower():
            self._is_searching = False
            self.raw_accumulated_text = ""
            self.text_buffer = ""
            return

        if "fetching your profile summary" in token.lower():
            self.raw_accumulated_text = "" 
            self.text_buffer = ""
            return

        self.text_buffer += token

    def _on_worker_finished(self):
        self._set_thinking(False)

    def _set_thinking(self, thinking):
        self._thinking = thinking
        if thinking:
            self.send_button.setDisabled(True)
        else:
            self.anim_timer.stop()
            self.status_label.setText("●  Online")
            self.status_label.setStyleSheet("color: #23a55a; font-size: 12px; font-weight: 500; background: transparent;")
            self.send_button.setDisabled(False)
            self.input_box.setFocus()


def main():
    import neira
    app = QApplication(sys.argv)
    window = NeiraDashboard()
    window.processor_callback = neira.proses_perintah_backend
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()