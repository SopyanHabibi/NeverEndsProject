import json
import datetime
from core.plugin_manager import BasePlugin
from database import db


class WorkflowEnginePlugin(BasePlugin):
    def initialize(self):
        print("Workflow Engine siap.")

    def execute(self, mode: str, *args, **kwargs):
        """
        mode dipakai buat bedain dipanggil buat apa, karena satu plugin
        bisa dipanggil dari beberapa keperluan (checker vs action executor).
        """
        if mode == "check_time_triggers":
            return self._check_time_triggers()
        elif mode == "run_actions":
            return self._run_actions(kwargs.get("actions"))
        else:
            raise ValueError(f"Mode '{mode}' tidak dikenali di Workflow Engine")

    def _check_time_triggers(self):
        """Dipanggil scheduler loop tiap interval. Cek workflow time-based yang cocok jam sekarang."""
        now = datetime.datetime.now()
        jam_sekarang = now.strftime("%H:%M")
        tanggal_sekarang = now.strftime("%Y-%m-%d")

        workflows = db.ambil_workflow_aktif_by_type("time")
        for wf in workflows:
            try:
                config = json.loads(wf["trigger_config"])
            except (json.JSONDecodeError, TypeError):
                continue

            target_jam = config.get("time")
            if target_jam != jam_sekarang:
                continue

            # Cegah double-trigger di menit yang sama
            if wf["last_run"] and wf["last_run"].startswith(f"{tanggal_sekarang} {jam_sekarang}"):
                continue

            try:
                actions = json.loads(wf["actions"])
                self._run_actions(actions)
                db.update_last_run_workflow(wf["id"], now.isoformat(sep=' ', timespec='seconds'))
                print(f"[Workflow] '{wf['nama']}' dijalankan.")
            except Exception as e:
                print(f"[Workflow] Gagal jalankan '{wf['nama']}': {e}")

    def _run_actions(self, actions: list):
        """Panggil plugin lain lewat plugin_manager, murni programmatic, tanpa LLM."""
        from core.llm_engine import plugin_manager as pm

        for act in actions:
            plugin_id = act.get("plugin")
            params = act.get("params", {})
            try:
                pm.execute_plugin(plugin_id, **params)
            except Exception as e:
                print(f"[Workflow] Action gagal ({plugin_id}): {e}")