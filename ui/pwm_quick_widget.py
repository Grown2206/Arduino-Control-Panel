# -*- coding: utf-8 -*-
"""
ui/pwm_quick_widget.py
Kompaktes PWM-Widget für das Dashboard
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QGroupBox, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal

class PWMQuickWidget(QWidget):
    """Schnellzugriff auf PWM-Pins"""
    command_signal = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pwm_pins = [3, 5, 6, 9, 10, 11]
        self.sliders = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Schnellzugriff auf 3 wichtigste PWM-Pins
        for pin in [9, 10, 11]:
            pin_layout = QHBoxLayout()
            
            label = QLabel(f"D{pin}")
            label.setStyleSheet("font-weight: bold; min-width: 30px;")
            pin_layout.addWidget(label)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(0)
            slider.valueChanged.connect(lambda v, p=pin: self.pwm_changed(p, v))
            pin_layout.addWidget(slider)
            
            value_label = QLabel("0")
            value_label.setFixedWidth(35)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            pin_layout.addWidget(value_label)
            
            self.sliders[pin] = {'slider': slider, 'label': value_label}
            
            layout.addLayout(pin_layout)
        
        # Preset-Buttons
        preset_layout = QHBoxLayout()
        
        presets = [("🌑", 0), ("◑", 128), ("🌕", 255)]
        for text, value in presets:
            btn = QPushButton(text)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, v=value: self.set_all(v))
            preset_layout.addWidget(btn)
        
        layout.addLayout(preset_layout)
        layout.addStretch()
    
    def pwm_changed(self, pin, value):
        """PWM-Wert wurde geändert"""
        self.sliders[pin]['label'].setText(str(value))
        
        self.command_signal.emit({
            'command': 'analog_write',
            'pin': f'D{pin}',
            'value': value
        })
    
    def set_all(self, value):
        """Setzt alle PWM-Pins auf einen Wert"""
        for pin, widgets in self.sliders.items():
            widgets['slider'].setValue(value)