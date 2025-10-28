# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QGroupBox, QGridLayout, QTextEdit)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
from collections import deque

class ConnectionWidget(QGroupBox):
    """Ein Widget zur Verwaltung der seriellen Verbindung auf dem Dashboard."""
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    refresh_ports_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("🔌 Verbindung", parent)
        self.setObjectName("DashboardConnectionWidget")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Status: Getrennt")
        self.status_label.setStyleSheet("font-weight: bold; padding-bottom: 5px;")
        layout.addWidget(self.status_label)

        port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        port_layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self.refresh_ports_requested.emit)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)

        self.connect_btn = QPushButton("Verbinden")
        self.connect_btn.clicked.connect(self._on_connect_toggle)
        layout.addWidget(self.connect_btn)
        
        layout.addStretch()

    def _on_connect_toggle(self):
        if self.connect_btn.text() == "Verbinden":
            port = self.port_combo.currentText()
            if port:
                self.connect_requested.emit(port)
        else:
            self.disconnect_requested.emit()

    def update_ports(self, ports):
        """Aktualisiert die Liste der verfügbaren COM-Ports."""
        current = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)

    def update_status(self, is_connected, port_name=""):
        """Aktualisiert den angezeigten Verbindungsstatus."""
        if is_connected:
            self.status_label.setText(f"Status: Verbunden ({port_name})")
            self.status_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
            self.connect_btn.setText("Trennen")
            self.port_combo.setDisabled(True)
        else:
            self.status_label.setText("Status: Getrennt")
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            self.connect_btn.setText("Verbinden")
            self.port_combo.setDisabled(False)

class QuickSequenceWidget(QGroupBox):
    """Ein Widget zum schnellen Starten von Testsequenzen."""
    start_sequence_signal = pyqtSignal(str)
    start_test_run_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("⚙️ Schnellstart", parent)
        self.setObjectName("DashboardQuickSequenceWidget")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Sequenz auswählen:"))
        self.sequence_combo = QComboBox()
        layout.addWidget(self.sequence_combo)
        
        start_btn = QPushButton("▶️ Sequenz starten")
        start_btn.clicked.connect(self._on_start_sequence)
        layout.addWidget(start_btn)
        
        test_run_btn = QPushButton("🔬 Testlauf starten")
        test_run_btn.setStyleSheet("background-color: #27ae60;")
        test_run_btn.clicked.connect(self._on_start_test_run)
        layout.addWidget(test_run_btn)
        
        layout.addStretch()

    def _on_start_sequence(self):
        seq_id = self.sequence_combo.currentData()
        if seq_id:
            self.start_sequence_signal.emit(seq_id)

    def _on_start_test_run(self):
        seq_id = self.sequence_combo.currentData()
        if seq_id:
            self.start_test_run_signal.emit(seq_id)

    def update_sequences(self, sequences):
        """Aktualisiert die Liste der verfügbaren Sequenzen."""
        current_id = self.sequence_combo.currentData()
        self.sequence_combo.clear()
        for seq_id, seq_data in sequences.items():
            self.sequence_combo.addItem(seq_data['name'], seq_id)
        
        if current_id in sequences:
            self.sequence_combo.setCurrentText(sequences[current_id]['name'])

class SensorDisplayWidget(QGroupBox):
    """Eine kompakte Anzeige für Live-Sensordaten."""
    def __init__(self, parent=None):
        super().__init__("🌡️ Live Sensoren", parent)
        self.setObjectName("DashboardSensorWidget")
        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout(self)

        self.temp_label = QLabel("Temperatur:")
        self.temp_value = QLabel("-- °C")
        self.temp_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c;")
        
        self.humid_label = QLabel("Luftfeuchtigkeit:")
        self.humid_value = QLabel("-- %")
        self.humid_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db;")
        
        layout.addWidget(self.temp_label, 0, 0)
        layout.addWidget(self.temp_value, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.humid_label, 1, 0)
        layout.addWidget(self.humid_value, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.setColumnStretch(1, 1)

    def update_temperature(self, value):
        self.temp_value.setText(f"{value:.1f} °C")

    def update_humidity(self, value):
        self.humid_value.setText(f"{value:.1f} %")

class RecentActivityWidget(QGroupBox):
    """Ein Widget, das die letzten wichtigen Aktivitäten anzeigt."""
    def __init__(self, parent=None):
        super().__init__("🕒 Letzte Aktivitäten", parent)
        self.setObjectName("DashboardActivityWidget")
        self.log_entries = deque(maxlen=20)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("font-size: 10px; color: #bdc3c7;")
        layout.addWidget(self.log_display)

    def add_entry(self, message):
        """Fügt einen neuen Eintrag zum Aktivitätslog hinzu."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        formatted_message = f"[{timestamp}] {message}"
        self.log_entries.appendleft(formatted_message)
        self.update_display()

    def update_display(self):
        """Aktualisiert die Textanzeige."""
        self.log_display.setHtml("<br>".join(self.log_entries))

