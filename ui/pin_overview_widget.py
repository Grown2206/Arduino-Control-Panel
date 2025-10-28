from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox,
                             QHBoxLayout, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QDateTime
import csv
import logging

logger = logging.getLogger("ArduinoPanel.PinOverview")

class PinIndicator(QWidget):
    """Eine kompakte visuelle Anzeige für den Zustand eines einzelnen Pins."""
    def __init__(self, pin_name, is_analog=False):
        super().__init__()
        self.pin_name = pin_name
        self.is_analog = is_analog
        self.current_value = 0
        self.current_mode = "INPUT" if is_analog else "INPUT"  # NEU: Pin-Modus tracken
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(2)

        name_label = QLabel(self.pin_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # NEU: Modus-Anzeige
        self.mode_label = QLabel("IN")
        self.mode_label.setStyleSheet("font-size: 8px; color: #95a5a6; background-color: #2c3e50; padding: 2px; border-radius: 3px;")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_label)

        # NEU: Emoji-basierte Status-Icons 🟢🔴🟡⚫
        self.led = QLabel("⚫")
        self.led.setStyleSheet("font-size: 28px;")  # Größer für bessere Sichtbarkeit
        self.led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.led)

        self.value_label = QLabel("0")
        self.value_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        self.setMinimumWidth(90)  # Etwas breiter für Modus-Label
        self.setMaximumWidth(90)
        
    def set_value(self, value):
        """NEU: Aktualisiert Wert mit Emoji-Icons 🟢🔴🟡⚫"""
        self.current_value = value

        if self.is_analog:
            self.value_label.setText(str(value))
            # Emoji-Icons für Analogwerte
            if value > 768:
                icon = "🔴"  # Rot (hoch)
            elif value > 256:
                icon = "🟡"  # Gelb (mittel)
            else:
                icon = "🟢"  # Grün (niedrig)
        else:  # Digital
            self.value_label.setText("HIGH" if value else "LOW")
            icon = "🟢" if value else "⚫"  # Grün (an) / Schwarz (aus)

        self.led.setText(icon)

    def set_mode(self, mode):
        """NEU: Setzt den Pin-Modus und aktualisiert die Anzeige"""
        self.current_mode = mode
        mode_display = {
            "INPUT": "IN",
            "OUTPUT": "OUT",
            "INPUT_PULLUP": "PULL",
            "ANALOG_INPUT": "AIN"
        }.get(mode, "IN")
        self.mode_label.setText(mode_display)


class PinOverviewWidget(QWidget):
    """Ein Tab, der den Live-Zustand aller Pins in einer kompakten Übersicht anzeigt."""
    def __init__(self):
        super().__init__()
        self.pin_indicators = {}
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Export-Button am oberen Rand
        export_layout = QHBoxLayout()
        export_btn = QPushButton("📄 CSV-Export: Pin-Übersicht")
        export_btn.setToolTip("Exportiert die Pin-Übersicht als CSV-Datei")
        export_btn.clicked.connect(self.export_overview_csv)
        export_btn.setMaximumWidth(250)
        export_layout.addWidget(export_btn)
        export_layout.addStretch()
        main_layout.addLayout(export_layout)

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

    def update_pin_mode(self, pin_name, mode):
        """NEU: Aktualisiert den Modus eines einzelnen Pin-Indikators."""
        if pin_name in self.pin_indicators:
            self.pin_indicators[pin_name].set_mode(mode)

    def export_overview_csv(self):
        """Exportiert die Pin-Übersicht als CSV-Datei."""
        timestamp = QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')
        default_filename = f"pin_overview_{timestamp}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Pin-Übersicht als CSV exportieren",
            default_filename,
            "CSV-Dateien (*.csv);;Alle Dateien (*)"
        )

        if not file_path:
            return  # User hat abgebrochen

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')

                # Header
                writer.writerow(['=== ARDUINO PIN ÜBERSICHT EXPORT ==='])
                writer.writerow(['Exportiert am', QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')])
                writer.writerow([])
                writer.writerow(['Pin', 'Typ', 'Modus', 'Wert', 'Status-Icon'])

                # Digitale Pins
                for i in range(14):
                    pin_name = f"D{i}"
                    if pin_name in self.pin_indicators:
                        indicator = self.pin_indicators[pin_name]
                        value = indicator.current_value
                        mode = indicator.current_mode

                        value_str = "HIGH" if value else "LOW"
                        icon = "🟢" if value else "⚫"

                        writer.writerow([pin_name, "Digital", mode, value_str, icon])

                # Analoge Pins
                for i in range(6):
                    pin_name = f"A{i}"
                    if pin_name in self.pin_indicators:
                        indicator = self.pin_indicators[pin_name]
                        value = indicator.current_value
                        mode = indicator.current_mode

                        # Icon basierend auf Analogwert
                        if value > 768:
                            icon = "🔴"
                        elif value > 256:
                            icon = "🟡"
                        else:
                            icon = "🟢"

                        writer.writerow([pin_name, "Analog", mode, str(value), icon])

            QMessageBox.information(
                self,
                "Export erfolgreich",
                f"Pin-Übersicht wurde erfolgreich exportiert:\n{file_path}"
            )
            logger.info(f"Pin-Übersicht exportiert nach: {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export fehlgeschlagen",
                f"Fehler beim Exportieren:\n{str(e)}"
            )
            logger.error(f"CSV-Export fehlgeschlagen: {e}")

