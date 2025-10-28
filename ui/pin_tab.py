from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QScrollArea,
                             QPushButton, QHBoxLayout, QFileDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime
from .pin_widget import PinWidget
import logging
import csv

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
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Export-Button am oberen Rand
        export_layout = QHBoxLayout()
        export_btn = QPushButton("📄 CSV-Export: Pin-Status")
        export_btn.setToolTip("Exportiert den aktuellen Status aller Pins als CSV-Datei")
        export_btn.clicked.connect(self.export_pin_status_csv)
        export_btn.setMaximumWidth(250)
        export_layout.addWidget(export_btn)
        export_layout.addStretch()
        main_layout.addLayout(export_layout)

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

    def export_pin_status_csv(self):
        """Exportiert den aktuellen Status aller Pins als CSV-Datei."""
        timestamp = QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')
        default_filename = f"pin_status_{timestamp}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Pin-Status als CSV exportieren",
            default_filename,
            "CSV-Dateien (*.csv);;Alle Dateien (*)"
        )

        if not file_path:
            return  # User hat abgebrochen

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')

                # Header
                writer.writerow(['=== ARDUINO PIN STATUS EXPORT ==='])
                writer.writerow(['Exportiert am', QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')])
                writer.writerow([])
                writer.writerow(['Pin', 'Typ', 'Modus', 'Wert', 'Status-Icon'])

                # Daten für jeden Pin
                for pin_name, widget in self.pin_widgets.items():
                    pin_type = widget.pin_type
                    mode = widget.get_mode()
                    value = widget.last_value if widget.last_value is not None else '-'

                    # Bestimme den Status-Text und Icon
                    if pin_type == 'D':
                        value_str = "HIGH" if value else "LOW" if value != '-' else '-'
                        icon = "🟢" if value else "🔴" if value != '-' else "⚫"
                    else:  # Analog
                        value_str = str(value)
                        if value == '-':
                            icon = "⚫"
                        elif value > 768:
                            icon = "🔴"
                        elif value > 256:
                            icon = "🟡"
                        else:
                            icon = "🟢"

                    type_str = "Digital" if pin_type == 'D' else "Analog"

                    writer.writerow([pin_name, type_str, mode, value_str, icon])

            QMessageBox.information(
                self,
                "Export erfolgreich",
                f"Pin-Status wurde erfolgreich exportiert:\n{file_path}"
            )
            logger.info(f"Pin-Status exportiert nach: {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export fehlgeschlagen",
                f"Fehler beim Exportieren:\n{str(e)}"
            )
            logger.error(f"CSV-Export fehlgeschlagen: {e}")
