from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QGraphicsView, QMessageBox, QMenu
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPainter, QAction

from .scene import VisualScene
from .node import StartNode, ActionNode, WaitNode
from .connection import Connection
import json

class VisualEditorWidget(QWidget):
    """Haupt-Widget, das die Szene und die Toolbar für den visuellen Editor enthält."""
    sequence_saved = pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_sequence = None
        self.current_sequence_id = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar = QHBoxLayout()
        # Buttons wurden in das Kontextmenü verschoben
        save_btn = QPushButton("💾 Speichern & Schließen")
        save_btn.clicked.connect(self.save_sequence)

        toolbar.addStretch()
        toolbar.addWidget(save_btn)
        layout.addLayout(toolbar)

        self.scene = VisualScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        # NEU: Kontextmenü-Policy setzen
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.open_context_menu)
        
        layout.addWidget(self.view)

    def open_context_menu(self, position):
        menu = QMenu()
        
        # Aktionen für das Menü erstellen
        add_action_action = QAction("➕ Aktion-Knoten hinzufügen", self)
        add_action_action.triggered.connect(lambda: self.scene.add_node_at('action', self.view.mapToScene(position)))
        menu.addAction(add_action_action)

        add_wait_action = QAction("⏳ Warten-Knoten hinzufügen", self)
        add_wait_action.triggered.connect(lambda: self.scene.add_node_at('wait', self.view.mapToScene(position)))
        menu.addAction(add_wait_action)

        # Lösch-Aktion nur anzeigen, wenn etwas ausgewählt ist
        if self.scene.selectedItems():
            menu.addSeparator()
            delete_action = QAction("🗑️ Auswahl löschen", self)
            delete_action.triggered.connect(self.scene.delete_selected_items)
            menu.addAction(delete_action)

        menu.exec(self.view.mapToGlobal(position))

    def highlight_step(self, step_index):
        """Leitet den Highlight-Befehl an die Szene weiter."""
        self.scene.highlight_node(step_index)

    def load_sequence(self, sequence_id, sequence_data):
        self.current_sequence_id = sequence_id
        self.current_sequence = sequence_data
        self.scene.clear_scene()
        self.scene.load_sequence_from_data(sequence_data)
    
    def save_sequence(self):
        if not self.current_sequence_id:
            return

        steps, is_valid, message = self.scene.to_sequence_steps()

        if not is_valid:
            QMessageBox.warning(self, "Ungültige Sequenz", f"Speichern fehlgeschlagen:\n{message}")
            return

        updated_sequence = self.current_sequence.copy()
        updated_sequence['steps'] = steps
        
        self.sequence_saved.emit(self.current_sequence_id, updated_sequence)
        
        # Zurück zur Listenansicht wechseln
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'setCurrentIndex'):
             parent_widget.setCurrentWidget(parent_widget.findChild(QWidget, "ListView"))

