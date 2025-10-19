import uuid
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPalette, QColor

class PinWidget(QFrame):
    """Ein modernes Widget zur Darstellung und Steuerung eines einzelnen Arduino-Pins."""
    command_signal = pyqtSignal(dict)
    
    def __init__(self, pin_name, pin_type):
        super().__init__()
        self.pin_name = pin_name
        self.pin_type = pin_type
        self.last_value = None

        # --- Style-Konfiguration ---
        self.setObjectName("PinWidgetFrame")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(180, 220)
        self.setMaximumSize(180, 220)
        
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # --- Header mit Pin-Name und LED ---
        header_layout = QHBoxLayout()
        pin_label = QLabel(self.pin_name)
        pin_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0;")
        self.led = QLabel("●")
        self.led.setStyleSheet("font-size: 24px; color: #555;") # Startfarbe grau
        header_layout.addWidget(pin_label)
        header_layout.addStretch()
        header_layout.addWidget(self.led)
        main_layout.addLayout(header_layout)
        
        # --- Wert-Anzeige ---
        self.value_label = QLabel("-")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setObjectName("ValueLabel")
        main_layout.addWidget(self.value_label)

        # --- Modus-Auswahl ---
        self.mode_combo = QComboBox()
        if self.pin_type == "A":
            self.mode_combo.addItems(["ANALOG_INPUT"])
        else:
            self.mode_combo.addItems(["INPUT", "OUTPUT", "INPUT_PULLUP"])
        self.mode_combo.currentTextChanged.connect(self.set_mode)
        main_layout.addWidget(self.mode_combo)

        # --- Steuerungs-Buttons ---
        btn_layout = QHBoxLayout()
        self.high_btn = QPushButton("HIGH")
        self.high_btn.clicked.connect(lambda: self.digital_write(1))
        
        self.low_btn = QPushButton("LOW")
        self.low_btn.clicked.connect(lambda: self.digital_write(0))

        btn_layout.addWidget(self.high_btn)
        btn_layout.addWidget(self.low_btn)
        main_layout.addLayout(btn_layout)
        
        self.read_btn = QPushButton("READ")
        self.read_btn.clicked.connect(self.read_pin)
        main_layout.addWidget(self.read_btn)
        
        self.update_buttons()
        self.update_value(0 if self.pin_type == 'D' else '-') # Initialzustand setzen

    def update_buttons(self):
        is_output = self.mode_combo.currentText() == "OUTPUT"
        is_input = not is_output
        self.high_btn.setEnabled(is_output)
        self.low_btn.setEnabled(is_output)
        self.read_btn.setEnabled(is_input)

    def set_mode(self):
        self.command_signal.emit({
            "id": str(uuid.uuid4()), "command": "pin_mode",
            "pin": self.pin_name, "mode": self.mode_combo.currentText()
        })
        self.update_buttons()

    def digital_write(self, value):
        self.command_signal.emit({
            "id": str(uuid.uuid4()), "command": "digital_write",
            "pin": self.pin_name, "value": value
        })

    def read_pin(self):
        cmd = "analog_read" if self.pin_type == "A" else "digital_read"
        self.command_signal.emit({
            "id": str(uuid.uuid4()), "command": cmd, "pin": self.pin_name
        })

    def update_value(self, value):
        if self.last_value == value and value != '-': return
        self.last_value = value

        val_color = "#95a5a6"

        if self.pin_type == 'D':
            state_text = "HIGH" if value else "LOW"
            led_color = "#27ae60" if value else "#555"
            val_color = "#2ecc71" if value else "#95a5a6"
            self.value_label.setText(state_text)
        else: # Analog
            self.value_label.setText(str(value))
            if value == '-':
                led_color = "#555"
            elif value > 768: 
                led_color, val_color = "#e74c3c", "#e67e22"
            elif value > 256: 
                led_color, val_color = "#f39c12", "#f1c40f"
            else: 
                led_color, val_color = "#3498db", "#5dade2"
        
        self.led.setStyleSheet(f"font-size: 24px; color: {led_color};")
        self.value_label.setStyleSheet(f"""
            #ValueLabel {{
                font-size: 28px; font-weight: bold; color: {val_color};
                background-color: #262A2E; border-radius: 5px;
                padding: 10px; min-height: 40px;
            }}
        """)

    def get_mode(self):
        return self.mode_combo.currentText()

