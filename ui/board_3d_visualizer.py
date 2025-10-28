# -*- coding: utf-8 -*-
"""
3D Board Visualizer - Isometric 3D View
Interaktive 3D-Ansicht des Arduino-Boards
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QGroupBox
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QPolygonF, QFont
import math
from typing import Dict, Tuple, List


class Point3D:
    """3D Punkt"""
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def rotate_x(self, angle: float):
        """Rotation um X-Achse"""
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        y = self.y * cos_a - self.z * sin_a
        z = self.y * sin_a + self.z * cos_a
        return Point3D(self.x, y, z)

    def rotate_y(self, angle: float):
        """Rotation um Y-Achse"""
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        x = self.x * cos_a + self.z * sin_a
        z = -self.x * sin_a + self.z * cos_a
        return Point3D(x, self.y, z)

    def rotate_z(self, angle: float):
        """Rotation um Z-Achse"""
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        x = self.x * cos_a - self.y * sin_a
        y = self.x * sin_a + self.y * cos_a
        return Point3D(x, y, self.z)

    def project(self, scale: float, offset_x: float, offset_y: float) -> QPointF:
        """Isometrische Projektion auf 2D"""
        # Isometrische Projektion
        iso_x = (self.x - self.y) * math.cos(math.radians(30))
        iso_y = (self.x + self.y) * math.sin(math.radians(30)) - self.z

        return QPointF(
            iso_x * scale + offset_x,
            iso_y * scale + offset_y
        )


class Pin3D:
    """3D Pin-Darstellung"""
    def __init__(self, name: str, position: Point3D, pin_type: str = "digital"):
        self.name = name
        self.position = position
        self.pin_type = pin_type
        self.state = "LOW"
        self.value = 0
        self.is_active = False

    def get_color(self) -> QColor:
        """Gibt Farbe basierend auf Status zurück"""
        if self.pin_type == "digital":
            if self.state == "HIGH":
                return QColor(39, 174, 96)  # Grün
            else:
                return QColor(60, 60, 60)  # Dunkelgrau
        else:  # analog
            # Gradient von Blau zu Rot basierend auf Wert
            intensity = self.value / 1023.0 if self.value <= 1023 else 1.0
            r = int(52 + (231 - 52) * intensity)
            g = int(152 - 152 * intensity)
            b = int(219 - 176 * intensity)
            return QColor(r, g, b)


class Board3DModel:
    """3D-Modell des Arduino-Boards"""

    def __init__(self, board_type: str = "Arduino Uno"):
        self.board_type = board_type
        self.rotation_x = 20
        self.rotation_y = 45
        self.rotation_z = 0
        self.scale = 3.0
        self.pins: Dict[str, Pin3D] = {}

        # Erstelle Board-Geometrie
        self.create_board_geometry()
        self.create_pins()

    def create_board_geometry(self):
        """Erstellt Board-Geometrie"""
        # Arduino Uno Dimensionen (vereinfacht in mm)
        self.board_width = 68.6
        self.board_length = 53.4
        self.board_height = 2.0

        # Board-Vertices (Ecken)
        self.board_vertices = [
            Point3D(0, 0, 0),
            Point3D(self.board_width, 0, 0),
            Point3D(self.board_width, self.board_length, 0),
            Point3D(0, self.board_length, 0),
            Point3D(0, 0, self.board_height),
            Point3D(self.board_width, 0, self.board_height),
            Point3D(self.board_width, self.board_length, self.board_height),
            Point3D(0, self.board_length, self.board_height),
        ]

        # USB-Connector
        self.usb_vertices = [
            Point3D(-8, 22, 2),
            Point3D(0, 22, 2),
            Point3D(0, 35, 2),
            Point3D(-8, 35, 2),
            Point3D(-8, 22, 8),
            Point3D(0, 22, 8),
            Point3D(0, 35, 8),
            Point3D(-8, 35, 8),
        ]

        # Power Jack
        self.power_vertices = [
            Point3D(-8, 4, 2),
            Point3D(0, 4, 2),
            Point3D(0, 14, 2),
            Point3D(-8, 14, 2),
            Point3D(-8, 4, 10),
            Point3D(0, 4, 10),
            Point3D(0, 14, 10),
            Point3D(-8, 14, 10),
        ]

    def create_pins(self):
        """Erstellt Pins"""
        # Digital Pins (rechte Seite)
        for i in range(14):
            x = self.board_width + 2
            y = 10 + i * 3
            z = self.board_height
            self.pins[f"D{i}"] = Pin3D(f"D{i}", Point3D(x, y, z), "digital")

        # Analog Pins (linke Seite)
        for i in range(6):
            x = -2
            y = 10 + i * 3
            z = self.board_height
            self.pins[f"A{i}"] = Pin3D(f"A{i}", Point3D(x, y, z), "analog")

    def rotate(self, dx: float, dy: float):
        """Rotiert das Board"""
        self.rotation_y += dx * 0.5
        self.rotation_x += dy * 0.5

        # Begrenze Rotation
        self.rotation_x = max(-90, min(90, self.rotation_x))

    def zoom(self, delta: float):
        """Zoomt das Board"""
        self.scale += delta * 0.1
        self.scale = max(0.5, min(10.0, self.scale))

    def project_vertices(self, vertices: List[Point3D], center_x: float, center_y: float) -> List[QPointF]:
        """Projiziert Vertices auf 2D"""
        projected = []

        for vertex in vertices:
            # Rotiere
            p = vertex.rotate_x(self.rotation_x)
            p = p.rotate_y(self.rotation_y)
            p = p.rotate_z(self.rotation_z)

            # Projiziere
            projected.append(p.project(self.scale, center_x, center_y))

        return projected

    def update_pin_state(self, pin_name: str, state: str = None, value: int = None):
        """Aktualisiert Pin-Status"""
        if pin_name in self.pins:
            pin = self.pins[pin_name]
            if state is not None:
                pin.state = state
            if value is not None:
                pin.value = value
            pin.is_active = True


class Board3DWidget(QWidget):
    """3D Board Visualisierungs-Widget"""

    pin_clicked = pyqtSignal(str)  # pin_name

    def __init__(self, parent=None):
        super().__init__(parent)

        self.board = Board3DModel()
        self.dragging = False
        self.last_mouse_pos = None

        # Animation Timer
        self.auto_rotate = False
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)

        self.setMinimumSize(600, 500)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        """Zeichnet das 3D Board"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Hintergrund
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        # Center
        center_x = self.width() // 2
        center_y = self.height() // 2

        # Zeichne Board
        self.draw_board(painter, center_x, center_y)

        # Zeichne USB/Power
        self.draw_connectors(painter, center_x, center_y)

        # Zeichne Pins
        self.draw_pins(painter, center_x, center_y)

        # Zeichne Info
        self.draw_info(painter)

    def draw_board(self, painter: QPainter, center_x: float, center_y: float):
        """Zeichnet das Board"""
        # Projiziere Board-Vertices
        projected = self.board.project_vertices(self.board.board_vertices, center_x, center_y)

        # Zeichne Seiten des Boards
        faces = [
            [0, 1, 5, 4],  # Front
            [1, 2, 6, 5],  # Right
            [2, 3, 7, 6],  # Back
            [3, 0, 4, 7],  # Left
            [4, 5, 6, 7],  # Top
            [0, 1, 2, 3],  # Bottom
        ]

        face_colors = [
            QColor(0, 128, 255, 180),  # Front - Blau
            QColor(0, 100, 200, 180),  # Right
            QColor(0, 80, 160, 180),   # Back
            QColor(0, 90, 180, 180),   # Left
            QColor(0, 120, 240, 200),  # Top - Hell
            QColor(0, 60, 120, 150),   # Bottom - Dunkel
        ]

        for face, color in zip(faces, face_colors):
            polygon = QPolygonF([projected[i] for i in face])

            # Gradient für Tiefeneffekt
            gradient = QLinearGradient(polygon.boundingRect().topLeft(), polygon.boundingRect().bottomRight())
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color.darker(120))

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.drawPolygon(polygon)

    def draw_connectors(self, painter: QPainter, center_x: float, center_y: float):
        """Zeichnet USB und Power-Connector"""
        # USB
        usb_projected = self.board.project_vertices(self.board.usb_vertices, center_x, center_y)
        usb_faces = [[0, 1, 5, 4], [1, 2, 6, 5], [4, 5, 6, 7]]

        for face in usb_faces:
            polygon = QPolygonF([usb_projected[i] for i in face])
            painter.setBrush(QColor(180, 180, 180))
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawPolygon(polygon)

        # Power
        power_projected = self.board.project_vertices(self.board.power_vertices, center_x, center_y)
        power_faces = [[0, 1, 5, 4], [1, 2, 6, 5], [4, 5, 6, 7]]

        for face in power_faces:
            polygon = QPolygonF([power_projected[i] for i in face])
            painter.setBrush(QColor(50, 50, 50))
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            painter.drawPolygon(polygon)

    def draw_pins(self, painter: QPainter, center_x: float, center_y: float):
        """Zeichnet Pins mit LED-Effekt"""
        for pin_name, pin in self.board.pins.items():
            # Rotiere und projiziere Pin-Position
            p = pin.position.rotate_x(self.board.rotation_x)
            p = p.rotate_y(self.board.rotation_y)
            p = p.rotate_z(self.board.rotation_z)
            pos = p.project(self.board.scale, center_x, center_y)

            # Pin-Farbe
            pin_color = pin.get_color()

            # Zeichne Pin-Body (kleines Rechteck)
            pin_size = 8
            painter.setBrush(QColor(100, 100, 100))
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.drawRect(QRectF(pos.x() - pin_size/2, pos.y() - pin_size/2, pin_size, pin_size))

            # Zeichne LED-Indikator
            led_size = 12
            if pin.state == "HIGH" or pin.value > 100:
                # Glow-Effekt für aktive Pins
                gradient = QRadialGradient(pos, led_size)
                gradient.setColorAt(0, pin_color.lighter(150))
                gradient.setColorAt(0.5, pin_color)
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(pos, led_size, led_size)
            else:
                # Inaktiver Pin
                painter.setBrush(pin_color)
                painter.setPen(QPen(pin_color.darker(120), 1))
                painter.drawEllipse(pos, led_size/2, led_size/2)

            # Pin-Label
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8))
            label_rect = QRectF(pos.x() - 20, pos.y() + 15, 40, 15)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, pin_name)

    def draw_info(self, painter: QPainter):
        """Zeichnet Info-Text"""
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Arial", 10))

        info_text = f"Board: {self.board.board_type} | Rotation: X:{self.board.rotation_x:.0f}° Y:{self.board.rotation_y:.0f}° | Zoom: {self.board.scale:.1f}x"
        painter.drawText(10, 20, info_text)

        # Steuerung-Hinweis
        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(10, self.height() - 10, "Linke Maustaste: Rotieren | Mausrad: Zoom")

    def mousePressEvent(self, event):
        """Mouse Press - Starte Rotation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        """Mouse Move - Rotiere Board"""
        if self.dragging and self.last_mouse_pos:
            dx = event.pos().x() - self.last_mouse_pos.x()
            dy = event.pos().y() - self.last_mouse_pos.y()

            self.board.rotate(dx, dy)
            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Mouse Release - Stoppe Rotation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def wheelEvent(self, event):
        """Mouse Wheel - Zoom"""
        delta = event.angleDelta().y() / 120.0
        self.board.zoom(delta)
        self.update()

    def update_pin_state(self, pin_name: str, state: str = None, value: int = None):
        """Aktualisiert Pin-Status"""
        self.board.update_pin_state(pin_name, state, value)
        self.update()

    def set_auto_rotate(self, enabled: bool):
        """Aktiviert/Deaktiviert Auto-Rotation"""
        self.auto_rotate = enabled
        if enabled:
            self.animation_timer.start(50)  # 20 FPS
        else:
            self.animation_timer.stop()

    def animate(self):
        """Animations-Loop"""
        if self.auto_rotate:
            self.board.rotation_y += 1
            self.update()

    def reset_view(self):
        """Setzt Ansicht zurück"""
        self.board.rotation_x = 20
        self.board.rotation_y = 45
        self.board.rotation_z = 0
        self.board.scale = 3.0
        self.update()


class Board3DVisualizerTab(QWidget):
    """Tab für 3D Board Visualisierung"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_ui()

        # Update Timer für Demo
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.demo_update)
        self.demo_active = False

    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()
        title = QLabel("<h2>🎮 3D Board Visualisierung</h2>")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Controls
        controls = QGroupBox("Steuerung")
        controls_layout = QHBoxLayout(controls)

        # Auto-Rotate
        self.auto_rotate_btn = QPushButton("🔄 Auto-Rotation")
        self.auto_rotate_btn.setCheckable(True)
        self.auto_rotate_btn.clicked.connect(self.toggle_auto_rotate)
        controls_layout.addWidget(self.auto_rotate_btn)

        # Reset View
        reset_btn = QPushButton("🏠 Reset Ansicht")
        reset_btn.clicked.connect(self.reset_view)
        controls_layout.addWidget(reset_btn)

        # Demo Mode
        self.demo_btn = QPushButton("✨ Demo Modus")
        self.demo_btn.setCheckable(True)
        self.demo_btn.clicked.connect(self.toggle_demo)
        controls_layout.addWidget(self.demo_btn)

        controls_layout.addStretch()

        layout.addWidget(controls)

        # 3D View
        self.board_3d = Board3DWidget()
        layout.addWidget(self.board_3d)

        # Info
        info = QLabel("💡 Tipp: Ziehen Sie mit der Maus um zu rotieren, Mausrad zum Zoomen")
        info.setStyleSheet("color: #95a5a6; font-size: 10px; padding: 5px;")
        layout.addWidget(info)

    def toggle_auto_rotate(self):
        """Toggle Auto-Rotation"""
        enabled = self.auto_rotate_btn.isChecked()
        self.board_3d.set_auto_rotate(enabled)

    def reset_view(self):
        """Reset View"""
        self.board_3d.reset_view()

    def toggle_demo(self):
        """Toggle Demo Mode"""
        self.demo_active = self.demo_btn.isChecked()

        if self.demo_active:
            self.demo_timer.start(100)
        else:
            self.demo_timer.stop()
            # Reset alle Pins
            for pin_name in self.board_3d.board.pins:
                self.board_3d.update_pin_state(pin_name, "LOW", 0)

    def demo_update(self):
        """Demo-Modus Update"""
        import random

        # Zufällige Pins aktivieren
        digital_pins = [f"D{i}" for i in range(14)]
        analog_pins = [f"A{i}" for i in range(6)]

        # Einige Digital-Pins toggeln
        for _ in range(3):
            pin = random.choice(digital_pins)
            state = random.choice(["HIGH", "LOW"])
            self.board_3d.update_pin_state(pin, state=state)

        # Einige Analog-Pins setzen
        for _ in range(2):
            pin = random.choice(analog_pins)
            value = random.randint(0, 1023)
            self.board_3d.update_pin_state(pin, value=value)

    def update_pin_from_data(self, pin_name: str, state: str = None, value: int = None):
        """Aktualisiert Pin aus externen Daten"""
        self.board_3d.update_pin_state(pin_name, state, value)

    def closeEvent(self, event):
        """Stoppt Timer beim Schließen"""
        if hasattr(self, 'demo_timer'):
            self.demo_timer.stop()
        if hasattr(self, 'board_3d') and hasattr(self.board_3d, 'animation_timer'):
            self.board_3d.animation_timer.stop()
        super().closeEvent(event)
