# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSpinBox, QFrame, QPushButton, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from datetime import datetime
import time
from collections import deque

from .live_chart_widget import LiveChartWidget

# NEU: Kalibrierungs-Integration
try:
    from core.calibration_manager import CalibrationManager
    from ui.calibration_wizard import CalibrationWizard
    CALIBRATION_AVAILABLE = True
except ImportError:
    CALIBRATION_AVAILABLE = False
    print("⚠️ Kalibrierungs-Module nicht verfügbar")

class B24Sensor(QGroupBox):
    """B24: Temperatur & Luftfeuchtigkeit (3-Pin)"""

    calibrate_requested = pyqtSignal(str)  # NEU: Signal für Kalibrierung

    def __init__(self):
        super().__init__("B24: Temperatur & Luftfeuchtigkeit")
        self.temp_history = deque(maxlen=100)
        self.humid_history = deque(maxlen=100)
        self.temp_min, self.temp_max = None, None
        self.humid_min, self.humid_max = None, None

        # NEU: Kalibrierungs-Status
        self.temp_calibration_active = False
        self.humid_calibration_active = False

        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        temp_widget = self._create_display_card("🌡️ Temperatur", "°C")
        self.temp_value = temp_widget.findChild(QLabel, "valueLabel")
        self.temp_minmax = temp_widget.findChild(QLabel, "minmaxLabel")
        self.temp_status = temp_widget.findChild(QLabel, "statusLabel")
        self.temp_last_update = temp_widget.findChild(QLabel, "lastUpdateLabel")

        # NEU: Kalibrierungs-Elemente
        if CALIBRATION_AVAILABLE:
            self.temp_calib_status = temp_widget.findChild(QLabel, "calibStatusLabel")
            temp_calib_btn = temp_widget.findChild(QPushButton, "calibButton")
            if temp_calib_btn:
                temp_calib_btn.clicked.connect(lambda: self.calibrate_requested.emit("B24_TEMP"))

        humid_widget = self._create_display_card("💧 Luftfeuchtigkeit", "%")
        self.humid_value = humid_widget.findChild(QLabel, "valueLabel")
        self.humid_minmax = humid_widget.findChild(QLabel, "minmaxLabel")
        self.humid_status = humid_widget.findChild(QLabel, "statusLabel")
        self.humid_last_update = humid_widget.findChild(QLabel, "lastUpdateLabel")

        # NEU: Kalibrierungs-Elemente
        if CALIBRATION_AVAILABLE:
            self.humid_calib_status = humid_widget.findChild(QLabel, "calibStatusLabel")
            humid_calib_btn = humid_widget.findChild(QPushButton, "calibButton")
            if humid_calib_btn:
                humid_calib_btn.clicked.connect(lambda: self.calibrate_requested.emit("B24_HUMIDITY"))

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

        # NEU: Kalibrierungs-Status und Button
        if CALIBRATION_AVAILABLE:
            calib_status_label = QLabel("○ Nicht kalibriert"); calib_status_label.setObjectName("calibStatusLabel"); calib_status_label.setStyleSheet("font-size: 9px; color: #95a5a6;"); calib_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(calib_status_label)

            calib_btn = QPushButton("📐 Kalibrieren"); calib_btn.setObjectName("calibButton"); calib_btn.setStyleSheet("font-size: 10px; padding: 5px;")
            layout.addWidget(calib_btn)

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

    def update_calibration_status(self, sensor_id, is_active):
        """NEU: Aktualisiert Kalibrierungs-Status-Anzeige"""
        if not CALIBRATION_AVAILABLE:
            return

        if sensor_id == "B24_TEMP":
            self.temp_calibration_active = is_active
            if hasattr(self, 'temp_calib_status'):
                if is_active:
                    self.temp_calib_status.setText("● Kalibriert")
                    self.temp_calib_status.setStyleSheet("font-size: 9px; color: #27ae60;")
                else:
                    self.temp_calib_status.setText("○ Nicht kalibriert")
                    self.temp_calib_status.setStyleSheet("font-size: 9px; color: #95a5a6;")

        elif sensor_id == "B24_HUMIDITY":
            self.humid_calibration_active = is_active
            if hasattr(self, 'humid_calib_status'):
                if is_active:
                    self.humid_calib_status.setText("● Kalibriert")
                    self.humid_calib_status.setStyleSheet("font-size: 9px; color: #27ae60;")
                else:
                    self.humid_calib_status.setText("○ Nicht kalibriert")
                    self.humid_calib_status.setStyleSheet("font-size: 9px; color: #95a5a6;")

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

        # NEU: Kalibrierungs-Manager
        if CALIBRATION_AVAILABLE:
            self.calibration_manager = CalibrationManager()
            # Verbinde Kalibrierungs-Signale
            self.b24_sensor.calibrate_requested.connect(self.open_calibration_wizard)
            # Lade Kalibrierungs-Status
            self.load_calibration_status()
        else:
            self.calibration_manager = None

        # Speichere letzte Rohwerte für Kalibrierung
        self.last_raw_values = {}

        # NEU: Daten-Freshness Tracking
        self.last_data_time = {}
        self.data_timeout_ms = 5000  # 5 Sekunden Timeout

        # NEU: Status Timer für Daten-Freshness Check
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_data_freshness)
        self.status_timer.start(1000)  # Prüfe jede Sekunde

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # NEU: Status-Banner für Verbindung
        self.connection_status = QLabel("⏳ Warte auf Sensor-Daten...")
        self.connection_status.setStyleSheet(
            "background-color: #f39c12; color: #ffffff; padding: 8px; "
            "border-radius: 4px; font-weight: bold; font-size: 12px;"
        )
        self.connection_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.connection_status)

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

        # NEU: Refresh Button
        self.refresh_btn = QPushButton("🔄 Sensoren aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh_sensors)
        settings_layout.addWidget(self.refresh_btn)

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

    def check_data_freshness(self):
        """NEU: Prüft, ob Sensor-Daten noch aktuell sind"""
        current_time = time.time() * 1000  # ms
        all_fresh = True

        for sensor_id, last_time in self.last_data_time.items():
            time_since_update = current_time - last_time
            if time_since_update > self.data_timeout_ms:
                all_fresh = False
                break

        # Update Connection Status
        if not self.last_data_time:
            self.connection_status.setText("⏳ Warte auf Sensor-Daten...")
            self.connection_status.setStyleSheet(
                "background-color: #f39c12; color: #ffffff; padding: 8px; "
                "border-radius: 4px; font-weight: bold; font-size: 12px;"
            )
        elif all_fresh:
            active_count = len(self.last_data_time)
            self.connection_status.setText(f"✅ {active_count} Sensor(en) aktiv - Daten aktuell")
            self.connection_status.setStyleSheet(
                "background-color: #27ae60; color: #ffffff; padding: 8px; "
                "border-radius: 4px; font-weight: bold; font-size: 12px;"
            )
        else:
            self.connection_status.setText("⚠️ Sensor-Daten veraltet - Keine neuen Daten empfangen")
            self.connection_status.setStyleSheet(
                "background-color: #e74c3c; color: #ffffff; padding: 8px; "
                "border-radius: 4px; font-weight: bold; font-size: 12px;"
            )

    def refresh_sensors(self):
        """NEU: Manuelles Aktualisieren der Sensoren"""
        self.last_data_time.clear()
        self.b24_sensor.temp_status.setText("⏳ Aktualisiere...")
        self.b24_sensor.humid_status.setText("⏳ Aktualisiere...")
        self.b39_sensor.status_label.setText("⏳ Aktualisiere...")
        self.connection_status.setText("🔄 Aktualisiere Sensoren...")
        self.connection_status.setStyleSheet(
            "background-color: #3498db; color: #ffffff; padding: 8px; "
            "border-radius: 4px; font-weight: bold; font-size: 12px;"
        )

    def handle_sensor_data(self, data):
        """Verarbeitet eingehende Sensor-Daten und leitet sie an die Widgets und das Diagramm weiter."""
        sensor = data.get("sensor")
        raw_value = data.get("value")
        timestamp = time.time() - self.chart_start_time

        if raw_value is None:
            return

        # NEU: Aktualisiere Daten-Zeitstempel für Freshness-Check
        self.last_data_time[sensor] = time.time() * 1000

        # Speichere Rohwert
        self.last_raw_values[sensor] = raw_value

        # NEU: Wende Kalibrierung an
        if CALIBRATION_AVAILABLE and self.calibration_manager:
            calibrated_value = self.calibration_manager.apply_calibration(sensor, raw_value)
        else:
            calibrated_value = raw_value

        if sensor == "B24_TEMP":
            self.b24_sensor.update_temperature(calibrated_value)
            self.b24_sensor.temp_status.setText("✅ Aktiv")
            self.b24_sensor.temp_status.setStyleSheet("font-size: 10px; color: #27ae60; font-style: italic;")
            self.history_chart.add_data_point("Temperatur", calibrated_value, timestamp)
        elif sensor == "B24_HUMIDITY":
            self.b24_sensor.update_humidity(calibrated_value)
            self.b24_sensor.humid_status.setText("✅ Aktiv")
            self.b24_sensor.humid_status.setStyleSheet("font-size: 10px; color: #27ae60; font-style: italic;")
            self.history_chart.add_data_point("Luftfeuchtigkeit", calibrated_value, timestamp)
        elif sensor == "B39_VIBRATION":
            self.b39_sensor.update_value(data.get("intensity", 0), data.get("vibrating", False))

    def load_calibration_status(self):
        """NEU: Lädt Kalibrierungs-Status für alle Sensoren"""
        if not CALIBRATION_AVAILABLE or not self.calibration_manager:
            return

        for sensor_id in ["B24_TEMP", "B24_HUMIDITY"]:
            cal = self.calibration_manager.get_calibration(sensor_id)
            is_active = cal is not None and cal.is_active
            self.b24_sensor.update_calibration_status(sensor_id, is_active)

    def open_calibration_wizard(self, sensor_id: str):
        """NEU: Öffnet Kalibrierungs-Wizard für Sensor"""
        if not CALIBRATION_AVAILABLE:
            QMessageBox.warning(self, "Nicht verfügbar", "Kalibrierungs-Module nicht geladen")
            return

        # Sensor-Name
        sensor_names = {
            "B24_TEMP": "Temperatur (B24)",
            "B24_HUMIDITY": "Luftfeuchtigkeit (B24)"
        }
        sensor_name = sensor_names.get(sensor_id, sensor_id)

        # Callback für aktuellen Wert
        def get_current_value(sid):
            return self.last_raw_values.get(sid, 0.0)

        # Öffne Wizard
        wizard = CalibrationWizard(
            sensor_id=sensor_id,
            sensor_name=sensor_name,
            current_value_callback=get_current_value,
            parent=self
        )

        wizard.calibration_completed.connect(self.on_calibration_completed)
        wizard.exec()

    def on_calibration_completed(self, sensor_id: str, calibration_data):
        """NEU: Wird aufgerufen wenn Kalibrierung abgeschlossen"""
        self.b24_sensor.update_calibration_status(sensor_id, calibration_data.is_active)

        QMessageBox.information(
            self,
            "Kalibrierung erfolgreich",
            f"Sensor '{sensor_id}' wurde erfolgreich kalibriert!\n\n"
            f"Qualität: {calibration_data.quality_score:.3f}"
        )
