# -*- coding: utf-8 -*-
"""
Scheduler Tab - UI für zeitgesteuerte Tests und Trigger-System
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QDialog,
                             QFormLayout, QLineEdit, QComboBox, QSpinBox,
                             QCheckBox, QTimeEdit, QGroupBox, QTabWidget,
                             QTextEdit, QMessageBox, QDateTimeEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QTime, QDateTime
from datetime import datetime, timedelta
from core.logging_config import get_logger

logger = get_logger(__name__)


class SchedulerTab(QWidget):
    """Tab für Scheduling & Automation."""

    # Signale
    task_triggered = pyqtSignal(str)  # sequence_id
    trigger_activated = pyqtSignal(str)  # sequence_id oder command

    def __init__(self, scheduler_manager, trigger_system, sequences):
        super().__init__()
        self.scheduler_manager = scheduler_manager
        self.trigger_system = trigger_system
        self.sequences = sequences

        self.init_ui()
        self.connect_signals()
        self.refresh_lists()

    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)

        # Tabs für Scheduler und Trigger
        self.tabs = QTabWidget()

        # === SCHEDULER TAB ===
        scheduler_widget = QWidget()
        scheduler_layout = QVBoxLayout(scheduler_widget)

        # Header
        header = QLabel("⏰ Zeitgesteuerte Tests")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        scheduler_layout.addWidget(header)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add_task = QPushButton("➕ Neue Aufgabe")
        self.btn_add_task.clicked.connect(self.add_task_dialog)
        btn_layout.addWidget(self.btn_add_task)

        self.btn_edit_task = QPushButton("✏️ Bearbeiten")
        self.btn_edit_task.clicked.connect(self.edit_task_dialog)
        btn_layout.addWidget(self.btn_edit_task)

        self.btn_delete_task = QPushButton("🗑️ Löschen")
        self.btn_delete_task.clicked.connect(self.delete_task)
        btn_layout.addWidget(self.btn_delete_task)

        btn_layout.addStretch()
        scheduler_layout.addLayout(btn_layout)

        # Task List
        self.task_list = QListWidget()
        self.task_list.setAlternatingRowColors(True)
        scheduler_layout.addWidget(self.task_list)

        # Upcoming Tasks Info
        upcoming_group = QGroupBox("📅 Nächste Ausführungen")
        upcoming_layout = QVBoxLayout(upcoming_group)
        self.upcoming_text = QTextEdit()
        self.upcoming_text.setReadOnly(True)
        self.upcoming_text.setMaximumHeight(120)
        upcoming_layout.addWidget(self.upcoming_text)
        scheduler_layout.addWidget(upcoming_group)

        self.tabs.addTab(scheduler_widget, "⏰ Zeitsteuerung")

        # === TRIGGER TAB ===
        trigger_widget = QWidget()
        trigger_layout = QVBoxLayout(trigger_widget)

        # Header
        header2 = QLabel("🎯 Trigger-System")
        header2.setStyleSheet("font-size: 16px; font-weight: bold;")
        trigger_layout.addWidget(header2)

        # Buttons
        btn_layout2 = QHBoxLayout()
        self.btn_add_trigger = QPushButton("➕ Neuer Trigger")
        self.btn_add_trigger.clicked.connect(self.add_trigger_dialog)
        btn_layout2.addWidget(self.btn_add_trigger)

        self.btn_edit_trigger = QPushButton("✏️ Bearbeiten")
        self.btn_edit_trigger.clicked.connect(self.edit_trigger_dialog)
        btn_layout2.addWidget(self.btn_edit_trigger)

        self.btn_delete_trigger = QPushButton("🗑️ Löschen")
        self.btn_delete_trigger.clicked.connect(self.delete_trigger)
        btn_layout2.addWidget(self.btn_delete_trigger)

        btn_layout2.addStretch()
        trigger_layout.addLayout(btn_layout2)

        # Trigger List
        self.trigger_list = QListWidget()
        self.trigger_list.setAlternatingRowColors(True)
        trigger_layout.addWidget(self.trigger_list)

        # Trigger Stats
        stats_group = QGroupBox("📊 Statistiken")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        stats_layout.addWidget(self.stats_text)
        trigger_layout.addWidget(stats_group)

        self.tabs.addTab(trigger_widget, "🎯 Trigger")

        layout.addWidget(self.tabs)

        logger.info("SchedulerTab UI initialisiert")

    def connect_signals(self):
        """Verbindet Signale."""
        self.scheduler_manager.task_triggered.connect(self.on_task_triggered)
        self.scheduler_manager.task_list_changed.connect(self.refresh_task_list)

        self.trigger_system.trigger_activated.connect(self.on_trigger_activated)
        self.trigger_system.trigger_list_changed.connect(self.refresh_trigger_list)

    def add_task_dialog(self):
        """Dialog zum Hinzufügen einer neuen Aufgabe."""
        dialog = TaskDialog(self, self.sequences)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.scheduler_manager.add_task(**task_data)
            QMessageBox.information(self, "Erfolg", f"Aufgabe '{task_data['name']}' erstellt!")

    def edit_task_dialog(self):
        """Dialog zum Bearbeiten einer Aufgabe."""
        if not self.task_list.currentItem():
            QMessageBox.warning(self, "Fehler", "Bitte wähle eine Aufgabe aus!")
            return

        task_id = self.task_list.currentItem().data(Qt.ItemDataRole.UserRole)
        task = self.scheduler_manager.get_task(task_id)

        dialog = TaskDialog(self, self.sequences, task)
        if dialog.exec():
            task_data = dialog.get_task_data()
            del task_data['sequence_id']  # Kann nicht geändert werden
            self.scheduler_manager.update_task(task_id, **task_data)
            QMessageBox.information(self, "Erfolg", "Aufgabe aktualisiert!")

    def delete_task(self):
        """Löscht eine Aufgabe."""
        if not self.task_list.currentItem():
            QMessageBox.warning(self, "Fehler", "Bitte wähle eine Aufgabe aus!")
            return

        task_id = self.task_list.currentItem().data(Qt.ItemDataRole.UserRole)
        task = self.scheduler_manager.get_task(task_id)

        reply = QMessageBox.question(self, "Löschen",
                                     f"Aufgabe '{task.name}' wirklich löschen?")
        if reply == QMessageBox.StandardButton.Yes:
            self.scheduler_manager.delete_task(task_id)
            QMessageBox.information(self, "Erfolg", "Aufgabe gelöscht!")

    def add_trigger_dialog(self):
        """Dialog zum Hinzufügen eines Triggers."""
        dialog = TriggerDialog(self, self.sequences, self.trigger_system)
        if dialog.exec():
            trigger_data = dialog.get_trigger_data()
            self.trigger_system.add_trigger(**trigger_data)
            QMessageBox.information(self, "Erfolg", f"Trigger '{trigger_data['name']}' erstellt!")

    def edit_trigger_dialog(self):
        """Dialog zum Bearbeiten eines Triggers."""
        if not self.trigger_list.currentItem():
            QMessageBox.warning(self, "Fehler", "Bitte wähle einen Trigger aus!")
            return

        trigger_id = self.trigger_list.currentItem().data(Qt.ItemDataRole.UserRole)
        trigger = self.trigger_system.get_trigger(trigger_id)

        dialog = TriggerDialog(self, self.sequences, self.trigger_system, trigger)
        if dialog.exec():
            trigger_data = dialog.get_trigger_data()
            self.trigger_system.update_trigger(trigger_id, **trigger_data)
            QMessageBox.information(self, "Erfolg", "Trigger aktualisiert!")

    def delete_trigger(self):
        """Löscht einen Trigger."""
        if not self.trigger_list.currentItem():
            QMessageBox.warning(self, "Fehler", "Bitte wähle einen Trigger aus!")
            return

        trigger_id = self.trigger_list.currentItem().data(Qt.ItemDataRole.UserRole)
        trigger = self.trigger_system.get_trigger(trigger_id)

        reply = QMessageBox.question(self, "Löschen",
                                     f"Trigger '{trigger.name}' wirklich löschen?")
        if reply == QMessageBox.StandardButton.Yes:
            self.trigger_system.delete_trigger(trigger_id)
            QMessageBox.information(self, "Erfolg", "Trigger gelöscht!")

    def refresh_lists(self):
        """Aktualisiert beide Listen."""
        self.refresh_task_list()
        self.refresh_trigger_list()

    def refresh_task_list(self):
        """Aktualisiert die Aufgaben-Liste."""
        self.task_list.clear()

        for task in self.scheduler_manager.get_all_tasks():
            status = "✅" if task.enabled else "❌"
            next_run = task.next_run.strftime("%d.%m. %H:%M") if task.next_run else "---"
            item_text = f"{status} {task.name} | Typ: {task.schedule_type} | Nächste: {next_run}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, task.task_id)
            self.task_list.addItem(item)

        # Update upcoming tasks
        upcoming = self.scheduler_manager.get_upcoming_tasks(5)
        upcoming_text = "<b>Nächste 5 Aufgaben:</b><br>"
        for task in upcoming:
            next_run_str = task.next_run.strftime("%d.%m.%Y %H:%M:%S")
            upcoming_text += f"• {task.name}: {next_run_str}<br>"

        if not upcoming:
            upcoming_text += "<i>Keine geplanten Aufgaben</i>"

        self.upcoming_text.setHtml(upcoming_text)

    def refresh_trigger_list(self):
        """Aktualisiert die Trigger-Liste."""
        self.trigger_list.clear()

        for trigger in self.trigger_system.get_all_triggers():
            status = "✅" if trigger.enabled else "❌"
            item_text = (f"{status} {trigger.name} | "
                        f"{trigger.condition_type} → {trigger.action_type} | "
                        f"Ausgeführt: {trigger.trigger_count}x")

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, trigger.trigger_id)
            self.trigger_list.addItem(item)

        # Update stats
        total_triggers = len(self.trigger_system.get_all_triggers())
        enabled = sum(1 for t in self.trigger_system.get_all_triggers() if t.enabled)
        total_activations = sum(t.trigger_count for t in self.trigger_system.get_all_triggers())

        stats_text = f"<b>Trigger-Statistiken:</b><br>"
        stats_text += f"• Gesamt: {total_triggers}<br>"
        stats_text += f"• Aktiv: {enabled}<br>"
        stats_text += f"• Gesamtausführungen: {total_activations}"

        self.stats_text.setHtml(stats_text)

    def on_task_triggered(self, task_id, sequence_id):
        """Wird aufgerufen, wenn eine Aufgabe ausgelöst wird."""
        logger.info(f"Task triggered: {task_id}, starting sequence {sequence_id}")
        self.task_triggered.emit(sequence_id)

    def on_trigger_activated(self, trigger_id, action_config):
        """Wird aufgerufen, wenn ein Trigger aktiviert wird."""
        trigger = self.trigger_system.get_trigger(trigger_id)
        logger.info(f"Trigger activated: {trigger.name}")

        if trigger.action_type == 'run_sequence':
            sequence_id = action_config.get('sequence_id')
            self.trigger_activated.emit(sequence_id)


class TaskDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten einer Aufgabe."""

    def __init__(self, parent, sequences, task=None):
        super().__init__(parent)
        self.sequences = sequences
        self.task = task
        self.init_ui()

    def init_ui(self):
        """Initialisiert die UI."""
        self.setWindowTitle("Aufgabe erstellen/bearbeiten")
        self.setMinimumWidth(500)

        layout = QFormLayout(self)

        # Name
        self.name_edit = QLineEdit()
        if self.task:
            self.name_edit.setText(self.task.name)
        layout.addRow("Name:", self.name_edit)

        # Sequenz auswählen
        self.sequence_combo = QComboBox()
        for seq_id, seq in self.sequences.items():
            self.sequence_combo.addItem(seq['name'], seq_id)
        if self.task:
            index = self.sequence_combo.findData(self.task.sequence_id)
            if index >= 0:
                self.sequence_combo.setCurrentIndex(index)
        layout.addRow("Sequenz:", self.sequence_combo)

        # Schedule Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(['daily', 'weekly', 'interval', 'once'])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        if self.task:
            index = self.type_combo.findText(self.task.schedule_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        layout.addRow("Typ:", self.type_combo)

        # Config widgets (dynamisch)
        self.config_widget = QWidget()
        self.config_layout = QFormLayout(self.config_widget)
        layout.addRow("Konfiguration:", self.config_widget)

        # Enabled
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(True if not self.task else self.task.enabled)
        layout.addRow("Aktiv:", self.enabled_check)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addRow("", btn_layout)

        # Initial config
        self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, schedule_type):
        """Aktualisiert die Config-Widgets basierend auf dem Typ."""
        # Clear existing
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if schedule_type == 'daily':
            self.time_edit = QTimeEdit()
            self.time_edit.setTime(QTime(9, 0))
            self.config_layout.addRow("Uhrzeit:", self.time_edit)

        elif schedule_type == 'interval':
            self.interval_spin = QSpinBox()
            self.interval_spin.setRange(1, 1440)
            self.interval_spin.setValue(60)
            self.interval_spin.setSuffix(" Minuten")
            self.config_layout.addRow("Intervall:", self.interval_spin)

        elif schedule_type == 'once':
            self.datetime_edit = QDateTimeEdit()
            self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
            self.config_layout.addRow("Datum/Zeit:", self.datetime_edit)

    def get_task_data(self):
        """Gibt die Aufgaben-Daten zurück."""
        schedule_type = self.type_combo.currentText()
        schedule_config = {}

        if schedule_type == 'daily':
            schedule_config['time'] = self.time_edit.time().toString("HH:mm")
        elif schedule_type == 'interval':
            schedule_config['interval_minutes'] = self.interval_spin.value()
        elif schedule_type == 'once':
            schedule_config['datetime'] = self.datetime_edit.dateTime().toPyDateTime().isoformat()

        return {
            'name': self.name_edit.text(),
            'sequence_id': self.sequence_combo.currentData(),
            'schedule_type': schedule_type,
            'schedule_config': schedule_config,
            'enabled': self.enabled_check.isChecked()
        }


class TriggerDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten eines Triggers."""

    def __init__(self, parent, sequences, trigger_system, trigger=None):
        super().__init__(parent)
        self.sequences = sequences
        self.trigger_system = trigger_system
        self.trigger = trigger
        self.init_ui()

    def init_ui(self):
        """Initialisiert die UI."""
        self.setWindowTitle("Trigger erstellen/bearbeiten")
        self.setMinimumWidth(500)

        layout = QFormLayout(self)

        # Name
        self.name_edit = QLineEdit()
        if self.trigger:
            self.name_edit.setText(self.trigger.name)
        layout.addRow("Name:", self.name_edit)

        # Condition Type
        self.condition_type_combo = QComboBox()
        self.condition_type_combo.addItems(self.trigger_system.get_condition_types())
        layout.addRow("Bedingung:", self.condition_type_combo)

        # Condition Config (vereinfacht)
        self.condition_value_edit = QLineEdit()
        self.condition_value_edit.setPlaceholderText("z.B. Sensor-ID oder Pin-Name")
        layout.addRow("Bedingungswert:", self.condition_value_edit)

        # Action Type
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(self.trigger_system.get_action_types())
        layout.addRow("Aktion:", self.action_type_combo)

        # Action Config (Sequenz auswählen)
        self.action_sequence_combo = QComboBox()
        for seq_id, seq in self.sequences.items():
            self.action_sequence_combo.addItem(seq['name'], seq_id)
        layout.addRow("Sequenz:", self.action_sequence_combo)

        # Enabled
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(True if not self.trigger else self.trigger.enabled)
        layout.addRow("Aktiv:", self.enabled_check)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addRow("", btn_layout)

    def get_trigger_data(self):
        """Gibt die Trigger-Daten zurück."""
        # Vereinfachte Version
        condition_config = {
            'sensor_id': self.condition_value_edit.text(),
            'threshold': 30.0,
            'operator': '>'
        }

        action_config = {
            'sequence_id': self.action_sequence_combo.currentData()
        }

        return {
            'name': self.name_edit.text(),
            'condition_type': self.condition_type_combo.currentText(),
            'condition_config': condition_config,
            'action_type': self.action_type_combo.currentText(),
            'action_config': action_config,
            'enabled': self.enabled_check.isChecked()
        }
