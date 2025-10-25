# -*- coding: utf-8 -*-
"""
Dashboard Builder - Widget Library
Vordefinierte Dashboard-Widgets
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
import math
from .base_widget import DashboardWidgetBase, DashboardWidgetFactory


class ValueDisplayWidget(DashboardWidgetBase):
    """Einfaches Wert-Anzeige-Widget"""

    def __init__(self, parent=None):
        super().__init__(title="Wert", parent=parent)
        self.widget_type = "value_display"
        self.current_value = 0
        self.unit = ""

        # Value Label
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: #3498db;"
        )
        self.content_layout.addWidget(self.value_label)

        # Unit Label
        self.unit_label = QLabel(self.unit)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unit_label.setStyleSheet("font-size: 14px; color: #95a5a6;")
        self.content_layout.addWidget(self.unit_label)

    def update_data(self, data):
        """Aktualisiert angezeigten Wert"""
        if isinstance(data, dict):
            self.current_value = data.get('value', 0)
            self.unit = data.get('unit', '')
        else:
            self.current_value = data

        self.value_label.setText(f"{self.current_value:.1f}")
        self.unit_label.setText(self.unit)

    def to_html(self):
        return f"""
        <div class="value-widget" style="text-align: center; padding: 10px;">
            <h3>{self.widget_title}</h3>
            <div style="font-size: 36px; color: #3498db; font-weight: bold;">
                {self.current_value:.1f}
            </div>
            <div style="font-size: 14px; color: #95a5a6;">
                {self.unit}
            </div>
        </div>
        """


class GaugeWidget(DashboardWidgetBase):
    """Gauge/Tachometer-Widget"""

    def __init__(self, parent=None):
        super().__init__(title="Gauge", parent=parent)
        self.widget_type = "gauge"
        self.current_value = 0
        self.min_value = 0
        self.max_value = 100
        self.warning_threshold = 75
        self.critical_threshold = 90

        self.setMinimumSize(150, 150)

    def paintEvent(self, event):
        """Zeichnet das Gauge"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Berechne Dimensionen
        width = self.width()
        height = self.height() - 40  # Platz für Titel
        center_x = width // 2
        center_y = height - 20
        radius = min(width, height) // 2 - 20

        # Zeichne Hintergrund-Arc
        painter.setPen(QPen(QColor(60, 60, 60), 8, Qt.PenStyle.SolidLine))
        painter.drawArc(
            center_x - radius, center_y - radius, radius * 2, radius * 2,
            -45 * 16, -270 * 16
        )

        # Berechne Wert-Prozent
        value_percent = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        value_percent = max(0, min(1, value_percent))

        # Farbe basierend auf Schwellwerten
        if self.current_value >= self.critical_threshold:
            color = QColor(231, 76, 60)  # Rot
        elif self.current_value >= self.warning_threshold:
            color = QColor(243, 156, 18)  # Orange
        else:
            color = QColor(39, 174, 96)  # Grün

        # Zeichne Wert-Arc
        painter.setPen(QPen(color, 8, Qt.PenStyle.SolidLine))
        span_angle = int(-270 * value_percent * 16)
        painter.drawArc(
            center_x - radius, center_y - radius, radius * 2, radius * 2,
            -45 * 16, span_angle
        )

        # Zeichne Wert-Text
        painter.setPen(QPen(QColor(224, 224, 224)))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_text = f"{self.current_value:.1f}"
        text_rect = painter.fontMetrics().boundingRect(value_text)
        painter.drawText(
            center_x - text_rect.width() // 2,
            center_y - 10,
            value_text
        )

        # Zeichne Min/Max Labels
        painter.setFont(QFont("Arial", 10))
        painter.drawText(10, height - 5, f"{self.min_value}")
        max_text = f"{self.max_value}"
        max_width = painter.fontMetrics().horizontalAdvance(max_text)
        painter.drawText(width - max_width - 10, height - 5, max_text)

    def update_data(self, data):
        """Aktualisiert Gauge-Wert"""
        if isinstance(data, dict):
            self.current_value = data.get('value', 0)
            self.min_value = data.get('min', 0)
            self.max_value = data.get('max', 100)
        else:
            self.current_value = data

        self.update()

    def to_html(self):
        value_percent = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        value_percent = max(0, min(1, value_percent)) * 100

        return f"""
        <div class="gauge-widget" style="text-align: center;">
            <h3>{self.widget_title}</h3>
            <div style="font-size: 32px; color: #3498db;">
                {self.current_value:.1f}
            </div>
            <div style="width: 200px; height: 20px; background: #333; border-radius: 10px; margin: 10px auto;">
                <div style="width: {value_percent}%; height: 100%; background: #27ae60; border-radius: 10px;"></div>
            </div>
        </div>
        """


