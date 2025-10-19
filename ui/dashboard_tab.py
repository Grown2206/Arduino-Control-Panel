# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QMdiArea, QMdiSubWindow, 
                             QPushButton, QHBoxLayout, QComboBox, QLabel, QInputDialog)
from PyQt6.QtCore import pyqtSignal, Qt

from .dashboard_widgets import (ConnectionWidget, QuickSequenceWidget,
                                SensorDisplayWidget, RecentActivityWidget)
from .pin_overview_widget import PinOverviewWidget
from .live_chart_widget import LiveChartWidget

class DashboardTab(QWidget):
    """Das Haupt-Dashboard mit verschiebbaren und anpassbaren Widgets."""
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    refresh_ports_requested = pyqtSignal()
    start_sequence_signal = pyqtSignal(str)
    start_test_run_signal = pyqtSignal(str)

    # NEUE Signale für das Layout-Management
    layout_save_requested = pyqtSignal(str, dict)
    layout_delete_requested = pyqtSignal(str)
    layout_load_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.widgets = {}
        self.mdi_area = QMdiArea()
        
        self.widget_definitions = {
            'connection': {'class': ConnectionWidget, 'title': '🔌 Verbindung', 'geom': (10, 10, 280, 220)},
            'quick_sequence': {'class': QuickSequenceWidget, 'title': '⚙️ Schnellstart', 'geom': (10, 240, 280, 200)},
            'sensor_display': {'class': SensorDisplayWidget, 'title': '🌡️ Live Sensoren', 'geom': (10, 450, 280, 130)},
            'activity': {'class': RecentActivityWidget, 'title': '🕒 Letzte Aktivitäten', 'geom': (10, 590, 280, 200)},
            'pin_overview': {'class': PinOverviewWidget, 'title': '📊 Pin Übersicht', 'geom': (300, 10, 550, 380)},
            'live_chart': {'class': LiveChartWidget, 'title': '📈 Live Pin-Verlauf', 'geom': (300, 400, 550, 390)},
        }
        
        self.setup_ui()
        self._create_widgets()
        self.setup_connections()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # NEU: Werkzeugleiste für Layout-Steuerung
        control_layout = self._create_layout_toolbar()
        main_layout.addLayout(control_layout)
        
        self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi_area.setStyleSheet("QMdiArea { background-color: transparent; }")
        
        main_layout.addWidget(self.mdi_area)

    def _create_layout_toolbar(self):
        """Erstellt die neue Werkzeugleiste für das Layout-Management."""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(QLabel("Layout:"))
        
        self.layout_combo = QComboBox()
        self.layout_combo.currentTextChanged.connect(self.on_layout_selected)
        toolbar_layout.addWidget(self.layout_combo)

        save_layout_btn = QPushButton("💾 Speichern...")
        save_layout_btn.clicked.connect(self.on_save_layout_clicked)
        toolbar_layout.addWidget(save_layout_btn)
        
        delete_layout_btn = QPushButton("🗑️ Löschen")
        delete_layout_btn.clicked.connect(self.on_delete_layout_clicked)
        toolbar_layout.addWidget(delete_layout_btn)

        toolbar_layout.addStretch()
        
        reset_layout_btn = QPushButton("🔄 Standard wiederherstellen")
        reset_layout_btn.clicked.connect(self.reset_layout_to_default)
        toolbar_layout.addWidget(reset_layout_btn)
        
        return toolbar_layout

    def _create_widgets(self):
        for name, definition in self.widget_definitions.items():
            widget_instance = definition['class']()
            setattr(self, f"{name}_widget", widget_instance)
            sub_window = QMdiSubWindow()
            sub_window.setWidget(widget_instance)
            sub_window.setWindowTitle(definition['title'])
            sub_window.setGeometry(*definition['geom'])
            sub_window.setObjectName(name)
            self.mdi_area.addSubWindow(sub_window)

    def setup_connections(self):
        self.connection_widget.connect_requested.connect(self.connect_requested)
        self.connection_widget.disconnect_requested.connect(self.disconnect_requested)
        self.connection_widget.refresh_ports_requested.connect(self.refresh_ports_requested)
        self.quick_sequence_widget.start_sequence_signal.connect(self.start_sequence_signal)
        self.quick_sequence_widget.start_test_run_signal.connect(self.start_test_run_signal)

    def on_save_layout_clicked(self):
        """Fragt nach einem Namen und sendet das Signal zum Speichern."""
        current_name = self.layout_combo.currentText()
        name, ok = QInputDialog.getText(self, "Layout speichern", "Name für das Layout:", text=current_name)
        if ok and name:
            layout_config = self.get_current_layout_config()
            self.layout_save_requested.emit(name, layout_config)
    
    def on_delete_layout_clicked(self):
        """Sendet das Signal zum Löschen des ausgewählten Layouts."""
        name = self.layout_combo.currentText()
        if name and name != "Standard":
            self.layout_delete_requested.emit(name)
    
    def on_layout_selected(self, name):
        """Sendet das Signal zum Laden des ausgewählten Layouts."""
        if name:
            self.layout_load_requested.emit(name)
    
    def get_current_layout_config(self):
        """Liest die Geometrie aller Sub-Fenster aus."""
        layout_config = {}
        for sub_window in self.mdi_area.subWindowList():
            name = sub_window.objectName()
            geom = sub_window.geometry()
            layout_config[name] = {'x': geom.x(), 'y': geom.y(), 'w': geom.width(), 'h': geom.height()}
        return layout_config

    def apply_layout(self, layout_config):
        """Wendet eine geladene Layout-Konfiguration an."""
        for sub_window in self.mdi_area.subWindowList():
            name = sub_window.objectName()
            if name in layout_config:
                geom_data = layout_config[name]
                sub_window.setGeometry(geom_data['x'], geom_data['y'], geom_data['w'], geom_data['h'])

    def update_layout_list(self, layout_names):
        """Aktualisiert die ComboBox mit den verfügbaren Layout-Namen."""
        self.layout_combo.blockSignals(True)
        current = self.layout_combo.currentText()
        self.layout_combo.clear()
        self.layout_combo.addItems(layout_names)
        if current in layout_names:
            self.layout_combo.setCurrentText(current)
        self.layout_combo.blockSignals(False)

    def reset_layout_to_default(self):
        """Setzt die Position und Größe aller Widgets auf die Standardwerte zurück."""
        default_config = {name: {'x': g['geom'][0], 'y': g['geom'][1], 'w': g['geom'][2], 'h': g['geom'][3]} for name, g in self.widget_definitions.items()}
        self.apply_layout(default_config)
