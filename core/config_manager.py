import json
import os
import sys

class ConfigManager:
    """
    Verwaltet die Lade- und Speichervorgänge für die JSON-Konfigurationsdatei.

    Diese Klasse ist jetzt "zustandsbehaftet" (stateful). Sie lädt die
    Konfiguration beim Start einmal in self.config und stellt
    get/set-Methoden für den Zugriff auf einzelne Schlüssel bereit.
    """
    
    def __init__(self, config_file="arduino_config.json"):
        """
        Initialisiert den ConfigManager und lädt die Konfiguration.
        """
        self.config_file = config_file
        self.config = {}
        self.load_config_from_file() # Konfiguration beim Start laden

    def load_config_from_file(self):
        """
        Lädt die Konfiguration aus der Datei in das Attribut 'self.config'.
        Gibt die geladene Konfiguration auch zurück.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    if not isinstance(self.config, dict):
                        print(f"Warnung: Konfigurationsdatei {self.config_file} ist beschädigt. Erstelle neue Konfiguration.")
                        self.config = {}
                    return self.config
            else:
                print(f"Hinweis: Konfigurationsdatei {self.config_file} nicht gefunden. Erstelle neue Konfiguration.")
                self.config = {}
                return self.config
        except json.JSONDecodeError:
            print(f"Fehler: Konfigurationsdatei {self.config_file} konnte nicht dekodiert werden. Erstelle Backup und neue Konfiguration.")
            # Versuche, ein Backup zu erstellen
            try:
                if os.path.exists(self.config_file):
                    os.rename(self.config_file, f"{self.config_file}.bak")
            except OSError as e:
                print(f"Konnte Backup-Datei nicht erstellen: {e}")
            self.config = {}
            return self.config
        except Exception as e:
            print(f"Allgemeiner Fehler beim Laden der Konfiguration: {e}")
            self.config = {}
            return self.config

    def save_config_to_file(self):
        """
        Speichert den aktuellen Inhalt von 'self.config' in die Datei.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4, sort_keys=True)
            # print("Konfiguration erfolgreich gespeichert.") # Optional: für Debugging
        except IOError as e:
            print(f"Fehler beim Speichern der Konfiguration in {self.config_file}: {e}")
        except Exception as e:
            print(f"Allgemeiner Fehler beim Speichern der Konfiguration: {e}")

    def get(self, key, default=None):
        """
        Ruft einen Wert aus der geladenen Konfiguration (self.config) ab.
        
        Beispiel:
        config.get("relay_ch1_pin", 2)
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """
        Setzt einen Wert in der Konfiguration (self.config).
        Dieser wird erst gespeichert, wenn save_config_to_file() aufgerufen wird.
        
        Beispiel:
        config.set("relay_ch1_pin", 2)
        """
        try:
            self.config[key] = value
        except Exception as e:
            print(f"Fehler beim Setzen des Konfigurationswerts für {key}: {e}")

    # --- Kompatibilitätsmethoden für main.py ---

    def load_config(self):
        """
        Veraltete Methode, die von main.py verwendet wird.
        Stellt sicher, dass die Konfiguration geladen ist und gibt sie zurück.
        """
        # Wenn self.config leer ist (z.B. beim ersten Aufruf), lade es.
        if not self.config:
            return self.load_config_from_file()
        return self.config

    def save_config(self, sequences, pin_configs, dashboard_layouts):
        """
        Veraltete Speichermethode (wird von main.py aufgerufen).
        
        Diese Methode aktualisiert self.config mit den Hauptdaten
        und speichert DANN die *gesamte* Konfiguration in die Datei.
        """
        # Aktualisiere die Hauptsektionen in self.config
        self.set("sequences", sequences)
        self.set("pin_configs", pin_configs)
        self.set("dashboard_layouts", dashboard_layouts)
        
        # Andere Sektionen (z.B. Relay-Einstellungen, die vorher via .set()
        # gesetzt wurden) bleiben erhalten.
        
        # Speichere die gesamte Konfiguration (inkl. Relay-Settings) in die Datei
        self.save_config_to_file()