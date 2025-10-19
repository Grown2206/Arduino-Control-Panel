# In main.py - Diese Änderungen vornehmen:

# === 1. IMPORT ÄNDERN ===
# ALT:
# from ui.dashboard_tab import DashboardTab

# NEU:
from ui.enhanced_dashboard_tab import EnhancedDashboardTab

# === 2. IN setup_ui() ÄNDERN ===
def setup_ui(self):
    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)

    self.tabs = QTabWidget()
    
    # GEÄNDERT: Verwende EnhancedDashboardTab statt DashboardTab
    self.dashboard_tab = EnhancedDashboardTab()
    
    self.pin_control_tab = PinTab()
    self.pin_overview_tab = PinOverviewWidget()
    self.sensor_tab = SensorTab()
    self.sequence_tab = SequenceTab()
    self.chart_tab = LiveChartWidget(title="Live Pin-Aufzeichnung")
    self.archive_tab = ArchiveTab()

    self._create_menu_bar()
    main_layout.addLayout(self._create_connection_bar())

    self.tabs.addTab(self.dashboard_tab, "🏠 Dashboard")
    self.tabs.addTab(self.pin_control_tab, "🔌 Pin Steuerung")
    self.tabs.addTab(self.pin_overview_tab, "📊 Pin Übersicht")
    self.tabs.addTab(self.sensor_tab, "🌡️ Sensoren")
    self.tabs.addTab(self.sequence_tab, "⚙️ Sequenzen")
    self.tabs.addTab(self.chart_tab, "📈 Live-Aufzeichnung")
    self.tabs.addTab(self.archive_tab, "🗄️ Archiv")
    
    # NEU: Neue Features zum Dashboard hinzufügen
    self._add_optional_tabs_to_dashboard()
    
    main_layout.addWidget(self.tabs)

    self.status_bar = QStatusBar()
    self.setStatusBar(self.status_bar)
    self.status_bar.showMessage("Bereit")


# === 3. NEUE METHODE HINZUFÜGEN ===
def _add_optional_tabs_to_dashboard(self):
    """Fügt neue Feature-Widgets zum Dashboard hinzu"""
    
    # Data Logger
    if hasattr(self, 'data_logger_tab') and self.data_logger_tab:
        # Kompakte Version für Dashboard erstellen
        from ui.data_logger_widget import DataLoggerWidget
        dashboard_logger = DataLoggerWidget()
        
        self.dashboard_tab.add_optional_widget(
            widget_id='data_logger',
            title='Data Logger',
            icon='📊',
            widget_instance=dashboard_logger,
            geometry=(860, 10, 400, 300),
            category='Erweitert'
        )
        
        # Mit Haupt-Logger synchronisieren
        def sync_logger(data):
            if data.get('type') == 'pin_update':
                pin = data.get('pin_name')
                value = data.get('value')
                if pin and value is not None:
                    dashboard_logger.log_pin_value(pin, value)
        
        self.worker.data_received.connect(sync_logger)
    
    # LED Matrix Simulator (Mini-Version)
    if hasattr(self, 'led_matrix_tab') and self.led_matrix_tab:
        from ui.led_matrix_simulator import LEDMatrixWidget
        
        dashboard_matrix = LEDMatrixWidget(rows=8, cols=8, led_size=15)
        
        self.dashboard_tab.add_optional_widget(
            widget_id='led_matrix',
            title='LED Matrix',
            icon='💡',
            widget_instance=dashboard_matrix,
            geometry=(860, 320, 400, 300),
            category='Ausgabe'
        )
    
    # Oszilloskop (Kompakt)
    if hasattr(self, 'oscilloscope_tab') and self.oscilloscope_tab:
        # Einfache Chart-Version für Dashboard
        from ui.live_chart_widget import LiveChartWidget
        
        dashboard_scope = LiveChartWidget(title="Oszilloskop (A0-A1)")
        
        self.dashboard_tab.add_optional_widget(
            widget_id='oscilloscope',
            title='Oszilloskop',
            icon='📡',
            widget_instance=dashboard_scope,
            geometry=(860, 630, 400, 170),
            category='Messung'
        )
        
        # Nur A0 und A1 anzeigen
        def forward_to_dash_scope(data):
            if data.get('type') == 'pin_update':
                pin = data.get('pin_name')
                value = data.get('value')
                if pin in ['A0', 'A1'] and value is not None:
                    import time
                    dashboard_scope.add_data_point(pin, value, time.time())
        
        self.worker.data_received.connect(forward_to_dash_scope)
    
    # PWM Schnellzugriff
    if hasattr(self, 'pwm_servo_tab') and self.pwm_servo_tab:
        from ui.pwm_quick_widget import PWMQuickWidget  # Siehe unten
        
        dashboard_pwm = PWMQuickWidget()
        dashboard_pwm.command_signal.connect(self.send_command)
        
        self.dashboard_tab.add_optional_widget(
            widget_id='pwm_quick',
            title='PWM Schnellzugriff',
            icon='⚡',
            widget_instance=dashboard_pwm,
            geometry=(1270, 10, 280, 200),
            category='Steuerung'
        )
    
    # Makro Schnellstart
    if hasattr(self, 'macro_tab') and self.macro_tab:
        from ui.macro_quick_widget import MacroQuickWidget  # Siehe unten
        
        dashboard_macros = MacroQuickWidget()
        
        self.dashboard_tab.add_optional_widget(
            widget_id='macro_quick',
            title='Makro Schnellstart',
            icon='🤖',
            widget_instance=dashboard_macros,
            geometry=(1270, 220, 280, 200),
            category='Automatisierung'
        )


# === 4. LAYOUT-SPEICHERUNG ANPASSEN ===
def save_dashboard_layout(self, name, layout_config):
    """Speichert Dashboard-Layout (mit Sichtbarkeit)"""
    self.dashboard_layouts[name] = layout_config
    self.dashboard_tab.update_layout_list(list(self.dashboard_layouts.keys()))
    self.dashboard_tab.layout_combo.setCurrentText(name)
    self.auto_save_config()
    self.status_bar.showMessage(f"Layout '{name}' gespeichert.", 2000)

def load_dashboard_layout(self, name):
    """Lädt Dashboard-Layout (mit Sichtbarkeit)"""
    layout_config = self.dashboard_layouts.get(name)
    if layout_config:
        self.dashboard_tab.apply_layout(layout_config)
        self.status_bar.showMessage(f"Layout '{name}' geladen.", 2000)
