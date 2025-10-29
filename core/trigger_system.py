# -*- coding: utf-8 -*-
"""
Trigger System - Ereignisbasierte Automation
Führt Aktionen basierend auf Sensor-Werten, Pin-Zuständen oder anderen Events aus.
"""

import uuid
import json
from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal
from core.logging_config import get_logger

logger = get_logger(__name__)


class Trigger:
    """Repräsentiert einen Trigger (Bedingung + Aktion)."""

    def __init__(self, trigger_id: str, name: str, condition_type: str,
                 condition_config: dict, action_type: str, action_config: dict,
                 enabled: bool = True):
        """
        Args:
            trigger_id: Eindeutige ID
            name: Name des Triggers
            condition_type: Typ der Bedingung: 'sensor_value', 'pin_state', 'time', 'sequence_event'
            condition_config: Konfiguration der Bedingung
            action_type: Typ der Aktion: 'run_sequence', 'send_command', 'send_notification', 'email'
            action_config: Konfiguration der Aktion
            enabled: Ob der Trigger aktiv ist
        """
        self.trigger_id = trigger_id
        self.name = name
        self.condition_type = condition_type
        self.condition_config = condition_config
        self.action_type = action_type
        self.action_config = action_config
        self.enabled = enabled
        self.trigger_count = 0
        self.last_triggered = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            'trigger_id': self.trigger_id,
            'name': self.name,
            'condition_type': self.condition_type,
            'condition_config': self.condition_config,
            'action_type': self.action_type,
            'action_config': self.action_config,
            'enabled': self.enabled,
            'trigger_count': self.trigger_count,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'Trigger':
        """Erstellt Trigger aus Dictionary."""
        from datetime import datetime
        trigger = Trigger(
            trigger_id=data['trigger_id'],
            name=data['name'],
            condition_type=data['condition_type'],
            condition_config=data['condition_config'],
            action_type=data['action_type'],
            action_config=data['action_config'],
            enabled=data.get('enabled', True)
        )
        trigger.trigger_count = data.get('trigger_count', 0)
        if data.get('last_triggered'):
            trigger.last_triggered = datetime.fromisoformat(data['last_triggered'])
        return trigger

    def check_condition(self, event_data: dict) -> bool:
        """Prüft, ob die Bedingung erfüllt ist."""
        event_type = event_data.get('type')

        if self.condition_type == 'sensor_value':
            # Beispiel: Temperatur > 30°C
            if event_type == 'sensor_update':
                sensor_id = self.condition_config.get('sensor_id')
                operator = self.condition_config.get('operator')  # '>', '<', '==', '!=', '>=', '<='
                threshold = self.condition_config.get('threshold')

                if event_data.get('sensor') == sensor_id:
                    value = event_data.get('value')
                    if value is not None:
                        return self._compare_values(value, operator, threshold)

        elif self.condition_type == 'pin_state':
            # Beispiel: Pin D13 == HIGH
            if event_type == 'pin_update':
                pin_name = self.condition_config.get('pin_name')
                expected_state = self.condition_config.get('state')  # 0 oder 1

                if event_data.get('pin_name') == pin_name:
                    actual_state = event_data.get('value')
                    return actual_state == expected_state

        elif self.condition_type == 'sequence_event':
            # Beispiel: Sequenz abgeschlossen
            if event_type == 'sequence_event':
                event_name = self.condition_config.get('event_name')  # 'started', 'completed', 'failed'
                return event_data.get('event') == event_name

        return False

    def _compare_values(self, value: float, operator: str, threshold: float) -> bool:
        """Vergleicht zwei Werte mit dem angegebenen Operator."""
        if operator == '>':
            return value > threshold
        elif operator == '<':
            return value < threshold
        elif operator == '==':
            return value == threshold
        elif operator == '!=':
            return value != threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<=':
            return value <= threshold
        return False


