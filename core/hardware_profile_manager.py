# -*- coding: utf-8 -*-
"""
core/hardware_profile_manager.py
Hardware-Profil-Management für verschiedene Arduino-Setups
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import serial.tools.list_ports


class HardwareProfile:
    """
    Repräsentiert ein Hardware-Profil
    """

    def __init__(
        self,
        profile_id: str,
        name: str,
        board_type: str = "Arduino Uno",
        description: str = "",
        pin_config: Optional[Dict[str, str]] = None,
        sensor_config: Optional[Dict[str, Any]] = None,
        custom_settings: Optional[Dict[str, Any]] = None
    ):
        self.profile_id = profile_id
        self.name = name
        self.board_type = board_type
        self.description = description
        self.pin_config = pin_config or {}
        self.sensor_config = sensor_config or {}
        self.custom_settings = custom_settings or {}
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Profil zu Dictionary"""
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'board_type': self.board_type,
            'description': self.description,
            'pin_config': self.pin_config,
            'sensor_config': self.sensor_config,
            'custom_settings': self.custom_settings,
            'created_at': self.created_at,
            'modified_at': self.modified_at
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'HardwareProfile':
        """Erstellt Profil aus Dictionary"""
        profile = HardwareProfile(
            profile_id=data['profile_id'],
            name=data['name'],
            board_type=data.get('board_type', 'Arduino Uno'),
            description=data.get('description', ''),
            pin_config=data.get('pin_config', {}),
            sensor_config=data.get('sensor_config', {}),
            custom_settings=data.get('custom_settings', {})
        )
        profile.created_at = data.get('created_at', datetime.now().isoformat())
        profile.modified_at = data.get('modified_at', datetime.now().isoformat())
        return profile

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        pin_config: Optional[Dict[str, str]] = None,
        sensor_config: Optional[Dict[str, Any]] = None,
        custom_settings: Optional[Dict[str, Any]] = None
    ):
        """Aktualisiert Profil-Daten"""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if pin_config is not None:
            self.pin_config = pin_config
        if sensor_config is not None:
            self.sensor_config = sensor_config
        if custom_settings is not None:
            self.custom_settings = custom_settings

        self.modified_at = datetime.now().isoformat()


