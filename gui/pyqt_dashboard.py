import sys
import html
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                             QStackedWidget, QScrollArea, QGraphicsOpacityEffect)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QTextCursor

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


class NeiraWorker(QThread):
    token_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, processor_callback, text):
        super().__init__()
        self.processor_callback = processor_callback
        self.text = text

    def run(self):
        try:
            if self.processor_callback:
                generator = self.processor_callback(self.text)
                if generator:
                    for token in generator:
                        self.token_received.emit(token)
        except Exception as e:
            self.token_received.emit(f"\n⚠️ Error: {e}\n")
        finally:
            self.finished.emit()


class NeiraDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor_callback = None
        self._thinking = False
        self._has_chatted = False
        self.text_buffer = ""
        self.current_neira_label = None  # Menyimpan label aktif Neira untuk streaming
        self.init_ui()

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

        # Timer untuk streaming text Neira agar smooth
        self.typing_timer = QTimer(self)
        self.typing_timer.setInterval(15)  
        self.typing_timer.timeout.connect(self._drain_text_buffer)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_main_area(), stretch=1)

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

        sub = QLabel("Ada yang bisa ku bantu hari ini?")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size: 16px; color: {TEXT_MUTED}; background: transparent; margin-bottom: 18px;")
        v.addWidget(sub)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(10)
        chips_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for chip_text in ["Cek performa model", "Jelasin konsep RIP v2", "Debug kode Python"]:
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
        chip.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER_SOFT};
                border-radius: 19px;
                padding: 0 16px;
                font-size: 12px;
                color: {TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {BG_SURFACE_2};
                border: 1px solid #3c3d40;
            }}
        """)
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

        # Mengganti QTextBrowser menjadi QScrollArea agar mendukung komponen kustom bermaterial QSS
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {BG_BASE};
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {BG_BASE};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {BG_SURFACE_2};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #3c3d40;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)

        # Kontainer utama di dalam scroll area untuk menampung baris chat
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet(f"background-color: {BG_BASE};")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 10, 0, 10)
        self.chat_layout.setSpacing(20)
        self.chat_layout.addStretch() # Dorong chat ke atas

        self.scroll_area.setWidget(self.chat_container)
        v.addWidget(self.scroll_area)
        return page

    def _build_input_row(self):
        row = QHBoxLayout()
        row.setSpacing(12)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Tanya Neira sesuatu...")
        self.input_box.setFixedHeight(52)
        self.input_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER_SOFT};
                border-radius: 26px;
                padding: 13px 20px;
                font-size: 14px;
                color: {TEXT_PRIMARY};
            }}
            QTextEdit:focus {{
                border: 1px solid {ACCENT_PURPLE};
            }}
        """)
        self.input_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_box.installEventFilter(self)
        row.addWidget(self.input_box)

        self.send_button = QPushButton("➤")
        self.send_button.setFixedSize(48, 48)
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background: {GRADIENT};
                color: white;
                border-radius: 24px;
                font-size: 16px;
                border: none;
            }}
            QPushButton:disabled {{
                background: {BG_SURFACE_2};
                color: {TEXT_MUTED};
            }}
        """)
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

    # --------------------------------------------------------
    # SMOOTH TYPING MOTOR (Untuk Polosan Chat Neira)
    # --------------------------------------------------------
    def _drain_text_buffer(self):
        if self.text_buffer and self.current_neira_label:
            chunk_size = 2 if len(self.text_buffer) > 10 else 1
            chars_to_print = self.text_buffer[:chunk_size]
            self.text_buffer = self.text_buffer[chunk_size:]

            # Update text pada label Neira secara bertahap
            current_text = self.current_neira_label.text()
            self.current_neira_label.setText(current_text + chars_to_print)
            
            # Paksa scrollbar otomatis turun mengikuti jalannya ketikan
            QTimer.singleShot(10, self._scroll_to_bottom)
        elif not self._thinking:
            self.typing_timer.stop()

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

        if not self._has_chatted:
            self._has_chatted = True
            self._animate_to_page(1)

        self.input_box.clear()
        self._set_thinking(True)

        # 1. ADD BUBBLE USER (Mendukung border-radius asli & fit-content secara alami)
        user_row = QHBoxLayout()
        user_row.setContentsMargins(0, 0, 0, 0)
        user_row.addStretch() # Dorong ke kanan

        user_bubble = QLabel(text)
        user_bubble.setWordWrap(True)
        user_bubble.setMaximumWidth(700) # Batasi lebar maksimal bubble
        user_bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {USER_BUBBLE_BG};
                color: {USER_TEXT_COLOR};
                font-size: 15px;
                padding: 12px 18px;
                border-radius: 18px; /* BULAT MELENGKUNG SEMPURNA SEKARANG! */
            }}
        """)
        user_row.addWidget(user_bubble)
        
        # Masukkan ke layout chat utama (di atas stretch)
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, user_row)

        # 2. ADD RESPONSE NEIRA (POLOS TANPA BUBBLE + IKON ✦)
        neira_row = QHBoxLayout()
        neira_row.setContentsMargins(0, 5, 0, 5)
        
        neira_icon = QLabel("✦ ")
        neira_icon.setStyleSheet(f"color: {ACCENT_PURPLE}; font-size: 16px; font-weight: bold; background: transparent;")
        neira_icon.setFixedWidth(20)
        neira_icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.current_neira_label = QLabel("")
        self.current_neira_label.setWordWrap(True)
        self.current_neira_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 15px;
                font-weight: 500;
                line-height: 150%;
                background: transparent;
            }}
        """)
        
        neira_row.addWidget(neira_icon)
        neira_row.addWidget(self.current_neira_label, stretch=1)
        
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, neira_row)

        # Reset buffer dan picu animasi ketik
        self.text_buffer = ""
        self.typing_timer.start()

        # Jalankan Backend Ollama/Gemini
        self.worker = NeiraWorker(self.processor_callback, text)
        self.worker.token_received.connect(self._on_token_received)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()
        
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _on_token_received(self, token):
        self.text_buffer += token

    def _on_worker_finished(self):
        self._set_thinking(False)

    def _set_thinking(self, thinking):
        self._thinking = thinking
        if thinking:
            self.status_label.setText("●  Memproses...")
            self.status_label.setStyleSheet("color: #e4b54e; font-size: 12px; font-weight: 500; background: transparent;")
            self.send_button.setDisabled(True)
        else:
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