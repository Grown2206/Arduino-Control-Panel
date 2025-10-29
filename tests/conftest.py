# -*- coding: utf-8 -*-
"""
pytest Fixtures und Konfiguration für alle Tests
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path

# Füge Projekt-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Erstellt ein temporäres Verzeichnis für Tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_file(temp_dir):
    """Erstellt eine temporäre Konfigurationsdatei"""
    config_file = temp_dir / "test_config.json"
    yield config_file
    # Cleanup wird automatisch durch temp_dir gemacht


@pytest.fixture
def temp_db_file(temp_dir):
    """Erstellt eine temporäre Datenbankdatei"""
    db_file = temp_dir / "test_database.db"
    yield str(db_file)
    # Cleanup wird automatisch durch temp_dir gemacht


@pytest.fixture
def sample_config_data():
    """Gibt Beispiel-Konfigurationsdaten zurück"""
    return {
        "sequences": {
            "test-seq-1": {
                "name": "Test Sequence 1",
                "cycles": 5,
                "steps": [
                    {"type": "digital_write", "pin": "D2", "value": 1, "delay": 100},
                    {"type": "digital_write", "pin": "D2", "value": 0, "delay": 100}
                ]
            }
        },
        "pin_configs": {
            "D2": {"mode": "OUTPUT", "label": "Test Pin"}
        },
        "relay_ch1_pin": 2,
        "relay_ch2_pin": 3,
        "theme": "dark"
    }


@pytest.fixture
def sample_pin_config():
    """Gibt Beispiel-Pin-Konfiguration zurück"""
    return {
        "pin_functions": {
            "D2": "OUTPUT",
            "D3": "OUTPUT",
            "A0": "INPUT"
        },
        "active_sensors": {
            "DHT11": {
                "sensor_type": "DHT11",
                "pin_config": {"data_pin": 4}
            }
        }
    }
