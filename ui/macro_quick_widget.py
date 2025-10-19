# -*- coding: utf-8 -*-
"""
ui/macro_quick_widget.py
Kompaktes Makro-Widget für das Dashboard
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal

class MacroQuickWidget(QWidget):
    """Schnellzugriff auf gespeicherte Makros"""
    play_macro_signal = pyqtSignal(str)  # macro_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.macros = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Info
        info = QLabel("Makros:")
        info.setStyleSheet("font-weight: bold;")
        layout.addWidget(info)
        
        # Makro-Liste
        self.macro_list = QListWidget()
        self.macro_list.itemDoubleClicked.connect(self.on_macro_clicked)
        layout.addWidget(self.macro_list)
        
        # Play-Button
        play_btn = QPushButton("▶️ Abspielen")
        play_btn.clicked.connect(self.play_selected)
        layout.addWidget(play_btn)
    
    def update_macros(self, macros):
        """Aktualisiert die Makro-Liste"""
        self.macros = macros
        self.macro_list.clear()
        for name in macros.keys():
            self.macro_list.addItem(f"🤖 {name}")
    
    def on_macro_clicked(self, item):
        """Makro wurde doppelt geklickt"""
        self.play_selected()
    
    def play_selected(self):
        """Spielt das ausgewählte Makro ab"""
        item = self.macro_list.currentItem()
        if item:
            name = item.text().replace("🤖 ", "")
            self.play_macro_signal.emit(name)
