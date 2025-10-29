# -*- coding: utf-8 -*-
"""
Unit Tests für ConfigManager
"""
import pytest
import json
from core.config_manager import ConfigManager


class TestConfigManager:
    """Test-Suite für ConfigManager"""

    def test_init_creates_empty_config(self, temp_config_file):
        """Test: Initialisierung mit nicht-existierender Datei"""
        config_manager = ConfigManager(str(temp_config_file))
        assert config_manager.config == {}
        assert config_manager.config_file == str(temp_config_file)

    def test_save_and_load_config(self, temp_config_file, sample_config_data):
        """Test: Speichern und Laden von Konfiguration"""
        # Speichern
        config_manager = ConfigManager(str(temp_config_file))
        config_manager.config = sample_config_data
        config_manager.save_config_to_file()

        # Datei sollte existieren
        assert temp_config_file.exists()

        # Laden
        config_manager2 = ConfigManager(str(temp_config_file))
        assert config_manager2.config == sample_config_data

    def test_get_existing_key(self, temp_config_file):
        """Test: Abrufen eines existierenden Schlüssels"""
        config_manager = ConfigManager(str(temp_config_file))
        config_manager.config = {"test_key": "test_value"}

        result = config_manager.get("test_key")
        assert result == "test_value"

    def test_get_non_existing_key_with_default(self, temp_config_file):
        """Test: Abrufen eines nicht-existierenden Schlüssels mit Default"""
        config_manager = ConfigManager(str(temp_config_file))

        result = config_manager.get("non_existing", "default_value")
        assert result == "default_value"

    def test_set_and_get(self, temp_config_file):
        """Test: Setzen und Abrufen eines Wertes"""
        config_manager = ConfigManager(str(temp_config_file))

        config_manager.set("new_key", "new_value")
        assert config_manager.get("new_key") == "new_value"

    def test_set_multiple_values(self, temp_config_file):
        """Test: Mehrere Werte setzen"""
        config_manager = ConfigManager(str(temp_config_file))

        config_manager.set("key1", "value1")
        config_manager.set("key2", 123)
        config_manager.set("key3", {"nested": "dict"})

        assert config_manager.get("key1") == "value1"
        assert config_manager.get("key2") == 123
        assert config_manager.get("key3") == {"nested": "dict"}

    def test_save_persists_data(self, temp_config_file):
        """Test: Gespeicherte Daten bleiben erhalten"""
        config_manager = ConfigManager(str(temp_config_file))

        config_manager.set("persist_key", "persist_value")
        config_manager.save_config_to_file()

        # Neue Instanz laden
        config_manager2 = ConfigManager(str(temp_config_file))
        assert config_manager2.get("persist_key") == "persist_value"

    def test_corrupted_json_creates_backup(self, temp_config_file):
        """Test: Korrupte JSON-Datei wird mit Backup behandelt"""
        # Erstelle korrupte JSON-Datei
        with open(temp_config_file, 'w') as f:
            f.write("{ invalid json }")

        config_manager = ConfigManager(str(temp_config_file))

        # Config sollte leer sein
        assert config_manager.config == {}

        # Backup sollte existieren
        backup_file = Path(str(temp_config_file) + ".bak")
        assert backup_file.exists()

    def test_load_config_compatibility_method(self, temp_config_file, sample_config_data):
        """Test: Kompatibilitätsmethode load_config()"""
        config_manager = ConfigManager(str(temp_config_file))
        config_manager.config = sample_config_data
        config_manager.save_config_to_file()

        # Verwende alte Methode
        loaded_config = config_manager.load_config()
        assert loaded_config == sample_config_data

    def test_save_config_compatibility_method(self, temp_config_file, sample_config_data):
        """Test: Kompatibilitätsmethode save_config()"""
        config_manager = ConfigManager(str(temp_config_file))

        # Verwende alte Methode
        config_manager.save_config(
            sequences=sample_config_data.get("sequences", {}),
            pin_configs=sample_config_data.get("pin_configs", {}),
            dashboard_layouts={}
        )

        # Lade und prüfe
        config_manager2 = ConfigManager(str(temp_config_file))
        assert config_manager2.get("sequences") == sample_config_data["sequences"]
        assert config_manager2.get("pin_configs") == sample_config_data["pin_configs"]
