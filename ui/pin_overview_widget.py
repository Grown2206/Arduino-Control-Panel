from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox, QHBoxLayout
from PyQt6.QtCore import Qt

class PinIndicator(QWidget):
    """Eine kompakte visuelle Anzeige für den Zustand eines einzelnen Pins."""
    def __init__(self, pin_name, is_analog=False):
        super().__init__()
        self.pin_name = pin_name
        self.is_analog = is_analog
        self.current_value = 0
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(2)
        
        name_label = QLabel(self.pin_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        self.led = QLabel("●")
        self.led.setStyleSheet("font-size: 24px; color: #34495e;") # Dunkelgrau für "aus"
        self.led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.led)
        
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
        self.setMinimumWidth(80)
        self.setMaximumWidth(80)
        
    def set_value(self, value):
        self.current_value = value
        
        if self.is_analog:
            self.value_label.setText(str(value))
            # Farbverlauf für Analogwerte
            if value > 768: color = "#e74c3c"  # Rot (hoch)
            elif value > 256: color = "#f39c12" # Orange (mittel)
            else: color = "#3498db" # Blau (niedrig)
        else: # Digital
            self.value_label.setText("HIGH" if value else "LOW")
            color = "#27ae60" if value else "#34495e" # Grün (an) / Grau (aus)
            
        self.led.setStyleSheet(f"font-size: 24px; color: {color};")


class PinOverviewWidget(QWidget):
    """Ein Tab, der den Live-Zustand aller Pins in einer kompakten Übersicht anzeigt."""
    def __init__(self):
        super().__init__()
        self.pin_indicators = {}
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        digital_group = QGroupBox("🔌 Digitale Pins (D0-D13)")
        digital_layout = QGridLayout(digital_group)
        
        for i in range(14):
            pin_name = f"D{i}"
            indicator = PinIndicator(pin_name)
            self.pin_indicators[pin_name] = indicator
            row, col = divmod(i, 7) # 2 Reihen mit 7 Pins
            digital_layout.addWidget(indicator, row, col)
            
        main_layout.addWidget(digital_group)
        
        analog_group = QGroupBox("📊 Analoge Pins (A0-A5)")
        analog_layout = QHBoxLayout(analog_group)
        
        for i in range(6):
            pin_name = f"A{i}"
            indicator = PinIndicator(pin_name, is_analog=True)
            self.pin_indicators[pin_name] = indicator
            analog_layout.addWidget(indicator)
            
        main_layout.addWidget(analog_group)
        main_layout.addStretch()
        
    def update_pin_state(self, pin_name, value):
        """Aktualisiert den Zustand eines einzelnen Pin-Indikators."""
        if pin_name in self.pin_indicators:
            self.pin_indicators[pin_name].set_value(value)