class LEDWidget(DashboardWidgetBase):
    """LED-Indikator-Widget"""

    def __init__(self, parent=None):
        super().__init__(title="LED", parent=parent)
        self.widget_type = "led"
        self.is_on = False
        self.color_on = QColor(39, 174, 96)  # Grün
        self.color_off = QColor(60, 60, 60)

        self.setMinimumSize(100, 100)
        self.setMaximumSize(200, 200)

    def paintEvent(self, event):
        """Zeichnet die LED"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Berechne LED-Position
        width = self.width()
        height = self.height() - 40
        center_x = width // 2
        center_y = height // 2 + 20
        radius = min(width, height) // 3

        # LED-Farbe
        color = self.color_on if self.is_on else self.color_off

        # Zeichne äußeren Ring
        painter.setPen(QPen(color.darker(150), 3))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # Glow-Effekt wenn an
        if self.is_on:
            painter.setPen(QPen(color.lighter(150), 8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                center_x - radius - 5, center_y - radius - 5,
                radius * 2 + 10, radius * 2 + 10
            )

        # Status-Text
        painter.setPen(QPen(QColor(224, 224, 224)))
        painter.setFont(QFont("Arial", 10))
        status_text = "ON" if self.is_on else "OFF"
        text_rect = painter.fontMetrics().boundingRect(status_text)
        painter.drawText(
            center_x - text_rect.width() // 2,
            height + 35,
            status_text
        )

    def update_data(self, data):
        """Aktualisiert LED-Status"""
        if isinstance(data, dict):
            self.is_on = data.get('value', False)
        else:
            self.is_on = bool(data)

        self.update()

    def to_html(self):
        color = "#27ae60" if self.is_on else "#3c3c3c"
        status = "ON" if self.is_on else "OFF"

        return f"""
        <div class="led-widget" style="text-align: center;">
            <h3>{self.widget_title}</h3>
            <div style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: {color};
                margin: 10px auto;
                box-shadow: 0 0 20px {color};
            "></div>
            <div>{status}</div>
        </div>
        """


class ButtonWidget(DashboardWidgetBase):
    """Button-Widget zum Auslösen von Aktionen"""

    clicked = pyqtSignal(str)  # widget_id

    def __init__(self, parent=None):
        super().__init__(title="Button", parent=parent)
        self.widget_type = "button"
        self.button_text = "Click Me"
        self.button_command = None

        # Button
        self.button = QPushButton(self.button_text)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.button.clicked.connect(self.on_button_clicked)
        self.content_layout.addWidget(self.button)

    def on_button_clicked(self):
        """Button wurde geklickt"""
        self.clicked.emit(self.widget_id)

    def set_config(self, config):
        """Setzt Button-Konfiguration"""
        super().set_config(config)

        if 'button_text' in config.get('config', {}):
            self.button_text = config['config']['button_text']
            self.button.setText(self.button_text)

        if 'button_command' in config.get('config', {}):
            self.button_command = config['config']['button_command']

    def to_html(self):
        return f"""
        <div class="button-widget" style="text-align: center;">
            <h3>{self.widget_title}</h3>
            <button style="
                background: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px 30px;
                font-size: 14px;
                cursor: pointer;
            ">{self.button_text}</button>
        </div>
        """


class ProgressBarWidget(DashboardWidgetBase):
    """Progress Bar Widget"""

    def __init__(self, parent=None):
        super().__init__(title="Progress", parent=parent)
        self.widget_type = "progress_bar"
        self.current_value = 0
        self.max_value = 100

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
        self.content_layout.addWidget(self.progress_bar)

    def update_data(self, data):
        """Aktualisiert Progress-Wert"""
        if isinstance(data, dict):
            self.current_value = data.get('value', 0)
            self.max_value = data.get('max', 100)
        else:
            self.current_value = data

        self.progress_bar.setMaximum(int(self.max_value))
        self.progress_bar.setValue(int(self.current_value))

    def to_html(self):
        percent = (self.current_value / self.max_value * 100) if self.max_value > 0 else 0

        return f"""
        <div class="progress-widget">
            <h3>{self.widget_title}</h3>
            <div style="
                width: 100%;
                height: 30px;
                background: #2b2b2b;
                border: 2px solid #555;
                border-radius: 5px;
                overflow: hidden;
            ">
                <div style="
                    width: {percent}%;
                    height: 100%;
                    background: #27ae60;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                ">{percent:.0f}%</div>
            </div>
        </div>
        """


class LabelWidget(DashboardWidgetBase):
    """Einfaches Text-Label-Widget"""

    def __init__(self, parent=None):
        super().__init__(title="Label", parent=parent)
        self.widget_type = "label"
        self.label_text = "Text"

        # Label
        self.text_label = QLabel(self.label_text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            font-size: 14px;
            color: #e0e0e0;
            padding: 10px;
        """)
        self.content_layout.addWidget(self.text_label)

    def update_data(self, data):
        """Aktualisiert Label-Text"""
        if isinstance(data, dict):
            self.label_text = str(data.get('text', ''))
        else:
            self.label_text = str(data)

        self.text_label.setText(self.label_text)

    def set_config(self, config):
        """Setzt Label-Konfiguration"""
        super().set_config(config)

        if 'label_text' in config.get('config', {}):
            self.label_text = config['config']['label_text']
            self.text_label.setText(self.label_text)

    def to_html(self):
        return f"""
        <div class="label-widget" style="text-align: center; padding: 10px;">
            <h3>{self.widget_title}</h3>
            <div style="font-size: 14px;">{self.label_text}</div>
        </div>
        """


# Registriere alle Widget-Typen
DashboardWidgetFactory.register_widget_type("value_display", ValueDisplayWidget)
DashboardWidgetFactory.register_widget_type("gauge", GaugeWidget)
DashboardWidgetFactory.register_widget_type("led", LEDWidget)
DashboardWidgetFactory.register_widget_type("button", ButtonWidget)
DashboardWidgetFactory.register_widget_type("progress_bar", ProgressBarWidget)
DashboardWidgetFactory.register_widget_type("label", LabelWidget)
