import sys
import os
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# Ambil path root project (satu level di atas folder gui)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Sekarang import neira dijamin aman tanpa error lagi!
import neira

# Import fungsi utama backend neira kamu
import neira

class NeiraBridge(QObject):
    """Jembatan komunikasi agar JavaScript di HTML bisa memanggil fungsi Python."""
    # Signal untuk mengirim token teks dari Python ke HTML secara streaming
    send_token_to_html = pyqtSignal(str, bool) # (text_token, is_final)
    
    def __init__(self, window_parent):
        super().__init__()
        self.window = window_parent
        self.active_session_id = "default_session" # Bisa disesuaikan dengan sistem session kamu

    @pyqtSlot(str)
    def kirim_perintah_ke_python(self, pesan_user):
        """Fungsi ini bakal dipanggil otomatis dari script.js saat Ian klik send."""
        if not pesan_user.strip():
            return
            
        # Jalankan proses backend neira.py di background thread agar UI HTML gak beku
        import threading
        threading.Thread(target=self._run_backend, args=(pesan_user,), daemon=True).start()

    def _run_backend(self, pesan_user):
        try:
            # Panggil generator fungsi utama dari neira.py kamu[cite: 1]
            generator_respon = neira.proses_perintah_backend(pesan_user, self.active_session_id)[cite: 1]
            
            for token in generator_respon:
                if token:
                    # Kirim token satu per satu ke JavaScript secara real-time
                    self.send_token_to_html.emit(token, False)
                    
            # Kirim sinyal kalau Neira sudah selesai berbicara
            self.send_token_to_html.emit("", True)
            
        except Exception as e:
            self.send_token_to_html.emit(f"<br>⚠️ Bridge Error: {e}", True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neira AI — Premium Desktop")
        self.resize(1100, 750)
        self.setMinimumSize(850, 600)

        # Inisialisasi komponen Browser WebEngine
        self.browser = QWebEngineView()
        
        # Aktifkan fitur lokal akselerasi video & inspektor developer (F12) jika dibutuhkan
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

        # Setup QWebChannel untuk registrasi objek bridge Python ke window JavaScript
        self.channel = QWebChannel()
        self.bridge = NeiraBridge(self)
        self.channel.registerObject("neira_backend", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # Load file index.html yang sudah kita buat tadi
        path_html = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "index.html"))
        self.browser.setUrl(QUrl.fromLocalFile(path_html))

        # Atur layout utama window
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()