# -*- coding: utf-8 -*-
"""
plugins/plugin_manager.py
Plugin-Manager für das Arduino Control Panel

Verwaltet Laden, Initialisieren und Ausführen von Plugins.
"""
import os
import sys
import json
import importlib.util
import logging
from typing import Dict, List, Optional, Type
from pathlib import Path

from plugins.plugin_api import (
    PluginInterface, PluginMetadata, PluginType,
    PluginPriority, ApplicationContext, PluginHook
)

logger = logging.getLogger("PluginManager")


class PluginManager:
    """
    Verwaltet alle Plugins der Anwendung.

    Verantwortlichkeiten:
    - Plugins aus Verzeichnissen laden
    - Abhängigkeiten prüfen
    - Plugins initialisieren/deaktivieren
    - Events an Plugins weiterleiten
    - Sicherheit und Sandboxing
    """

    def __init__(self, app_context: ApplicationContext, plugin_dirs: List[str] = None):
        """
        Initialisiert den Plugin-Manager.

        Args:
            app_context: Anwendungskontext
            plugin_dirs: Liste der Plugin-Verzeichnisse
        """
        self.app_context = app_context
        self.plugin_dirs = plugin_dirs or [
            "plugins/installed",
            "plugins/user"
        ]

        # Plugin-Registry
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.enabled_plugins: List[str] = []
        self.disabled_plugins: List[str] = []

        # Konfiguration
        self.config_file = "plugins/plugin_config.json"
        self.load_config()

    def load_config(self):
        """Lädt die Plugin-Konfiguration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.enabled_plugins = config.get('enabled', [])
                    self.disabled_plugins = config.get('disabled', [])
                    logger.info(f"Plugin-Konfiguration geladen: {len(self.enabled_plugins)} aktiviert")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Plugin-Konfiguration: {e}")

    def save_config(self):
        """Speichert die Plugin-Konfiguration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config = {
                'enabled': self.enabled_plugins,
                'disabled': self.disabled_plugins
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Plugin-Konfiguration gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Plugin-Konfiguration: {e}")

    def discover_plugins(self) -> List[str]:
        """
        Entdeckt verfügbare Plugins in den Plugin-Verzeichnissen.

        Returns:
            List[str]: Liste der gefundenen Plugin-Pfade
        """
        discovered = []

        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"Plugin-Verzeichnis nicht gefunden: {plugin_dir}")
                continue

            logger.info(f"Suche Plugins in: {plugin_dir}")

            # Durchsuche Verzeichnis nach Python-Modulen
            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)

                # Python-Datei
                if item.endswith('.py') and not item.startswith('__'):
                    discovered.append(item_path)
                    logger.info(f"  Gefunden: {item}")

                # Verzeichnis mit __init__.py
                elif os.path.isdir(item_path):
                    init_file = os.path.join(item_path, '__init__.py')
                    if os.path.exists(init_file):
                        discovered.append(init_file)
                        logger.info(f"  Gefunden: {item}/")

        logger.info(f"Insgesamt {len(discovered)} Plugins entdeckt")
        return discovered

    def load_plugin(self, plugin_path: str) -> Optional[PluginInterface]:
        """
        Lädt ein einzelnes Plugin aus einem Pfad.

        Args:
            plugin_path: Pfad zur Plugin-Datei

        Returns:
            Optional[PluginInterface]: Plugin-Instanz oder None bei Fehler
        """
        try:
            # Modul-Name generieren
            module_name = Path(plugin_path).stem
            if module_name == '__init__':
                module_name = Path(plugin_path).parent.name

            logger.info(f"Lade Plugin: {module_name}")

            # Modul laden
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Konnte Modul-Spec nicht erstellen: {plugin_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Plugin-Klasse finden
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                        issubclass(attr, PluginInterface) and
                        attr is not PluginInterface):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.error(f"Keine Plugin-Klasse gefunden in: {plugin_path}")
                return None

            # Plugin instantiieren
            plugin = plugin_class()
            metadata = plugin.get_metadata()

            logger.info(f"Plugin geladen: {metadata.name} v{metadata.version}")
            return plugin

        except Exception as e:
            logger.error(f"Fehler beim Laden des Plugins {plugin_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def register_plugin(self, plugin: PluginInterface) -> bool:
        """
        Registriert ein Plugin.

        Args:
            plugin: Plugin-Instanz

        Returns:
            bool: True bei Erfolg
        """
        try:
            metadata = plugin.get_metadata()

            # Prüfe, ob bereits registriert
            if metadata.id in self.plugins:
                logger.warning(f"Plugin bereits registriert: {metadata.id}")
                return False

            # Registriere
            self.plugins[metadata.id] = plugin
            self.plugin_metadata[metadata.id] = metadata

            logger.info(f"Plugin registriert: {metadata.name} ({metadata.id})")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Registrieren des Plugins: {e}")
            return False

    def initialize_plugin(self, plugin_id: str) -> bool:
        """
        Initialisiert ein Plugin.

        Args:
            plugin_id: Plugin-ID

        Returns:
            bool: True bei Erfolg
        """
        if plugin_id not in self.plugins:
            logger.error(f"Plugin nicht gefunden: {plugin_id}")
            return False

        try:
            plugin = self.plugins[plugin_id]
            metadata = self.plugin_metadata[plugin_id]

            logger.info(f"Initialisiere Plugin: {metadata.name}")

            # Prüfe Abhängigkeiten
            if not self._check_dependencies(plugin_id):
                logger.error(f"Abhängigkeiten nicht erfüllt für: {plugin_id}")
                return False

            # Initialisiere
            if plugin.initialize(self.app_context):
                plugin.enable()
                if plugin_id not in self.enabled_plugins:
                    self.enabled_plugins.append(plugin_id)
                if plugin_id in self.disabled_plugins:
                    self.disabled_plugins.remove(plugin_id)
                logger.info(f"Plugin initialisiert: {metadata.name}")
                return True
            else:
                logger.error(f"Plugin-Initialisierung fehlgeschlagen: {metadata.name}")
                return False

        except Exception as e:
            logger.error(f"Fehler beim Initialisieren des Plugins {plugin_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def shutdown_plugin(self, plugin_id: str) -> bool:
        """
        Fährt ein Plugin herunter.

        Args:
            plugin_id: Plugin-ID

        Returns:
            bool: True bei Erfolg
        """
        if plugin_id not in self.plugins:
            return False

        try:
            plugin = self.plugins[plugin_id]
            metadata = self.plugin_metadata[plugin_id]

            logger.info(f"Fahre Plugin herunter: {metadata.name}")

            plugin.disable()
            result = plugin.shutdown()

            if plugin_id in self.enabled_plugins:
                self.enabled_plugins.remove(plugin_id)
            if plugin_id not in self.disabled_plugins:
                self.disabled_plugins.append(plugin_id)

            logger.info(f"Plugin heruntergefahren: {metadata.name}")
            return result

        except Exception as e:
            logger.error(f"Fehler beim Herunterfahren des Plugins {plugin_id}: {e}")
            return False

    def load_all_plugins(self):
        """Lädt und initialisiert alle verfügbaren Plugins"""
        logger.info("Lade alle Plugins...")

        # Entdecke Plugins
        plugin_paths = self.discover_plugins()

        # Lade Plugins
        loaded_plugins = []
        for path in plugin_paths:
            plugin = self.load_plugin(path)
            if plugin:
                if self.register_plugin(plugin):
                    loaded_plugins.append(plugin)

        # Sortiere nach Priorität
        loaded_plugins.sort(
            key=lambda p: p.get_metadata().priority.value
        )

        # Initialisiere Plugins in Prioritäts-Reihenfolge
        for plugin in loaded_plugins:
            metadata = plugin.get_metadata()

            # Prüfe, ob in enabled_plugins oder nicht in disabled
            should_enable = (
                    metadata.id in self.enabled_plugins or
                    (metadata.id not in self.disabled_plugins and
                     metadata.priority in [PluginPriority.CRITICAL, PluginPriority.HIGH])
            )

            if should_enable:
                self.initialize_plugin(metadata.id)

        self.save_config()
        logger.info(f"Plugin-Laden abgeschlossen: {len(self.enabled_plugins)} aktiv")

    def shutdown_all_plugins(self):
        """Fährt alle Plugins herunter"""
        logger.info("Fahre alle Plugins herunter...")

        for plugin_id in list(self.enabled_plugins):
            self.shutdown_plugin(plugin_id)

        self.save_config()
        logger.info("Alle Plugins heruntergefahren")

    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """
        Holt ein Plugin anhand der ID.

        Args:
            plugin_id: Plugin-ID

        Returns:
            Optional[PluginInterface]: Plugin oder None
        """
        return self.plugins.get(plugin_id)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """
        Holt alle Plugins eines bestimmten Typs.

        Args:
            plugin_type: Plugin-Typ

        Returns:
            List[PluginInterface]: Liste der Plugins
        """
        result = []
        for plugin_id, metadata in self.plugin_metadata.items():
            if metadata.plugin_type == plugin_type and plugin_id in self.enabled_plugins:
                result.append(self.plugins[plugin_id])
        return result

    def trigger_hook(self, hook_name: str, *args, **kwargs):
        """
        Triggert einen Plugin-Hook und benachrichtigt alle registrierten Plugins.

        Args:
            hook_name: Hook-Name (z.B. PluginHook.SEQUENCE_START)
            *args: Positionsargumente
            **kwargs: Keyword-Argumente
        """
        self.app_context.trigger_event(hook_name, *args, **kwargs)

    def _check_dependencies(self, plugin_id: str) -> bool:
        """
        Prüft, ob alle Abhängigkeiten eines Plugins erfüllt sind.

        Args:
            plugin_id: Plugin-ID

        Returns:
            bool: True wenn alle Abhängigkeiten erfüllt
        """
        metadata = self.plugin_metadata.get(plugin_id)
        if not metadata or not metadata.dependencies:
            return True

        for dep_id in metadata.dependencies:
            if dep_id not in self.plugins:
                logger.error(f"Abhängigkeit nicht gefunden: {dep_id} für {plugin_id}")
                return False
            if dep_id not in self.enabled_plugins:
                logger.error(f"Abhängigkeit nicht aktiviert: {dep_id} für {plugin_id}")
                return False

        return True

    def get_plugin_info(self) -> List[Dict]:
        """
        Gibt Informationen über alle Plugins zurück.

        Returns:
            List[Dict]: Plugin-Informationen
        """
        info = []
        for plugin_id, metadata in self.plugin_metadata.items():
            plugin = self.plugins[plugin_id]
            info.append({
                'id': metadata.id,
                'name': metadata.name,
                'version': metadata.version,
                'author': metadata.author,
                'description': metadata.description,
                'type': metadata.plugin_type.value,
                'enabled': plugin.is_enabled(),
                'capabilities': [cap.value for cap in plugin.get_capabilities()]
            })
        return info
