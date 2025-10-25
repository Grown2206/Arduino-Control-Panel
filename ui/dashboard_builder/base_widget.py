# -*- coding: utf-8 -*-
"""
Dashboard Builder - Base Widget System
Basis-Klassen für alle Dashboard-Widgets
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor
from typing import Dict, Any, Optional
import uuid


class DashboardWidgetBase(QFrame):
    """Basis-Klasse für alle Dashboard-Widgets"""

    # Signals
    widget_moved = pyqtSignal(str, QPoint)  # widget_id, position
    widget_resized = pyqtSignal(str, tuple)  # widget_id, (width, height)
    widget_deleted = pyqtSignal(str)  # widget_id
    widget_config_changed = pyqtSignal(str, dict)  # widget_id, config

    def __init__(self, widget_id: str = None, title: str = "Widget", parent=None):
        super().__init__(parent)

        # Widget Identifikation
        self.widget_id = widget_id or str(uuid.uuid4())
        self.widget_title = title
        self.widget_type = "base"

        # Drag & Drop State
        self.is_dragging = False
        self.drag_start_pos = None
        self.is_resizing = False
        self.resize_start_pos = None
        self.resize_start_size = None

        # Edit Mode
        self.edit_mode = True

        # Widget-Konfiguration
        self.config = {
            'title': title,
            'background_color': '#2b2b2b',
            'border_color': '#555',
            'title_color': '#e0e0e0',
            'update_interval': 1000,  # ms
        }

        # UI Setup
        self.setMinimumSize(100, 80)
        self.setMaximumSize(800, 600)
        self.setup_base_ui()

        # Enable mouse tracking
        self.setMouseTracking(True)

        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_base_ui(self):
        """Setup der Basis-UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)

        # Haupt-Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(3)

        # Titel-Label
        self.title_label = QLabel(self.widget_title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            f"font-weight: bold; font-size: 11px; color: {self.config['title_color']}; "
            "background-color: rgba(0, 0, 0, 0.3); padding: 3px; border-radius: 3px;"
        )
        self.main_layout.addWidget(self.title_label)

        # Content Container
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.addWidget(self.content_widget)

        self.update_style()

    def update_style(self):
        """Aktualisiert das Widget-Styling"""
        border_color = '#27ae60' if self.edit_mode else self.config['border_color']
        border_width = 3 if self.edit_mode else 2

        self.setStyleSheet(f"""
            DashboardWidgetBase {{
                background-color: {self.config['background_color']};
                border: {border_width}px solid {border_color};
                border-radius: 6px;
            }}
        """)

    def set_edit_mode(self, enabled: bool):
        """Aktiviert/Deaktiviert Edit-Modus"""
        self.edit_mode = enabled
        self.update_style()
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor if enabled else Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event):
        """Mouse Press Event für Drag & Drop"""
        if not self.edit_mode:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # Prüfe ob Resize-Handle geklickt wurde (untere rechte Ecke)
            if self.is_in_resize_handle(event.pos()):
                self.is_resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                event.accept()
            else:
                # Starte Dragging
                self.is_dragging = True
                self.drag_start_pos = event.pos()
                self.raise_()
                event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Mouse Move Event für Drag & Drop"""
        if not self.edit_mode:
            super().mouseMoveEvent(event)
            return

        if self.is_resizing:
            # Resize Widget
            delta = event.globalPosition().toPoint() - self.resize_start_pos
            new_width = max(self.minimumWidth(), self.resize_start_size.width() + delta.x())
            new_height = max(self.minimumHeight(), self.resize_start_size.height() + delta.y())

            self.resize(new_width, new_height)
            event.accept()

        elif self.is_dragging and self.drag_start_pos:
            # Move Widget
            new_pos = self.mapToParent(event.pos() - self.drag_start_pos)

            # Begrenze auf Parent-Widget
            if self.parent():
                parent_rect = self.parent().rect()
                new_pos.setX(max(0, min(new_pos.x(), parent_rect.width() - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent_rect.height() - self.height())))

            self.move(new_pos)
            event.accept()

        else:
            # Update Cursor für Resize-Handle
            if self.is_in_resize_handle(event.pos()):
                self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor if self.edit_mode else Qt.CursorShape.ArrowCursor))

            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Mouse Release Event"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging:
                self.is_dragging = False
                self.widget_moved.emit(self.widget_id, self.pos())
                event.accept()
            elif self.is_resizing:
                self.is_resizing = False
                self.widget_resized.emit(self.widget_id, (self.width(), self.height()))
                event.accept()

        super().mouseReleaseEvent(event)

    def is_in_resize_handle(self, pos: QPoint) -> bool:
        """Prüft ob Position im Resize-Handle ist"""
        handle_size = 15
        return (self.width() - handle_size < pos.x() < self.width() and
                self.height() - handle_size < pos.y() < self.height())

    def paintEvent(self, event):
        """Paint Event - Zeichnet Resize-Handle"""
        super().paintEvent(event)

        if self.edit_mode:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Resize-Handle zeichnen
            handle_size = 12
            handle_rect = QRect(
                self.width() - handle_size - 3,
                self.height() - handle_size - 3,
                handle_size,
                handle_size
            )

            painter.setBrush(QColor(39, 174, 96))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawRect(handle_rect)

    def show_context_menu(self, pos: QPoint):
        """Zeigt Kontext-Menü"""
        if not self.edit_mode:
            return

        menu = QMenu(self)

        # Konfigurieren
        config_action = menu.addAction("⚙️ Konfigurieren")
        config_action.triggered.connect(self.open_config_dialog)

        # Duplizieren
        duplicate_action = menu.addAction("📋 Duplizieren")
        duplicate_action.triggered.connect(self.duplicate_widget)

        menu.addSeparator()

        # Löschen
        delete_action = menu.addAction("🗑️ Löschen")
        delete_action.triggered.connect(self.delete_widget)

        menu.exec(self.mapToGlobal(pos))

    def open_config_dialog(self):
        """Öffnet Konfigurations-Dialog (Override in Subclasses)"""
        pass

    def duplicate_widget(self):
        """Dupliziert das Widget"""
        # Wird vom Dashboard-Builder gehandhabt
        pass

    def delete_widget(self):
        """Löscht das Widget"""
        self.widget_deleted.emit(self.widget_id)
        self.deleteLater()

    def get_config(self) -> Dict[str, Any]:
        """Gibt Widget-Konfiguration zurück"""
        return {
            'widget_id': self.widget_id,
            'widget_type': self.widget_type,
            'title': self.widget_title,
            'position': (self.x(), self.y()),
            'size': (self.width(), self.height()),
            'config': self.config.copy()
        }

    def set_config(self, config: Dict[str, Any]):
        """Setzt Widget-Konfiguration"""
        if 'title' in config:
            self.widget_title = config['title']
            self.title_label.setText(self.widget_title)

        if 'position' in config:
            self.move(*config['position'])

        if 'size' in config:
            self.resize(*config['size'])

        if 'config' in config:
            self.config.update(config['config'])
            self.update_style()

        self.widget_config_changed.emit(self.widget_id, config)

    def update_data(self, data: Any):
        """Aktualisiert Widget-Daten (Override in Subclasses)"""
        pass

    def to_html(self) -> str:
        """Exportiert Widget als HTML (Override in Subclasses)"""
        return f"""
        <div class="dashboard-widget" style="
            width: {self.width()}px;
            height: {self.height()}px;
            background-color: {self.config['background_color']};
            border: 2px solid {self.config['border_color']};
            border-radius: 6px;
            padding: 5px;
        ">
            <h3 style="color: {self.config['title_color']}; text-align: center;">
                {self.widget_title}
            </h3>
        </div>
        """


class DashboardWidgetFactory:
    """Factory für Dashboard-Widgets"""

    _widget_types = {}

    @classmethod
    def register_widget_type(cls, widget_type: str, widget_class):
        """Registriert einen Widget-Typ"""
        cls._widget_types[widget_type] = widget_class

    @classmethod
    def create_widget(cls, widget_type: str, config: Dict[str, Any] = None, parent=None) -> Optional[DashboardWidgetBase]:
        """Erstellt ein Widget"""
        if widget_type not in cls._widget_types:
            return None

        widget_class = cls._widget_types[widget_type]
        widget = widget_class(parent=parent)

        if config:
            widget.set_config(config)

        return widget

    @classmethod
    def get_available_widgets(cls) -> Dict[str, type]:
        """Gibt alle verfügbaren Widget-Typen zurück"""
        return cls._widget_types.copy()
