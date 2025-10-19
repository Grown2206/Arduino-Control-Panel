# -*- coding: utf-8 -*-
"""
Sensor-Konfigurations-Tab: Visuelles Setup für Sensoren
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QListWidget, QListWidgetItem, QPushButton, QLabel,
                             QGridLayout, QComboBox, QSpinBox, QCheckBox, QFrame,
                             QScrollArea, QMessageBox, QLineEdit, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QTimer
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QFont
import json
import time  # ← WICHTIG: time importieren!


# Import der Sensor-Bibliothek (aus vorherigem Artifact)
# from sensor_library import SensorLibrary, SensorType

class SensorCard(QFrame):
    """Eine Karte für einen konfigurierten Sensor"""
    remove_requested = pyqtSignal(str)  # sensor_instance_id
    
    def __init__(self, sensor_def, instance_id, parent=None):
        super().__init__(parent)
        self.sensor_def = sensor_def
        self.instance_id = instance_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            SensorCard {
                background-color: #2D3B4A;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 10px;
            }
            SensorCard:hover {
                border-color: #5dade2;
                background-color: #34495e;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header mit Icon und Name
        header = QHBoxLayout()
        icon_label = QLabel(self.sensor_def.icon)
        icon_label.setStyleSheet("font-size: 32px;")
        header.addWidget(icon_label)
        
        name_label = QLabel(self.sensor_def.name)
        name_label.setStyleSheet("font-weight: bold; color: #ecf0f1;")
        header.addWidget(name_label, 1)
        
        remove_btn = QPushButton("✖")
        remove_btn.setFixedSize(25, 25)
        remove_btn.setStyleSheet("background-color: #e74c3c; border-radius: 12px;")
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.instance_id))
        header.addWidget(remove_btn)
        layout.addLayout(header)
        
        # Pin-Konfiguration
        self.pin_widgets = {}
        for pin_name, default_pin in self.sensor_def.pins.items():
            pin_layout = QHBoxLayout()
            pin_layout.addWidget(QLabel(f"{pin_name}:"))
            
            pin_combo = QComboBox()
            # Digital Pins
            pin_combo.addItems([f"D{i}" for i in range(14)])
            # Analog Pins
            pin_combo.addItems([f"A{i}" for i in range(6)])
            pin_combo.setCurrentText(default_pin)
            self.pin_widgets[pin_name] = pin_combo
            
            pin_layout.addWidget(pin_combo)
            layout.addLayout(pin_layout)
        
        # Abfrageintervall
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervall:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 60000)
        self.interval_spin.setValue(self.sensor_def.read_interval_ms)
        self.interval_spin.setSuffix(" ms")
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)
        
        # Aktiv-Status
        self.active_check = QCheckBox("Sensor aktiv")
        self.active_check.setChecked(True)
        layout.addWidget(self.active_check)
        
        # Live-Wert-Anzeige
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #f39c12;
            background-color: #1e1e1e;
            border-radius: 5px;
            padding: 5px;
        """)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
    
    def update_value(self, value):
        """Aktualisiert den angezeigten Wert"""
        if isinstance(value, float):
            self.value_label.setText(f"{value:.2f} {self.sensor_def.unit}")
        else:
            self.value_label.setText(f"{value} {self.sensor_def.unit}")
    
    def get_config(self):
        """Gibt die aktuelle Konfiguration zurück"""
        return {
            "sensor_id": self.sensor_def.id,
            "instance_id": self.instance_id,
            "pins": {name: widget.currentText() for name, widget in self.pin_widgets.items()},
            "interval_ms": self.interval_spin.value(),
            "active": self.active_check.isChecked()
        }


