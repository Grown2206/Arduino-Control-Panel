# -*- coding: utf-8 -*-
"""
Board Setup Tab - Konsolidiert Board Config, Profile und 3D View
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import pyqtSignal

from .board_config_tab import BoardConfigTab
from .hardware_profile_tab import HardwareProfileTab
from .board_3d_visualizer import Board3DVisualizerTab


class BoardSetupTab(QWidget):
    """Kombinierter Tab für alle Board-bezogenen Funktionen"""

    apply_config_signal = pyqtSignal(dict)
    load_profile_signal = pyqtSignal(dict)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Subtabs
        self.subtabs = QTabWidget()

        # 1. Board Konfiguration
        self.board_config = BoardConfigTab(self.config_manager)
        self.board_config.apply_config_signal.connect(self.apply_config_signal.emit)
        self.subtabs.addTab(self.board_config, "🛠️ Konfiguration")

        # 2. Hardware Profile
        self.hardware_profile = HardwareProfileTab()
        self.hardware_profile.load_profile_signal.connect(self.load_profile_signal.emit)
        self.subtabs.addTab(self.hardware_profile, "💾 Profile")

        # 3. 3D Board Visualizer
        self.board_3d = Board3DVisualizerTab()
        self.subtabs.addTab(self.board_3d, "🎮 3D Ansicht")

        layout.addWidget(self.subtabs)

    def update_pin_from_data(self, pin_name: str, state: str = None, value: int = None):
        """Aktualisiert 3D Board mit Pin-Daten"""
        self.board_3d.update_pin_from_data(pin_name, state, value)
