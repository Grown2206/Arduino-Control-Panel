# -*- coding: utf-8 -*-
"""
Dashboard Builder - Main Builder UI
Editor zum Erstellen individueller Dashboards
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLabel,
                             QPushButton, QScrollArea, QFrame, QListWidget, QListWidgetItem,
                             QSplitter, QFileDialog, QInputDialog, QMessageBox, QComboBox,
                             QGroupBox)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QDrag, QPixmap, QPainter, QColor
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from .base_widget import DashboardWidgetBase, DashboardWidgetFactory
from .widget_library import *  # Importiert alle Widget-Typen


class DashboardCanvas(QFrame):
    """Canvas zum Platzieren von Widgets"""

    widget_added = pyqtSignal(str)  # widget_id
    widget_removed = pyqtSignal(str)  # widget_id
    layout_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.widgets = {}  # widget_id -> widget
        self.edit_mode = True

        # Canvas Setup
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            DashboardCanvas {
                background-color: #1e1e1e;
                border: 2px solid #555;
                border-radius: 5px;
            }
        """)

        self.setAcceptDrops(True)

    def add_widget(self, widget: DashboardWidgetBase, position=None):
        """Fügt ein Widget zum Canvas hinzu"""
        widget.setParent(self)

        # Positioniere Widget
        if position:
            widget.move(*position)
        else:
            # Automatische Positionierung
            x = 20 + (len(self.widgets) * 30) % (self.width() - 200)
            y = 20 + ((len(self.widgets) * 30) // (self.width() - 200)) * 150
            widget.move(x, y)

        # Verbinde Signals
        widget.widget_moved.connect(self.on_widget_moved)
        widget.widget_resized.connect(self.on_widget_resized)
        widget.widget_deleted.connect(self.remove_widget)

        # Speichere Widget
        self.widgets[widget.widget_id] = widget
        widget.set_edit_mode(self.edit_mode)
        widget.show()

        self.widget_added.emit(widget.widget_id)
        self.layout_changed.emit()

    def remove_widget(self, widget_id: str):
        """Entfernt ein Widget"""
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            widget.deleteLater()
            del self.widgets[widget_id]

            self.widget_removed.emit(widget_id)
            self.layout_changed.emit()

    def on_widget_moved(self, widget_id: str, position):
        """Widget wurde verschoben"""
        self.layout_changed.emit()

    def on_widget_resized(self, widget_id: str, size):
        """Widget wurde resized"""
        self.layout_changed.emit()

    def set_edit_mode(self, enabled: bool):
        """Setzt Edit-Modus für alle Widgets"""
        self.edit_mode = enabled
        for widget in self.widgets.values():
            widget.set_edit_mode(enabled)

    def clear(self):
        """Löscht alle Widgets"""
        widget_ids = list(self.widgets.keys())
        for widget_id in widget_ids:
            self.remove_widget(widget_id)

    def get_layout_config(self) -> List[Dict]:
        """Gibt Layout-Konfiguration zurück"""
        return [widget.get_config() for widget in self.widgets.values()]

    def load_layout_config(self, config: List[Dict]):
        """Lädt Layout-Konfiguration"""
        self.clear()

        for widget_config in config:
            widget_type = widget_config.get('widget_type')
            widget = DashboardWidgetFactory.create_widget(widget_type, config=widget_config, parent=self)

            if widget:
                self.add_widget(widget, widget_config.get('position'))

    def dragEnterEvent(self, event):
        """Drag Enter Event"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Drag Move Event"""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """Drop Event - Erstellt neues Widget"""
        widget_type = event.mimeData().text()

        # Erstelle Widget
        widget = DashboardWidgetFactory.create_widget(widget_type, parent=self)

        if widget:
            # Positioniere an Drop-Position
            drop_pos = event.position().toPoint()
            self.add_widget(widget, (drop_pos.x(), drop_pos.y()))

        event.acceptProposedAction()


class WidgetPalette(QListWidget):
    """Palette mit verfügbaren Widgets"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMaximumWidth(200)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:hover {
                background-color: #3498db;
            }
        """)

        self.setDragEnabled(True)
        self.setIconSize(QSize(32, 32))

        self.populate_widgets()

    def populate_widgets(self):
        """Füllt die Palette mit Widgets"""
        widget_info = [
            ("value_display", "📊 Wert-Anzeige", "Zeigt einen einzelnen Wert an"),
            ("gauge", "🎯 Gauge", "Tachometer/Gauge-Anzeige"),
            ("led", "💡 LED", "LED-Indikator"),
            ("button", "🔘 Button", "Anklickbarer Button"),
            ("progress_bar", "📈 Progress Bar", "Fortschrittsbalken"),
            ("label", "🏷️ Label", "Text-Label"),
        ]

        for widget_type, name, description in widget_info:
            item = QListWidgetItem(f"{name}\n{description}")
            item.setData(Qt.ItemDataRole.UserRole, widget_type)
            item.setToolTip(description)
            self.addItem(item)

    def startDrag(self, supportedActions):
        """Startet Drag-Operation"""
        item = self.currentItem()
        if not item:
            return

        widget_type = item.data(Qt.ItemDataRole.UserRole)

        # Erstelle Drag-Object
        drag = QDrag(self)
        mime_data = drag.mimeData()
        mime_data.setText(widget_type)
        drag.setMimeData(mime_data)

        # Drag ausführen
        drag.exec(Qt.DropAction.CopyAction)


