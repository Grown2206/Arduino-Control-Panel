from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt
from .pin_widget import PinWidget
import logging

logger = logging.getLogger("ArduinoPanel.PinTab")

class PinTab(QWidget):
    """Ein Tab zur Steuerung aller Arduino-Pins in einem sauberen Gitter-Layout."""
    command_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.pin_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        main_layout.addWidget(scroll_area)

        container = QWidget()
        grid_layout = QGridLayout(container)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(15, 15, 15, 15)
        
        pins_digital = [(f"D{i}", "D") for i in range(14)]
        pins_analog = [(f"A{i}", "A") for i in range(6)]
        all_pins = pins_digital + pins_analog
        
        # Pins im Gitter anordnen (optimierte Spaltenanzahl)
        num_columns = 5
        for idx, (pin_name, pin_type) in enumerate(all_pins):
            pin_widget = PinWidget(pin_name, pin_type)
            pin_widget.command_signal.connect(self.command_signal.emit)
            self.pin_widgets[pin_name] = pin_widget
            
            row, col = divmod(idx, num_columns)
            grid_layout.addWidget(pin_widget, row, col, Qt.AlignmentFlag.AlignTop)
        
        # Leeren Raum in der letzten Reihe auffüllen, falls vorhanden
        grid_layout.setRowStretch(grid_layout.rowCount(), 1)
        grid_layout.setColumnStretch(num_columns, 1)

        scroll_area.setWidget(container)

    def update_pin_value(self, pin_name, value):
        """Aktualisiert den Wert eines bestimmten Pin-Widgets."""
        if pin_name in self.pin_widgets:
            self.pin_widgets[pin_name].update_value(value)

    def get_pin_configs(self):
        """Sammelt die aktuellen Modus-Einstellungen aller Pins."""
        return {name: widget.get_mode() for name, widget in self.pin_widgets.items()}

    def set_pin_configs(self, pin_configs):
        """Setzt die Modus-Einstellungen aus einer geladenen Konfiguration.

        Args:
            pin_configs: Dict mit Pin-Namen und Modi {pin_name: mode}
        """
        # Validiere Input
        if not isinstance(pin_configs, dict):
            logger.error(f"pin_configs muss ein Dict sein, bekam: {type(pin_configs)}")
            return

        VALID_MODES = ["INPUT", "OUTPUT", "INPUT_PULLUP", "ANALOG_INPUT"]
        MODE_MAPPING = {
            "ANALOG_INPUT": "INPUT",  # Analoge Pins -> INPUT
            "INPUT": "INPUT",
            "OUTPUT": "OUTPUT",
            "INPUT_PULLUP": "INPUT_PULLUP"
        }

        for pin_name, mode in pin_configs.items():
            # Validiere Pin-Name
            if not isinstance(pin_name, str):
                logger.warning(f"Ungültiger Pin-Name Typ: {type(pin_name)}, überspringe")
                continue

            if pin_name not in self.pin_widgets:
                logger.debug(f"Pin {pin_name} nicht gefunden, überspringe")
                continue

            # Validiere Mode
            if not isinstance(mode, str):
                logger.warning(f"Ungültiger Mode-Typ für Pin {pin_name}: {type(mode)}, überspringe")
                continue

            if mode not in VALID_MODES:
                logger.warning(f"Ungültiger Mode '{mode}' für Pin {pin_name}, verwende INPUT")
                mode = "INPUT"
            else:
                # Mappe zu Arduino-kompatiblem Modus
                mode = MODE_MAPPING.get(mode, "INPUT")

            # Setze Mode
            try:
                self.pin_widgets[pin_name].mode_combo.setCurrentText(mode)
            except Exception as e:
                logger.error(f"Fehler beim Setzen von Mode für Pin {pin_name}: {e}")
