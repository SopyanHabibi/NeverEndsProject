import os
import re
from core.plugin_manager import BasePlugin

SKIP_DIRS = {"node_modules", ".git", "venv", "__pycache__", ".venv", "dist", "build", "out"}
MAX_DEPTH = 6
MAX_FILE_CHARS = 8000
MAX_AUTO_READ = 3  # batas jumlah file yang di-auto-read, biar gak membanjiri context

# Pola buat nangkep nama modul yang di-import, beberapa bahasa umum
IMPORT_PATTERNS = [
    r'from\s+([\w\.]+)\s+import',        # Python: from helper import x
    r'^\s*import\s+([\w\.]+)',           # Python: import helper
    r'require\([\'"]([\w\./]+)[\'"]\)',  # JS: require('./helper')
    r'from\s+[\'"]([\w\./]+)[\'"]',      # JS/TS: import x from './helper'
]


class WorkspaceAwarenessPlugin(BasePlugin):

    def initialize(self):
        self._cache = {}

    def execute(self, mode: str, project_root: str, path: str = None, selected_code: str = None):
        if not project_root or not os.path.isdir(project_root):
            return "Project root tidak valid atau belum tersedia."

        if mode == "get_structure":
            return self._get_structure(project_root)
        elif mode == "read_file":
            return self._read_file(project_root, path)
        elif mode == "auto_read_related":
            return self._auto_read_related(project_root, selected_code or "")
        return "Mode tidak dikenali."

    def _get_structure(self, project_root: str) -> str:
        if project_root in self._cache:
            return self._cache[project_root]

        lines = []
        base_depth = project_root.rstrip(os.sep).count(os.sep)

        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            depth = root.rstrip(os.sep).count(os.sep) - base_depth
            if depth > MAX_DEPTH:
                dirs[:] = []
                continue

            indent = "  " * depth
            folder_name = os.path.basename(root) or root
            lines.append(f"{indent}{folder_name}/")
            for f in files:
                lines.append(f"{indent}  {f}")

        hasil = "\n".join(lines) if lines else "(folder kosong)"
        self._cache[project_root] = hasil
        return hasil

    def _read_file(self, project_root: str, rel_path: str) -> str:
        if not rel_path:
            return "Path file gak dikasih."

        target = os.path.normpath(os.path.join(project_root, rel_path))
        if not target.startswith(os.path.normpath(project_root)):
            return "Akses ditolak: path di luar project."

        if not os.path.isfile(target):
            return f"File '{rel_path}' tidak ditemukan."

        try:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                isi = f.read()
            if len(isi) > MAX_FILE_CHARS:
                isi = isi[:MAX_FILE_CHARS] + "\n... (dipotong, file terlalu panjang)"
            return isi
        except Exception as e:
            return f"Gagal baca file: {e}"

    def _extract_imported_names(self, selected_code: str) -> list:
        """Ambil nama modul dari statement import di kode yang diblok."""
        names = set()
        for pattern in IMPORT_PATTERNS:
            for match in re.finditer(pattern, selected_code, re.MULTILINE):
                raw = match.group(1)
                # ambil segmen terakhir aja, misal 'utils.helper' -> 'helper', './helper' -> 'helper'
                segmen_terakhir = raw.replace('\\', '/').split('/')[-1].split('.')[-1]
                if segmen_terakhir and segmen_terakhir not in {"", ".", ".."}:
                    names.add(segmen_terakhir)
        return list(names)

    def _auto_read_related(self, project_root: str, selected_code: str) -> str:
        """Deteksi otomatis file yang di-import dari kode yang diblok, lalu baca isinya."""
        nama_modul = self._extract_imported_names(selected_code)
        if not nama_modul:
            return ""

        hasil_bacaan = []
        jumlah_dibaca = 0

        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            if jumlah_dibaca >= MAX_AUTO_READ:
                break
            for f in files:
                if jumlah_dibaca >= MAX_AUTO_READ:
                    break
                nama_file_tanpa_ext = os.path.splitext(f)[0]
                if nama_file_tanpa_ext in nama_modul:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, project_root)
                    isi = self._read_file(project_root, rel_path)
                    hasil_bacaan.append(f"--- {rel_path} ---\n{isi}")
                    jumlah_dibaca += 1

        return "\n\n".join(hasil_bacaan)