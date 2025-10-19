import json
import os
from datetime import datetime

class ConfigManager:
    """Verwaltet das Laden und Speichern der JSON-Konfigurationsdatei."""

    def __init__(self, config_file="arduino_config.json"):
        self.config_file = config_file

    def save_config(self, sequences, pin_configs, dashboard_layouts=None):
        """Speichert die aktuelle Konfiguration in die JSON-Datei."""
        config = {
            "version": "2.7", # Version erhöht
            "sequences": sequences,
            "pin_configs": pin_configs,
            "dashboard_layouts": dashboard_layouts or {}, # NEU: Speichert ein Dictionary von Layouts
            "saved_at": datetime.now().isoformat()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")
            return False

    def load_config(self):
        """Lädt die Konfiguration aus der JSON-Datei."""
        if not os.path.exists(self.config_file):
            return None
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            return None
