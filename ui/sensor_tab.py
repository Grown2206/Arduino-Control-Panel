# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSpinBox, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from datetime import datetime
import time
from collections import deque

from .live_chart_widget import LiveChartWidget

class B24Sensor(QGroupBox):
    """B24: Temperatur & Luftfeuchtigkeit (3-Pin)"""
    
    def __init__(self):
        super().__init__("B24: Temperatur & Luftfeuchtigkeit")
        self.temp_history = deque(maxlen=100)
        self.humid_history = deque(maxlen=100)
        self.temp_min, self.temp_max = None, None
        self.humid_min, self.humid_max = None, None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        temp_widget = self._create_display_card("🌡️ Temperatur", "°C")
        self.temp_value = temp_widget.findChild(QLabel, "valueLabel")
        self.temp_minmax = temp_widget.findChild(QLabel, "minmaxLabel")
        self.temp_status = temp_widget.findChild(QLabel, "statusLabel")
        self.temp_last_update = temp_widget.findChild(QLabel, "lastUpdateLabel")

        humid_widget = self._create_display_card("💧 Luftfeuchtigkeit", "%")
        self.humid_value = humid_widget.findChild(QLabel, "valueLabel")
        self.humid_minmax = humid_widget.findChild(QLabel, "minmaxLabel")
        self.humid_status = humid_widget.findChild(QLabel, "statusLabel")
        self.humid_last_update = humid_widget.findChild(QLabel, "lastUpdateLabel")

        layout.addWidget(temp_widget)
        layout.addWidget(humid_widget)

    def _create_display_card(self, title, unit):
        widget = QFrame(); widget.setObjectName("SensorCard"); widget.setStyleSheet("#SensorCard { background-color: #31363B; border-radius: 8px; }")
        layout = QVBoxLayout(widget)
        
        header = QLabel(title); header.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0;"); header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        value_label = QLabel("--"); value_label.setObjectName("valueLabel"); value_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #f39c12; padding: 10px;"); value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        minmax_label = QLabel("Min: -- | Max: --"); minmax_label.setObjectName("minmaxLabel"); minmax_label.setStyleSheet("font-size: 10px; color: #7f8c8d;"); minmax_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(minmax_label)
        
        status_label = QLabel("⏳ Warte auf Daten..."); status_label.setObjectName("statusLabel"); status_label.setStyleSheet("font-size: 10px; color: #f39c12; font-style: italic;"); status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        last_update_label = QLabel(); last_update_label.setObjectName("lastUpdateLabel"); last_update_label.setStyleSheet("font-size: 9px; color: #7f8c8d;"); last_update_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(last_update_label)

        return widget

    def update_temperature(self, value):
        self.temp_value.setText(f"{value:.1f}°C")
        if self.temp_min is None or value < self.temp_min: self.temp_min = value
        if self.temp_max is None or value > self.temp_max: self.temp_max = value
        self.temp_minmax.setText(f"Min: {self.temp_min:.1f}°C | Max: {self.temp_max:.1f}°C")
        self.temp_last_update.setText(f"Update: {datetime.now().strftime('%H:%M:%S')}")

    def update_humidity(self, value):
        self.humid_value.setText(f"{value:.1f}%")
        if self.humid_min is None or value < self.humid_min: self.humid_min = value
        if self.humid_max is None or value > self.humid_max: self.humid_max = value
        self.humid_minmax.setText(f"Min: {self.humid_min:.1f}% | Max: {self.humid_max:.1f}%")
        self.humid_last_update.setText(f"Update: {datetime.now().strftime('%H:%M:%S')}")

class B39VibrationSensor(QGroupBox):
    """B39 Vibrationssensor"""
    
    def __init__(self):
        super().__init__("🔔 B39 Vibrationssensor")
        self.vibrating = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.intensity_label = QLabel("--")
        self.intensity_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #27ae60; padding: 20px;")
        self.intensity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.intensity_label)
        
        self.status_label = QLabel("⏳ Warte auf Daten...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f39c12; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.last_update = QLabel("")
        self.last_update.setStyleSheet("font-size: 9px; color: #7f8c8d;")
        self.last_update.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.last_update)
        
    def update_value(self, intensity, vibrating):
        """Aktualisiert Vibrations-Anzeige"""
        self.intensity_label.setText(str(intensity))
        self.vibrating = vibrating
        
        self.last_update.setText(f"Update: {datetime.now().strftime('%H:%M:%S')}")
        
        if vibrating:
            self.status_label.setText("⚠️ VIBRATION ERKANNT!")
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; padding: 10px;")
        else:
            self.status_label.setText("✅ Ruhig")
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; padding: 10px;")


class SensorTab(QWidget):
    """Der komplette 'Sensoren'-Tab, inklusive der neuen Poll-Einstellung und Diagramm."""
    poll_interval_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.b24_sensor = B24Sensor()
        self.b39_sensor = B39VibrationSensor()
        self.history_chart = LiveChartWidget(title="Sensorverlauf (Temp/Humid)")
        self.chart_start_time = time.time()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        settings_group = QGroupBox("Sensor-Einstellungen")
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.addWidget(QLabel("Abfrageintervall:"))
        self.poll_interval_spinbox = QSpinBox()
        self.poll_interval_spinbox.setRange(500, 60000)
        self.poll_interval_spinbox.setSingleStep(100)
        self.poll_interval_spinbox.setValue(2000)
        self.poll_interval_spinbox.setSuffix(" ms")
        self.poll_interval_spinbox.valueChanged.connect(self.poll_interval_changed.emit)
        settings_layout.addWidget(self.poll_interval_spinbox)
        settings_layout.addStretch()
        
        layout.addWidget(settings_group)
        
        sensor_layout = QHBoxLayout()
        sensor_layout.addWidget(self.b24_sensor)
        sensor_layout.addWidget(self.b39_sensor)
        layout.addLayout(sensor_layout)

        layout.addWidget(self.history_chart)
        self.history_chart.clear_button_pressed.connect(self.clear_chart_data)

        layout.addStretch()

    def clear_chart_data(self):
        self.history_chart.clear()
        self.chart_start_time = time.time()

    def get_poll_interval(self):
        return self.poll_interval_spinbox.value()

    def handle_sensor_data(self, data):
        """Verarbeitet eingehende Sensor-Daten und leitet sie an die Widgets und das Diagramm weiter."""
        sensor = data.get("sensor")
        value = data.get("value")
        timestamp = time.time() - self.chart_start_time

        if sensor == "B24_TEMP" and value is not None:
            self.b24_sensor.update_temperature(value)
            self.history_chart.add_data_point("Temperatur", value, timestamp)
        elif sensor == "B24_HUMIDITY" and value is not None:
            self.b24_sensor.update_humidity(value)
            self.history_chart.add_data_point("Luftfeuchtigkeit", value, timestamp)
        elif sensor == "B39_VIBRATION":
            self.b39_sensor.update_value(data.get("intensity", 0), data.get("vibrating", False))
