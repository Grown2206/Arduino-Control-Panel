# -*- coding: utf-8 -*-
"""
ui/calibration_wizard.py
Schritt-für-Schritt-Wizard für Sensor-Kalibrierung
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QGroupBox, QFormLayout, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from typing import Optional, List, Tuple
import time

try:
    from core.calibration_manager import CalibrationManager, CalibrationData
    CALIBRATION_AVAILABLE = True
except ImportError:
    CALIBRATION_AVAILABLE = False


class CalibrationWizard(QDialog):
    """
    Schritt-für-Schritt-Wizard für Sensor-Kalibrierung
    """

    # Signal wenn Kalibrierung abgeschlossen
    calibration_completed = pyqtSignal(str, object)  # sensor_id, CalibrationData

    def __init__(
        self,
        sensor_id: str,
        sensor_name: str = "",
        current_value_callback=None,  # Funktion die aktuellen Sensor-Wert liefert
        parent=None
    ):
        super().__init__(parent)

        if not CALIBRATION_AVAILABLE:
            QMessageBox.critical(self, "Fehler", "Calibration Manager nicht verfügbar")
            self.reject()
            return

        self.sensor_id = sensor_id
        self.sensor_name = sensor_name or sensor_id
        self.current_value_callback = current_value_callback
        self.calibration_manager = CalibrationManager()

        self.current_step = 0
        self.calibration_type = "two_point"  # Default
        self.measurement_points = []  # [(measured, reference), ...]
        self.current_measured_value = 0.0

        self.setWindowTitle(f"Kalibrierung: {self.sensor_name}")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self.setup_ui()
        self.show_step(0)

        # Timer für Live-Wert-Update
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_current_value)
        self.update_timer.start(500)  # Update alle 500ms

    def setup_ui(self):
        """Erstellt die UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"📐 Kalibrierungs-Wizard für {self.sensor_name}")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; padding: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(4)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Step Container (wird dynamisch gefüllt)
        self.step_container = QGroupBox()
        self.step_layout = QVBoxLayout(self.step_container)
        layout.addWidget(self.step_container)

        # Navigation Buttons
        nav_layout = QHBoxLayout()

        self.back_btn = QPushButton("◀ Zurück")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        nav_layout.addWidget(self.back_btn)

        nav_layout.addStretch()

        self.next_btn = QPushButton("Weiter ▶")
        self.next_btn.clicked.connect(self.go_next)
        nav_layout.addWidget(self.next_btn)

        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)
        nav_layout.addWidget(self.cancel_btn)

        layout.addLayout(nav_layout)

    def show_step(self, step: int):
        """Zeigt einen bestimmten Schritt an"""
        # Lösche vorherigen Inhalt
        while self.step_layout.count():
            item = self.step_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.current_step = step
        self.progress_bar.setValue(step)

        # Zeige entsprechenden Schritt
        if step == 0:
            self.show_step_intro()
        elif step == 1:
            self.show_step_type_selection()
        elif step == 2:
            self.show_step_measurement()
        elif step == 3:
            self.show_step_validation()
        elif step == 4:
            self.show_step_summary()

        # Update Navigation
        self.back_btn.setEnabled(step > 0)

        if step == 4:
            self.next_btn.setText("Abschließen")
        else:
            self.next_btn.setText("Weiter ▶")

    def show_step_intro(self):
        """Schritt 0: Einführung"""
        self.step_container.setTitle("Willkommen zum Kalibrierungs-Wizard")

        intro_text = QLabel(f"""
<h3>Kalibrierung für Sensor: {self.sensor_name}</h3>
<p>Dieser Wizard führt Sie durch den Kalibrierungsprozess.</p>

<h4>Was ist Kalibrierung?</h4>
<p>Bei der Kalibrierung werden die Sensor-Messwerte mit bekannten Referenzwerten verglichen,
um systematische Abweichungen zu korrigieren und die Messgenauigkeit zu verbessern.</p>

<h4>Vorbereitung:</h4>
<ul>
  <li>Stellen Sie sicher, dass der Sensor angeschlossen ist</li>
  <li>Halten Sie Referenzwerte bereit (z.B. kalibriertes Thermometer)</li>
  <li>Lassen Sie den Sensor ggf. stabilisieren</li>
</ul>

<p><b>Klicken Sie auf "Weiter", um fortzufahren.</b></p>
        """)
        intro_text.setWordWrap(True)
        self.step_layout.addWidget(intro_text)

    def show_step_type_selection(self):
        """Schritt 1: Kalibrierungs-Typ auswählen"""
        self.step_container.setTitle("Kalibrierungs-Typ wählen")

        info_label = QLabel("Wählen Sie die Art der Kalibrierung:")
        self.step_layout.addWidget(info_label)

        # Typ-Auswahl
        self.type_combo = QComboBox()
        self.type_combo.addItem("🎯 2-Punkt-Kalibrierung (empfohlen)", "two_point")
        self.type_combo.addItem("📏 Offset/Faktor-Kalibrierung (einfach)", "offset_factor")
        self.type_combo.addItem("📊 Multi-Point-Kalibrierung (präzise)", "multi_point")
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        self.step_layout.addWidget(self.type_combo)

        # Beschreibung
        self.type_description = QTextEdit()
        self.type_description.setReadOnly(True)
        self.type_description.setMaximumHeight(150)
        self.step_layout.addWidget(self.type_description)

        self.on_type_changed()  # Update Beschreibung

        self.step_layout.addStretch()

    def on_type_changed(self):
        """Update Beschreibung wenn Typ geändert wird"""
        cal_type = self.type_combo.currentData()

        descriptions = {
            "two_point": """
<b>2-Punkt-Kalibrierung:</b>
<p>Sie messen bei zwei bekannten Referenzwerten (z.B. Eis-Wasser = 0°C und kochendes Wasser = 100°C).
Daraus wird eine lineare Korrektur berechnet.</p>
<p><b>Vorteile:</b> Einfach, schnell, für die meisten Sensoren ausreichend<br>
<b>Geeignet für:</b> Temperatur, Luftfeuchtigkeit, Druck</p>
            """,
            "offset_factor": """
<b>Offset/Faktor-Kalibrierung:</b>
<p>Sie geben manuell einen Offset (Verschiebung) und Faktor (Multiplikator) ein.
Formel: kalibriert = (gemessen + offset) × faktor</p>
<p><b>Vorteile:</b> Sehr schnell, wenn Sie die Werte bereits kennen<br>
<b>Geeignet für:</b> Wenn Sie Offset/Faktor aus Datenblatt haben</p>
            """,
            "multi_point": """
<b>Multi-Point-Kalibrierung:</b>
<p>Sie messen bei 3 oder mehr Referenzwerten. Ein Polynom wird gefittet für höchste Präzision.</p>
<p><b>Vorteile:</b> Höchste Genauigkeit, korrigiert auch nicht-lineare Abweichungen<br>
<b>Geeignet für:</b> Hochpräzise Messungen, nicht-lineare Sensoren</p>
            """
        }

        self.type_description.setHtml(descriptions.get(cal_type, ""))

    def show_step_measurement(self):
        """Schritt 2: Messungen durchführen"""
        cal_type = self.type_combo.currentData()
        self.calibration_type = cal_type

        if cal_type == "offset_factor":
            self.show_step_offset_factor()
        elif cal_type == "two_point":
            self.show_step_two_point()
        elif cal_type == "multi_point":
            self.show_step_multi_point()

    def show_step_offset_factor(self):
        """Offset/Faktor manuelle Eingabe"""
        self.step_container.setTitle("Offset und Faktor eingeben")

        form_layout = QFormLayout()

        # Offset
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-10000, 10000)
        self.offset_spin.setDecimals(3)
        self.offset_spin.setValue(0.0)
        form_layout.addRow("Offset:", self.offset_spin)

        # Faktor
        self.factor_spin = QDoubleSpinBox()
        self.factor_spin.setRange(0.001, 1000)
        self.factor_spin.setDecimals(3)
        self.factor_spin.setValue(1.0)
        form_layout.addRow("Faktor:", self.factor_spin)

        self.step_layout.addLayout(form_layout)

        # Info
        info = QLabel("Formel: <b>kalibriert = (gemessen + offset) × faktor</b>")
        self.step_layout.addWidget(info)

        self.step_layout.addStretch()

    def show_step_two_point(self):
        """2-Punkt-Messung"""
        self.step_container.setTitle("2-Punkt-Messung durchführen")

        # Punkt 1
        point1_group = QGroupBox("📍 Messpunkt 1 (niedriger Wert)")
        point1_layout = QFormLayout(point1_group)

        self.current_value_1_label = QLabel("-- warte auf Daten --")
        self.current_value_1_label.setStyleSheet("font-size: 18px; color: #3498db; font-weight: bold;")
        point1_layout.addRow("Aktueller Messwert:", self.current_value_1_label)

        self.reference_value_1_spin = QDoubleSpinBox()
        self.reference_value_1_spin.setRange(-10000, 10000)
        self.reference_value_1_spin.setDecimals(2)
        point1_layout.addRow("Referenzwert:", self.reference_value_1_spin)

        self.capture_btn_1 = QPushButton("📸 Messwert erfassen")
        self.capture_btn_1.clicked.connect(lambda: self.capture_measurement(0))
        point1_layout.addRow(self.capture_btn_1)

        self.step_layout.addWidget(point1_group)

        # Punkt 2
        point2_group = QGroupBox("📍 Messpunkt 2 (hoher Wert)")
        point2_layout = QFormLayout(point2_group)

        self.current_value_2_label = QLabel("-- warte auf Daten --")
        self.current_value_2_label.setStyleSheet("font-size: 18px; color: #3498db; font-weight: bold;")
        point2_layout.addRow("Aktueller Messwert:", self.current_value_2_label)

        self.reference_value_2_spin = QDoubleSpinBox()
        self.reference_value_2_spin.setRange(-10000, 10000)
        self.reference_value_2_spin.setDecimals(2)
        point2_layout.addRow("Referenzwert:", self.reference_value_2_spin)

        self.capture_btn_2 = QPushButton("📸 Messwert erfassen")
        self.capture_btn_2.clicked.connect(lambda: self.capture_measurement(1))
        point2_layout.addRow(self.capture_btn_2)

        self.step_layout.addWidget(point2_group)

        # Status
        self.measurement_status = QLabel("Status: Kein Messpunkt erfasst")
        self.step_layout.addWidget(self.measurement_status)

        # Weiter-Button nur wenn beide Punkte erfasst
        self.next_btn.setEnabled(False)

    def show_step_multi_point(self):
        """Multi-Point-Messung"""
        self.step_container.setTitle("Multi-Point-Messung (min. 3 Punkte)")

        # Aktueller Wert
        current_group = QGroupBox("📊 Aktuelle Messung")
        current_layout = QFormLayout(current_group)

        self.current_value_multi_label = QLabel("-- warte auf Daten --")
        self.current_value_multi_label.setStyleSheet("font-size: 18px; color: #3498db; font-weight: bold;")
        current_layout.addRow("Aktueller Messwert:", self.current_value_multi_label)

        self.reference_value_multi_spin = QDoubleSpinBox()
        self.reference_value_multi_spin.setRange(-10000, 10000)
        self.reference_value_multi_spin.setDecimals(2)
        current_layout.addRow("Referenzwert:", self.reference_value_multi_spin)

        self.add_point_btn = QPushButton("➕ Messpunkt hinzufügen")
        self.add_point_btn.clicked.connect(self.add_multi_point)
        current_layout.addRow(self.add_point_btn)

        self.step_layout.addWidget(current_group)

        # Tabelle mit erfassten Punkten
        points_group = QGroupBox("Erfasste Messpunkte")
        points_layout = QVBoxLayout(points_group)

        self.points_table = QTableWidget()
        self.points_table.setColumnCount(3)
        self.points_table.setHorizontalHeaderLabels(["Gemessen", "Referenz", ""])
        self.points_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        points_layout.addWidget(self.points_table)

        self.step_layout.addWidget(points_group)

        # Status
        self.multi_point_status = QLabel("Status: Mindestens 3 Punkte benötigt")
        self.step_layout.addWidget(self.multi_point_status)

        self.next_btn.setEnabled(False)

    def show_step_validation(self):
        """Schritt 3: Validierung (optional)"""
        self.step_container.setTitle("Validierung (optional)")

        info = QLabel("Möchten Sie die Kalibrierung mit einem Testpunkt validieren?")
        self.step_layout.addWidget(info)

        # Validierungs-Optionen
        self.skip_validation_check = QCheckBox("Validierung überspringen")
        self.skip_validation_check.setChecked(True)
        self.skip_validation_check.toggled.connect(self.toggle_validation)
        self.step_layout.addWidget(self.skip_validation_check)

        # Validierungs-Gruppe
        self.validation_group = QGroupBox("Validierungs-Messung")
        validation_layout = QFormLayout(self.validation_group)

        self.validation_measured_spin = QDoubleSpinBox()
        self.validation_measured_spin.setRange(-10000, 10000)
        self.validation_measured_spin.setDecimals(2)
        validation_layout.addRow("Gemessener Wert:", self.validation_measured_spin)

        self.validation_expected_spin = QDoubleSpinBox()
        self.validation_expected_spin.setRange(-10000, 10000)
        self.validation_expected_spin.setDecimals(2)
        validation_layout.addRow("Erwarteter Wert:", self.validation_expected_spin)

        validate_btn = QPushButton("Testen")
        validate_btn.clicked.connect(self.run_validation)
        validation_layout.addRow(validate_btn)

        self.validation_result_label = QLabel("")
        validation_layout.addRow(self.validation_result_label)

        self.step_layout.addWidget(self.validation_group)
        self.validation_group.setEnabled(False)

        self.step_layout.addStretch()

    def toggle_validation(self, checked):
        """Toggle Validierungs-Gruppe"""
        self.validation_group.setEnabled(not checked)

    def run_validation(self):
        """Führt Validierung durch"""
        # Erstelle temporäre Kalibrierung
        temp_cal = self.create_calibration_data()

        measured = self.validation_measured_spin.value()
        expected = self.validation_expected_spin.value()

        calibrated = temp_cal.apply(measured)
        error = abs(calibrated - expected)

        if expected != 0:
            rel_error = (error / abs(expected)) * 100
        else:
            rel_error = 0

        # Zeige Ergebnis
        if rel_error < 1:
            result = f"✅ Exzellent: Fehler = {error:.2f} ({rel_error:.2f}%)"
            color = "#27ae60"
        elif rel_error < 5:
            result = f"✅ Gut: Fehler = {error:.2f} ({rel_error:.2f}%)"
            color = "#f39c12"
        else:
            result = f"⚠️ Fehler zu groß: {error:.2f} ({rel_error:.2f}%)"
            color = "#e74c3c"

        self.validation_result_label.setText(result)
        self.validation_result_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def show_step_summary(self):
        """Schritt 4: Zusammenfassung"""
        self.step_container.setTitle("✅ Kalibrierung abgeschlossen")

        # Erstelle Kalibrierung
        cal_data = self.create_calibration_data()

        # Zusammenfassung
        summary_text = f"""
<h3>Kalibrierung erfolgreich erstellt!</h3>

<table border="1" cellpadding="5">
<tr><td><b>Sensor:</b></td><td>{self.sensor_name}</td></tr>
<tr><td><b>Typ:</b></td><td>{cal_data.calibration_type}</td></tr>
<tr><td><b>Qualität:</b></td><td>{cal_data.quality_score:.3f}</td></tr>
"""

        if cal_data.calibration_type == "offset_factor":
            summary_text += f"""
<tr><td><b>Offset:</b></td><td>{cal_data.offset:.3f}</td></tr>
<tr><td><b>Faktor:</b></td><td>{cal_data.factor:.3f}</td></tr>
"""
        elif cal_data.calibration_type in ["two_point", "multi_point"]:
            summary_text += f"""
<tr><td><b>Messpunkte:</b></td><td>{len(cal_data.reference_points)}</td></tr>
"""

        summary_text += """
</table>

<p><b>Die Kalibrierung wird automatisch auf alle zukünftigen Messungen angewendet.</b></p>
        """

        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        self.step_layout.addWidget(summary_label)

        # Aktivieren?
        self.activate_check = QCheckBox("Kalibrierung aktivieren")
        self.activate_check.setChecked(True)
        self.step_layout.addWidget(self.activate_check)

        self.step_layout.addStretch()

    def update_current_value(self):
        """Update den aktuellen Sensor-Wert"""
        if not self.current_value_callback:
            return

        try:
            value = self.current_value_callback(self.sensor_id)
            self.current_measured_value = value

            # Update Labels je nach Schritt
            if self.current_step == 2:
                if self.calibration_type == "two_point":
                    self.current_value_1_label.setText(f"{value:.2f}")
                    self.current_value_2_label.setText(f"{value:.2f}")
                elif self.calibration_type == "multi_point":
                    self.current_value_multi_label.setText(f"{value:.2f}")

        except Exception as e:
            print(f"Fehler beim Abrufen des Sensor-Werts: {e}")

    def capture_measurement(self, point_index: int):
        """Erfasst Messpunkt"""
        measured = self.current_measured_value

        if point_index == 0:
            reference = self.reference_value_1_spin.value()
            self.capture_btn_1.setText(f"✅ Erfasst: {measured:.2f}")
            self.capture_btn_1.setEnabled(False)
        else:
            reference = self.reference_value_2_spin.value()
            self.capture_btn_2.setText(f"✅ Erfasst: {measured:.2f}")
            self.capture_btn_2.setEnabled(False)

        # Speichere Punkt
        if len(self.measurement_points) <= point_index:
            self.measurement_points.append((measured, reference))
        else:
            self.measurement_points[point_index] = (measured, reference)

        # Update Status
        if len(self.measurement_points) >= 2:
            self.measurement_status.setText("✅ Beide Messpunkte erfasst!")
            self.measurement_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.next_btn.setEnabled(True)
        else:
            self.measurement_status.setText(f"Status: {len(self.measurement_points)}/2 Messpunkte erfasst")

    def add_multi_point(self):
        """Fügt Messpunkt zu Multi-Point-Liste hinzu"""
        measured = self.current_measured_value
        reference = self.reference_value_multi_spin.value()

        self.measurement_points.append((measured, reference))

        # Füge zu Tabelle hinzu
        row = self.points_table.rowCount()
        self.points_table.insertRow(row)

        self.points_table.setItem(row, 0, QTableWidgetItem(f"{measured:.2f}"))
        self.points_table.setItem(row, 1, QTableWidgetItem(f"{reference:.2f}"))

        # Delete Button
        delete_btn = QPushButton("🗑️")
        delete_btn.clicked.connect(lambda: self.remove_multi_point(row))
        self.points_table.setCellWidget(row, 2, delete_btn)

        # Update Status
        count = len(self.measurement_points)
        if count >= 3:
            self.multi_point_status.setText(f"✅ {count} Messpunkte erfasst (bereit)")
            self.multi_point_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.next_btn.setEnabled(True)
        else:
            self.multi_point_status.setText(f"Status: {count}/3 Messpunkte erfasst")
            self.next_btn.setEnabled(False)

    def remove_multi_point(self, row: int):
        """Entfernt Messpunkt"""
        if row < len(self.measurement_points):
            self.measurement_points.pop(row)
            self.points_table.removeRow(row)

            # Update Status
            count = len(self.measurement_points)
            if count >= 3:
                self.multi_point_status.setText(f"✅ {count} Messpunkte erfasst (bereit)")
                self.next_btn.setEnabled(True)
            else:
                self.multi_point_status.setText(f"Status: {count}/3 Messpunkte erfasst")
                self.next_btn.setEnabled(False)

    def create_calibration_data(self) -> CalibrationData:
        """Erstellt CalibrationData aus gesammelten Daten"""
        if self.calibration_type == "offset_factor":
            cal = CalibrationData(
                sensor_id=self.sensor_id,
                calibration_type="offset_factor",
                offset=self.offset_spin.value(),
                factor=self.factor_spin.value()
            )

        elif self.calibration_type == "two_point":
            cal = CalibrationData(
                sensor_id=self.sensor_id,
                calibration_type="two_point",
                reference_points=self.measurement_points
            )

        elif self.calibration_type == "multi_point":
            cal = CalibrationData(
                sensor_id=self.sensor_id,
                calibration_type="multi_point",
                reference_points=self.measurement_points
            )

        cal.calculate_quality()
        return cal

    def go_next(self):
        """Nächster Schritt"""
        if self.current_step < 4:
            self.show_step(self.current_step + 1)
        else:
            # Abschließen
            self.finish_calibration()

    def go_back(self):
        """Vorheriger Schritt"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def finish_calibration(self):
        """Schließt Kalibrierung ab"""
        cal_data = self.create_calibration_data()
        cal_data.is_active = self.activate_check.isChecked()

        # Speichere Kalibrierung
        if self.calibration_manager.add_calibration(cal_data):
            self.calibration_completed.emit(self.sensor_id, cal_data)
            self.accept()
        else:
            QMessageBox.critical(self, "Fehler", "Kalibrierung konnte nicht gespeichert werden")

    def closeEvent(self, event):
        """Stop Timer beim Schließen"""
        self.update_timer.stop()
        super().closeEvent(event)