class SensorBrowserWidget(QGroupBox):
    """Browser für verfügbare Sensoren"""
    sensor_selected = pyqtSignal(str)  # sensor_id
    
    def __init__(self, parent=None):
        super().__init__("📚 Sensor-Bibliothek", parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Filter nach Typ
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("Alle Typen", None)
        # self.type_filter.addItems([t.value for t in SensorType])
        self.type_filter.currentIndexChanged.connect(self.filter_sensors)
        filter_layout.addWidget(self.type_filter)
        layout.addLayout(filter_layout)
        
        # Sucheingabe
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Sensor suchen...")
        self.search_input.textChanged.connect(self.filter_sensors)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Sensor-Liste
        self.sensor_list = QListWidget()
        self.sensor_list.itemDoubleClicked.connect(self.on_sensor_double_clicked)
        layout.addWidget(self.sensor_list)
        
        # Add-Button
        add_btn = QPushButton("➕ Sensor hinzufügen")
        add_btn.clicked.connect(self.on_add_clicked)
        layout.addWidget(add_btn)
        
        self.populate_sensors()
    
    def populate_sensors(self):
        """Füllt die Liste mit allen Sensoren"""
        self.sensor_list.clear()
        # for sensor_id, sensor in SensorLibrary.SENSORS.items():
        #     item = QListWidgetItem(f"{sensor.icon} {sensor.name}")
        #     item.setData(Qt.ItemDataRole.UserRole, sensor_id)
        #     self.sensor_list.addItem(item)
        
        # Dummy-Daten für Demo
        dummy_sensors = [
            ("🌡️", "DHT11 Temp/Humidity", "DHT11"),
            ("📏", "HC-SR04 Ultraschall", "HC_SR04"),
            ("🚶", "PIR Bewegungsmelder", "HC_SR501"),
            ("💡", "Fotowiderstand LDR", "LDR"),
            ("🎤", "Mikrofon", "MIC_ANALOG"),
            ("💨", "MQ-2 Rauch/Gas", "MQ2"),
            ("🌱", "Bodenfeuchte", "SOIL_MOISTURE"),
        ]
        for icon, name, sensor_id in dummy_sensors:
            item = QListWidgetItem(f"{icon} {name}")
            item.setData(Qt.ItemDataRole.UserRole, sensor_id)
            self.sensor_list.addItem(item)
    
    def filter_sensors(self):
        """Filtert die Sensor-Liste"""
        search_term = self.search_input.text().lower()
        for i in range(self.sensor_list.count()):
            item = self.sensor_list.item(i)
            visible = search_term in item.text().lower()
            item.setHidden(not visible)
    
    def on_sensor_double_clicked(self, item):
        sensor_id = item.data(Qt.ItemDataRole.UserRole)
        self.sensor_selected.emit(sensor_id)
    
    def on_add_clicked(self):
        item = self.sensor_list.currentItem()
        if item:
            sensor_id = item.data(Qt.ItemDataRole.UserRole)
            self.sensor_selected.emit(sensor_id)


class SensorConfigTab(QWidget):
    """Haupt-Tab für Sensor-Konfiguration"""
    sensor_update_signal = pyqtSignal(dict)  # Sensor-Daten
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.configured_sensors = {}
        self.sensor_counter = 0
        self.setup_ui()
        
        # Timer für periodische Sensor-Abfragen
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_all_sensors)
        self.poll_timer.start(1000)  # Jede Sekunde
        
        # Letzte Poll-Zeit pro Sensor tracken
        self.last_poll_times = {}

        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Linke Seite: Sensor-Browser
        self.browser = SensorBrowserWidget()
        self.browser.sensor_selected.connect(self.add_sensor)
        self.browser.setMaximumWidth(350)
        layout.addWidget(self.browser)
        
        # Rechte Seite: Konfigurierte Sensoren
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Header mit Statistiken
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("📊 0 Sensoren konfiguriert")
        self.stats_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ Alle entfernen")
        clear_btn.clicked.connect(self.clear_all_sensors)
        stats_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("💾 Konfiguration exportieren")
        export_btn.clicked.connect(self.export_config)
        stats_layout.addWidget(export_btn)
        
        right_layout.addLayout(stats_layout)
        
        # Scroll-Bereich für Sensor-Karten
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.sensor_container = QWidget()
        self.sensor_layout = QVBoxLayout(self.sensor_container)
        self.sensor_layout.addStretch()
        scroll.setWidget(self.sensor_container)
        
        right_layout.addWidget(scroll)
        layout.addWidget(right_widget, 1)
    
    def add_sensor(self, sensor_id: str):
        """Fügt einen neuen Sensor hinzu"""
        # sensor_def = SensorLibrary.get_sensor(sensor_id)
        # if not sensor_def:
        #     return
        
        # Dummy für Demo - sollte durch echte Sensor-Bibliothek ersetzt werden
        from dataclasses import dataclass
        from typing import Dict
        
        @dataclass
        class DummySensor:
            id: str
            name: str
            icon: str
            pins: Dict[str, str]
            unit: str
            read_interval_ms: int
        
        dummy_sensors = {
            "DHT11": DummySensor("DHT11", "DHT11 Temp/Humidity", "🌡️", {"data": "D2"}, "°C/%", 2000),
            "HC_SR04": DummySensor("HC_SR04", "HC-SR04 Ultraschall", "📏", {"trigger": "D9", "echo": "D10"}, "cm", 500),
            "LDR": DummySensor("LDR", "Fotowiderstand", "💡", {"analog": "A0"}, "Lux", 1000),
        }
        sensor_def = dummy_sensors.get(sensor_id)
        if not sensor_def:
            return
        
        # Neue Instanz erstellen
        self.sensor_counter += 1
        instance_id = f"{sensor_id}_{self.sensor_counter}"
        
        card = SensorCard(sensor_def, instance_id)
        card.remove_requested.connect(self.remove_sensor)
        
        # Vor dem Stretch einfügen
        self.sensor_layout.insertWidget(self.sensor_layout.count() - 1, card)
        self.configured_sensors[instance_id] = card
        
        self.update_stats()
    
    def remove_sensor(self, instance_id: str):
        """Entfernt einen Sensor"""
        if instance_id in self.configured_sensors:
            card = self.configured_sensors.pop(instance_id)
            card.deleteLater()
            self.update_stats()
    
    def clear_all_sensors(self):
        """Entfernt alle Sensoren"""
        reply = QMessageBox.question(
            self, "Bestätigung",
            "Möchten Sie wirklich alle Sensoren entfernen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for instance_id in list(self.configured_sensors.keys()):
                self.remove_sensor(instance_id)
    
    def update_stats(self):
        """Aktualisiert die Statistik-Anzeige"""
        count = len(self.configured_sensors)
        active_count = sum(1 for card in self.configured_sensors.values() if card.active_check.isChecked())
        self.stats_label.setText(f"📊 {count} Sensoren konfiguriert ({active_count} aktiv)")
    
    def poll_all_sensors(self):
        """Fragt alle aktiven Sensoren ab (mit individuellem Intervall)"""
        import random
        
        current_time = time.time()
        
        for instance_id, card in self.configured_sensors.items():
            if not card.active_check.isChecked():
                continue
            
            # Prüfe, ob genug Zeit seit letztem Poll vergangen ist
            last_poll = self.last_poll_times.get(instance_id, 0)
            interval_seconds = card.interval_spin.value() / 1000.0
            
            if current_time - last_poll < interval_seconds:
                continue  # Noch nicht Zeit für diesen Sensor
            
            # Poll durchführen
            self.last_poll_times[instance_id] = current_time
            
            # Hier würde die echte Sensor-Abfrage stattfinden
            # Für Demo: Zufallswerte generieren
            if card.sensor_def.id == "DHT11":
                temp = 20 + random.random() * 10
                card.update_value(temp)
            elif card.sensor_def.id == "HC_SR04":
                distance = random.randint(10, 200)
                card.update_value(distance)
            elif card.sensor_def.id == "LDR":
                lux = random.randint(0, 1000)
                card.update_value(lux)
    
    def export_config(self):
        """Exportiert die aktuelle Konfiguration"""
        config = {
            "sensors": [card.get_config() for card in self.configured_sensors.values()]
        }
        
        # In Zwischenablage kopieren
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(json.dumps(config, indent=2))
        
        QMessageBox.information(
            self, "Export",
            f"Konfiguration für {len(config['sensors'])} Sensoren wurde in die Zwischenablage kopiert!"
        )
    
    def get_all_configs(self):
        """Gibt alle Sensor-Konfigurationen zurück"""
        return [card.get_config() for card in self.configured_sensors.values()]
