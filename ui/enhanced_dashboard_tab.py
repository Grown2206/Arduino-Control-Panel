# -*- coding: utf-8 -*-
"""
Erweitertes Dashboard mit konfigurierbaren Widgets
Alle Features der App in einer übersichtlichen Ansicht
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QMdiArea, QMdiSubWindow,
                             QPushButton, QHBoxLayout, QComboBox, QLabel, QInputDialog,
                             QCheckBox, QMenu, QDialog, QListWidget, QListWidgetItem,
                             QDialogButtonBox, QGroupBox, QGridLayout, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction

from .dashboard_widgets import (ConnectionWidget, QuickSequenceWidget,
                                SensorDisplayWidget, RecentActivityWidget)
from .pin_overview_widget import PinOverviewWidget
from .live_chart_widget import LiveChartWidget
from .sequence_info_widget import SequenceInfoWidget

class WidgetSelectorDialog(QDialog):
    # Unverändert
    def __init__(self, available_widgets, visible_widgets, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dashboard-Widgets verwalten")
        self.setMinimumSize(500, 400)
        self.available_widgets = available_widgets
        self.visible_widgets = visible_widgets.copy()
        self.setup_ui()
    def setup_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel("Wähle die Widgets aus, die im Dashboard angezeigt werden sollen:")
        info.setWordWrap(True); layout.addWidget(info)
        self.widget_list = QListWidget()
        for widget_id, widget_info in self.available_widgets.items():
            item = QListWidgetItem(f"{widget_info['icon']} {widget_info['title']}")
            item.setData(Qt.ItemDataRole.UserRole, widget_id)
            item.setCheckState(Qt.CheckState.Checked if widget_id in self.visible_widgets else Qt.CheckState.Unchecked)
            self.widget_list.addItem(item)
        layout.addWidget(self.widget_list)
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Alle auswählen"); select_all_btn.clicked.connect(self.select_all); btn_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Alle abwählen"); deselect_all_btn.clicked.connect(self.deselect_all); btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch(); layout.addLayout(btn_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject); layout.addWidget(button_box)
    def select_all(self):
        for i in range(self.widget_list.count()): self.widget_list.item(i).setCheckState(Qt.CheckState.Checked)
    def deselect_all(self):
        for i in range(self.widget_list.count()): self.widget_list.item(i).setCheckState(Qt.CheckState.Unchecked)
    def get_selected_widgets(self):
        selected = set()
        for i in range(self.widget_list.count()):
            item = self.widget_list.item(i)
            if item.checkState() == Qt.CheckState.Checked: selected.add(item.data(Qt.ItemDataRole.UserRole))
        return selected

class EnhancedDashboardTab(QWidget):
    # Signale unverändert
    connect_requested = pyqtSignal(str)
    disconnect_requested = pyqtSignal()
    refresh_ports_requested = pyqtSignal()
    start_sequence_signal = pyqtSignal(str)
    start_test_run_signal = pyqtSignal(str)
    layout_save_requested = pyqtSignal(str, dict)
    layout_delete_requested = pyqtSignal(str)
    layout_load_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.widgets = {}
        self.mdi_area = QMdiArea()
        self.visible_widgets = set()

        # Widget-Definitionen OHNE LED Matrix und PWM Quick
        self.widget_definitions = {
            'connection': {'class': ConnectionWidget, 'title': 'Verbindung', 'icon': '🔌', 'geom': (10, 10, 280, 220), 'category': 'Basis'},
            'quick_sequence': {'class': QuickSequenceWidget, 'title': 'Schnellstart', 'icon': '⚙️', 'geom': (10, 240, 280, 200), 'category': 'Basis'},
            'activity': {'class': RecentActivityWidget, 'title': 'Aktivitäten', 'icon': '🕒', 'geom': (10, 450, 280, 200), 'category': 'Basis'},
            'sensor_display': {'class': SensorDisplayWidget, 'title': 'Live Sensoren', 'icon': '🌡️', 'geom': (300, 10, 280, 130), 'category': 'Sensoren'},
            'pin_overview': {'class': PinOverviewWidget, 'title': 'Pin Übersicht', 'icon': '📊', 'geom': (300, 150, 550, 380), 'category': 'Pins'},
            'live_chart': {'class': LiveChartWidget, 'title': 'Live Pin-Verlauf', 'icon': '📈', 'geom': (300, 540, 550, 260), 'category': 'Visualisierung', 'init_args': {'title': 'Live Pin-Verlauf'}},
            'sequence_info': {'class': SequenceInfoWidget, 'title': 'Testlauf-Status', 'icon': '⏱️', 'geom': (860, 10, 400, 300), 'category': 'Automatisierung'},
            # REMOVED: 'led_matrix': { ... }
            # REMOVED: 'pwm_quick': { ... }
        }

        # Standardmäßig sichtbare Widgets OHNE LED Matrix und PWM Quick
        self.default_visible = {
            'connection', 'quick_sequence', 'activity',
            'sensor_display', 'pin_overview', 'live_chart',
            'sequence_info'
        }
        self.visible_widgets = self.default_visible.copy()

        self.setup_ui()
        self._create_widgets()
        self.setup_connections() # Diese Methode verbindet nur die noch vorhandenen Widgets

    # setup_ui, _create_enhanced_toolbar, _create_widgets, setup_connections,
    # open_widget_selector, toggle_widget_visibility, add_optional_widget,
    # show_widget, hide_widget, on_save_layout_clicked, on_delete_layout_clicked,
    # on_layout_selected, get_current_layout_config, apply_layout,
    # update_layout_list, reset_layout_to_default
    # bleiben strukturell gleich, aber greifen auf die reduzierte widget_definitions zu.
    # Hier werden sie aus Platzgründen weggelassen, die Logik ist wie in der vorherigen Version.

    def setup_ui(self): # Wie zuvor
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout = self._create_enhanced_toolbar()
        main_layout.addLayout(toolbar_layout)
        self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdi_area.setStyleSheet("QMdiArea { background-color: transparent; }")
        main_layout.addWidget(self.mdi_area)

    def _create_enhanced_toolbar(self): # Wie zuvor, aber ohne Toggles für entfernte Widgets
        toolbar_layout = QHBoxLayout()
        widget_group = QGroupBox("Widgets")
        widget_layout = QHBoxLayout(widget_group)
        self.manage_widgets_btn = QPushButton("📦 Widgets verwalten")
        self.manage_widgets_btn.clicked.connect(self.open_widget_selector)
        widget_layout.addWidget(self.manage_widgets_btn)
        self.quick_toggles = {}
        important_widgets = ['pin_overview', 'live_chart', 'sensor_display', 'sequence_info'] # Ohne led_matrix, pwm_quick
        for widget_id in important_widgets:
            if widget_id in self.widget_definitions:
                info = self.widget_definitions[widget_id]
                toggle = QCheckBox(info['icon'])
                toggle.setToolTip(f"{info['title']} ein/ausblenden")
                toggle.setChecked(widget_id in self.visible_widgets)
                toggle.stateChanged.connect(lambda state, wid=widget_id: self.toggle_widget_visibility(wid, state))
                self.quick_toggles[widget_id] = toggle
                widget_layout.addWidget(toggle)
        toolbar_layout.addWidget(widget_group)

        layout_group = QGroupBox("Layout")
        layout_layout = QHBoxLayout(layout_group)
        layout_layout.addWidget(QLabel("Preset:"))
        self.layout_combo = QComboBox(); self.layout_combo.currentTextChanged.connect(self.on_layout_selected); layout_layout.addWidget(self.layout_combo)
        save_layout_btn = QPushButton("💾"); save_layout_btn.setToolTip("Layout speichern"); save_layout_btn.setMaximumWidth(35); save_layout_btn.clicked.connect(self.on_save_layout_clicked); layout_layout.addWidget(save_layout_btn)
        delete_layout_btn = QPushButton("🗑️"); delete_layout_btn.setToolTip("Layout löschen"); delete_layout_btn.setMaximumWidth(35); delete_layout_btn.clicked.connect(self.on_delete_layout_clicked); layout_layout.addWidget(delete_layout_btn)
        toolbar_layout.addWidget(layout_group)

        view_group = QGroupBox("Ansicht")
        view_layout = QHBoxLayout(view_group)
        reset_layout_btn = QPushButton("🔄 Zurücksetzen"); reset_layout_btn.clicked.connect(self.reset_layout_to_default); view_layout.addWidget(reset_layout_btn)
        tile_btn = QPushButton("🗃️ Kacheln"); tile_btn.clicked.connect(self.mdi_area.tileSubWindows); view_layout.addWidget(tile_btn)
        cascade_btn = QPushButton("📚 Kaskade"); cascade_btn.clicked.connect(self.mdi_area.cascadeSubWindows); view_layout.addWidget(cascade_btn)
        toolbar_layout.addWidget(view_group)

        toolbar_layout.addStretch()
        return toolbar_layout

    def _create_widgets(self): # Wie zuvor, erstellt nur noch vorhandene Widgets
        for name, definition in self.widget_definitions.items():
            init_args = definition.get('init_args', {})
            widget_instance = definition['class'](**init_args) if init_args else definition['class']()
            setattr(self, f"{name}_widget", widget_instance)
            sub_window = QMdiSubWindow(); sub_window.setWidget(widget_instance)
            sub_window.setWindowTitle(f"{definition['icon']} {definition['title']}")
            sub_window.setGeometry(*definition['geom']); sub_window.setObjectName(name)
            self.mdi_area.addSubWindow(sub_window)
            sub_window.setVisible(name in self.visible_widgets)
            self.widgets[name] = {'window': sub_window, 'widget': widget_instance, 'definition': definition}
        # Aliase für noch vorhandene Widgets
        if 'sensor_display' in self.widgets: self.sensor_display_widget = self.widgets['sensor_display']['widget']
        if 'live_chart' in self.widgets: self.live_chart_widget = self.widgets['live_chart']['widget']
        if 'pin_overview' in self.widgets: self.pin_overview_widget = self.widgets['pin_overview']['widget']
        if 'connection' in self.widgets: self.connection_widget = self.widgets['connection']['widget']
        if 'quick_sequence' in self.widgets: self.quick_sequence_widget = self.widgets['quick_sequence']['widget']
        if 'activity' in self.widgets: self.activity_widget = self.widgets['activity']['widget']
        if 'sequence_info' in self.widgets: self.sequence_info_widget = self.widgets['sequence_info']['widget']

    def setup_connections(self): # Wie zuvor, verbindet nur noch vorhandene Widgets
        if hasattr(self, 'connection_widget'):
            self.connection_widget.connect_requested.connect(self.connect_requested)
            self.connection_widget.disconnect_requested.connect(self.disconnect_requested)
            self.connection_widget.refresh_ports_requested.connect(self.refresh_ports_requested)
        if hasattr(self, 'quick_sequence_widget'):
            self.quick_sequence_widget.start_sequence_signal.connect(self.start_sequence_signal)
            self.quick_sequence_widget.start_test_run_signal.connect(self.start_test_run_signal)

    def open_widget_selector(self): # Wie zuvor
        dialog = WidgetSelectorDialog(self.widget_definitions, self.visible_widgets, self)
        if dialog.exec():
            new_visible = dialog.get_selected_widgets()
            for widget_id in self.widget_definitions.keys():
                should_be_visible = widget_id in new_visible
                is_currently_visible = widget_id in self.visible_widgets
                if should_be_visible != is_currently_visible: self.widgets[widget_id]['window'].setVisible(should_be_visible)
            self.visible_widgets = new_visible
            for widget_id, toggle in self.quick_toggles.items():
                toggle.blockSignals(True); toggle.setChecked(widget_id in self.visible_widgets); toggle.blockSignals(False)

    def toggle_widget_visibility(self, widget_id, state): # Wie zuvor
        is_visible = (state == Qt.CheckState.Checked.value)
        if widget_id in self.widgets:
            self.widgets[widget_id]['window'].setVisible(is_visible)
            if is_visible: self.visible_widgets.add(widget_id)
            else: self.visible_widgets.discard(widget_id)

    def add_optional_widget(self, widget_id, title, icon, widget_instance, geometry, category='Erweitert'): # Wie zuvor
        if widget_id in self.widget_definitions: print(f"⚠️ Widget '{widget_id}' existiert bereits!"); return False
        self.widget_definitions[widget_id] = {'class': widget_instance.__class__, 'title': title, 'icon': icon, 'geom': geometry, 'category': category}
        sub_window = QMdiSubWindow(); sub_window.setWidget(widget_instance); sub_window.setWindowTitle(f"{icon} {title}"); sub_window.setGeometry(*geometry); sub_window.setObjectName(widget_id)
        self.mdi_area.addSubWindow(sub_window); sub_window.setVisible(False)
        self.widgets[widget_id] = {'window': sub_window, 'widget': widget_instance, 'definition': self.widget_definitions[widget_id]}
        setattr(self, f"{widget_id}_widget", widget_instance)
        print(f"✅ Widget '{title}' zum Dashboard hinzugefügt!"); return True

    def show_widget(self, widget_id): # Wie zuvor
        if widget_id in self.widgets: self.widgets[widget_id]['window'].show(); self.visible_widgets.add(widget_id)

    def hide_widget(self, widget_id): # Wie zuvor
        if widget_id in self.widgets: self.widgets[widget_id]['window'].hide(); self.visible_widgets.discard(widget_id)

    def on_save_layout_clicked(self): # Wie zuvor
        current_name = self.layout_combo.currentText()
        name, ok = QInputDialog.getText(self, "Layout speichern", "Name:", text=current_name)
        if ok and name: self.layout_save_requested.emit(name, self.get_current_layout_config())

    def on_delete_layout_clicked(self): # Wie zuvor
        name = self.layout_combo.currentText()
        if name and name != "Standard": self.layout_delete_requested.emit(name)

    def on_layout_selected(self, name): # Wie zuvor
        if name: self.layout_load_requested.emit(name)

    def get_current_layout_config(self): # Wie zuvor
        layout_config = {'geometry': {}, 'visible_widgets': list(self.visible_widgets)}
        for widget_id, widget_data in self.widgets.items():
            geom = widget_data['window'].geometry()
            layout_config['geometry'][widget_id] = {'x': geom.x(), 'y': geom.y(), 'w': geom.width(), 'h': geom.height()}
        return layout_config

    def apply_layout(self, layout_config): # Wie zuvor
        geometry = layout_config.get('geometry', {})
        for widget_id, geom_data in geometry.items():
            if widget_id in self.widgets: self.widgets[widget_id]['window'].setGeometry(geom_data['x'], geom_data['y'], geom_data['w'], geom_data['h'])
        visible = set(layout_config.get('visible_widgets', self.default_visible))
        self.visible_widgets = visible
        for widget_id, widget_data in self.widgets.items(): widget_data['window'].setVisible(widget_id in visible)
        for widget_id, toggle in self.quick_toggles.items():
            toggle.blockSignals(True); toggle.setChecked(widget_id in visible); toggle.blockSignals(False)

    def update_layout_list(self, layout_names): # Wie zuvor
        self.layout_combo.blockSignals(True); current = self.layout_combo.currentText(); self.layout_combo.clear(); self.layout_combo.addItems(layout_names)
        if current in layout_names: self.layout_combo.setCurrentText(current)
        self.layout_combo.blockSignals(False)

    def reset_layout_to_default(self): # Wie zuvor
        default_config = {
            'geometry': {name: {'x': d['geom'][0], 'y': d['geom'][1], 'w': d['geom'][2], 'h': d['geom'][3]} for name, d in self.widget_definitions.items()},
            'visible_widgets': list(self.default_visible)
        }
        self.apply_layout(default_config)