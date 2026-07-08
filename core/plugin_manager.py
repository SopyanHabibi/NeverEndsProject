import os
import json
import importlib.util
from typing import Dict, Any

class BasePlugin:
    """Semua plugin di Neira WAJIB mewarisi class ini"""
    def __init__(self, manifest: dict):
        self.manifest = manifest
        self.name = manifest.get("name")
        self.version = manifest.get("version")

    def initialize(self):
        """Dipanggil saat plugin pertama kali di-load"""
        pass

    def execute(self, *args, **kwargs) -> Any:
        """Fungsi utama yang dipanggil saat plugin dijalankan"""
        raise NotImplementedError("Plugin harus mengimplementasikan fungsi execute()")


class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, BasePlugin] = {}

    def load_plugins(self):
        """Scan folder plugins dan load semuanya secara dinamis"""
        if not os.path.exists(self.plugins_dir):
            print(f"Folder {self.plugins_dir} tidak ditemukan.")
            return

        for folder_name in os.listdir(self.plugins_dir):
            plugin_folder = os.path.join(self.plugins_dir, folder_name)
            
            # Pastikan ini folder dan punya manifest.json & plugin.py
            if os.path.isdir(plugin_folder):
                manifest_path = os.path.join(plugin_folder, "manifest.json")
                script_path = os.path.join(plugin_folder, "plugin.py")

                if os.path.exists(manifest_path) and os.path.exists(script_path):
                    try:
                        # 1. Baca Manifest
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        
                        plugin_id = manifest.get("id", folder_name)

                        # 2. Load script python secara dinamis
                        spec = importlib.util.spec_from_file_location(folder_name, script_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # 3. Cari class yang meng-inherit BasePlugin di dalam script
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                                # Instansiasi plugin
                                plugin_instance = attr(manifest)
                                plugin_instance.initialize()
                                
                                # Simpan ke dictionary manager
                                self.plugins[plugin_id] = plugin_instance
                                print(f"Successfully loaded plugin: {manifest.get('name')} ({plugin_id})")
                                break
                    except Exception as e:
                        print(f"Failed to load plugin {folder_name}: {e}")

    def get_plugin(self, plugin_id: str) -> BasePlugin:
        return self.plugins.get(plugin_id)

    def execute_plugin(self, plugin_id: str, *args, **kwargs):
        plugin = self.get_plugin(plugin_id)
        if plugin:
            return plugin.execute(*args, **kwargs)
        else:
            print(f"Plugin {plugin_id} tidak ditemukan.")
            return None