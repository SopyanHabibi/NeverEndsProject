from database import db
from core.plugin_manager import BasePlugin

class TasksPlugin(BasePlugin):

    def execute(self):

        tugas = db.ambil_tugas()

        return self._format_tugas(tugas)

    def _format_tugas(self, daftar):

        if not daftar:
            return "No pending tasks, Ian. You're all clear!"

        baris = [
            f"#{t['id']} - {t['deskripsi']}"
            + (f" (deadline: {t['deadline']})" if t["deadline"] else "")
            for t in daftar
        ]

        return "Here's your task list:\n" + "\n".join(baris)