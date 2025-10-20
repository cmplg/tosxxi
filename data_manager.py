# data_manager.py
import json
from pathlib import Path

class DataManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "technical-apps"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.studios_file = self.config_dir / "studios.json"
        self.dcp_log_file = self.config_dir / "dcp_log.json"
        self.technicians_file = self.config_dir / "technicians.json"
        self.fpkb_file = self.config_dir / "fpkb.json"

        self.default_config = {
            "save_path": str(Path.home() / "LSS_Screenshots"), "theme": "darkly",
            "auto_zip": False, "outlet_name": "NAMA_OUTLET"
        }

    def _load_json(self, file_path, default_data=None):
        if default_data is None: default_data = []
        try:
            with open(file_path, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._save_json(file_path, default_data); return default_data

    def _save_json(self, file_path, data):
        with open(file_path, 'w') as f: json.dump(data, f, indent=4)

    def load_config(self):
        config = self._load_json(self.config_file, default_data=self.default_config)
        for key, value in self.default_config.items(): config.setdefault(key, value)
        self.save_config(config); return config

    def save_config(self, config_data): self._save_json(self.config_file, config_data)
    def load_studios(self): return self._load_json(self.studios_file, [])
    def save_studios(self, studios_data): self._save_json(self.studios_file, studios_data)
    def load_dcp_logs(self): return self._load_json(self.dcp_log_file, [])
    def save_dcp_logs(self, dcp_data): self._save_json(self.dcp_log_file, dcp_data)
    def load_technicians(self): return self._load_json(self.technicians_file, [])
    def save_technicians(self, tech_data): self._save_json(self.technicians_file, tech_data)
    
    def load_fpkb(self):
        data = self._load_json(self.fpkb_file, [])
        # Validasi struktur data. Jika tidak sesuai, reset file.
        if data and (not isinstance(data, list) or (data and 'items' not in data[0])):
            self.save_fpkb([])
            return []
        return data

    def save_fpkb(self, fpkb_data): self._save_json(self.fpkb_file, fpkb_data)