# -*- coding: utf-8 -*-
"""
plugins/plugin_api.py
Plugin API Definition für das Arduino Control Panel

Diese Datei definiert die Plugin-Schnittstelle und das Plugin-System.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger("PluginAPI")


class PluginType(Enum):
    """Plugin-Typen"""
    SENSOR = "sensor"              # Neuer Sensor-Typ
    EXPORT = "export"              # Export-Format (PDF, CSV, etc.)
    ANALYSIS = "analysis"          # Datenanalyse
    VISUALIZATION = "visualization" # Visualisierung
    HARDWARE = "hardware"          # Hardware-Integration
    AUTOMATION = "automation"      # Automatisierung
    UI = "ui"                      # UI-Erweiterung
    GENERAL = "general"            # Allgemein


class PluginPriority(Enum):
    """Plugin-Priorität für Lade-Reihenfolge"""
    CRITICAL = 0   # Muss zuerst geladen werden
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class PluginMetadata:
    """Plugin-Metadaten"""
    id: str                        # Eindeutige Plugin-ID (z.B. "com.example.my_plugin")
    name: str                      # Anzeigename
    version: str                   # Version (z.B. "1.0.0")
    author: str                    # Autor
    description: str               # Beschreibung
    plugin_type: PluginType        # Plugin-Typ
    priority: PluginPriority = PluginPriority.NORMAL
    dependencies: List[str] = None # Andere benötigte Plugins (IDs)
    min_app_version: str = "1.0.0" # Minimale App-Version
    website: str = ""              # Website/Repository
    license: str = "MIT"           # Lizenz

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginCapability(Enum):
    """Plugin-Fähigkeiten (was kann das Plugin)"""
    # Daten-Operationen
    READ_SENSOR_DATA = "read_sensor_data"
    WRITE_SENSOR_DATA = "write_sensor_data"
    PROCESS_DATA = "process_data"
    EXPORT_DATA = "export_data"

    # Hardware
    HARDWARE_CONTROL = "hardware_control"
    SERIAL_COMMUNICATION = "serial_communication"

    # UI
    ADD_MENU = "add_menu"
    ADD_TAB = "add_tab"
    ADD_WIDGET = "add_widget"
    ADD_TOOLBAR = "add_toolbar"

    # System
    BACKGROUND_TASK = "background_task"
    DATABASE_ACCESS = "database_access"
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"


class PluginInterface(ABC):
    """
    Basis-Interface für alle Plugins.

    Jedes Plugin muss diese Klasse erweitern und die abstrakten Methoden implementieren.
    """

    def __init__(self):
        self._enabled = False
        self._app_context = None
        self._config = {}

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Gibt die Plugin-Metadaten zurück.

        Returns:
            PluginMetadata: Metadaten des Plugins
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[PluginCapability]:
        """
        Gibt die Fähigkeiten des Plugins zurück.

        Returns:
            List[PluginCapability]: Liste der Fähigkeiten
        """
        pass

    @abstractmethod
    def initialize(self, app_context: 'ApplicationContext') -> bool:
        """
        Initialisiert das Plugin.

        Args:
            app_context: Anwendungskontext mit Zugriff auf App-Funktionen

        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        Fährt das Plugin herunter und gibt Ressourcen frei.

        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        pass

    def enable(self) -> bool:
        """
        Aktiviert das Plugin.

        Returns:
            bool: True bei Erfolg
        """
        self._enabled = True
        logger.info(f"Plugin {self.get_metadata().name} aktiviert")
        return True

    def disable(self) -> bool:
        """
        Deaktiviert das Plugin.

        Returns:
            bool: True bei Erfolg
        """
        self._enabled = False
        logger.info(f"Plugin {self.get_metadata().name} deaktiviert")
        return True

    def is_enabled(self) -> bool:
        """Prüft, ob das Plugin aktiviert ist"""
        return self._enabled

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Konfigurationswert.

        Args:
            key: Konfigurations-Schlüssel
            default: Standardwert falls nicht vorhanden

        Returns:
            Any: Konfigurationswert
        """
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any):
        """
        Setzt einen Konfigurationswert.

        Args:
            key: Konfigurations-Schlüssel
            value: Wert
        """
        self._config[key] = value

    def get_settings_widget(self) -> Optional[Any]:
        """
        Gibt ein QWidget für Plugin-Einstellungen zurück (optional).

        Returns:
            Optional[QWidget]: Einstellungs-Widget oder None
        """
        return None


class ApplicationContext:
    """
    Anwendungskontext, der Plugins Zugriff auf App-Funktionen gibt.

    Dies ist eine sichere Schnittstelle, die verhindert, dass Plugins
    direkten Zugriff auf die gesamte Anwendung haben.
    """

    def __init__(self, main_window, db, config_manager):
        self._main_window = main_window
        self._db = db
        self._config_manager = config_manager
        self._registered_callbacks = {}

    def get_database(self):
        """Gibt Zugriff auf die Datenbank"""
        return self._db

    def get_config_manager(self):
        """Gibt Zugriff auf den Konfigurations-Manager"""
        return self._config_manager

    def add_menu_item(self, menu_name: str, item_name: str, callback: Callable):
        """
        Fügt ein Menü-Item hinzu.

        Args:
            menu_name: Name des Menüs
            item_name: Name des Items
            callback: Callback-Funktion
        """
        # Implementation wird später in main.py hinzugefügt
        pass

    def add_tab(self, tab_name: str, widget: Any):
        """
        Fügt einen Tab hinzu.

        Args:
            tab_name: Name des Tabs
            widget: QWidget für den Tab
        """
        # Implementation wird später in main.py hinzugefügt
        pass

    def register_callback(self, event_name: str, callback: Callable):
        """
        Registriert einen Event-Callback.

        Args:
            event_name: Event-Name (z.B. "sequence_start", "data_received")
            callback: Callback-Funktion
        """
        if event_name not in self._registered_callbacks:
            self._registered_callbacks[event_name] = []
        self._registered_callbacks[event_name].append(callback)

    def trigger_event(self, event_name: str, *args, **kwargs):
        """
        Triggert ein Event und ruft alle registrierten Callbacks auf.

        Args:
            event_name: Event-Name
            *args: Positionsargumente
            **kwargs: Keyword-Argumente
        """
        if event_name in self._registered_callbacks:
            for callback in self._registered_callbacks[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in plugin callback for {event_name}: {e}")

    def get_sensor_data(self, sensor_id: str) -> Optional[Dict]:
        """
        Holt Sensordaten.

        Args:
            sensor_id: Sensor-ID

        Returns:
            Optional[Dict]: Sensordaten oder None
        """
        # Implementation später
        pass

    def send_command(self, command: str, params: Dict = None) -> bool:
        """
        Sendet einen Befehl an das Arduino.

        Args:
            command: Befehl
            params: Parameter

        Returns:
            bool: True bei Erfolg
        """
        # Implementation später
        pass


class PluginHook:
    """Definiert verfügbare Plugin-Hooks (Event-Punkte)"""

    # Anwendungs-Lifecycle
    APP_STARTUP = "app_startup"
    APP_SHUTDOWN = "app_shutdown"

    # Sequenz-Events
    SEQUENCE_START = "sequence_start"
    SEQUENCE_END = "sequence_end"
    SEQUENCE_STEP = "sequence_step"

    # Daten-Events
    DATA_RECEIVED = "data_received"
    DATA_PROCESSED = "data_processed"
    DATA_SAVED = "data_saved"

    # UI-Events
    TAB_CHANGED = "tab_changed"
    WIDGET_CREATED = "widget_created"

    # Hardware-Events
    ARDUINO_CONNECTED = "arduino_connected"
    ARDUINO_DISCONNECTED = "arduino_disconnected"
    PIN_CHANGED = "pin_changed"


# Für Typ-Hints
__all__ = [
    'PluginInterface',
    'PluginMetadata',
    'PluginType',
    'PluginPriority',
    'PluginCapability',
    'ApplicationContext',
    'PluginHook'
]