class TriggerSystem(QObject):
    """
    System zur ereignisbasierten Automation.
    Überwacht Events und führt Trigger-Aktionen aus.
    """

    # Signale
    trigger_activated = pyqtSignal(str, dict)  # trigger_id, action_config
    trigger_list_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.triggers: Dict[str, Trigger] = {}
        logger.info("TriggerSystem initialisiert")

    def add_trigger(self, name: str, condition_type: str, condition_config: dict,
                   action_type: str, action_config: dict, enabled: bool = True) -> str:
        """Fügt einen neuen Trigger hinzu."""
        trigger_id = str(uuid.uuid4())
        trigger = Trigger(trigger_id, name, condition_type, condition_config,
                         action_type, action_config, enabled)

        self.triggers[trigger_id] = trigger
        self.trigger_list_changed.emit()

        logger.info(f"Trigger erstellt: {name} ({condition_type} -> {action_type})")
        return trigger_id

    def update_trigger(self, trigger_id: str, **kwargs) -> bool:
        """Aktualisiert einen Trigger."""
        if trigger_id not in self.triggers:
            return False

        trigger = self.triggers[trigger_id]
        for key, value in kwargs.items():
            if hasattr(trigger, key):
                setattr(trigger, key, value)

        self.trigger_list_changed.emit()
        logger.info(f"Trigger aktualisiert: {trigger_id}")
        return True

    def delete_trigger(self, trigger_id: str) -> bool:
        """Löscht einen Trigger."""
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            self.trigger_list_changed.emit()
            logger.info(f"Trigger gelöscht: {trigger_id}")
            return True
        return False

    def enable_trigger(self, trigger_id: str, enabled: bool) -> bool:
        """Aktiviert oder deaktiviert einen Trigger."""
        if trigger_id in self.triggers:
            self.triggers[trigger_id].enabled = enabled
            self.trigger_list_changed.emit()
            logger.info(f"Trigger {'aktiviert' if enabled else 'deaktiviert'}: {trigger_id}")
            return True
        return False

    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        """Gibt einen Trigger zurück."""
        return self.triggers.get(trigger_id)

    def get_all_triggers(self) -> List[Trigger]:
        """Gibt alle Trigger zurück."""
        return list(self.triggers.values())

    def process_event(self, event_data: dict):
        """
        Verarbeitet ein Event und prüft alle Trigger.

        Args:
            event_data: Event-Daten mit 'type' und weiteren Feldern
        """
        from datetime import datetime

        for trigger in self.triggers.values():
            if not trigger.enabled:
                continue

            # Prüfe Bedingung
            if trigger.check_condition(event_data):
                logger.info(f"Trigger aktiviert: {trigger.name}")

                # Update Statistiken
                trigger.trigger_count += 1
                trigger.last_triggered = datetime.now()

                # Führe Aktion aus
                self._execute_action(trigger)

                # Signal emittieren
                self.trigger_activated.emit(trigger.trigger_id, trigger.action_config)

    def _execute_action(self, trigger: Trigger):
        """Führt die Aktion eines Triggers aus."""
        action_type = trigger.action_type
        action_config = trigger.action_config

        if action_type == 'run_sequence':
            # Sequenz starten (wird über Signal gehandelt)
            logger.info(f"Trigger-Aktion: Starte Sequenz {action_config.get('sequence_id')}")

        elif action_type == 'send_command':
            # Befehl senden (wird über Signal gehandelt)
            logger.info(f"Trigger-Aktion: Sende Befehl {action_config.get('command')}")

        elif action_type == 'send_notification':
            # Benachrichtigung (könnte später erweitert werden)
            message = action_config.get('message', 'Trigger aktiviert')
            logger.info(f"Trigger-Aktion: Benachrichtigung '{message}'")

        elif action_type == 'email':
            # Email senden (könnte später implementiert werden)
            logger.info(f"Trigger-Aktion: Email an {action_config.get('recipient')}")

    def save_triggers(self, file_path: str):
        """Speichert alle Trigger in eine JSON-Datei."""
        triggers_data = [trigger.to_dict() for trigger in self.triggers.values()]
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(triggers_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Trigger gespeichert: {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Trigger: {e}")

    def load_triggers(self, file_path: str):
        """Lädt Trigger aus einer JSON-Datei."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                triggers_data = json.load(f)

            self.triggers.clear()
            for trigger_data in triggers_data:
                trigger = Trigger.from_dict(trigger_data)
                self.triggers[trigger.trigger_id] = trigger

            self.trigger_list_changed.emit()
            logger.info(f"Trigger geladen: {len(self.triggers)} Trigger aus {file_path}")
        except FileNotFoundError:
            logger.info(f"Keine gespeicherten Trigger gefunden: {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Trigger: {e}")

    def get_condition_types(self) -> List[str]:
        """Gibt verfügbare Bedingungstypen zurück."""
        return ['sensor_value', 'pin_state', 'sequence_event']

    def get_action_types(self) -> List[str]:
        """Gibt verfügbare Aktionstypen zurück."""
        return ['run_sequence', 'send_command', 'send_notification', 'email']

    def get_operators(self) -> List[str]:
        """Gibt verfügbare Vergleichsoperatoren zurück."""
        return ['>', '<', '==', '!=', '>=', '<=']
