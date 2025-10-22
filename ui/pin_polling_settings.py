# ui/pin_polling_settings.py
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QCheckBox, QSpinBox, QPushButton, QGroupBox,
                              QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal

class PinPollingSettings(QWidget):
    """Widget zur Konfiguration welche Pins gepollt werden sollen"""
    
    polling_changed = pyqtSignal(list, int)  # (pin_list, interval_ms)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pin_checkboxes = {}
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("⚙️ Live Pin-Monitoring Einstellungen")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0;")
        main_layout.addWidget(header)
        
        info = QLabel("Wähle welche Pins kontinuierlich abgefragt werden sollen:")
        info.setStyleSheet("color: #999; font-size: 12px;")
        main_layout.addWidget(info)
        
        main_layout.addSpacing(10)
        
        # Interval Einstellung
        interval_group = QGroupBox("Poll-Intervall")
        interval_layout = QHBoxLayout(interval_group)
        
        interval_layout.addWidget(QLabel("Aktualisierung alle"))
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 5000)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.setSingleStep(100)
        self.interval_spin.valueChanged.connect(self.on_settings_changed)
        interval_layout.addWidget(self.interval_spin)
        
        interval_layout.addStretch()
        
        main_layout.addWidget(interval_group)
        
        # Scroll Area für Pin-Checkboxen
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Digital Pins
        digital_group = QGroupBox("🔌 Digital Pins (D0-D13)")
        digital_layout = QGridLayout(digital_group)

        for i in range(14):
            pin_name = f"D{i}"
            cb = QCheckBox(pin_name)
            cb.setStyleSheet("font-size: 12px;")
            cb.setChecked(True)  # ÄNDERE: Digital Pins auch standardmäßig AN
            cb.stateChanged.connect(self.on_settings_changed)
            self.pin_checkboxes[pin_name] = cb
            
            row, col = divmod(i, 7)
            digital_layout.addWidget(cb, row, col)
        
        scroll_layout.addWidget(digital_group)
        
        # Analog Pins
        analog_group = QGroupBox("📊 Analog Pins (A0-A5)")
        analog_layout = QHBoxLayout(analog_group)
        
        for i in range(6):
            pin_name = f"A{i}"
            cb = QCheckBox(pin_name)
            cb.setStyleSheet("font-size: 12px;")
            cb.setChecked(True)  # Analog Pins standardmäßig AN
            cb.stateChanged.connect(self.on_settings_changed)
            self.pin_checkboxes[pin_name] = cb
            analog_layout.addWidget(cb)
        
        scroll_layout.addWidget(analog_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Quick Actions
        btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("✓ Alle auswählen")
        select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("✗ Alle abwählen")
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(deselect_all_btn)
        
        analog_only_btn = QPushButton("📊 Nur Analog")
        analog_only_btn.clicked.connect(self.select_analog_only)
        btn_layout.addWidget(analog_only_btn)
        
        btn_layout.addStretch()
        
        main_layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel("● 6 Pins aktiv")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        main_layout.addWidget(self.status_label)
    
    def on_settings_changed(self):
        """Wird aufgerufen wenn Einstellungen geändert werden"""
        selected_pins = self.get_selected_pins()
        interval = self.interval_spin.value()
        
        # Update Status
        count = len(selected_pins)
        if count == 0:
            self.status_label.setText("● Kein Pin aktiv")
            self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        else:
            self.status_label.setText(f"● {count} Pin{'s' if count != 1 else ''} aktiv")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        
        # Signal senden
        self.polling_changed.emit(selected_pins, interval)
    
    def get_selected_pins(self):
        """Gibt Liste der ausgewählten Pins zurück"""
        return [pin for pin, cb in self.pin_checkboxes.items() if cb.isChecked()]
    
    def get_interval(self):
        """Gibt aktuelles Intervall zurück"""
        return self.interval_spin.value()
    
    def select_all(self):
        """Wählt alle Pins aus"""
        for cb in self.pin_checkboxes.values():
            cb.setChecked(True)
    
    def deselect_all(self):
        """Wählt alle Pins ab"""
        for cb in self.pin_checkboxes.values():
            cb.setChecked(False)
    
    def select_analog_only(self):
        """Wählt nur Analog-Pins aus"""
        for pin, cb in self.pin_checkboxes.items():
            cb.setChecked(pin.startswith('A'))
    
    def set_pin_states(self, pin_states):
        """
        Setzt Pin-Zustände programmatisch
        
        Args:
            pin_states: Dict mit pin_name -> bool
        """
        for pin, state in pin_states.items():
            if pin in self.pin_checkboxes:
                self.pin_checkboxes[pin].setChecked(state)
    
    def save_settings(self):
        """Gibt Settings als Dict zurück zum Speichern"""
        return {
            'selected_pins': self.get_selected_pins(),
            'interval': self.get_interval()
        }
    
    def load_settings(self, settings):
        """Lädt Settings aus Dict"""
        if 'selected_pins' in settings:
            # Erst alle abwählen
            self.deselect_all()
            # Dann gespeicherte auswählen
            for pin in settings['selected_pins']:
                if pin in self.pin_checkboxes:
                    self.pin_checkboxes[pin].setChecked(True)
        
        if 'interval' in settings:
            self.interval_spin.setValue(settings['interval'])
