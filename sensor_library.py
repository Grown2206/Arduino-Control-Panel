# -*- coding: utf-8 -*-
"""
Sensor-Bibliothek für Arduino Control Panel
Unterstützt gängige Sensoren aus Arduino Starter Kits
UND lädt benutzerdefinierte Sensoren aus user_sensor_library.json.
"""

import json
import os
import copy
from dataclasses import dataclass, field # field importieren
from typing import Dict, Any, Callable, Optional, Tuple # Tuple importieren
from enum import Enum

# Pfad zur JSON-Datei für benutzerdefinierte Sensoren
# Gehe davon aus, dass diese Datei im selben Verzeichnis wie sensor_library.py liegt
# oder im Hauptverzeichnis (passe Pfad ggf. an)
script_dir = os.path.dirname(os.path.abspath(__file__))
# USER_SENSOR_FILE = os.path.join(script_dir, "user_sensor_library.json") # Wenn im selben Ordner
USER_SENSOR_FILE = os.path.join(os.path.dirname(script_dir), "user_sensor_library.json") # Wenn im Parent-Ordner


class SensorType(Enum):
    """Sensor-Kategorien"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    LIGHT = "light"
    MOTION = "motion"
    DISTANCE = "distance"
    SOUND = "sound"
    GAS = "gas"
    PRESSURE = "pressure"
    ACCELERATION = "acceleration"
    MAGNETIC = "magnetic"
    ROTATION = "rotation"
    TOUCH = "touch"
    WATER = "water"
    FLAME = "flame"
    OTHER = "other" # Kategorie für Unbekannt/Sonstige


@dataclass
class SensorDefinition:
    """Definition eines Sensors"""
    id: str
    name: str
    sensor_type: SensorType
    pins: Dict[str, str] = field(default_factory=dict)
    protocol: str = "other"
    value_range: Tuple[float, float] = (0.0, 0.0) # Tuple statt tuple
    unit: str = ""
    read_interval_ms: int = 1000
    calibration_func: Optional[Callable] = None
    description: str = ""
    icon: str = "❓" # Geändert von 📊 auf ❓
    is_user: bool = False # NEU: Flag für benutzerdefinierte Sensoren

    # Mache das Objekt Dictionary-ähnlich für einfachen Zugriff (optional)
    def __getitem__(self, key):
         return getattr(self, key)

    def to_dict(self):
        """ Konvertiert das Objekt in ein Dictionary zum Speichern """
        return {
            'id': self.id,
            'name': self.name,
            'sensor_type': self.sensor_type.value if isinstance(self.sensor_type, Enum) else self.sensor_type,
            'pins': self.pins,
            'protocol': self.protocol,
            'value_range': list(self.value_range),
            'unit': self.unit,
            'icon': self.icon,
            'description': self.description,
            # read_interval_ms etc. können hier auch gespeichert werden
        }

    @classmethod
    def from_dict(cls, data):
        """ Erstellt ein Objekt aus einem Dictionary """
        if not isinstance(data, dict): return None
        try:
             sensor_type_enum = SensorType(data.get('sensor_type', 'other'))
        except ValueError:
             sensor_type_enum = SensorType.OTHER # Fallback

        return cls(
            id=data.get('id', ''),
            name=data.get('name', 'Unbenannt'),
            sensor_type=sensor_type_enum,
            pins=data.get('pins', {}),
            protocol=data.get('protocol', 'other'),
            value_range=tuple(data.get('value_range', (0.0, 0.0))),
            unit=data.get('unit', ''),
            icon=data.get('icon', '❓'),
            description=data.get('description', ''),
            is_user=True # Markiere als User-Sensor
            # read_interval_ms etc.
        )


class SensorLibrary:
    """
    Verwaltet Built-in und benutzerdefinierte Sensoren.
    Lädt benutzerdefinierte Sensoren aus user_sensor_library.json.
    """

    # --- Fest codierte Built-in Sensoren ---
    # (Beachte: SensorType Enum verwenden)
    _BUILTIN_SENSORS: Dict[str, SensorDefinition] = {
        "DHT11": SensorDefinition(id="DHT11", name="DHT11 Temp/Humidity", sensor_type=SensorType.TEMPERATURE, pins={"data": "D2"}, protocol="digital", value_range=(0, 50), unit="°C/%", icon="🌡️"),
        "DHT22": SensorDefinition(id="DHT22", name="DHT22 Precision Temp/Humidity", sensor_type=SensorType.TEMPERATURE, pins={"data": "D2"}, protocol="digital", value_range=(-40, 80), unit="°C/%", icon="🌡️"),
        "DS18B20": SensorDefinition(id="DS18B20", name="DS18B20 Waterproof Temp", sensor_type=SensorType.TEMPERATURE, pins={"data": "D3"}, protocol="onewire", value_range=(-55, 125), unit="°C", icon="🌊"),
        "LM35": SensorDefinition(id="LM35", name="LM35 Analog Temperature", sensor_type=SensorType.TEMPERATURE, pins={"analog": "A0"}, protocol="analog", value_range=(-55, 150), unit="°C", calibration_func=lambda x: (x * 5.0 / 1024.0) * 100, icon="🌡️"),
        "LDR": SensorDefinition(id="LDR", name="Photoresistor (LDR)", sensor_type=SensorType.LIGHT, pins={"analog": "A0"}, protocol="analog", value_range=(0, 1023), unit="raw", icon="💡"), # Einheit von Lux auf raw geändert
        "HC_SR501": SensorDefinition(id="HC_SR501", name="HC-SR501 PIR Motion", sensor_type=SensorType.MOTION, pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="motion", icon="🚶"),
        "HC_SR04": SensorDefinition(id="HC_SR04", name="HC-SR04 Ultrasonic Distance", sensor_type=SensorType.DISTANCE, pins={"trigger": "D9", "echo": "D10"}, protocol="digital", value_range=(2, 400), unit="cm", icon="📏"),
        "VIBRATION_SW420": SensorDefinition(id="VIBRATION_SW420", name="SW-420 Vibration Sensor", sensor_type=SensorType.MOTION, pins={"digital": "D2", "analog": "A0"}, protocol="digital", value_range=(0, 1), unit="vibration", icon="📳"),
        # Füge hier weitere Built-in Sensoren hinzu...
    }

    # --- Speicher für geladene User-Sensoren ---
    _user_sensors: Dict[str, SensorDefinition] = {}
    _combined_sensors: Dict[str, SensorDefinition] = {}
    _loaded = False # Flag, ob schon geladen wurde

    @classmethod
    def load_all_sensors(cls, force_reload=False):
        """ Lädt Built-in und User-Sensoren und kombiniert sie. """
        if cls._loaded and not force_reload:
             return

        print("Lade Sensorbibliothek...")
        cls._user_sensors = {}
        cls._combined_sensors = {}

        # 1. Built-in Sensoren laden (als Kopie)
        for sid, sdef in cls._BUILTIN_SENSORS.items():
            if isinstance(sdef, SensorDefinition): # Nur gültige Definitionen
                cls._combined_sensors[sid] = copy.deepcopy(sdef)
                cls._combined_sensors[sid].is_user = False # Sicherstellen, dass Flag gesetzt ist


        # 2. User-Sensoren aus JSON laden
        if os.path.exists(USER_SENSOR_FILE):
            try:
                with open(USER_SENSOR_FILE, 'r', encoding='utf-8') as f:
                    loaded_user_data = json.load(f)
                    if not isinstance(loaded_user_data, dict):
                         print(f"WARNUNG: {USER_SENSOR_FILE} enthält kein valides JSON-Objekt.")
                         loaded_user_data = {}

                    for sensor_id, data in loaded_user_data.items():
                         user_def = SensorDefinition.from_dict(data)
                         if user_def:
                             cls._user_sensors[sensor_id] = user_def
                             # Überschreibe Built-in mit User-Definition, falls ID gleich
                             cls._combined_sensors[sensor_id] = user_def
                             print(f"  - Benutzerdefinierten Sensor geladen: {sensor_id}")
                         else:
                              print(f"WARNUNG: Ungültige Daten für Sensor '{sensor_id}' in {USER_SENSOR_FILE}.")

            except json.JSONDecodeError:
                print(f"FEHLER: {USER_SENSOR_FILE} konnte nicht als JSON geparsed werden.")
            except Exception as e:
                print(f"FEHLER: Unbekannter Fehler beim Laden von {USER_SENSOR_FILE}: {e}")
        else:
             print(f"INFO: {USER_SENSOR_FILE} nicht gefunden. Keine benutzerdefinierten Sensoren geladen.")

        cls._loaded = True
        print(f"Sensorbibliothek geladen: {len(cls._combined_sensors)} Sensoren insgesamt ({len(cls._user_sensors)} benutzerdefiniert).")


    @classmethod
    def get_all_sensors(cls) -> Dict[str, SensorDefinition]:
        """ Gibt alle geladenen (kombinierten) Sensoren zurück. """
        if not cls._loaded:
            cls.load_all_sensors()
        return cls._combined_sensors

    @classmethod
    def get_user_sensors(cls) -> Dict[str, SensorDefinition]:
         """ Gibt nur die benutzerdefinierten Sensoren zurück. """
         if not cls._loaded:
            cls.load_all_sensors()
         return cls._user_sensors

    @classmethod
    def get_sensor(cls, sensor_id: str) -> Optional[SensorDefinition]:
        """ Ruft eine spezifische Sensor-Definition ab (User überschreibt Built-in). """
        if not cls._loaded:
            cls.load_all_sensors()
        return cls._combined_sensors.get(sensor_id)

    @classmethod
    def save_user_sensors(cls, user_sensors_dict: Dict[str, SensorDefinition]) -> bool:
         """ Speichert das übergebene Dictionary von User-Sensoren in die JSON-Datei. """
         try:
            # Konvertiere SensorDefinition Objekte in Dictionaries für JSON
            data_to_save = {sid: sdef.to_dict() for sid, sdef in user_sensors_dict.items()}

            with open(USER_SENSOR_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            print(f"Benutzerdefinierte Sensoren gespeichert in {USER_SENSOR_FILE}")
            # Markiere als neu geladen, damit get_all_sensors etc. die Änderungen bemerken
            cls._loaded = False
            return True
         except Exception as e:
            print(f"FEHLER: Konnte {USER_SENSOR_FILE} nicht schreiben: {e}")
            return False

# --- Initiales Laden beim Importieren des Moduls ---
SensorLibrary.load_all_sensors()


# === VERWENDUNGSBEISPIEL ===
if __name__ == "__main__":
    all_sensors = SensorLibrary.get_all_sensors()
    print("\n--- Alle geladenen Sensoren ---")
    for sid, sensor in all_sensors.items():
        user_flag = "[User]" if sensor.is_user else ""
        print(f"ID: {sid:<20} Name: {sensor.name:<30} Typ: {sensor.sensor_type.value:<15} {user_flag}")

    # Beispiel: Einen Sensor abrufen
    dht = SensorLibrary.get_sensor("DHT11")
    if dht:
        print(f"\nDetails für {dht.id}:")
        print(f"  Pins: {dht.pins}")
        print(f"  User defined: {dht.is_user}")

    # Beispiel: Neuen Sensor hinzufügen (simuliert) und speichern
    print("\n--- Füge Test-Sensor hinzu ---")
    new_sensor = SensorDefinition.from_dict({
        'id': 'TEST_SENSOR', 'name': 'Mein Test Sensor', 'sensor_type': 'other',
        'pins': {'analog': 'A5'}, 'protocol': 'analog', 'value_range': [0, 1023],
        'unit': 'TestUnits', 'icon': '🧪', 'description': 'Ein einfacher Test'
    })
    if new_sensor:
        current_user_sensors = SensorLibrary.get_user_sensors()
        current_user_sensors[new_sensor.id] = new_sensor
        SensorLibrary.save_user_sensors(current_user_sensors)

        # Neu laden und prüfen
        SensorLibrary.load_all_sensors(force_reload=True)
        test_sensor_loaded = SensorLibrary.get_sensor("TEST_SENSOR")
        if test_sensor_loaded:
             print(f"Test-Sensor '{test_sensor_loaded.name}' erfolgreich geladen/gespeichert (is_user={test_sensor_loaded.is_user}).")
        else:
             print("FEHLER: Test-Sensor konnte nach Speichern nicht geladen werden.")