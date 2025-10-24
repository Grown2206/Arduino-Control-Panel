# -*- coding: utf-8 -*-
"""
Pin Heatmap Widget - Visualisiert Pin-Nutzung als Heatmap
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QGridLayout, QScrollArea,
                             QComboBox, QFrame, QToolTip)
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
import time


class PinHeatmapCell(QFrame):
    """Einzelne Zelle in der Heatmap"""

    def __init__(self, pin_name: str, parent=None):
        super().__init__(parent)
        self.pin_name = pin_name
        self.intensity = 0.0  # 0.0 - 1.0
        self.access_count = 0
        self.current_state = None
        self.pin_type = "digital"
        self.last_used_ago = None
        self.error_count = 0

        self.setMinimumSize(80, 60)
        self.setMaximumSize(100, 80)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Pin-Name
        self.name_label = QLabel(pin_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.name_label)

        # Access-Count
        self.count_label = QLabel("0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.count_label)

        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(self.status_label)

        self.update_appearance()

    def set_intensity(self, intensity: float, access_count: int, current_state=None,
                     pin_type="digital", last_used_ago=None, error_count=0):
        """Aktualisiert die Intensität und Daten"""
        self.intensity = max(0.0, min(1.0, intensity))
        self.access_count = access_count
        self.current_state = current_state
        self.pin_type = pin_type
        self.last_used_ago = last_used_ago
        self.error_count = error_count

        self.count_label.setText(str(access_count))

        # Status-Text
        if error_count > 0:
            self.status_label.setText(f"⚠️ {error_count} Fehler")
        elif current_state == "HIGH":
            self.status_label.setText("🟢 AKTIV")
        elif current_state == "LOW":
            self.status_label.setText("⚫ LOW")
        elif access_count == 0:
            self.status_label.setText("○ Ungenutzt")
        else:
            self.status_label.setText("✓ Verwendet")

        self.update_appearance()
        self.update_tooltip()

    def update_appearance(self):
        """Aktualisiert die visuelle Darstellung basierend auf Intensität"""
        if self.error_count > 0:
            # Fehler: Rot
            bg_color = QColor(231, 76, 60)  # Red
            text_color = "white"
        elif self.intensity == 0.0:
            # Nicht genutzt: Grau
            bg_color = QColor(52, 58, 64)
            text_color = "#95a5a6"
        else:
            # Heatmap: Grün -> Gelb -> Orange -> Rot
            if self.intensity < 0.25:
                # Grün
                r = int(39 + (243 - 39) * (self.intensity / 0.25))
                g = int(174 + (156 - 174) * (self.intensity / 0.25))
                b = int(96 + (18 - 96) * (self.intensity / 0.25))
            elif self.intensity < 0.5:
                # Gelb
                t = (self.intensity - 0.25) / 0.25
                r = int(243 + (241 - 243) * t)
                g = int(156 + (196 - 156) * t)
                b = int(18 + (15 - 18) * t)
            elif self.intensity < 0.75:
                # Orange
                t = (self.intensity - 0.5) / 0.25
                r = int(241 + (230 - 241) * t)
                g = int(196 + (126 - 196) * t)
                b = int(15 + (34 - 15) * t)
            else:
                # Rot
                t = (self.intensity - 0.75) / 0.25
                r = int(230 + (192 - 230) * t)
                g = int(126 + (57 - 126) * t)
                b = int(34 + (43 - 34) * t)

            bg_color = QColor(r, g, b)
            text_color = "white" if self.intensity > 0.3 else "#e0e0e0"

        # Border-Farbe für aktive Pins
        if self.current_state == "HIGH":
            border_color = "#27ae60"
            border_width = 3
        else:
            border_color = "#555"
            border_width = 1

        self.setStyleSheet(f"""
            PinHeatmapCell {{
                background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});
                border: {border_width}px solid {border_color};
                border-radius: 6px;
            }}
        """)

        self.name_label.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {text_color};")
        self.count_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {text_color};")
        self.status_label.setStyleSheet(f"font-size: 8px; color: {text_color};")

    def update_tooltip(self):
        """Aktualisiert den Tooltip mit detaillierten Informationen"""
        tooltip_parts = [
            f"<b>{self.pin_name}</b> ({self.pin_type})",
            f"Zugriffe: {self.access_count}",
            f"Intensität: {self.intensity * 100:.1f}%"
        ]

        if self.current_state:
            tooltip_parts.append(f"Status: {self.current_state}")

        if self.last_used_ago is not None:
            if self.last_used_ago < 1:
                tooltip_parts.append(f"Zuletzt: vor < 1s")
            elif self.last_used_ago < 60:
                tooltip_parts.append(f"Zuletzt: vor {int(self.last_used_ago)}s")
            else:
                tooltip_parts.append(f"Zuletzt: vor {int(self.last_used_ago / 60)}min")

        if self.error_count > 0:
            tooltip_parts.append(f"⚠️ Fehler: {self.error_count}")

        self.setToolTip("<br>".join(tooltip_parts))


class PinHeatmapWidget(QWidget):
    """Widget zur Visualisierung der Pin-Nutzung als Heatmap"""

    def __init__(self, pin_tracker=None, parent=None):
        super().__init__(parent)
        self.pin_tracker = pin_tracker
        self.cells = {}
        self.board_type = "Arduino Uno"
        self.setup_ui()

        # Auto-Update Timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_heatmap)
        self.update_timer.start(1000)  # Update jede Sekunde

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()

        title = QLabel("<h2>📊 Pin-Nutzung Heatmap</h2>")
        header.addWidget(title)

        header.addStretch()

        # Board-Selector
        header.addWidget(QLabel("Board:"))
        self.board_combo = QComboBox()
        self.board_combo.addItems([
            "Arduino Uno", "Arduino Mega", "Arduino Nano",
            "ESP32", "Custom"
        ])
        self.board_combo.currentTextChanged.connect(self.on_board_changed)
        header.addWidget(self.board_combo)

        # Refresh Button
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self.update_heatmap)
        header.addWidget(refresh_btn)

        # Reset Button
        reset_btn = QPushButton("🗑️ Zurücksetzen")
        reset_btn.clicked.connect(self.reset_tracker)
        header.addWidget(reset_btn)

        layout.addLayout(header)

        # Statistiken
        stats_group = QGroupBox("Statistiken")
        stats_layout = QHBoxLayout(stats_group)

        self.total_accesses_label = QLabel("Gesamt: 0")
        self.total_accesses_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.total_accesses_label)

        self.active_pins_label = QLabel("Aktive Pins: 0")
        self.active_pins_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.active_pins_label)

        self.unused_pins_label = QLabel("Ungenutzt: 0")
        self.unused_pins_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.unused_pins_label)

        self.most_used_label = QLabel("Meist genutzt: -")
        self.most_used_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        stats_layout.addWidget(self.most_used_label)

        stats_layout.addStretch()
        layout.addWidget(stats_group)

        # Legende
        legend_group = QGroupBox("Legende")
        legend_layout = QHBoxLayout(legend_group)

        legend_items = [
            ("Ungenutzt", QColor(52, 58, 64)),
            ("Niedrig", QColor(39, 174, 96)),
            ("Mittel", QColor(243, 156, 18)),
            ("Hoch", QColor(230, 126, 34)),
            ("Sehr Hoch", QColor(192, 57, 43)),
            ("Fehler", QColor(231, 76, 60))
        ]

        for label, color in legend_items:
            item_layout = QHBoxLayout()
            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #555; border-radius: 3px;")
            item_layout.addWidget(color_box)
            item_layout.addWidget(QLabel(label))
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        layout.addWidget(legend_group)

        # Scroll Area für Heatmap
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #555; background-color: #2b2b2b; }")

        # Heatmap Container
        self.heatmap_container = QWidget()
        self.heatmap_layout = QGridLayout(self.heatmap_container)
        self.heatmap_layout.setSpacing(8)
        self.heatmap_layout.setContentsMargins(10, 10, 10, 10)

        scroll.setWidget(self.heatmap_container)
        layout.addWidget(scroll)

        # Initialisiere Heatmap
        self.create_heatmap()

    def create_heatmap(self):
        """Erstellt die Heatmap-Zellen"""
        # Lösche alte Zellen
        for cell in self.cells.values():
            cell.deleteLater()
        self.cells.clear()

        if not self.pin_tracker:
            return

        # Hole alle Pins für das Board
        all_pins = self.pin_tracker.get_all_pins(self.board_type)

        # Trenne Digital und Analog Pins
        digital_pins = [p for p in all_pins if p.startswith("D")]
        analog_pins = [p for p in all_pins if p.startswith("A")]

        # Digital Pins Section
        row = 0
        self.heatmap_layout.addWidget(QLabel("<b>Digital Pins</b>"), row, 0, 1, 10)
        row += 1

        # Erstelle Digital Pin Zellen
        col = 0
        for pin in digital_pins:
            cell = PinHeatmapCell(pin, self.heatmap_container)
            self.cells[pin] = cell
            self.heatmap_layout.addWidget(cell, row, col)
            col += 1
            if col >= 10:  # 10 Zellen pro Reihe
                col = 0
                row += 1

        # Analog Pins Section
        row += 1
        self.heatmap_layout.addWidget(QLabel("<b>Analog Pins</b>"), row, 0, 1, 10)
        row += 1

        # Erstelle Analog Pin Zellen
        col = 0
        for pin in analog_pins:
            cell = PinHeatmapCell(pin, self.heatmap_container)
            self.cells[pin] = cell
            self.heatmap_layout.addWidget(cell, row, col)
            col += 1
            if col >= 10:
                col = 0
                row += 1

        self.update_heatmap()

    def update_heatmap(self):
        """Aktualisiert die Heatmap mit aktuellen Daten"""
        if not self.pin_tracker:
            return

        # Hole Heatmap-Daten
        heatmap_data = self.pin_tracker.get_heatmap_data()
        summary = self.pin_tracker.get_pin_usage_summary()

        # Update Zellen
        for pin_name, cell in self.cells.items():
            intensity = heatmap_data.get(pin_name, 0.0)
            pin_data = summary.get(pin_name, {})

            cell.set_intensity(
                intensity=intensity,
                access_count=pin_data.get('access_count', 0),
                current_state=pin_data.get('current_state'),
                pin_type=pin_data.get('pin_type', 'digital'),
                last_used_ago=pin_data.get('last_used_ago'),
                error_count=pin_data.get('error_count', 0)
            )

        # Update Statistiken
        total_accesses = sum(data.get('access_count', 0) for data in summary.values())
        active_pins = len([p for p, d in summary.items() if d.get('access_count', 0) > 0])
        unused_pins = len(self.pin_tracker.get_unused_pins(self.board_type))

        self.total_accesses_label.setText(f"Gesamt: {total_accesses}")
        self.active_pins_label.setText(f"Aktive Pins: {active_pins}")
        self.unused_pins_label.setText(f"Ungenutzt: {unused_pins}")

        # Meist genutzter Pin
        if summary:
            most_used = max(summary.items(), key=lambda x: x[1].get('access_count', 0))
            self.most_used_label.setText(f"Meist genutzt: {most_used[0]} ({most_used[1]['access_count']})")
        else:
            self.most_used_label.setText("Meist genutzt: -")

    def on_board_changed(self, board_type: str):
        """Behandelt Änderungen des Board-Typs"""
        self.board_type = board_type
        self.create_heatmap()

    def reset_tracker(self):
        """Setzt den Tracker zurück"""
        if self.pin_tracker:
            self.pin_tracker.reset()
            self.update_heatmap()

    def set_pin_tracker(self, tracker):
        """Setzt den Pin-Tracker"""
        self.pin_tracker = tracker
        self.create_heatmap()