class DashboardBuilderWidget(QWidget):
    """Haupt-Widget für Dashboard-Builder"""

    dashboard_saved = pyqtSignal(str)  # filepath

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file = None
        self.is_modified = False

        self.setup_ui()

    def setup_ui(self):
        """Setup der UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # Splitter (Palette | Canvas)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Linke Seite: Widget-Palette
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        palette_label = QLabel("<b>Widget-Palette</b>")
        palette_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(palette_label)

        self.widget_palette = WidgetPalette()
        left_layout.addWidget(self.widget_palette)

        # Hilfetext
        help_text = QLabel("Ziehen Sie Widgets\nauf das Canvas")
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_text.setStyleSheet("color: #95a5a6; font-size: 10px; padding: 10px;")
        left_layout.addWidget(help_text)

        splitter.addWidget(left_panel)

        # Rechte Seite: Canvas
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Canvas Header
        canvas_header = QHBoxLayout()
        canvas_label = QLabel("<b>Dashboard Canvas</b>")
        canvas_header.addWidget(canvas_label)

        # Edit Mode Toggle
        self.edit_mode_toggle = QPushButton("✏️ Edit-Modus")
        self.edit_mode_toggle.setCheckable(True)
        self.edit_mode_toggle.setChecked(True)
        self.edit_mode_toggle.clicked.connect(self.toggle_edit_mode)
        self.edit_mode_toggle.setStyleSheet("""
            QPushButton:checked {
                background-color: #27ae60;
            }
        """)
        canvas_header.addWidget(self.edit_mode_toggle)

        canvas_header.addStretch()
        right_layout.addLayout(canvas_header)

        # Canvas Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.canvas = DashboardCanvas()
        self.canvas.layout_changed.connect(self.on_layout_changed)
        scroll.setWidget(self.canvas)

        right_layout.addWidget(scroll)

        splitter.addWidget(right_panel)

        # Splitter-Proportionen
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        layout.addWidget(splitter)

        # Status Bar
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("padding: 5px; background-color: #2b2b2b; border-top: 1px solid #555;")
        layout.addWidget(self.status_label)

    def create_toolbar(self) -> QWidget:
        """Erstellt die Toolbar"""
        toolbar_widget = QWidget()
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(5, 5, 5, 5)

        # Neu
        new_btn = QPushButton("📄 Neu")
        new_btn.clicked.connect(self.new_dashboard)
        toolbar.addWidget(new_btn)

        # Öffnen
        open_btn = QPushButton("📂 Öffnen")
        open_btn.clicked.connect(self.open_dashboard)
        toolbar.addWidget(open_btn)

        # Speichern
        save_btn = QPushButton("💾 Speichern")
        save_btn.clicked.connect(self.save_dashboard)
        toolbar.addWidget(save_btn)

        # Speichern als
        save_as_btn = QPushButton("💾 Speichern als...")
        save_as_btn.clicked.connect(self.save_dashboard_as)
        toolbar.addWidget(save_as_btn)

        toolbar.addWidget(QLabel("|"))

        # Export HTML
        export_btn = QPushButton("🌐 HTML Export")
        export_btn.clicked.connect(self.export_html)
        toolbar.addWidget(export_btn)

        toolbar.addWidget(QLabel("|"))

        # Clear
        clear_btn = QPushButton("🗑️ Löschen")
        clear_btn.clicked.connect(self.clear_dashboard)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()

        # Widget-Count
        self.widget_count_label = QLabel("Widgets: 0")
        toolbar.addWidget(self.widget_count_label)

        toolbar_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-bottom: 1px solid #555;
            }
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #3c3c3c;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)

        return toolbar_widget

    def toggle_edit_mode(self):
        """Schaltet Edit-Modus um"""
        is_edit = self.edit_mode_toggle.isChecked()
        self.canvas.set_edit_mode(is_edit)

        if is_edit:
            self.edit_mode_toggle.setText("✏️ Edit-Modus")
            self.status_label.setText("Edit-Modus aktiv - Widgets können verschoben werden")
        else:
            self.edit_mode_toggle.setText("👁️ Ansicht")
            self.status_label.setText("Ansichts-Modus - Widgets sind fixiert")

    def new_dashboard(self):
        """Erstellt ein neues Dashboard"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Ungespeicherte Änderungen",
                "Möchten Sie die Änderungen speichern?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_dashboard()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.canvas.clear()
        self.current_file = None
        self.is_modified = False
        self.status_label.setText("Neues Dashboard erstellt")

    def open_dashboard(self):
        """Öffnet ein Dashboard"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Dashboard öffnen", "", "Dashboard Files (*.json)"
        )

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self.canvas.load_layout_config(config.get('widgets', []))
                self.current_file = filepath
                self.is_modified = False
                self.status_label.setText(f"Dashboard geladen: {os.path.basename(filepath)}")

            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Laden:\n{str(e)}")

    def save_dashboard(self):
        """Speichert das Dashboard"""
        if not self.current_file:
            return self.save_dashboard_as()

        return self._save_to_file(self.current_file)

    def save_dashboard_as(self):
        """Speichert das Dashboard unter neuem Namen"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Dashboard speichern", "", "Dashboard Files (*.json)"
        )

        if filepath:
            if not filepath.endswith('.json'):
                filepath += '.json'

            return self._save_to_file(filepath)

        return False

    def _save_to_file(self, filepath: str) -> bool:
        """Speichert in Datei"""
        try:
            config = {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'canvas_size': (self.canvas.width(), self.canvas.height()),
                'widgets': self.canvas.get_layout_config()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.current_file = filepath
            self.is_modified = False
            self.status_label.setText(f"Gespeichert: {os.path.basename(filepath)}")
            self.dashboard_saved.emit(filepath)
            return True

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{str(e)}")
            return False

    def export_html(self):
        """Exportiert Dashboard als HTML"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "HTML Export", "", "HTML Files (*.html)"
        )

        if filepath:
            if not filepath.endswith('.html'):
                filepath += '.html'

            try:
                html = self._generate_html()

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)

                self.status_label.setText(f"HTML exportiert: {os.path.basename(filepath)}")
                QMessageBox.information(self, "Erfolg", f"Dashboard als HTML exportiert:\n{filepath}")

            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim HTML-Export:\n{str(e)}")

    def _generate_html(self) -> str:
        """Generiert HTML aus aktuellem Dashboard"""
        widgets_html = ""

        for widget in self.canvas.widgets.values():
            widget_html = widget.to_html()
            widgets_html += f"""
            <div style="
                position: absolute;
                left: {widget.x()}px;
                top: {widget.y()}px;
                width: {widget.width()}px;
                height: {widget.height()}px;
            ">
                {widget_html}
            </div>
            """

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Arduino Dashboard</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: Arial, sans-serif;
        }}
        #dashboard {{
            position: relative;
            width: {self.canvas.width()}px;
            height: {self.canvas.height()}px;
            background-color: #1e1e1e;
            border: 2px solid #555;
            border-radius: 5px;
            margin: 0 auto;
        }}
        .dashboard-widget {{
            padding: 10px;
        }}
    </style>
</head>
<body>
    <h1 style="text-align: center;">Arduino Control Panel - Dashboard</h1>
    <div id="dashboard">
        {widgets_html}
    </div>
    <script>
        // Hier könnte WebSocket-Code für Live-Updates stehen
        console.log('Dashboard geladen');
    </script>
</body>
</html>
        """

        return html

    def clear_dashboard(self):
        """Löscht alle Widgets"""
        reply = QMessageBox.question(
            self, "Dashboard löschen",
            "Möchten Sie wirklich alle Widgets löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.clear()
            self.is_modified = True
            self.status_label.setText("Dashboard geleert")

    def on_layout_changed(self):
        """Layout wurde geändert"""
        self.is_modified = True
        widget_count = len(self.canvas.widgets)
        self.widget_count_label.setText(f"Widgets: {widget_count}")

    def get_canvas(self) -> DashboardCanvas:
        """Gibt das Canvas zurück"""
        return self.canvas

    def update_widget_data(self, widget_id: str, data: Any):
        """Aktualisiert Daten für ein Widget"""
        if widget_id in self.canvas.widgets:
            self.canvas.widgets[widget_id].update_data(data)
