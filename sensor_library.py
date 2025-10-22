# -*- coding: utf-8 -*-
"""
Sensor-Bibliothek für Arduino Control Panel
Unterstützt 40 Sensoren aus Arduino 4duino Sensor-Kit 40-in-1
UND lädt benutzerdefinierte Sensoren aus user_sensor_library.json.
"""

import json
import os
import copy
from dataclasses import dataclass, field
from typing import Dict, Any, Callable, Optional, Tuple
from enum import Enum

# Pfad zur JSON-Datei für benutzerdefinierte Sensoren
script_dir = os.path.dirname(os.path.abspath(__file__))
USER_SENSOR_FILE = os.path.join(os.path.dirname(script_dir), "user_sensor_library.json")


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
    OTHER = "other"


@dataclass
class SensorDefinition:
    """Definition eines Sensors"""
    id: str
    name: str
    sensor_type: SensorType
    pins: Dict[str, str] = field(default_factory=dict)
    protocol: str = "other"
    value_range: Tuple[float, float] = (0.0, 0.0)
    unit: str = ""
    read_interval_ms: int = 1000
    calibration_func: Optional[Callable] = None
    description: str = ""
    icon: str = "❓"
    is_user: bool = False

    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        """Konvertiert das Objekt in ein Dictionary zum Speichern"""
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
        }

    @classmethod
    def from_dict(cls, data):
        """Erstellt ein Objekt aus einem Dictionary"""
        if not isinstance(data, dict):
            return None
        try:
            sensor_type_enum = SensorType(data.get('sensor_type', 'other'))
        except ValueError:
            sensor_type_enum = SensorType.OTHER

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
            is_user=True
        )


