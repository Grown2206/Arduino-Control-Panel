# -*- coding: utf-8 -*-
"""
Ein Tab zur Steuerung eines 4-Kanal-Relais-Moduls, der das neue
visuelle Widget verwendet.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal

# Importiert das neue visuelle Widget
from .relay_visual_widget import VisualRelayChannelWidget

class RelayControlTab(QWidget):
    """Ein Tab-Widget zur Steuerung mehrerer Relais-Kanäle."""
    command_signal = pyqtSignal(str)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.channels = []
        self.init_ui()

    def init_ui(self):
        """Initialisiert die UI-Komponenten."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Verwendet ein horizontales Layout, um die Relais zu zentrieren
        center_layout = QHBoxLayout()
        main_layout.addLayout(center_layout)
        
        center_layout.addStretch()

        # Erstellt und fügt die Kanal-Widgets hinzu
        for i in range(1, 5):
            # Verwendet das neue VisualRelayChannelWidget
            channel_widget = VisualRelayChannelWidget(i, self.config_manager)
            channel_widget.command_signal.connect(self.command_signal)
            self.channels.append(channel_widget)
            center_layout.addWidget(channel_widget)
        
        center_layout.addStretch()
        main_layout.addStretch()

    def update_pin_state(self, pin, state):
        """Öffentliche Methode, um einen Kanal basierend auf dem Pin-Zustand zu aktualisieren."""
        for channel in self.channels:
            if channel.current_pin == pin:
                channel.update_pin_state(pin, state)
                break
    
    def save_settings(self):
        """Speichert die Einstellungen für alle Kanäle."""
        for channel in self.channels:
            channel.save_settings()

    def load_settings(self):
        """Lädt die Einstellungen für alle Kanäle."""
        for channel in self.channels:
            channel.load_settings()

