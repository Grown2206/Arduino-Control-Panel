from PyQt6.QtWidgets import QWidget, QGridLayout, QGroupBox, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

class RelayQuickWidget(QGroupBox):
    """Ein kompaktes Widget für das Dashboard zum schnellen Schalten von Relais."""
    
    command_signal = pyqtSignal(str)
    
    def __init__(self, config_manager, parent=None):
        super().__init__("Relais Schnellzugriff", parent)
        self.config_manager = config_manager
        self.buttons = {}
        self.pin_map = {}
        
        self.init_ui()
        # load_pin_map wird von main.py aufgerufen, nachdem die Konfig geladen wurde
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche."""
        self.grid_layout = QGridLayout(self)
        for i in range(1, 5):
            label = QLabel(f"CH {i}:")
            button = QPushButton("NC") 
            button.setCheckable(True)
            button.clicked.connect(lambda state, ch=i: self.toggle_relay(ch, state))
            
            self.buttons[i] = button
            self.grid_layout.addWidget(label, i-1, 0)
            self.grid_layout.addWidget(button, i-1, 1)
        self.update_styles()

    def load_pin_map(self):
        """Lädt die Pin-Konfiguration aus dem Config-Manager."""
        self.pin_map.clear()
        for i in range(1, 5):
            pin = self.config_manager.get(f"relay_ch{i}_pin")
            if pin:
                self.pin_map[i] = int(pin)
            else:
                print(f"Warnung: Kein Pin für Relais CH{i} im QuickWidget gefunden.")
        
        self.init_pin_modes()

    def init_pin_modes(self):
        """Setzt alle konfigurierten Pins auf OUTPUT."""
        for pin in self.pin_map.values():
            self.command_signal.emit(f"pin_mode {pin} 1")

    def toggle_relay(self, channel, state):
        """Sendet einen Befehl zum Schalten eines Relais."""
        pin = self.pin_map.get(channel)
        if pin:
            self.command_signal.emit(f"digital_write {pin} {1 if state else 0}")
            self.update_styles()
    
    def update_pin_state(self, pin, state):
        """Aktualisiert den Button-Zustand basierend auf externen Pin-Daten."""
        for channel, mapped_pin in self.pin_map.items():
            if mapped_pin == pin:
                self.buttons[channel].setChecked(bool(state))
                self.update_styles()
                break
                
    def update_styles(self):
        """Aktualisiert den Button-Text und die Farbe basierend auf seinem Zustand."""
        for channel, button in self.buttons.items():
            if button.isChecked():
                button.setText("NO")
                button.setStyleSheet("background-color: #2ecc71; color: white;")
            else:
                button.setText("NC")
                button.setStyleSheet("background-color: #e74c3c; color: white;")

