# -*- coding: utf-8 -*-
"""
Pin Management Tab - Konsolidiert Pin Steuerung, Übersicht und Heatmap
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import pyqtSignal

from .pin_tab import PinTab
from .pin_overview_widget import PinOverviewWidget
from .pin_heatmap_widget import PinHeatmapWidget


class PinManagementTab(QWidget):
    """Kombinierter Tab für alle Pin-bezogenen Funktionen"""

    command_signal = pyqtSignal(dict)

    def __init__(self, pin_tracker=None, parent=None):
        super().__init__(parent)
        self.pin_tracker = pin_tracker
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Subtabs
        self.subtabs = QTabWidget()

        # 1. Pin Steuerung
        self.pin_control = PinTab()
        self.pin_control.command_signal.connect(self.command_signal.emit)
        self.subtabs.addTab(self.pin_control, "🎛️ Steuerung")

        # 2. Pin Übersicht
        self.pin_overview = PinOverviewWidget()
        self.subtabs.addTab(self.pin_overview, "📊 Übersicht")

        # 3. Pin Heatmap
        if self.pin_tracker:
            self.pin_heatmap = PinHeatmapWidget(self.pin_tracker)
            self.subtabs.addTab(self.pin_heatmap, "🔥 Heatmap")
        else:
            self.pin_heatmap = None

        layout.addWidget(self.subtabs)

    def update_pin_value(self, pin_name, value):
        """Aktualisiert Pin-Wert in allen Subtabs"""
        self.pin_control.update_pin_value(pin_name, value)
        self.pin_overview.update_pin_value(pin_name, value)

    def update_pin_mode(self, pin, mode):
        """Aktualisiert Pin-Modus"""
        self.pin_overview.update_pin_mode(pin, mode)

    def get_pin_configs(self):
        """Gibt Pin-Konfiguration zurück"""
        return self.pin_control.get_pin_configs()

    def set_pin_configs(self, pin_configs):
        """Setzt Pin-Konfiguration"""
        self.pin_control.set_pin_configs(pin_configs)
