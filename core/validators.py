# -*- coding: utf-8 -*-
"""
Input-Validatoren für Arduino Control Panel.
Zentrale Validierungslogik für Pins, Sensoren und Konfigurationen.
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("ArduinoPanel.Validators")


class PinValidator:
    """Validator für Arduino-Pin-Konfigurationen."""

    # Gültige Pin-Namen
    DIGITAL_PINS = [f"D{i}" for i in range(14)]
    ANALOG_PINS = [f"A{i}" for i in range(6)]
    ALL_PINS = DIGITAL_PINS + ANALOG_PINS

    # Gültige Pin-Modi
    VALID_MODES = ["INPUT", "OUTPUT", "INPUT_PULLUP"]

    @classmethod
    def validate_pin_name(cls, pin_name: Any) -> Optional[str]:
        """
        Validiert einen Pin-Namen.

        Args:
            pin_name: Zu validierender Pin-Name

        Returns:
            Pin-Name als String wenn gültig, sonst None
        """
        if not isinstance(pin_name, str):
            logger.warning(f"Pin-Name ist kein String: {type(pin_name)}")
            return None

        if pin_name not in cls.ALL_PINS:
            logger.warning(f"Ungültiger Pin-Name: {pin_name}")
            return None

        return pin_name

    @classmethod
    def validate_pin_mode(cls, mode: Any, default: str = "INPUT") -> str:
        """
        Validiert einen Pin-Modus.

        Args:
            mode: Zu validierender Modus
            default: Fallback-Modus bei ungültigem Input

        Returns:
            Validierter Modus (oder default)
        """
        if not isinstance(mode, str):
            logger.warning(f"Pin-Modus ist kein String: {type(mode)}, verwende {default}")
            return default

        if mode not in cls.VALID_MODES:
            logger.warning(f"Ungültiger Pin-Modus: {mode}, verwende {default}")
            return default

        return mode

    @classmethod
    def validate_pin_configs(cls, pin_configs: Any) -> Dict[str, str]:
        """
        Validiert ein Dict von Pin-Konfigurationen.

        Args:
            pin_configs: Dict mit {pin_name: mode}

        Returns:
            Validiertes Dict (ungültige Einträge werden entfernt)
        """
        if not isinstance(pin_configs, dict):
            logger.error(f"pin_configs ist kein Dict: {type(pin_configs)}")
            return {}

        validated = {}
        for pin_name, mode in pin_configs.items():
            valid_pin = cls.validate_pin_name(pin_name)
            if valid_pin is None:
                continue

            valid_mode = cls.validate_pin_mode(mode)
            validated[valid_pin] = valid_mode

        return validated


class SensorValidator:
    """Validator für Sensor-Konfigurationen."""

    REQUIRED_FIELDS = ['sensor_type', 'pin_config']

    @classmethod
    def validate_sensor_config(cls, sensor_id: str, config: Any) -> Optional[Dict[str, Any]]:
        """
        Validiert eine einzelne Sensor-Konfiguration.

        Args:
            sensor_id: Sensor-ID (für Logging)
            config: Zu validierende Konfiguration

        Returns:
            Validierte Config oder None bei Fehler
        """
        if not isinstance(config, dict):
            logger.warning(f"Sensor {sensor_id} Config ist kein Dict: {type(config)}")
            return None

        # Prüfe erforderliche Felder
        for field in cls.REQUIRED_FIELDS:
            if field not in config:
                logger.warning(f"Sensor {sensor_id} fehlt erforderliches Feld: {field}")
                return None

        return config

    @classmethod
    def validate_sensor_configs(cls, sensor_configs: Any) -> Dict[str, Dict[str, Any]]:
        """
        Validiert ein Dict von Sensor-Konfigurationen.

        Args:
            sensor_configs: Dict mit {sensor_id: config}

        Returns:
            Validiertes Dict (ungültige Einträge werden entfernt)
        """
        if not isinstance(sensor_configs, dict):
            logger.error(f"sensor_configs ist kein Dict: {type(sensor_configs)}")
            return {}

        validated = {}
        for sensor_id, config in sensor_configs.items():
            valid_config = cls.validate_sensor_config(sensor_id, config)
            if valid_config is not None:
                validated[sensor_id] = valid_config

        return validated


class ConfigValidator:
    """Validator für Gesamt-Konfigurationen."""

    @classmethod
    def validate_config_data(cls, config_data: Any) -> Dict[str, Any]:
        """
        Validiert ein komplettes Config-Data Dict.

        Args:
            config_data: Zu validierende Konfiguration

        Returns:
            Validierte Konfiguration mit bereinigten Daten
        """
        if not isinstance(config_data, dict):
            logger.error(f"config_data ist kein Dict: {type(config_data)}")
            return {}

        validated = {}

        # Validiere Pin-Funktionen
        pin_functions = config_data.get('pin_functions', {})
        validated['pin_functions'] = PinValidator.validate_pin_configs(pin_functions)

        # Validiere Sensor-Konfigurationen
        active_sensors = config_data.get('active_sensors', {})
        validated['active_sensors'] = SensorValidator.validate_sensor_configs(active_sensors)

        # Kopiere andere Felder unverändert
        for key, value in config_data.items():
            if key not in ['pin_functions', 'active_sensors']:
                validated[key] = value

        return validated