class HardwareProfileManager:
    """
    Verwaltet Hardware-Profile
    - Profile speichern, laden, löschen
    - Import/Export
    - Auto-Erkennung von Boards
    """

    # Standard-Board-Typen
    BOARD_TYPES = [
        "Arduino Uno",
        "Arduino Mega 2560",
        "Arduino Nano",
        "Arduino Leonardo",
        "Arduino Due",
        "Arduino Micro",
        "Custom Board"
    ]

    # Board-spezifische Pin-Konfigurationen
    BOARD_PIN_CONFIGS = {
        "Arduino Uno": {
            "digital_pins": ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13"],
            "analog_pins": ["A0", "A1", "A2", "A3", "A4", "A5"],
            "pwm_pins": ["D3", "D5", "D6", "D9", "D10", "D11"],
            "i2c_pins": {"SDA": "A4", "SCL": "A5"}
        },
        "Arduino Mega 2560": {
            "digital_pins": [f"D{i}" for i in range(54)],
            "analog_pins": [f"A{i}" for i in range(16)],
            "pwm_pins": ["D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12", "D13"],
            "i2c_pins": {"SDA": "D20", "SCL": "D21"}
        },
        "Arduino Nano": {
            "digital_pins": [f"D{i}" for i in range(14)],
            "analog_pins": [f"A{i}" for i in range(8)],
            "pwm_pins": ["D3", "D5", "D6", "D9", "D10", "D11"],
            "i2c_pins": {"SDA": "A4", "SCL": "A5"}
        }
    }

    def __init__(self, profiles_file: str = "hardware_profiles.json"):
        self.profiles_file = profiles_file
        self.profiles: Dict[str, HardwareProfile] = {}
        self.load_profiles()

    def load_profiles(self) -> bool:
        """Lädt Profile aus Datei"""
        if not os.path.exists(self.profiles_file):
            print(f"Keine Profile-Datei gefunden: {self.profiles_file}")
            self._create_default_profiles()
            return True

        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.profiles = {}
            for profile_id, profile_data in data.items():
                self.profiles[profile_id] = HardwareProfile.from_dict(profile_data)

            print(f"✅ {len(self.profiles)} Profile geladen")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Laden der Profile: {e}")
            return False

    def save_profiles(self) -> bool:
        """Speichert Profile in Datei"""
        try:
            data = {}
            for profile_id, profile in self.profiles.items():
                data[profile_id] = profile.to_dict()

            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✅ {len(self.profiles)} Profile gespeichert")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Speichern der Profile: {e}")
            return False

    def _create_default_profiles(self):
        """Erstellt Standard-Profile"""
        # Standard Arduino Uno Profil
        default_uno = HardwareProfile(
            profile_id="default_uno",
            name="Standard Arduino Uno",
            board_type="Arduino Uno",
            description="Standard-Konfiguration für Arduino Uno",
            pin_config={
                "D13": "OUTPUT",  # LED_BUILTIN
                "D2": "INPUT",
                "D3": "INPUT",
                "A0": "ANALOG_INPUT",
                "A1": "ANALOG_INPUT"
            },
            sensor_config={},
            custom_settings={
                "baud_rate": 115200,
                "timeout": 1.0
            }
        )

        self.profiles["default_uno"] = default_uno
        self.save_profiles()

    def add_profile(self, profile: HardwareProfile) -> bool:
        """Fügt neues Profil hinzu"""
        if profile.profile_id in self.profiles:
            print(f"❌ Profil mit ID '{profile.profile_id}' existiert bereits")
            return False

        self.profiles[profile.profile_id] = profile
        return self.save_profiles()

    def update_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        pin_config: Optional[Dict[str, str]] = None,
        sensor_config: Optional[Dict[str, Any]] = None,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Aktualisiert bestehendes Profil"""
        if profile_id not in self.profiles:
            print(f"❌ Profil '{profile_id}' nicht gefunden")
            return False

        self.profiles[profile_id].update(
            name=name,
            description=description,
            pin_config=pin_config,
            sensor_config=sensor_config,
            custom_settings=custom_settings
        )

        return self.save_profiles()

    def delete_profile(self, profile_id: str) -> bool:
        """Löscht Profil"""
        if profile_id not in self.profiles:
            print(f"❌ Profil '{profile_id}' nicht gefunden")
            return False

        del self.profiles[profile_id]
        return self.save_profiles()

    def get_profile(self, profile_id: str) -> Optional[HardwareProfile]:
        """Gibt Profil zurück"""
        return self.profiles.get(profile_id)

    def get_all_profiles(self) -> List[HardwareProfile]:
        """Gibt alle Profile zurück"""
        return list(self.profiles.values())

    def export_profile(self, profile_id: str, file_path: str) -> bool:
        """Exportiert Profil in Datei"""
        profile = self.get_profile(profile_id)
        if not profile:
            print(f"❌ Profil '{profile_id}' nicht gefunden")
            return False

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

            print(f"✅ Profil '{profile.name}' exportiert nach: {file_path}")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Exportieren: {e}")
            return False

    def import_profile(self, file_path: str) -> Optional[str]:
        """
        Importiert Profil aus Datei

        Returns:
            Profile-ID wenn erfolgreich, sonst None
        """
        if not os.path.exists(file_path):
            print(f"❌ Datei nicht gefunden: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            profile = HardwareProfile.from_dict(data)

            # Prüfe ob ID bereits existiert
            if profile.profile_id in self.profiles:
                # Generiere neue ID
                base_id = profile.profile_id
                counter = 1
                while f"{base_id}_{counter}" in self.profiles:
                    counter += 1
                profile.profile_id = f"{base_id}_{counter}"
                print(f"ℹ️ Profil-ID wurde geändert zu: {profile.profile_id}")

            self.profiles[profile.profile_id] = profile
            self.save_profiles()

            print(f"✅ Profil '{profile.name}' importiert mit ID: {profile.profile_id}")
            return profile.profile_id

        except Exception as e:
            print(f"❌ Fehler beim Importieren: {e}")
            return None

    def clone_profile(self, profile_id: str, new_name: str) -> Optional[str]:
        """
        Klont ein bestehendes Profil

        Returns:
            Neue Profile-ID wenn erfolgreich, sonst None
        """
        source_profile = self.get_profile(profile_id)
        if not source_profile:
            print(f"❌ Quell-Profil '{profile_id}' nicht gefunden")
            return None

        # Generiere neue ID
        new_id = f"clone_{profile_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        new_profile = HardwareProfile(
            profile_id=new_id,
            name=new_name,
            board_type=source_profile.board_type,
            description=f"Klon von '{source_profile.name}'",
            pin_config=source_profile.pin_config.copy(),
            sensor_config=source_profile.sensor_config.copy(),
            custom_settings=source_profile.custom_settings.copy()
        )

        if self.add_profile(new_profile):
            print(f"✅ Profil geklont: {new_name} (ID: {new_id})")
            return new_id

        return None

    @staticmethod
    def detect_connected_boards() -> List[Dict[str, str]]:
        """
        Erkennt verbundene Arduino-Boards automatisch

        Returns:
            Liste von erkannten Boards mit Port und Beschreibung
        """
        detected_boards = []

        ports = serial.tools.list_ports.comports()

        for port in ports:
            # Prüfe auf Arduino-typische Vendor IDs
            if port.vid is not None:
                board_info = {
                    'port': port.device,
                    'description': port.description,
                    'hwid': port.hwid,
                    'vid': port.vid,
                    'pid': port.pid
                }

                # Versuche Board-Typ zu identifizieren
                desc_lower = port.description.lower()

                if 'arduino' in desc_lower or port.vid in [0x2341, 0x2A03]:  # Arduino Vendor IDs
                    if 'mega' in desc_lower:
                        board_info['board_type'] = 'Arduino Mega 2560'
                    elif 'nano' in desc_lower:
                        board_info['board_type'] = 'Arduino Nano'
                    elif 'leonardo' in desc_lower:
                        board_info['board_type'] = 'Arduino Leonardo'
                    elif 'uno' in desc_lower:
                        board_info['board_type'] = 'Arduino Uno'
                    else:
                        board_info['board_type'] = 'Arduino (Unbekannt)'

                    detected_boards.append(board_info)

        return detected_boards

    def create_profile_from_board(
        self,
        board_info: Dict[str, str],
        profile_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Erstellt automatisch ein Profil aus erkanntem Board

        Args:
            board_info: Board-Info von detect_connected_boards()
            profile_name: Optional - Name für das Profil

        Returns:
            Profile-ID wenn erfolgreich, sonst None
        """
        board_type = board_info.get('board_type', 'Custom Board')

        if profile_name is None:
            profile_name = f"{board_type} ({board_info['port']})"

        # Generiere ID
        profile_id = f"auto_{board_info['port'].replace('/', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Hole Standard-Pin-Konfiguration für Board-Typ
        pin_config = {}
        if board_type in self.BOARD_PIN_CONFIGS:
            # Setze alle Pins auf Standard (INPUT für digital, ANALOG_INPUT für analog)
            board_pins = self.BOARD_PIN_CONFIGS[board_type]
            for pin in board_pins.get('digital_pins', []):
                pin_config[pin] = "INPUT"
            for pin in board_pins.get('analog_pins', []):
                pin_config[pin] = "ANALOG_INPUT"

        new_profile = HardwareProfile(
            profile_id=profile_id,
            name=profile_name,
            board_type=board_type,
            description=f"Automatisch erkannt: {board_info['description']}",
            pin_config=pin_config,
            sensor_config={},
            custom_settings={
                'port': board_info['port'],
                'vid': board_info.get('vid'),
                'pid': board_info.get('pid'),
                'baud_rate': 115200
            }
        )

        if self.add_profile(new_profile):
            print(f"✅ Profil automatisch erstellt: {profile_name}")
            return profile_id

        return None

    def get_board_capabilities(self, board_type: str) -> Dict[str, Any]:
        """
        Gibt Board-Capabilities zurück

        Args:
            board_type: Board-Typ

        Returns:
            Dict mit Board-Capabilities
        """
        if board_type not in self.BOARD_PIN_CONFIGS:
            return {}

        config = self.BOARD_PIN_CONFIGS[board_type]

        return {
            'board_type': board_type,
            'digital_pin_count': len(config.get('digital_pins', [])),
            'analog_pin_count': len(config.get('analog_pins', [])),
            'pwm_pin_count': len(config.get('pwm_pins', [])),
            'has_i2c': bool(config.get('i2c_pins')),
            'has_spi': True,  # Die meisten Arduinos haben SPI
            'pins': config
        }
