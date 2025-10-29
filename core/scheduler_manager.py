# -*- coding: utf-8 -*-
"""
Scheduler Manager - Zeitgesteuerte Tests und Automation
Ermöglicht zeitgesteuerte Ausführung von Sequenzen und Trigger-basierte Automation.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from core.logging_config import get_logger

logger = get_logger(__name__)


class ScheduledTask:
    """Repräsentiert eine geplante Aufgabe."""

    def __init__(self, task_id: str, name: str, sequence_id: str,
                 schedule_type: str, schedule_config: dict, enabled: bool = True):
        """
        Args:
            task_id: Eindeutige ID der Aufgabe
            name: Name der Aufgabe
            sequence_id: ID der auszuführenden Sequenz
            schedule_type: Typ: 'once', 'daily', 'weekly', 'interval', 'cron'
            schedule_config: Konfiguration für den Schedule
            enabled: Ob die Aufgabe aktiv ist
        """
        self.task_id = task_id
        self.name = name
        self.sequence_id = sequence_id
        self.schedule_type = schedule_type
        self.schedule_config = schedule_config
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.success_count = 0
        self.error_count = 0

    def to_dict(self) -> dict:
        """Konvertiert die Aufgabe zu einem Dictionary."""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'sequence_id': self.sequence_id,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'success_count': self.success_count,
            'error_count': self.error_count
        }

    @staticmethod
    def from_dict(data: dict) -> 'ScheduledTask':
        """Erstellt eine Aufgabe aus einem Dictionary."""
        task = ScheduledTask(
            task_id=data['task_id'],
            name=data['name'],
            sequence_id=data['sequence_id'],
            schedule_type=data['schedule_type'],
            schedule_config=data['schedule_config'],
            enabled=data.get('enabled', True)
        )
        if data.get('last_run'):
            task.last_run = datetime.fromisoformat(data['last_run'])
        if data.get('next_run'):
            task.next_run = datetime.fromisoformat(data['next_run'])
        task.run_count = data.get('run_count', 0)
        task.success_count = data.get('success_count', 0)
        task.error_count = data.get('error_count', 0)
        return task

    def calculate_next_run(self) -> Optional[datetime]:
        """Berechnet die nächste Ausführungszeit."""
        now = datetime.now()

        if self.schedule_type == 'once':
            # Einmalige Ausführung
            target_time = datetime.fromisoformat(self.schedule_config['datetime'])
            if target_time > now:
                return target_time
            return None

        elif self.schedule_type == 'daily':
            # Täglich zu bestimmter Uhrzeit
            time_str = self.schedule_config['time']  # Format: "HH:MM"
            hour, minute = map(int, time_str.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif self.schedule_type == 'weekly':
            # Wöchentlich an bestimmten Tagen
            weekdays = self.schedule_config['weekdays']  # Liste von 0-6 (Mo-So)
            time_str = self.schedule_config['time']
            hour, minute = map(int, time_str.split(':'))

            # Finde nächsten passenden Wochentag
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            for days_ahead in range(8):  # Max 7 Tage voraus
                candidate = now + timedelta(days=days_ahead)
                candidate = candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if candidate.weekday() in weekdays and candidate > now:
                    return candidate
            return None

        elif self.schedule_type == 'interval':
            # Regelmäßiges Intervall
            interval_minutes = self.schedule_config['interval_minutes']
            if self.last_run:
                return self.last_run + timedelta(minutes=interval_minutes)
            else:
                return now + timedelta(minutes=interval_minutes)

        elif self.schedule_type == 'cron':
            # Cron-ähnliche Expression (vereinfacht)
            # Format: "minute hour day_of_month month day_of_week"
            # Für diese Version: Nur Stunden und Minuten
            cron_expr = self.schedule_config['cron']
            parts = cron_expr.split()
            if len(parts) >= 2:
                minute = parts[0]
                hour = parts[1]

                if minute == '*':
                    minute = 0
                else:
                    minute = int(minute)

                if hour == '*':
                    # Jede Stunde
                    next_run = now.replace(minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(hours=1)
                    return next_run
                else:
                    hour = int(hour)
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    return next_run

        return None


class SchedulerManager(QObject):
    """
    Manager für zeitgesteuerte Aufgaben.
    Überwacht geplante Aufgaben und führt sie zur richtigen Zeit aus.
    """

    # Signale
    task_triggered = pyqtSignal(str, str)  # task_id, sequence_id
    task_completed = pyqtSignal(str, bool, str)  # task_id, success, message
    task_list_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tasks: Dict[str, ScheduledTask] = {}

        # Timer für regelmäßige Überprüfung (alle 10 Sekunden)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_scheduled_tasks)
        self.check_timer.start(10000)  # 10 Sekunden

        logger.info("SchedulerManager initialisiert")

    def add_task(self, name: str, sequence_id: str, schedule_type: str,
                 schedule_config: dict, enabled: bool = True) -> str:
        """Fügt eine neue geplante Aufgabe hinzu."""
        task_id = str(uuid.uuid4())
        task = ScheduledTask(task_id, name, sequence_id, schedule_type,
                           schedule_config, enabled)
        task.next_run = task.calculate_next_run()

        self.tasks[task_id] = task
        self.task_list_changed.emit()

        logger.info(f"Aufgabe erstellt: {name} ({schedule_type}), nächste Ausführung: {task.next_run}")
        return task_id

    def update_task(self, task_id: str, **kwargs) -> bool:
        """Aktualisiert eine bestehende Aufgabe."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        # Neu berechnen wenn Schedule geändert
        if 'schedule_type' in kwargs or 'schedule_config' in kwargs:
            task.next_run = task.calculate_next_run()

        self.task_list_changed.emit()
        logger.info(f"Aufgabe aktualisiert: {task_id}")
        return True

    def delete_task(self, task_id: str) -> bool:
        """Löscht eine geplante Aufgabe."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.task_list_changed.emit()
            logger.info(f"Aufgabe gelöscht: {task_id}")
            return True
        return False

    def enable_task(self, task_id: str, enabled: bool) -> bool:
        """Aktiviert oder deaktiviert eine Aufgabe."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = enabled
            if enabled:
                self.tasks[task_id].next_run = self.tasks[task_id].calculate_next_run()
            self.task_list_changed.emit()
            logger.info(f"Aufgabe {'aktiviert' if enabled else 'deaktiviert'}: {task_id}")
            return True
        return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Gibt eine Aufgabe zurück."""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[ScheduledTask]:
        """Gibt alle Aufgaben zurück."""
        return list(self.tasks.values())

    def _check_scheduled_tasks(self):
        """Überprüft, ob Aufgaben ausgeführt werden müssen."""
        now = datetime.now()

        for task in self.tasks.values():
            if not task.enabled:
                continue

            if task.next_run and task.next_run <= now:
                logger.info(f"Führe geplante Aufgabe aus: {task.name}")

                # Trigger Signal
                self.task_triggered.emit(task.task_id, task.sequence_id)

                # Update Task
                task.last_run = now
                task.run_count += 1
                task.next_run = task.calculate_next_run()

                self.task_list_changed.emit()

    def mark_task_completed(self, task_id: str, success: bool, message: str = ""):
        """Markiert eine Aufgabe als abgeschlossen."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if success:
                task.success_count += 1
            else:
                task.error_count += 1

            self.task_completed.emit(task_id, success, message)
            logger.info(f"Aufgabe abgeschlossen: {task.name}, Erfolg: {success}")

    def save_tasks(self, file_path: str):
        """Speichert alle Aufgaben in eine JSON-Datei."""
        tasks_data = [task.to_dict() for task in self.tasks.values()]
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Aufgaben gespeichert: {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Aufgaben: {e}")

    def load_tasks(self, file_path: str):
        """Lädt Aufgaben aus einer JSON-Datei."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)

            self.tasks.clear()
            for task_data in tasks_data:
                task = ScheduledTask.from_dict(task_data)
                # Neu berechnen für Zukunft
                task.next_run = task.calculate_next_run()
                self.tasks[task.task_id] = task

            self.task_list_changed.emit()
            logger.info(f"Aufgaben geladen: {len(self.tasks)} Aufgaben aus {file_path}")
        except FileNotFoundError:
            logger.info(f"Keine gespeicherten Aufgaben gefunden: {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Aufgaben: {e}")

    def get_upcoming_tasks(self, limit: int = 10) -> List[ScheduledTask]:
        """Gibt die nächsten geplanten Aufgaben zurück."""
        enabled_tasks = [t for t in self.tasks.values() if t.enabled and t.next_run]
        enabled_tasks.sort(key=lambda t: t.next_run)
        return enabled_tasks[:limit]

    def stop(self):
        """Stoppt den Scheduler."""
        self.check_timer.stop()
        logger.info("SchedulerManager gestoppt")
