# -*- coding: utf-8 -*-
"""
Erweiterter Daten-Logger mit CSV-Export und Trigger-Funktionen
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QCheckBox, QSpinBox, QComboBox, QFileDialog, QMessageBox,
                             QSplitter, QTextEdit, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QColor
import csv
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class LogEntry:
    """Ein einzelner Log-Eintrag"""
    timestamp: float
    pin_name: str
    value: Any
    event_type: str  # "change", "threshold", "periodic"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "datetime": QDateTime.fromMSecsSinceEpoch(int(self.timestamp * 1000)).toString("yyyy-MM-dd hh:mm:ss.zzz"),
            "pin": self.pin_name,
            "value": self.value,
            "type": self.event_type,
            **self.metadata
        }


class TriggerCondition:
    """Trigger-Bedingung für automatisches Logging"""
    def __init__(self, pin: str, operator: str, threshold: float):
        self.pin = pin
        self.operator = operator  # ">", "<", "==", "!=", "change"
        self.threshold = threshold
        self.last_value = None
    
    def check(self, pin: str, value: float) -> bool:
        """Prüft, ob die Trigger-Bedingung erfüllt ist"""
        if pin != self.pin:
            return False
        
        if self.operator == "change":
            triggered = self.last_value is not None and self.last_value != value
            self.last_value = value
            return triggered
        elif self.operator == ">":
            return value > self.threshold
        elif self.operator == "<":
            return value < self.threshold
        elif self.operator == "==":
            return value == self.threshold
        elif self.operator == "!=":
            return value != self.threshold
        
        return False


class DataLoggerWidget(QWidget):
    """Erweiterter Datenlogger mit Trigger-Funktionen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_entries: deque = deque(maxlen=10000)  # Letzte 10.000 Einträge
        self.triggers: List[TriggerCondition] = []
        self.recording = False
        self.start_time = time.time()
        
        self.watched_pins = set()
        self.pin_states = {}
        
        self.setup_ui()
        
        # Auto-Update Timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)  # 2x pro Sekunde
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Splitter für oberen und unteren Bereich
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # === OBERER BEREICH: Steuerung ===
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Status und Hauptsteuerung
        status_layout = QHBoxLayout()
        
        self.status_indicator = QLabel("⏸️")
        self.status_indicator.setStyleSheet("font-size: 32px;")
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(self.status_label, 1)
        
        self.start_btn = QPushButton("🔴 Aufzeichnung starten")
        self.start_btn.clicked.connect(self.toggle_recording)
        status_layout.addWidget(self.start_btn)
        
        self.clear_btn = QPushButton("🗑️ Löschen")
        self.clear_btn.clicked.connect(self.clear_log)
        status_layout.addWidget(self.clear_btn)
        
        control_layout.addLayout(status_layout)
        
        # Statistiken
        stats_group = QGroupBox("📊 Statistiken")
        stats_layout = QHBoxLayout(stats_group)
        
        self.entry_count_label = QLabel("Einträge: 0")
        self.duration_label = QLabel("Dauer: 00:00")
        self.rate_label = QLabel("Rate: 0 Hz")
        self.size_label = QLabel("Größe: 0 KB")
        
        for label in [self.entry_count_label, self.duration_label, self.rate_label, self.size_label]:
            label.setStyleSheet("padding: 5px;")
            stats_layout.addWidget(label)
        
        control_layout.addWidget(stats_group)
        
        # Pin-Auswahl und Trigger
        config_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Pin-Auswahl
        pin_group = QGroupBox("📌 Überwachte Pins")
        pin_layout = QVBoxLayout(pin_group)
        
        pin_btn_layout = QHBoxLayout()
        self.pin_combo = QComboBox()
        self.pin_combo.addItems([f"D{i}" for i in range(14)] + [f"A{i}" for i in range(6)])
        pin_btn_layout.addWidget(self.pin_combo)
        
        add_pin_btn = QPushButton("➕")
        add_pin_btn.clicked.connect(self.add_watched_pin)
        pin_btn_layout.addWidget(add_pin_btn)
        pin_layout.addLayout(pin_btn_layout)
        
        self.watched_pins_list = QTextEdit()
        self.watched_pins_list.setReadOnly(True)
        self.watched_pins_list.setMaximumHeight(100)
        pin_layout.addWidget(self.watched_pins_list)
        
        config_splitter.addWidget(pin_group)
        
        # Trigger-Konfiguration
        trigger_group = QGroupBox("⚡ Trigger-Bedingungen")
        trigger_layout = QVBoxLayout(trigger_group)
        
        trigger_config_layout = QHBoxLayout()
        
        self.trigger_pin_combo = QComboBox()
        self.trigger_pin_combo.addItems([f"D{i}" for i in range(14)] + [f"A{i}" for i in range(6)])
        trigger_config_layout.addWidget(self.trigger_pin_combo)
        
        self.trigger_operator_combo = QComboBox()
        self.trigger_operator_combo.addItems([">", "<", "==", "!=", "Änderung"])
        trigger_config_layout.addWidget(self.trigger_operator_combo)
        
        self.trigger_value_spin = QSpinBox()
        self.trigger_value_spin.setRange(0, 1023)
        trigger_config_layout.addWidget(self.trigger_value_spin)
        
        add_trigger_btn = QPushButton("➕ Trigger")
        add_trigger_btn.clicked.connect(self.add_trigger)
        trigger_config_layout.addWidget(add_trigger_btn)
        
        trigger_layout.addLayout(trigger_config_layout)
        
        self.trigger_list = QTextEdit()
        self.trigger_list.setReadOnly(True)
        self.trigger_list.setMaximumHeight(100)
        trigger_layout.addWidget(self.trigger_list)
        
        config_splitter.addWidget(trigger_group)
        control_layout.addWidget(config_splitter)
        
        # Logging-Optionen
        options_group = QGroupBox("⚙️ Optionen")
        options_layout = QHBoxLayout(options_group)
        
        self.log_all_check = QCheckBox("Alle Pins loggen")
        options_layout.addWidget(self.log_all_check)
        
        self.log_changes_only_check = QCheckBox("Nur Änderungen")
        self.log_changes_only_check.setChecked(True)
        options_layout.addWidget(self.log_changes_only_check)
        
        options_layout.addWidget(QLabel("Intervall:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 10000)
        self.interval_spin.setValue(100)
        self.interval_spin.setSuffix(" ms")
        options_layout.addWidget(self.interval_spin)
        
        options_layout.addStretch()
        control_layout.addWidget(options_group)
        
        splitter.addWidget(control_widget)
        
        # === UNTERER BEREICH: Daten-Tabelle ===
        data_widget = QWidget()
        data_layout = QVBoxLayout(data_widget)
        
        # Export-Buttons
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Export:"))
        
        csv_btn = QPushButton("📄 CSV")
        csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(csv_btn)
        
        json_btn = QPushButton("📋 JSON")
        json_btn.clicked.connect(self.export_json)
        export_layout.addWidget(json_btn)
        
        excel_btn = QPushButton("📊 Excel")
        excel_btn.clicked.connect(self.export_excel)
        export_layout.addWidget(excel_btn)
        
        export_layout.addStretch()
        
        auto_scroll_check = QCheckBox("Auto-Scroll")
        auto_scroll_check.setChecked(True)
        self.auto_scroll = auto_scroll_check
        export_layout.addWidget(auto_scroll_check)
        
        data_layout.addLayout(export_layout)
        
        # Daten-Tabelle
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["Zeit", "Datum/Uhrzeit", "Pin", "Wert", "Typ"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setAlternatingRowColors(True)
        data_layout.addWidget(self.data_table)
        
        splitter.addWidget(data_widget)
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter)
    
    def add_watched_pin(self):
        """Fügt einen Pin zur Überwachungsliste hinzu"""
        pin = self.pin_combo.currentText()
        if pin not in self.watched_pins:
            self.watched_pins.add(pin)
            self.update_watched_pins_display()
    
    def add_trigger(self):
        """Fügt eine Trigger-Bedingung hinzu"""
        pin = self.trigger_pin_combo.currentText()
        operator_text = self.trigger_operator_combo.currentText()
        
        operator_map = {
            ">": ">",
            "<": "<",
            "==": "==",
            "!=": "!=",
            "Änderung": "change"
        }
        operator = operator_map[operator_text]
        threshold = self.trigger_value_spin.value()
        
        trigger = TriggerCondition(pin, operator, threshold)
        self.triggers.append(trigger)
        self.update_triggers_display()
    
    def update_watched_pins_display(self):
        """Aktualisiert die Anzeige der überwachten Pins"""
        self.watched_pins_list.setPlainText(", ".join(sorted(self.watched_pins)))
    
    def update_triggers_display(self):
        """Aktualisiert die Anzeige der Trigger"""
        trigger_texts = []
        for i, trigger in enumerate(self.triggers, 1):
            trigger_texts.append(f"{i}. {trigger.pin} {trigger.operator} {trigger.threshold}")
        self.trigger_list.setPlainText("\n".join(trigger_texts))
    
    def toggle_recording(self):
        """Startet/Stoppt die Aufzeichnung"""
        self.recording = not self.recording
        
        if self.recording:
            self.status_indicator.setText("🔴")
            self.status_label.setText("Aufzeichnung läuft...")
            self.start_btn.setText("⏸️ Aufzeichnung stoppen")
            self.start_time = time.time()
        else:
            self.status_indicator.setText("⏸️")
            self.status_label.setText("Pausiert")
            self.start_btn.setText("🔴 Aufzeichnung starten")
    
    def log_pin_value(self, pin_name: str, value: Any):
        """Loggt einen Pin-Wert (wird von außen aufgerufen)"""
        if not self.recording:
            return
        
        # Prüfen, ob der Pin überwacht werden soll
        if not self.log_all_check.isChecked() and pin_name not in self.watched_pins:
            return
        
        # Nur Änderungen loggen?
        if self.log_changes_only_check.isChecked():
            if pin_name in self.pin_states and self.pin_states[pin_name] == value:
                return
        
        self.pin_states[pin_name] = value
        
        # Event-Typ bestimmen
        event_type = "periodic"
        
        # Trigger prüfen
        for trigger in self.triggers:
            if trigger.check(pin_name, value):
                event_type = "trigger"
                break
        
        # Log-Eintrag erstellen
        entry = LogEntry(
            timestamp=time.time(),
            pin_name=pin_name,
            value=value,
            event_type=event_type
        )
        
        self.log_entries.append(entry)
    
    def update_display(self):
        """Aktualisiert die Anzeige"""
        if not self.recording:
            return
        
        # Statistiken
        count = len(self.log_entries)
        duration = time.time() - self.start_time
        rate = count / duration if duration > 0 else 0
        
        self.entry_count_label.setText(f"Einträge: {count:,}")
        self.duration_label.setText(f"Dauer: {int(duration // 60):02d}:{int(duration % 60):02d}")
        self.rate_label.setText(f"Rate: {rate:.1f} Hz")
        
        # Geschätzte Größe
        estimated_size = count * 50 / 1024  # ~50 Bytes pro Eintrag
        self.size_label.setText(f"Größe: {estimated_size:.1f} KB")
        
        # Tabelle aktualisieren (nur letzte 100 Einträge)
        display_entries = list(self.log_entries)[-100:]
        self.data_table.setRowCount(len(display_entries))
        
        for row, entry in enumerate(display_entries):
            data = entry.to_dict()
            
            # Zeit (Sekunden seit Start)
            time_item = QTableWidgetItem(f"{entry.timestamp - self.start_time:.3f}")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.data_table.setItem(row, 0, time_item)
            
            # Datum/Uhrzeit
            self.data_table.setItem(row, 1, QTableWidgetItem(data["datetime"]))
            
            # Pin
            self.data_table.setItem(row, 2, QTableWidgetItem(data["pin"]))
            
            # Wert
            value_item = QTableWidgetItem(str(data["value"]))
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.data_table.setItem(row, 3, value_item)
            
            # Typ mit Farbe
            type_item = QTableWidgetItem(data["type"])
            if data["type"] == "trigger":
                type_item.setForeground(QColor("#e74c3c"))
                type_item.setBackground(QColor("#2c1a1a"))
            self.data_table.setItem(row, 4, type_item)
        
        # Auto-Scroll
        if self.auto_scroll.isChecked():
            self.data_table.scrollToBottom()
    
    def clear_log(self):
        """Löscht alle Log-Einträge"""
        reply = QMessageBox.question(
            self, "Bestätigung",
            f"Möchten Sie wirklich {len(self.log_entries)} Einträge löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_entries.clear()
            self.pin_states.clear()
            self.data_table.setRowCount(0)
    
    def export_csv(self):
        """Exportiert die Daten als CSV"""
        if not self.log_entries:
            QMessageBox.warning(self, "Warnung", "Keine Daten zum Exportieren vorhanden!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "CSV exportieren",
            f"log_{QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.csv",
            "CSV (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=["timestamp", "datetime", "pin", "value", "type"])
                    writer.writeheader()
                    for entry in self.log_entries:
                        writer.writerow(entry.to_dict())
                
                QMessageBox.information(
                    self, "Erfolg",
                    f"{len(self.log_entries)} Einträge wurden nach {file_path} exportiert!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")
    
    def export_json(self):
        """Exportiert die Daten als JSON"""
        if not self.log_entries:
            QMessageBox.warning(self, "Warnung", "Keine Daten zum Exportieren vorhanden!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSON exportieren",
            f"log_{QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.json",
            "JSON (*.json)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    data = [entry.to_dict() for entry in self.log_entries]
                    json.dump(data, f, indent=2)
                
                QMessageBox.information(
                    self, "Erfolg",
                    f"{len(self.log_entries)} Einträge wurden nach {file_path} exportiert!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")
    
    def export_excel(self):
        """Exportiert die Daten als Excel"""
        if not self.log_entries:
            QMessageBox.warning(self, "Warnung", "Keine Daten zum Exportieren vorhanden!")
            return
        
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment
        except ImportError:
            QMessageBox.critical(
                self, "Fehler",
                "openpyxl ist nicht installiert!\nBitte installieren: pip install openpyxl"
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Excel exportieren",
            f"log_{QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.xlsx",
            "Excel (*.xlsx)"
        )
        
        if file_path:
            try:
                wb = Workbook()
                ws = wb.active
                ws.title = "Datenlog"
                
                # Header
                headers = ["Zeitstempel", "Datum/Uhrzeit", "Pin", "Wert", "Typ"]
                ws.append(headers)
                
                # Header formatieren
                for cell in ws[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
                
                # Daten
                for entry in self.log_entries:
                    data = entry.to_dict()
                    ws.append([
                        data["timestamp"],
                        data["datetime"],
                        data["pin"],
                        data["value"],
                        data["type"]
                    ])
                
                # Spaltenbreiten anpassen
                ws.column_dimensions['A'].width = 15
                ws.column_dimensions['B'].width = 22
                ws.column_dimensions['C'].width = 10
                ws.column_dimensions['D'].width = 12
                ws.column_dimensions['E'].width = 12
                
                wb.save(file_path)
                
                QMessageBox.information(
                    self, "Erfolg",
                    f"{len(self.log_entries)} Einträge wurden nach {file_path} exportiert!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")
