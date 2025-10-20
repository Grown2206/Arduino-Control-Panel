# -*- coding: utf-8 -*-
"""
Ein visuell ansprechendes Relais-Kanal-Widget, das von einem echten
Relais-Modul inspiriert ist. Dieses Widget verwendet QPainter für ein
benutzerdefiniertes Erscheinungsbild.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF

class VisualRelayChannelWidget(QFrame):
    """Ein benutzerdefiniertes Widget, das einen einzelnen Relais-Kanal darstellt."""
    command_signal = pyqtSignal(str)

    def __init__(self, channel_num, config_manager, parent=None):
        super().__init__(parent)
        self.channel_num = channel_num
        self.config_manager = config_manager
        self.config_key = f"relay_ch{channel_num}_pin"
        
        self.current_pin = None
        self.is_on = False  # True = NO, False = NC
        
        self.setMinimumSize(140, 280)
        self.setMaximumSize(140, 280)
        
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialisiert die UI-Komponenten (hier nur die Pin-Auswahl)."""
        layout = QVBoxLayout(self)
        # Steuerelemente unten positionieren
        layout.setContentsMargins(10, 210, 10, 10) 

        pin_layout = QHBoxLayout()
        pin_layout.addWidget(QLabel("Pin:"))
        
        self.pin_combo = QComboBox()
        self.pin_combo.addItems([f"D{i}" for i in range(2, 14)]) 
        pin_layout.addWidget(self.pin_combo)
        layout.addLayout(pin_layout)

        self.pin_combo.currentIndexChanged.connect(self._pin_changed)

    def paintEvent(self, event):
        """Benutzerdefiniertes Zeichnen zur Visualisierung des Relais."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Haupt-Hintergrund
        painter.fillRect(self.rect(), QColor("#3c3c3c"))

        # --- Blauen Relais-Körper zeichnen ---
        relay_rect = QRectF(20, 20, 100, 60)
        painter.setBrush(QColor("#0077c2"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(relay_rect, 5, 5)
        
        # --- Text auf Relais zeichnen ---
        painter.setPen(QColor(Qt.GlobalColor.white))
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(relay_rect.adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignLeft, "SONGLE\nSRD-12VDC-SL-C")

        # --- ON/OFF Button zeichnen ---
        button_rect = QRectF(35, 95, 70, 70)
        center = button_rect.center()
        
        if self.is_on:
            base_color = QColor("#2ecc71") # Grün
            text = "NO"
        else:
            base_color = QColor("#e74c3c") # Rot
            text = "NC"
        
        # Äußerer Schein
        glow_color = base_color.lighter(150)
        glow_color.setAlpha(100)
        painter.setBrush(glow_color)
        painter.drawEllipse(button_rect.adjusted(-3, -3, 3, 3))

        # Button-Farbverlauf
        gradient = QLinearGradient(center, QPointF(center.x(), button_rect.bottom()))
        gradient.setColorAt(0, base_color.lighter(120))
        gradient.setColorAt(1, base_color.darker(120))
        painter.setBrush(gradient)
        painter.setPen(QPen(base_color.darker(150), 2))
        painter.drawEllipse(button_rect)
        
        # Button-Text
        painter.setPen(Qt.GlobalColor.white)
        font.setPixelSize(20)
        painter.setFont(font)
        painter.drawText(button_rect, Qt.AlignmentFlag.AlignCenter, text)

        # --- Anschlüsse zeichnen ---
        font.setPixelSize(12)
        painter.setFont(font)
        terminals = {"NO": 25, "COM": 70, "NC": 115}
        for label, x_pos in terminals.items():
            painter.drawText(QRectF(x_pos - 15, 175, 30, 20), Qt.AlignmentFlag.AlignCenter, label)
            painter.setBrush(QColor("#2c2c2c"))
            painter.setPen(QPen(QColor("#1c1c1c"), 2))
            painter.drawEllipse(QPointF(x_pos, 200), 8, 8)

    def mousePressEvent(self, event):
        """Schaltet den Zustand um, wenn der Button-Bereich geklickt wird."""
        button_rect = QRectF(35, 95, 70, 70)
        # KORREKTUR: Konvertiere QPoint zu QPointF für den `contains` Aufruf
        if button_rect.contains(QPointF(event.pos())):
            self._toggle_relay()
        else:
            super().mousePressEvent(event)

    def _toggle_relay(self):
        if self.current_pin is None: return
        self.is_on = not self.is_on
        command_str = f"digital_write {self.current_pin} {1 if self.is_on else 0}"
        self.command_signal.emit(command_str)
        self.update() # Neuzeichnen auslösen

    def _pin_changed(self):
        self.current_pin = int(self.pin_combo.currentText().replace("D", ""))
        self.save_settings()
        if self.current_pin is not None:
            command_str = f"pin_mode {self.current_pin} 1" # 1 for OUTPUT
            self.command_signal.emit(command_str)
            # Zustand bei Pin-Wechsel zurücksetzen
            if self.is_on:
                self._toggle_relay()

    def update_pin_state(self, pin, state):
        if pin == self.current_pin:
            is_on = bool(state)
            if self.is_on != is_on:
                self.is_on = is_on
                self.update()

    def save_settings(self):
        if self.current_pin is not None:
            self.config_manager.set(self.config_key, self.current_pin)

    def load_settings(self):
        pin = self.config_manager.get(self.config_key)
        if pin is not None:
            index = self.pin_combo.findText(f"D{pin}")
            if index >= 0:
                self.pin_combo.setCurrentIndex(index)
        else:
            if self.pin_combo.count() > 0:
                self.pin_combo.setCurrentIndex(0)
        
        self._pin_changed()