class SensorLibrary:
    """
    Verwaltet Built-in und benutzerdefinierte Sensoren.
    Lädt benutzerdefinierte Sensoren aus user_sensor_library.json.
    """

    # --- Fest codierte Built-in Sensoren (40-in-1 Kit) ---
    _BUILTIN_SENSORS: Dict[str, SensorDefinition] = {
        # ===== TEMPERATUR SENSOREN =====
        "DHT11": SensorDefinition(
            id="DHT11", name="DHT11 Temp/Humidity", sensor_type=SensorType.TEMPERATURE,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 50), unit="°C/%", icon="🌡️",
            description="Günstiger Temperatur- und Feuchtigkeitssensor, Genauigkeit ±2°C / ±5%"
        ),
        "DHT22": SensorDefinition(
            id="DHT22", name="DHT22 Precision Temp/Humidity", sensor_type=SensorType.TEMPERATURE,
            pins={"data": "D2"}, protocol="digital", value_range=(-40, 80), unit="°C/%", icon="🌡️",
            description="Präziser Temperatur- und Feuchtigkeitssensor, Genauigkeit ±0.5°C / ±2%"
        ),
        "DS18B20": SensorDefinition(
            id="DS18B20", name="DS18B20 Waterproof Temp", sensor_type=SensorType.TEMPERATURE,
            pins={"data": "D3"}, protocol="onewire", value_range=(-55, 125), unit="°C", icon="🌊",
            description="Wasserdichter digitaler Temperatursensor mit OneWire-Protokoll"
        ),
        "LM35": SensorDefinition(
            id="LM35", name="LM35 Analog Temperature", sensor_type=SensorType.TEMPERATURE,
            pins={"analog": "A0"}, protocol="analog", value_range=(-55, 150), unit="°C", icon="🌡️",
            calibration_func=lambda x: (x * 5.0 / 1024.0) * 100,
            description="Analoger Präzisions-Temperatursensor, 10mV/°C"
        ),
        "TMP36": SensorDefinition(
            id="TMP36", name="TMP36 Temperature", sensor_type=SensorType.TEMPERATURE,
            pins={"analog": "A0"}, protocol="analog", value_range=(-40, 125), unit="°C", icon="🌡️",
            calibration_func=lambda x: ((x * 5.0 / 1024.0) - 0.5) * 100,
            description="Analoger Temperatursensor mit niedriger Spannung"
        ),
        
        # ===== LICHT SENSOREN =====
        "LDR": SensorDefinition(
            id="LDR", name="Photoresistor (LDR)", sensor_type=SensorType.LIGHT,
            pins={"analog": "A0"}, protocol="analog", value_range=(0, 1023), unit="raw", icon="💡",
            description="Lichtabhängiger Widerstand zur Helligkeitsmessung"
        ),
        "BH1750": SensorDefinition(
            id="BH1750", name="BH1750 Digital Light", sensor_type=SensorType.LIGHT,
            pins={"SDA": "A4", "SCL": "A5"}, protocol="i2c", value_range=(1, 65535), unit="lux", icon="☀️",
            description="Digitaler Lichtsensor mit I2C, misst bis 65535 Lux"
        ),
        
        # ===== BEWEGUNGS- UND NÄHERUNGSSENSOREN =====
        "HC_SR501": SensorDefinition(
            id="HC_SR501", name="HC-SR501 PIR Motion", sensor_type=SensorType.MOTION,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="motion", icon="🚶",
            description="Passiver Infrarot-Bewegungsmelder, Reichweite bis 7m"
        ),
        "HC_SR04": SensorDefinition(
            id="HC_SR04", name="HC-SR04 Ultrasonic Distance", sensor_type=SensorType.DISTANCE,
            pins={"trigger": "D9", "echo": "D10"}, protocol="digital", value_range=(2, 400), unit="cm", icon="📏",
            description="Ultraschall-Entfernungssensor, Messbereich 2-400cm"
        ),
        "VIBRATION_SW420": SensorDefinition(
            id="VIBRATION_SW420", name="SW-420 Vibration Sensor", sensor_type=SensorType.MOTION,
            pins={"digital": "D2", "analog": "A0"}, protocol="digital", value_range=(0, 1), unit="vibration", icon="📳",
            description="Erschütterungssensor mit einstellbarer Empfindlichkeit"
        ),
        "TILT_SWITCH": SensorDefinition(
            id="TILT_SWITCH", name="Tilt Switch (Ball)", sensor_type=SensorType.MOTION,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="tilt", icon="⚖️",
            description="Neigungsschalter mit Metallkugel"
        ),
        
        # ===== HALL-EFFEKT & MAGNETFELD =====
        "HALL_A3144": SensorDefinition(
            id="HALL_A3144", name="A3144 Hall Effect", sensor_type=SensorType.MAGNETIC,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="magnetic", icon="🧲",
            description="Hall-Effekt-Sensor zur Magneterkennung (digital)"
        ),
        "HALL_49E": SensorDefinition(
            id="HALL_49E", name="49E Linear Hall Sensor", sensor_type=SensorType.MAGNETIC,
            pins={"analog": "A0"}, protocol="analog", value_range=(0, 1023), unit="gauss", icon="🧲",
            description="Linearer Hall-Sensor für analoge Magnetfeldmessung"
        ),
        "REED_SWITCH": SensorDefinition(
            id="REED_SWITCH", name="Reed Switch (Magnetic)", sensor_type=SensorType.MAGNETIC,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="magnetic", icon="🧲",
            description="Magnetischer Reed-Schalter"
        ),
        
        # ===== FEUER & FLAMMEN =====
        "FLAME_SENSOR": SensorDefinition(
            id="FLAME_SENSOR", name="Flame Sensor", sensor_type=SensorType.FLAME,
            pins={"digital": "D2", "analog": "A0"}, protocol="digital", value_range=(0, 1), unit="flame", icon="🔥",
            description="Infrarot-Flammendetektor, Wellenlänge 760-1100nm"
        ),
        
        # ===== KLANG & AUDIO =====
        "SOUND_SENSOR": SensorDefinition(
            id="SOUND_SENSOR", name="Sound Detection Module", sensor_type=SensorType.SOUND,
            pins={"digital": "D2", "analog": "A0"}, protocol="analog", value_range=(0, 1023), unit="sound", icon="🔊",
            description="Mikrofon-Modul zur Geräuscherkennung"
        ),
        
        # ===== FEUCHTIGKEIT =====
        "SOIL_MOISTURE": SensorDefinition(
            id="SOIL_MOISTURE", name="Soil Moisture Sensor", sensor_type=SensorType.WATER,
            pins={"analog": "A0"}, protocol="analog", value_range=(0, 1023), unit="moisture", icon="🌱",
            description="Bodenfeuchtigkeitssensor (kapazitiv oder resistiv)"
        ),
        "RAIN_SENSOR": SensorDefinition(
            id="RAIN_SENSOR", name="Rain Drop Sensor", sensor_type=SensorType.WATER,
            pins={"digital": "D2", "analog": "A0"}, protocol="analog", value_range=(0, 1023), unit="rain", icon="🌧️",
            description="Regentropfen-Erkennungssensor"
        ),
        
        # ===== GAS & LUFT QUALITÄT =====
        "MQ2": SensorDefinition(
            id="MQ2", name="MQ-2 Gas Sensor", sensor_type=SensorType.GAS,
            pins={"analog": "A0", "digital": "D2"}, protocol="analog", value_range=(0, 1023), unit="ppm", icon="💨",
            description="Gas-Sensor für LPG, Propan, Methan, Rauch"
        ),
        
        # ===== JOYSTICKS & EINGABE =====
        "JOYSTICK": SensorDefinition(
            id="JOYSTICK", name="Analog Joystick", sensor_type=SensorType.OTHER,
            pins={"x": "A0", "y": "A1", "button": "D2"}, protocol="analog", value_range=(0, 1023), unit="xy", icon="🕹️",
            description="2-Achsen Analog Joystick mit Taster"
        ),
        
        # ===== ROTARY ENCODER =====
        "ROTARY_ENCODER": SensorDefinition(
            id="ROTARY_ENCODER", name="Rotary Encoder", sensor_type=SensorType.ROTATION,
            pins={"CLK": "D2", "DT": "D3", "SW": "D4"}, protocol="digital", value_range=(-1000, 1000), unit="steps", icon="🔄",
            description="Drehgeber mit Taster für Menüsteuerung"
        ),
        
        # ===== TOUCH & KAPAZITIV =====
        "TOUCH_TTP223": SensorDefinition(
            id="TOUCH_TTP223", name="TTP223 Capacitive Touch", sensor_type=SensorType.TOUCH,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="touch", icon="👆",
            description="Kapazitiver Touch-Sensor"
        ),
        
        # ===== TRACKING SENSOR =====
        "LINE_TRACKING": SensorDefinition(
            id="LINE_TRACKING", name="Line Tracking Sensor", sensor_type=SensorType.OTHER,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="line", icon="🛤️",
            description="Infrarot-Linienverfolgungs-Sensor"
        ),
        "OBSTACLE_AVOIDANCE": SensorDefinition(
            id="OBSTACLE_AVOIDANCE", name="Obstacle Avoidance IR", sensor_type=SensorType.DISTANCE,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="obstacle", icon="🚧",
            description="Infrarot-Hindernis-Vermeidungssensor"
        ),
        
        # ===== RGB & FARBE =====
        "RGB_LED": SensorDefinition(
            id="RGB_LED", name="RGB LED Module", sensor_type=SensorType.OTHER,
            pins={"red": "D9", "green": "D10", "blue": "D11"}, protocol="digital", value_range=(0, 255), unit="rgb", icon="🎨",
            description="RGB LED Modul (gemeinsame Kathode/Anode)"
        ),
        
        # ===== IR EMPFÄNGER =====
        "IR_RECEIVER": SensorDefinition(
            id="IR_RECEIVER", name="IR Receiver VS1838B", sensor_type=SensorType.OTHER,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="ir", icon="📡",
            description="Infrarot-Empfänger für Fernbedienungen"
        ),
        
        # ===== BUZZER =====
        "BUZZER_ACTIVE": SensorDefinition(
            id="BUZZER_ACTIVE", name="Active Buzzer", sensor_type=SensorType.OTHER,
            pins={"data": "D8"}, protocol="digital", value_range=(0, 1), unit="beep", icon="🔔",
            description="Aktiver Buzzer (feste Frequenz)"
        ),
        "BUZZER_PASSIVE": SensorDefinition(
            id="BUZZER_PASSIVE", name="Passive Buzzer", sensor_type=SensorType.OTHER,
            pins={"data": "D8"}, protocol="digital", value_range=(0, 1), unit="tone", icon="🎵",
            description="Passiver Buzzer (variable Frequenzen möglich)"
        ),
        
        # ===== RELAIS =====
        "RELAY_1CH": SensorDefinition(
            id="RELAY_1CH", name="1-Channel Relay", sensor_type=SensorType.OTHER,
            pins={"control": "D7"}, protocol="digital", value_range=(0, 1), unit="relay", icon="⚡",
            description="1-Kanal Relais Modul 5V/10A"
        ),
        
        # ===== LASER & LED =====
        "LASER_DIODE": SensorDefinition(
            id="LASER_DIODE", name="Laser Diode Module", sensor_type=SensorType.OTHER,
            pins={"data": "D8"}, protocol="digital", value_range=(0, 1), unit="laser", icon="🔴",
            description="Laser-Dioden-Modul (Klasse 2, <1mW)"
        ),
        "LED_MODULE": SensorDefinition(
            id="LED_MODULE", name="LED Module", sensor_type=SensorType.OTHER,
            pins={"data": "D8"}, protocol="digital", value_range=(0, 1), unit="led", icon="💡",
            description="Einfaches LED Modul"
        ),
        
        # ===== TASTEN =====
        "BUTTON_MODULE": SensorDefinition(
            id="BUTTON_MODULE", name="Push Button Module", sensor_type=SensorType.OTHER,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="button", icon="🔘",
            description="Taster-Modul mit Pull-Up/Down"
        ),
        
        # ===== TEMPERATUR & LUFTDRUCK =====
        "BMP180": SensorDefinition(
            id="BMP180", name="BMP180 Pressure/Temp", sensor_type=SensorType.PRESSURE,
            pins={"SDA": "A4", "SCL": "A5"}, protocol="i2c", value_range=(300, 1100), unit="hPa/°C", icon="🌡️",
            description="Luftdruck- und Temperatursensor (I2C)"
        ),
        
        # ===== OPTOKOPPLER =====
        "PHOTO_INTERRUPTER": SensorDefinition(
            id="PHOTO_INTERRUPTER", name="Photo Interrupter", sensor_type=SensorType.OTHER,
            pins={"data": "D2"}, protocol="digital", value_range=(0, 1), unit="interrupt", icon="🚦",
            description="Optischer Unterbrecher / Lichtschranke"
        ),
    }

    # --- Speicher für geladene User-Sensoren ---
    _user_sensors: Dict[str, SensorDefinition] = {}
    _combined_sensors: Dict[str, SensorDefinition] = {}
    _loaded = False

    @classmethod
    def load_all_sensors(cls, force_reload=False):
        """Lädt Built-in und User-Sensoren und kombiniert sie."""
        if cls._loaded and not force_reload:
            return

        print("Lade Sensorbibliothek...")
        cls._user_sensors = {}
        cls._combined_sensors = {}

        # 1. Built-in Sensoren laden (als Kopie)
        for sid, sdef in cls._BUILTIN_SENSORS.items():
            if isinstance(sdef, SensorDefinition):
                cls._combined_sensors[sid] = copy.deepcopy(sdef)
                cls._combined_sensors[sid].is_user = False

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
        """Gibt alle geladenen (kombinierten) Sensoren zurück."""
        if not cls._loaded:
            cls.load_all_sensors()
        return cls._combined_sensors

    @classmethod
    def get_user_sensors(cls) -> Dict[str, SensorDefinition]:
        """Gibt nur die benutzerdefinierten Sensoren zurück."""
        if not cls._loaded:
            cls.load_all_sensors()
        return cls._user_sensors

    @classmethod
    def get_sensor(cls, sensor_id: str) -> Optional[SensorDefinition]:
        """Ruft eine spezifische Sensor-Definition ab (User überschreibt Built-in)."""
        if not cls._loaded:
            cls.load_all_sensors()
        return cls._combined_sensors.get(sensor_id)

    @classmethod
    def save_user_sensors(cls, user_sensors_dict: Dict[str, SensorDefinition]) -> bool:
        """Speichert das übergebene Dictionary von User-Sensoren in die JSON-Datei."""
        try:
            data_to_save = {sid: sdef.to_dict() for sid, sdef in user_sensors_dict.items()}

            with open(USER_SENSOR_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            print(f"Benutzerdefinierte Sensoren gespeichert in {USER_SENSOR_FILE}")
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

    dht = SensorLibrary.get_sensor("DHT11")
    if dht:
        print(f"\nDetails für {dht.id}:")
        print(f"  Pins: {dht.pins}")
        print(f"  User defined: {dht.is_user}")