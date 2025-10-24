# -*- coding: utf-8 -*-
"""
Pin Usage Tracker - Verfolgt die Nutzung aller Arduino Pins
"""

import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple
import json


class PinUsageTracker:
    """Verfolgt Pin-Nutzung für Analyse und Visualisierung"""

    def __init__(self):
        # Pin-Nutzungs-Zähler
        self.pin_counts = defaultdict(int)

        # Zeitstempel für jeden Pin-Zugriff
        self.pin_timestamps = defaultdict(list)

        # Letzte Pin-States
        self.pin_states = {}

        # Gesamte Nutzungszeit pro Pin (in Sekunden)
        self.pin_active_time = defaultdict(float)

        # Letzte Aktivierungs-Zeit pro Pin
        self.pin_last_active = {}

        # Session-Start
        self.session_start = time.time()

        # Pin-Typen (digital/analog)
        self.pin_types = {}

        # Fehler-Zähler pro Pin
        self.pin_errors = defaultdict(int)

    def track_pin_access(self, pin_name: str, pin_type: str = "digital", state: any = None):
        """
        Verfolgt einen Pin-Zugriff

        Args:
            pin_name: Name des Pins (z.B. "D13", "A0")
            pin_type: Typ des Pins ("digital" oder "analog")
            state: Aktueller State (HIGH/LOW für digital, Wert für analog)
        """
        current_time = time.time()

        # Zähle Zugriff
        self.pin_counts[pin_name] += 1

        # Speichere Timestamp
        self.pin_timestamps[pin_name].append(current_time)

        # Speichere Pin-Typ
        self.pin_types[pin_name] = pin_type

        # Update State
        old_state = self.pin_states.get(pin_name)
        self.pin_states[pin_name] = state

        # Für digitale Pins: Verfolge Active-Time (HIGH)
        if pin_type == "digital":
            if old_state == "HIGH" and state == "LOW":
                # Pin wurde deaktiviert
                if pin_name in self.pin_last_active:
                    duration = current_time - self.pin_last_active[pin_name]
                    self.pin_active_time[pin_name] += duration
                    del self.pin_last_active[pin_name]
            elif state == "HIGH" and old_state != "HIGH":
                # Pin wurde aktiviert
                self.pin_last_active[pin_name] = current_time

    def track_pin_error(self, pin_name: str):
        """Verfolgt Fehler auf einem Pin"""
        self.pin_errors[pin_name] += 1

    def get_pin_usage_summary(self) -> Dict:
        """
        Gibt eine Zusammenfassung der Pin-Nutzung zurück

        Returns:
            Dict mit Pin-Statistiken
        """
        summary = {}
        current_time = time.time()
        session_duration = current_time - self.session_start

        for pin_name in set(list(self.pin_counts.keys()) + list(self.pin_types.keys())):
            # Berechne aktuelle Active-Time (falls Pin noch HIGH)
            active_time = self.pin_active_time[pin_name]
            if pin_name in self.pin_last_active:
                active_time += (current_time - self.pin_last_active[pin_name])

            # Berechne Nutzungsrate
            access_count = self.pin_counts[pin_name]
            usage_rate = (access_count / session_duration * 60) if session_duration > 0 else 0

            # Letzte Nutzung
            last_used = None
            if pin_name in self.pin_timestamps and self.pin_timestamps[pin_name]:
                last_used = self.pin_timestamps[pin_name][-1]

            summary[pin_name] = {
                'access_count': access_count,
                'pin_type': self.pin_types.get(pin_name, 'unknown'),
                'current_state': self.pin_states.get(pin_name),
                'active_time_seconds': active_time,
                'active_time_percent': (active_time / session_duration * 100) if session_duration > 0 else 0,
                'usage_rate_per_minute': usage_rate,
                'last_used_timestamp': last_used,
                'last_used_ago': (current_time - last_used) if last_used else None,
                'error_count': self.pin_errors[pin_name],
                'timestamps': self.pin_timestamps[pin_name][-10:]  # Letzte 10 Zugriffe
            }

        return summary

    def get_heatmap_data(self) -> Dict[str, float]:
        """
        Gibt normalisierte Heatmap-Daten zurück (0.0 - 1.0)

        Returns:
            Dict mit Pin-Name -> Intensität (0.0 = ungenutzt, 1.0 = maximale Nutzung)
        """
        summary = self.get_pin_usage_summary()

        if not summary:
            return {}

        # Finde maximale Access-Count für Normalisierung
        max_count = max(data['access_count'] for data in summary.values()) if summary else 1

        # Normalisiere Werte
        heatmap = {}
        for pin_name, data in summary.items():
            # Verwende Access-Count als Basis
            intensity = data['access_count'] / max_count if max_count > 0 else 0

            # Boost für aktuell aktive Pins
            if data['current_state'] == "HIGH":
                intensity = min(1.0, intensity * 1.2)

            # Reduzierung für lange nicht genutzte Pins
            if data['last_used_ago'] and data['last_used_ago'] > 60:  # > 1 Minute
                intensity *= 0.8

            heatmap[pin_name] = intensity

        return heatmap

    def get_all_pins(self, board_type: str = "Arduino Uno") -> List[str]:
        """
        Gibt alle verfügbaren Pins für einen Board-Typ zurück

        Args:
            board_type: Typ des Arduino-Boards

        Returns:
            Liste aller Pin-Namen
        """
        # Arduino Uno Standard-Pins
        if "Uno" in board_type or "Nano" in board_type:
            digital_pins = [f"D{i}" for i in range(14)]
            analog_pins = [f"A{i}" for i in range(6)]
        # Arduino Mega
        elif "Mega" in board_type:
            digital_pins = [f"D{i}" for i in range(54)]
            analog_pins = [f"A{i}" for i in range(16)]
        # ESP32
        elif "ESP32" in board_type:
            digital_pins = [f"D{i}" for i in [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]]
            analog_pins = [f"A{i}" for i in range(8)]
        # Default: Arduino Uno
        else:
            digital_pins = [f"D{i}" for i in range(14)]
            analog_pins = [f"A{i}" for i in range(6)]

        return digital_pins + analog_pins

    def get_unused_pins(self, board_type: str = "Arduino Uno") -> List[str]:
        """
        Gibt alle ungenutzten Pins zurück

        Args:
            board_type: Typ des Arduino-Boards

        Returns:
            Liste aller ungenutzten Pin-Namen
        """
        all_pins = set(self.get_all_pins(board_type))
        used_pins = set(self.pin_counts.keys())
        return sorted(list(all_pins - used_pins))

    def reset(self):
        """Setzt alle Statistiken zurück"""
        self.pin_counts.clear()
        self.pin_timestamps.clear()
        self.pin_states.clear()
        self.pin_active_time.clear()
        self.pin_last_active.clear()
        self.pin_types.clear()
        self.pin_errors.clear()
        self.session_start = time.time()

    def export_to_json(self, filepath: str):
        """Exportiert Statistiken zu JSON"""
        summary = self.get_pin_usage_summary()

        export_data = {
            'session_start': datetime.fromtimestamp(self.session_start).isoformat(),
            'session_duration_seconds': time.time() - self.session_start,
            'pins': summary,
            'total_accesses': sum(self.pin_counts.values()),
            'total_errors': sum(self.pin_errors.values())
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def import_from_json(self, filepath: str):
        """Importiert Statistiken aus JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Rekonstruiere Daten
        for pin_name, pin_data in data.get('pins', {}).items():
            self.pin_counts[pin_name] = pin_data.get('access_count', 0)
            self.pin_types[pin_name] = pin_data.get('pin_type', 'unknown')
            self.pin_states[pin_name] = pin_data.get('current_state')
            self.pin_active_time[pin_name] = pin_data.get('active_time_seconds', 0)
            self.pin_errors[pin_name] = pin_data.get('error_count', 0)


# Singleton-Instanz
_tracker_instance = None

def get_pin_tracker() -> PinUsageTracker:
    """Gibt die globale Pin-Tracker-Instanz zurück"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PinUsageTracker()
    return _tracker_instance
