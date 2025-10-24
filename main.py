# -*- coding: utf-8 -*-
import sys
import os
import uuid
import serial.tools.list_ports
import time
import numpy as np
import base64
import logging

# Setup Logging with UTF-8 encoding to support Unicode characters (emojis, etc.)
import io

# Create a UTF-8 encoded stdout wrapper for logging to prevent UnicodeEncodeError on Windows
utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arduino_panel.log', encoding='utf-8'),
        logging.StreamHandler(utf8_stdout)
    ]
)
logger = logging.getLogger("ArduinoPanel")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QPushButton, QCheckBox, QStatusBar, QTabWidget,
                             QInputDialog, QMessageBox, QDialog, QTextEdit, QListWidget, QFileDialog,
                             QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut, QAction

# --- CORE ---
from core.database import Database
from core.database_worker import DatabaseWorker
from core.config_manager import ConfigManager
from core.serial_worker import SerialWorker
from core.sequence_runner import SequenceRunner
from core.validators import PinValidator, SensorValidator, ConfigValidator

# --- ANALYSIS ---
from analysis.trend_analyzer import TrendAnalyzer  # ✅ Erweiterte Version mit Quality-Metrics  # ✅ Erweiterte Version mit Quality-Metrics
from analysis.report_generator import ReportGenerator
from analysis.report_viewer import ReportViewerDialog
from analysis.comparison_viewer import ComparisonViewerDialog
from analysis.export_manager import ExportManager  # NEU: CSV Export

# --- UI ---
from ui.pin_tab import PinTab
from ui.pin_overview_widget import PinOverviewWidget
from ui.sequence_tab import SequenceTab
from ui.archive_tab import ArchiveTab
from ui.live_chart_widget import LiveChartWidget
from ui.sequence_dialog import SequenceDialog
from ui.sensor_tab import SensorTab
from ui.enhanced_dashboard_tab import EnhancedDashboardTab
from live_stats_widget import LiveStatsWidget
from ui.branding import get_full_stylesheet, LOGO_PATH
from ui.sequence_info_widget import SequenceInfoWidget
# NEU: Board Config Tab importieren
from ui.board_config_tab import BoardConfigTab

# NEU: Analytics Dashboard
try:
    from ui.analytics_dashboard import AnalyticsDashboardTab
    ANALYTICS_DASHBOARD_AVAILABLE = True
    print('✅ Analytics Dashboard verfügbar')
except ImportError as e:
    ANALYTICS_DASHBOARD_AVAILABLE = False
    print(f'⚠️ Analytics Dashboard nicht verfügbar: {e}')

# NEU: Hardware Profile Management
try:
    from ui.hardware_profile_tab import HardwareProfileTab
    from core.hardware_profile_manager import HardwareProfileManager
    HARDWARE_PROFILE_AVAILABLE = True
    print('✅ Hardware Profile Management verfügbar')
except ImportError as e:
    HARDWARE_PROFILE_AVAILABLE = False
    print(f'⚠️ Hardware Profile Management nicht verfügbar: {e}')

# === NEUE FEATURES ===
# Hardware-Simulation
try:
    from hardware_simulator import ArduinoSimulator, create_simulator
    SIMULATOR_AVAILABLE = True
    print('✅ Hardware-Simulator verfügbar')
except ImportError:
    SIMULATOR_AVAILABLE = False
    print('⚠️ Hardware-Simulator nicht gefunden')

# Theme-Manager
try:
    from ui.theme_manager import ThemeManager
    THEME_MANAGER_AVAILABLE = True
except ImportError:
    THEME_MANAGER_AVAILABLE = False

# --- ADVANCED FEATURES ---
try:
    from advanced_features_fixed import integrate_advanced_features
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

class MainWindow(QMainWindow):
    pin_update_for_runner = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        # ... (Rest von __init__ bleibt größtenteils gleich) ...
        self.setWindowTitle("Drexler Dynamics - Arduino Control Panel")
        self.setGeometry(100, 100, 1600, 950)
        if os.path.exists(LOGO_PATH): self.setWindowIcon(QIcon(LOGO_PATH))
        print("Starte Arduino Control Panel...")
        self.data_handlers = []
        self.sequences = {}
        self.dashboard_layouts = {}
        self.db = Database(db_file="arduino_tests.db")
        self.db_thread = QThread(); self.db_worker = DatabaseWorker(db_file="arduino_tests.db")
        self.db_worker.moveToThread(self.db_thread); self.db_thread.start()
        print("Asynchroner Datenbank-Worker gestartet.")
        self.config_manager = ConfigManager(config_file="arduino_config.json")
        self.worker = SerialWorker()
        self.seq_runner = SequenceRunner()
        self.current_test_id = None; self.sensor_log = []; self.test_start_time = 0
        self.chart_start_time = time.time()
        self.active_sensor_config_for_polling = {} # Speichert, welche Sensoren gepollt werden sollen
        self.current_theme = "dark"  # NEU: Theme-Tracking

        # Command Queue für sequentielle Befehle ohne UI-Blocking
        self.command_queue = []
        self.command_timer = QTimer(self)
        self.command_timer.timeout.connect(self._process_command_queue)

        # === Live-Statistik-Widget ===
        self.live_stats_widget = LiveStatsWidget()
        print("✅ Live-Statistik-Widget initialisiert")

        self.setup_ui()
        self.setup_connections()
        self.setStyleSheet(get_full_stylesheet())
        self.load_saved_config() # Lädt auch Board Config

        # ... (Advanced Features, Timer, etc.) ...
        if ADVANCED_FEATURES_AVAILABLE:
            print("\n🔧 Integriere Advanced Features...")
            integrate_advanced_features(self)
            print("✅ Advanced Features erfolgreich integriert!")
        self.auto_save_timer = QTimer(self, timeout=self.auto_save_config, interval=30000); self.auto_save_timer.start()
        self.sensor_poll_timer = QTimer(self, timeout=self.poll_sensors)

        # Keyboard Shortcuts einrichten
        self.setup_shortcuts()

        print("\nAnwendung bereit.")


    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()

        # --- Basis-Tabs ---
        self.dashboard_tab = EnhancedDashboardTab()

        # Live-Statistik Widget

        # === Live-Statistik zum Dashboard ===
        if hasattr(self, "dashboard_tab") and hasattr(self.dashboard_tab, "add_widget"):
            try:
                self.dashboard_tab.add_widget(
                    widget_id="live_stats",
                    title="📊 Live-Statistiken",
                    icon="📊",
                    widget_instance=self.live_stats_widget,
                    geometry=(10, 400, 400, 550),
                    category="Monitoring"
                )
                print("✅ Live-Stats zum Dashboard hinzugefügt")
            except Exception as e:
                print(f"⚠️ Dashboard-Integration fehlgeschlagen: {e}")
                # Fallback: Dock-Widget
                # Fallback: Als Dock-Widget
                from PyQt6.QtWidgets import QDockWidget
                from PyQt6.QtCore import Qt
                
                self.live_stats_dock = QDockWidget("📊 Live-Statistiken", self)
                self.live_stats_dock.setWidget(self.live_stats_widget)
                self.live_stats_dock.setFeatures(
                    QDockWidget.DockWidgetFeature.DockWidgetMovable |
                    QDockWidget.DockWidgetFeature.DockWidgetFloatable
                )
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.live_stats_dock)
                print("✅ Live-Stats als Dock-Widget hinzugefügt")


        # Live-Statistik Widget
        self.pin_control_tab = PinTab()
        self.pin_overview_tab = PinOverviewWidget()
        self.sensor_tab = SensorTab() # Wird evtl. weniger relevant, behalten wir vorerst
        self.sequence_tab = SequenceTab()
        self.chart_tab = LiveChartWidget(title="Live Pin-Aufzeichnung")
        self.archive_tab = ArchiveTab()
        # NEU: Board Config Tab Instanz erstellen
        self.board_config_tab = BoardConfigTab(self.config_manager)


        self._create_menu_bar()
        main_layout.addLayout(self._create_connection_bar())

        self.tabs.addTab(self.dashboard_tab, "🏠 Dashboard")
        # NEU: Board Config Tab hinzufügen (z.B. nach Dashboard)
        self.tabs.addTab(self.board_config_tab, "🛠️ Board Konfiguration")

        # NEU: Hardware Profile Tab
        if HARDWARE_PROFILE_AVAILABLE:
            try:
                self.hardware_profile_tab = HardwareProfileTab()
                # Verbinde Signal zum Laden von Profilen
                self.hardware_profile_tab.load_profile_signal.connect(self.load_hardware_profile)
                self.tabs.addTab(self.hardware_profile_tab, "💾 Profile")
                print("✅ Hardware Profile Tab hinzugefügt")
            except Exception as e:
                print(f"⚠️ Hardware Profile Tab konnte nicht geladen werden: {e}")
                self.hardware_profile_tab = None
        else:
            self.hardware_profile_tab = None

        self.tabs.addTab(self.pin_control_tab, "🔌 Pin Steuerung")
        self.tabs.addTab(self.pin_overview_tab, "📊 Pin Übersicht")
        self.tabs.addTab(self.sensor_tab, "🌡️ Sensoren")
        self.tabs.addTab(self.sequence_tab, "⚙️ Sequenzen")
        self.tabs.addTab(self.chart_tab, "📈 Live-Aufzeichnung")
        self.tabs.addTab(self.archive_tab, "🗄️ Archiv")

        # NEU: Analytics Dashboard Tab
        if ANALYTICS_DASHBOARD_AVAILABLE:
            try:
                self.analytics_tab = AnalyticsDashboardTab(db_file="arduino_tests.db")
                self.tabs.addTab(self.analytics_tab, "📊 Analytics")
                print("✅ Analytics Dashboard Tab hinzugefügt")
            except Exception as e:
                print(f"⚠️ Analytics Dashboard konnte nicht geladen werden: {e}")
                self.analytics_tab = None
        else:
            self.analytics_tab = None

        self._add_optional_tabs() # Fügt weitere Tabs hinzu
        self._add_optional_tabs_to_dashboard() # Fügt Widgets zum Dashboard hinzu

        main_layout.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bereit")
        
        # In main.py, nach setup_ui()
        print(f"Live-Stats erstellt: {hasattr(self, 'live_stats_widget')}")
        print(f"Dashboard vorhanden: {hasattr(self, 'dashboard_tab')}")


        # === GARANTIERT: Live-Stats als Dock-Widget ===
        # Falls Dashboard-Integration fehlschlägt, wird es hier trotzdem hinzugefügt
        if not hasattr(self, 'live_stats_dock'):
            from PyQt6.QtWidgets import QDockWidget
            from PyQt6.QtCore import Qt
            
            self.live_stats_dock = QDockWidget('📊 Live-Statistiken', self)
            self.live_stats_dock.setWidget(self.live_stats_widget)
            self.live_stats_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable |
                QDockWidget.DockWidgetFeature.DockWidgetFloatable
            )
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.live_stats_dock)
            print('✅ Live-Stats Dock-Widget (Garantie-Code) hinzugefügt')

    def _add_optional_tabs(self):
        """ Fügt optionale Tabs hinzu (ohne PWM/Servo, LED Matrix) """
        try:
            from ui.data_logger_widget import DataLoggerWidget
            self.data_logger_tab = DataLoggerWidget(); self.tabs.addTab(self.data_logger_tab, "📝 Data Logger")
            print("✅ Data Logger geladen")
        except ImportError: self.data_logger_tab = None
        try:
            from ui.oscilloscope_widget import OscilloscopeWidget
            self.oscilloscope_tab = OscilloscopeWidget(); self.tabs.addTab(self.oscilloscope_tab, "📡 Oszilloskop")
            print("✅ Oszilloskop geladen")
        except ImportError: self.oscilloscope_tab = None
        try:
            from ui.macro_system import MacroRecorder
            self.macro_tab = MacroRecorder(); self.tabs.addTab(self.macro_tab, "🤖 Makros")
            print("✅ Makro-Recorder geladen")
        except ImportError: self.macro_tab = None
        try:
            from ui.relay_control_tab import RelayControlTab
            self.relay_tab = RelayControlTab(self.config_manager); self.tabs.addTab(self.relay_tab, "🔩 Relais Steuerung")
            print("✅ Relais Steuerung geladen")
        except ImportError as e: self.relay_tab = None; print(f"⚠️ Relais Steuerung nicht verfügbar: {e}")

    def _add_optional_tabs_to_dashboard(self):
         """ Fügt Widgets zum Dashboard hinzu (ohne PWM/Servo, LED Matrix) """
         if hasattr(self, 'data_logger_tab') and self.data_logger_tab:
            from ui.data_logger_widget import DataLoggerWidget
            dashboard_logger = DataLoggerWidget()
            self.dashboard_tab.add_optional_widget('data_logger', 'Data Logger', '📝', dashboard_logger, (860, 310, 400, 300), 'Erweitert')
            def sync_logger(data):
                if data.get('type') == 'pin_update':
                    pin, value = data.get('pin_name'), data.get('value')
                    if pin and value is not None: dashboard_logger.log_pin_value(pin, value)
            self.worker.data_received.connect(sync_logger)

         if hasattr(self, 'oscilloscope_tab') and self.oscilloscope_tab:
            from ui.live_chart_widget import LiveChartWidget
            dashboard_scope = LiveChartWidget(title="Oszilloskop (A0-A1)")
            self.dashboard_tab.add_optional_widget('oscilloscope', 'Oszilloskop', '📡', dashboard_scope, (1270, 630, 280, 170), 'Messung')
            def forward_to_dash_scope(data):
                if data.get('type') == 'pin_update':
                    pin, value = data.get('pin_name'), data.get('value')
                    if pin in ['A0', 'A1'] and value is not None: dashboard_scope.add_data_point(pin, value, time.time())
            self.worker.data_received.connect(forward_to_dash_scope)

         if hasattr(self, 'macro_tab') and self.macro_tab:
            from ui.macro_quick_widget import MacroQuickWidget
            dashboard_macros = MacroQuickWidget()
            # if hasattr(dashboard_macros, 'play_macro_signal'):
            #      dashboard_macros.play_macro_signal.connect(self.play_macro_by_name) # Implementiere play_macro_by_name
            self.dashboard_tab.add_optional_widget('macro_quick','Makro Schnellstart','🤖',dashboard_macros,(1270, 220, 280, 200),'Automatisierung')

         if hasattr(self, 'relay_tab') and self.relay_tab:
            try:
                from ui.relay_quick_widget import RelayQuickWidget
                dashboard_relay = RelayQuickWidget(self.config_manager); dashboard_relay.command_signal.connect(self.send_command)
                self.dashboard_tab.add_optional_widget('relay_quick','Relais Schnellzugriff','🔩',dashboard_relay,(1270, 430, 280, 200),'Steuerung')
                print("✅ Relais Schnellzugriff geladen und verbunden.")
            except ImportError as e: print(f"⚠️ Relais Schnellzugriff nicht verfügbar: {e}")

    def _create_menu_bar(self):
        menubar = self.menuBar()

        # Datei-Menü
        file_menu = menubar.addMenu("Datei")
        save_action = file_menu.addAction("💾 Speichern"); save_action.triggered.connect(self.auto_save_config); save_action.setShortcut("Ctrl+S")
        load_action = file_menu.addAction("📂 Laden"); load_action.triggered.connect(self.load_saved_config); load_action.setShortcut("Ctrl+O")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("❌ Beenden"); exit_action.triggered.connect(self.close)

        # NEU: Ansicht-Menü mit Theme Toggle
        view_menu = menubar.addMenu("Ansicht")
        self.theme_action = view_menu.addAction("🌓 Dark/Light Theme")
        self.theme_action.triggered.connect(self.toggle_theme)
        self.theme_action.setShortcut("Ctrl+T")


    def _create_connection_bar(self): # Unverändert
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox(); self.refresh_ports(); conn_layout.addWidget(self.port_combo)
        refresh_btn = QPushButton("↻"); refresh_btn.setMaximumWidth(40); refresh_btn.clicked.connect(self.refresh_ports); conn_layout.addWidget(refresh_btn)
        self.sim_check = QCheckBox("Simulation"); conn_layout.addWidget(self.sim_check)
        self.connect_btn = QPushButton("Verbinden"); self.connect_btn.clicked.connect(self.initiate_connection) # Geändert auf initiate_connection
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addStretch()
        return conn_layout


        # === NEUE FEATURES ===
        # Tools-Menü erweitern
        if hasattr(self, 'tools_menu'):
            # Simulator Toggle
            if SIMULATOR_AVAILABLE:
                self.simulator_action = self.tools_menu.addAction('🎮 Simulator-Modus')
                self.simulator_action.setCheckable(True)
                self.simulator_action.setChecked(self.use_simulator)
                self.simulator_action.triggered.connect(self.toggle_simulator)

            # Theme-Menü
            if THEME_MANAGER_AVAILABLE:
                theme_menu = self.tools_menu.addMenu('🎨 Theme')
                
                dark_action = theme_menu.addAction('🌙 Dark')
                dark_action.triggered.connect(lambda: self.change_theme('dark'))
                
                light_action = theme_menu.addAction('☀️ Light')
                light_action.triggered.connect(lambda: self.change_theme('light'))
                
                contrast_action = theme_menu.addAction('🔲 High Contrast')
                contrast_action.triggered.connect(lambda: self.change_theme('high_contrast'))

            # Fullscreen
            fullscreen_action = self.tools_menu.addAction('🖥️ Fullscreen (F11)')
            fullscreen_action.setShortcut('F11')
            fullscreen_action.triggered.connect(self.toggle_fullscreen)

        # === NEUE FEATURES ===
        # Tools-Menü erweitern
        if hasattr(self, 'tools_menu'):
            # Simulator Toggle
            if SIMULATOR_AVAILABLE:
                self.simulator_action = self.tools_menu.addAction('🎮 Simulator-Modus')
                self.simulator_action.setCheckable(True)
                self.simulator_action.setChecked(self.use_simulator)
                self.simulator_action.triggered.connect(self.toggle_simulator)

            # Theme-Menü
            if THEME_MANAGER_AVAILABLE:
                theme_menu = self.tools_menu.addMenu('🎨 Theme')
                
                dark_action = theme_menu.addAction('🌙 Dark')
                dark_action.triggered.connect(lambda: self.change_theme('dark'))
                
                light_action = theme_menu.addAction('☀️ Light')
                light_action.triggered.connect(lambda: self.change_theme('light'))
                
                contrast_action = theme_menu.addAction('🔲 High Contrast')
                contrast_action.triggered.connect(lambda: self.change_theme('high_contrast'))

            # Fullscreen
            fullscreen_action = self.tools_menu.addAction('🖥️ Fullscreen (F11)')
            fullscreen_action.setShortcut('F11')
            fullscreen_action.triggered.connect(self.toggle_fullscreen)

    def setup_connections(self):
        """ Verbindet Signale und Slots """
        # --- Core ---
        self.worker.data_received.connect(self.handle_data)
        self.worker.status_changed.connect(self.update_status)

        # === Live-Stats Signals ===
        if hasattr(self, "seq_runner") and hasattr(self.seq_runner, "cycle_completed"):
            self.seq_runner.cycle_completed.connect(
                self.live_stats_widget.add_cycle
            )
            print("✅ Live-Stats Signals verbunden")
        else:
            print("⚠️ SequenceRunner hat kein cycle_completed Signal")

        self.db.add_run_requested.connect(self.db_worker.add_run)
        self.db.update_run_requested.connect(self.db_worker.update_run)

        # --- Pin Control ---
        self.pin_control_tab.command_signal.connect(self.send_command)

        # --- Sequence ---
        self.seq_runner.command_signal.connect(self.send_command)
        self.seq_runner.step_update.connect(self.sequence_tab.update_sequence_info)
        if hasattr(self.dashboard_tab, 'sequence_info_widget'): # Prüfen ob Widget existiert
            self.seq_runner.step_update.connect(self.dashboard_tab.sequence_info_widget.update_sequence_info)
        self.seq_runner.step_highlight_signal.connect(self.sequence_tab.highlight_step)
        self.seq_runner.finished.connect(self.sequence_finished)
        self.pin_update_for_runner.connect(self.seq_runner.on_pin_update)
        self.sequence_tab.start_sequence_signal.connect(self.start_sequence)
        self.sequence_tab.start_test_run_signal.connect(self.start_test_run)
        self.sequence_tab.stop_sequence_signal.connect(self.seq_runner.stop_sequence)
        self.sequence_tab.pause_sequence_signal.connect(self.seq_runner.pause_sequence)
        self.sequence_tab.new_sequence_signal.connect(self.new_sequence)
        self.sequence_tab.edit_sequence_signal.connect(self.edit_sequence)
        self.sequence_tab.delete_sequence_signal.connect(self.delete_sequence)
        self.sequence_tab.toggle_favorite_signal.connect(self.toggle_favorite)  # NEU: Favoriten
        self.sequence_tab.sequence_updated_signal.connect(self.on_sequence_updated_from_editor)

        # --- Archive ---
        self.archive_tab.refresh_signal.connect(self.load_archive)
        self.archive_tab.export_pdf_signal.connect(self.export_pdf)
        self.archive_tab.export_excel_signal.connect(self.export_excel)
        self.archive_tab.export_csv_signal.connect(self.export_csv)  # NEU: CSV Export
        self.archive_tab.show_analysis_signal.connect(self.show_trend_analysis)
        self.archive_tab.show_report_signal.connect(self.show_report_viewer)
        self.archive_tab.compare_runs_signal.connect(self.show_comparison_report)

        # --- Sensor ---
        self.sensor_tab.poll_interval_changed.connect(self.update_poll_interval) # Sollte jetzt funktionieren

        # --- Chart ---
        self.chart_tab.clear_button_pressed.connect(self.clear_chart)

        # --- Tabs ---
        self.tabs.currentChanged.connect(lambda i: self.load_archive() if self.tabs.widget(i) == self.archive_tab else None)

        # --- Dashboard ---
        self.dashboard_tab.connect_requested.connect(self.handle_dashboard_connect)
        self.dashboard_tab.disconnect_requested.connect(self.disconnect_connection) # Geändert auf disconnect_connection
        self.dashboard_tab.refresh_ports_requested.connect(self.refresh_ports)
        self.dashboard_tab.start_sequence_signal.connect(self.start_sequence)
        self.dashboard_tab.start_test_run_signal.connect(self.start_test_run)
        if hasattr(self.dashboard_tab, 'live_chart_widget'):
             self.dashboard_tab.live_chart_widget.clear_button_pressed.connect(self.clear_chart)
        self.dashboard_tab.layout_save_requested.connect(self.save_dashboard_layout)
        self.dashboard_tab.layout_delete_requested.connect(self.delete_dashboard_layout)
        self.dashboard_tab.layout_load_requested.connect(self.load_dashboard_layout)

        # NEU: Board Config Tab Signal verbinden
        self.board_config_tab.apply_config_signal.connect(self.apply_config_and_connect)

        # --- Optionale Tabs (Rest) ---

        if hasattr(self, 'data_logger_tab') and self.data_logger_tab:
            def forward_to_data_logger(data):
                if data.get('type') == 'pin_update':
                    pin, value = data.get('pin_name'), data.get('value')
                    if pin and value is not None: self.data_logger_tab.log_pin_value(pin, value)
            self.worker.data_received.connect(forward_to_data_logger)

        if hasattr(self, 'oscilloscope_tab') and self.oscilloscope_tab:
            def forward_to_oscilloscope(data):
                if data.get('type') == 'pin_update':
                    pin, value = data.get('pin_name'), data.get('value')
                    if pin and value is not None and pin.startswith('A'): self.oscilloscope_tab.add_sample(pin, value)
            self.worker.data_received.connect(forward_to_oscilloscope)
            self.oscilloscope_update_timer = QTimer(self); self.oscilloscope_update_timer.timeout.connect(self.oscilloscope_tab.update_plot); self.oscilloscope_update_timer.start(100)

        if hasattr(self, 'macro_tab') and self.macro_tab:
            self.macro_tab.command_signal.connect(self.send_command)
            def record_pin_action(data):
                 if not self.macro_tab.recording: return
                 if data.get('type') == 'pin_update':
                     pin, value = data.get('pin_name'), data.get('value')
                     if pin and value is not None and pin.startswith('D'):
                         self.macro_tab.record_action(action_type='pin_write', parameters={'pin': pin, 'value': value}, description=f"{pin} → {value}")
            self.worker.data_received.connect(record_pin_action)

        if hasattr(self, 'relay_tab') and self.relay_tab:
            self.relay_tab.command_signal.connect(self.send_command)
            def forward_to_relay_widgets(data):
                if data.get('type') == 'pin_update':
                    pin_name = data.get('pin_name', ''); value = data.get('value')
                    if pin_name.startswith('D') and pin_name[1:].isdigit() and value is not None:
                        pin_int = int(pin_name[1:])
                        self.relay_tab.update_pin_state(pin_int, value)
                        try:
                            if hasattr(self.dashboard_tab, 'relay_quick_widget'): self.dashboard_tab.relay_quick_widget.update_pin_state(pin_int, value)
                        except AttributeError as e:
                            logger.debug(f"Relay quick widget nicht verfügbar: {e}")
            self.worker.data_received.connect(forward_to_relay_widgets)
        try: # Relay Quick Widget
            if hasattr(self.dashboard_tab, 'relay_quick_widget'): self.dashboard_tab.relay_quick_widget.command_signal.connect(self.send_command)
        except AttributeError: pass

    def setup_shortcuts(self):
        """Richtet Keyboard Shortcuts ein."""
        logger.info("Richte Keyboard Shortcuts ein...")

        # Ctrl+S: Konfiguration speichern
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_config_shortcut)

        # Ctrl+R: Aktuell ausgewählte Sequenz starten
        run_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        run_shortcut.activated.connect(self.start_sequence_shortcut)

        # Ctrl+Q: Anwendung beenden
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

        # F5: Aktuellen Tab aktualisieren
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh_current_tab)

        logger.info("✅ Keyboard Shortcuts eingerichtet (Ctrl+S, Ctrl+R, Ctrl+Q, F5)")

    def save_config_shortcut(self):
        """Speichert die aktuelle Konfiguration (Ctrl+S)."""
        try:
            self.auto_save_config()
            self.status_bar.showMessage("✅ Konfiguration gespeichert", 2000)
            logger.info("Konfiguration manuell gespeichert (Ctrl+S)")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
            self.status_bar.showMessage(f"❌ Fehler beim Speichern: {e}", 3000)

    def start_sequence_shortcut(self):
        """Startet die aktuell ausgewählte Sequenz (Ctrl+R)."""
        try:
            # Versuche, die aktuell ausgewählte Sequenz zu ermitteln
            if hasattr(self.sequence_tab, 'seq_list') and self.sequence_tab.seq_list.currentItem():
                seq_id = self.sequence_tab.seq_list.currentItem().data(Qt.ItemDataRole.UserRole)
                if seq_id:
                    logger.info(f"Starte Sequenz via Ctrl+R: {seq_id}")
                    self.start_test_run(seq_id)
                    self.status_bar.showMessage(f"▶️ Sequenz gestartet", 2000)
                else:
                    self.status_bar.showMessage("⚠️ Keine Sequenz ausgewählt", 2000)
            else:
                self.status_bar.showMessage("⚠️ Keine Sequenz ausgewählt", 2000)
        except Exception as e:
            logger.error(f"Fehler beim Starten der Sequenz: {e}")
            self.status_bar.showMessage(f"❌ Fehler: {e}", 3000)

    def refresh_current_tab(self):
        """Aktualisiert den aktuellen Tab (F5)."""
        try:
            current_widget = self.tabs.currentWidget()

            if current_widget == self.archive_tab:
                self.load_archive()
                self.status_bar.showMessage("🔄 Archiv aktualisiert", 2000)
                logger.info("Archiv aktualisiert (F5)")
            elif current_widget == self.dashboard_tab:
                # Dashboard-Daten aktualisieren
                self.refresh_ports()
                if hasattr(self.dashboard_tab, 'refresh'):
                    self.dashboard_tab.refresh()
                self.status_bar.showMessage("🔄 Dashboard aktualisiert", 2000)
                logger.info("Dashboard aktualisiert (F5)")
            elif current_widget == self.sequence_tab:
                # Sequenzliste aktualisieren
                self.sequence_tab.update_sequence_list(self.sequences)
                self.status_bar.showMessage("🔄 Sequenzen aktualisiert", 2000)
                logger.info("Sequenzen aktualisiert (F5)")
            elif current_widget == self.pin_overview_tab:
                # Pin-Übersicht aktualisieren
                if hasattr(self.pin_overview_tab, 'refresh'):
                    self.pin_overview_tab.refresh()
                self.status_bar.showMessage("🔄 Pin-Übersicht aktualisiert", 2000)
                logger.info("Pin-Übersicht aktualisiert (F5)")
            else:
                self.status_bar.showMessage("🔄 Tab aktualisiert", 2000)
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren: {e}")
            self.status_bar.showMessage(f"❌ Fehler: {e}", 3000)

    def toggle_theme(self):
        """NEU: Wechselt zwischen Dark und Light Theme (Ctrl+T)"""
        try:
            # Toggle theme
            self.current_theme = "light" if self.current_theme == "dark" else "dark"

            # Apply new stylesheet
            from ui.branding import get_full_stylesheet
            self.setStyleSheet(get_full_stylesheet(self.current_theme))

            # Update status
            theme_name = "Light" if self.current_theme == "light" else "Dark"
            self.status_bar.showMessage(f"🌓 {theme_name} Theme aktiviert", 2000)
            logger.info(f"Theme gewechselt zu: {theme_name}")

            # Save preference to config
            self.config_manager.set("theme", self.current_theme)
            self.config_manager.save_config_to_file()

        except Exception as e:
            logger.error(f"Fehler beim Theme-Wechsel: {e}")
            self.status_bar.showMessage(f"❌ Theme-Fehler: {e}", 3000)

    # --- Connection Handling ---
    def initiate_connection(self):
        """ Startet den Verbindungsprozess: Zeigt Config Tab oder verbindet direkt """
        if self.worker.is_connected():
            self.disconnect_connection() # Wenn verbunden, dann trennen
        else:
            if self.sim_check.isChecked():
                # Simulation direkt starten
                print("Starte Simulation...")
                self.worker.connect_simulation()
                self.sensor_poll_timer.setInterval(self.sensor_tab.get_poll_interval())
                self.sensor_poll_timer.start()
                self.connect_btn.setText("Trennen")
            elif self.port_combo.currentText():
                # Zeige Board Config Tab vor der echten Verbindung
                print("Zeige Board Konfiguration vor Verbindung...")
                self.tabs.setCurrentWidget(self.board_config_tab)
                # Der eigentliche Verbindungsaufbau geschieht in apply_config_and_connect
            else:
                QMessageBox.warning(self, "Fehler", "Kein Port ausgewählt!")

    def apply_config_and_connect(self, config_data):
        """ Empfängt Konfig vom BoardConfigTab, sendet sie und verbindet """
        port = self.port_combo.currentText()
        if not port:
             QMessageBox.warning(self, "Fehler", "Kein Port ausgewählt für Verbindung nach Konfiguration!")
             return

        print(f"Empfangene Konfiguration zum Senden an {port}: {config_data}")
        self.active_sensor_config_for_polling = config_data.get('active_sensors', {})

        # 1. Konfigurationsbefehle senden (sobald Verbindung steht)
        def send_config_after_connect(status_message):
            if "Verbunden" in status_message:
                print("Verbindung hergestellt, sende Sensor-Konfiguration...")
                # Trenne dieses Signal, um Endlosschleife zu vermeiden
                try: self.worker.status_changed.disconnect(send_config_after_connect)
                except TypeError: pass # Falls schon getrennt

                # Validiere Konfiguration mit zentralem Validator
                validated_config = ConfigValidator.validate_config_data(config_data)

                # Sammle alle Befehle in einer Liste (ohne UI-Blocking)
                commands = []

                # Sende Pin Modi (bereits validiert)
                pin_functions = validated_config.get('pin_functions', {})
                for pin_name, function in pin_functions.items():
                    if function == "OUTPUT":
                        cmd = {"id": f"cfg_pm_{pin_name}", "command": "pin_mode", "pin": pin_name, "mode": "OUTPUT"}
                        commands.append(cmd)

                # Sende Sensor-Konfigurationen (bereits validiert)
                active_sensors = validated_config.get('active_sensors', {})
                for sensor_id, sensor_config in active_sensors.items():
                    cmd = {
                        "id": f"cfg_sens_{sensor_id}",
                        "command": "configure_sensor_pin",
                        "sensor_type": sensor_config['sensor_type'],
                        "pin_config": sensor_config['pin_config']
                    }
                    commands.append(cmd)

                # Sende alle Befehle über Queue (non-blocking)
                if commands:
                    self._queue_commands(commands, interval_ms=20)

                print("Sensor-Konfiguration gesendet.")
                # Starte Polling Timer NACHDEM Konfig gesendet wurde
                self.sensor_poll_timer.setInterval(self.sensor_tab.get_poll_interval()) # Nutze Intervall vom SensorTab
                self.sensor_poll_timer.start()
                print(f"Sensor Polling gestartet (Intervall: {self.sensor_poll_timer.interval()}ms).")
                self.connect_btn.setText("Trennen")
                # Wechsle zurück zum Dashboard nach erfolgreicher Konfiguration/Verbindung
                self.tabs.setCurrentWidget(self.dashboard_tab)


            elif "Fehler" in status_message:
                 print("Verbindungsfehler, Konfiguration nicht gesendet.")
                 try: self.worker.status_changed.disconnect(send_config_after_connect)
                 except TypeError: pass

        # Verbinde das Signal *bevor* der Verbindungsversuch gestartet wird
        self.worker.status_changed.connect(send_config_after_connect)
        print(f"Versuche Verbindung zu {port}...")
        self.worker.connect_serial(port)
        # Button wird erst in send_config_after_connect auf "Trennen" gesetzt

    def disconnect_connection(self):
        """ Trennt die Verbindung und stoppt Timer """
        if self.worker.is_connected():
            print("Trenne Verbindung...")
            self.sensor_poll_timer.stop()
            self.worker.disconnect_serial()
            self.connect_btn.setText("Verbinden")
            self.active_sensor_config_for_polling = {} # Polling-Liste leeren

    def handle_dashboard_connect(self, port):
        """ Verbindet über das Dashboard, zeigt aber auch erst Config Tab """
        self.port_combo.setCurrentText(port)
        self.initiate_connection() # Startet den Prozess inkl. Config Tab

    # --- Restliche Methoden (handle_data, update_status, poll_sensors etc.) ---

    def send_command(self, command):
        """Sendet Befehle an den Arduino (mit Debug-Logging)."""
        if isinstance(command, dict):
            # Filter veraltete Commands
            if command.get('command') == 'analog_write':
                logger.debug("analog_write Command ignoriert (nicht unterstützt)")
                return
            if command.get('command', '').startswith('servo_'):
                logger.debug("servo Command ignoriert (nicht unterstützt)")
                return

            # Prüfe Verbindung
            if not self.worker.is_connected():
                logger.warning(f"Command kann nicht gesendet werden - nicht verbunden: {command}")
                return

            # NEU: Aktualisiere Pin-Modus in Overview wenn pin_mode Command
            if command.get('command') == 'pin_mode':
                pin = command.get('pin')
                mode = command.get('mode')
                if pin and mode:
                    self.pin_overview_tab.update_pin_mode(pin, mode)
                    try:
                        if hasattr(self.dashboard_tab, 'pin_overview_widget'):
                            self.dashboard_tab.pin_overview_widget.update_pin_mode(pin, mode)
                    except AttributeError:
                        pass

            # Sende Command
            logger.info(f"Sende Command an Arduino: {command}")
            self.worker.send_command(command)

        elif isinstance(command, str):
            parts = command.split()
            try:
                if len(parts) >= 3 and parts[0] == 'digital_write':
                    pin_str = parts[1] if parts[1].startswith('D') else f"D{parts[1]}"
                    json_cmd = {"id": str(uuid.uuid4()), "command": "digital_write", "pin": pin_str, "value": int(parts[2])}
                    self.send_command(json_cmd)
                elif len(parts) >= 3 and parts[0] == 'pin_mode':
                    pin_str = parts[1] if parts[1].startswith('D') else f"D{parts[1]}"
                    json_cmd = {"id": str(uuid.uuid4()), "command": "pin_mode", "pin": pin_str, "mode": "OUTPUT"}
                    self.send_command(json_cmd)
            except (ValueError, IndexError, KeyError) as e:
                logger.error(f"Fehler bei Konvertierung von Befehl '{command}': {e}", exc_info=True)


    def handle_data(self, data): # Unverändert von letzter Version
         msg_type = data.get("type")
         if msg_type == "response":
             if data.get("status") == "ok":
                 QTimer.singleShot(0, lambda: self.status_bar.setStyleSheet("background-color: #27ae60;"))
                 QTimer.singleShot(1000, lambda: self.status_bar.setStyleSheet(""))
         elif msg_type == "pin_update":
             pin = data.get("pin_name"); value = data.get("value")
             if pin is not None and value is not None:
                 current_time = time.time() - self.chart_start_time
                 self.pin_control_tab.update_pin_value(pin, value)
                 self.pin_overview_tab.update_pin_state(pin, value)
                 self.chart_tab.add_data_point(pin, value, current_time)
                 try:
                     self.dashboard_tab.pin_overview_widget.update_pin_state(pin, value)
                     self.dashboard_tab.live_chart_widget.add_data_point(pin, value, current_time)
                 except AttributeError: pass
                 self.pin_update_for_runner.emit(pin, value)
         elif msg_type == "sensor_update":
             if self.current_test_id is not None: data['time_ms'] = (time.time() - self.test_start_time) * 1000; self.sensor_log.append(data)
             self.sensor_tab.handle_sensor_data(data)
             try:
                 if data.get("sensor") == "B24_TEMP": self.dashboard_tab.sensor_display_widget.update_temperature(data.get("value", 0))
                 elif data.get("sensor") == "B24_HUMIDITY": self.dashboard_tab.sensor_display_widget.update_humidity(data.get("value", 0))
             except AttributeError as e:
                 logger.warning(f"Dashboard sensor widget nicht verfügbar: {e}")
         for handler in self.data_handlers:
             try: handler(data)
             except Exception as e:
                 logger.error(f"Handler {handler.__name__ if hasattr(handler, '__name__') else handler} failed: {e}", exc_info=True)


    def update_status(self, message): # Unverändert von letzter Version
         self.status_bar.showMessage(message)
         is_connected = "Verbunden" in message or "Simulation" in message
         port_name = ""
         if is_connected: port_name = message.split(':')[1].strip() if ':' in message else ("Simulation" if "Simulation" in message else "")
         try:
             self.dashboard_tab.connection_widget.update_status(is_connected, port_name)
             self.dashboard_tab.activity_widget.add_entry(message)
         except AttributeError as e:
             logger.debug(f"Dashboard connection/activity widget nicht verfügbar: {e}")

    # HIER IST DIE FEHLENDE METHODE
    def update_poll_interval(self, interval_ms):
        """Aktualisiert das Sensor-Polling-Intervall"""
        self.sensor_poll_timer.setInterval(interval_ms)
        if self.sensor_poll_timer.isActive():
            self.sensor_poll_timer.start() # Timer neu starten, wenn er läuft, um das Intervall sofort anzuwenden
        self.status_bar.showMessage(f"Sensor-Intervall auf {interval_ms} ms gesetzt.", 2000)

    def poll_sensors(self):
        """ Fragt die *aktiv konfigurierten* Sensoren ab """
        if self.worker.is_connected():
            # print(f"Polling Sensoren: {list(self.active_sensor_config_for_polling.keys())}") # Debug
            for sensor_id in self.active_sensor_config_for_polling.keys():
                # Finde die 'offizielle' ID aus der Konfiguration
                sensor_type = self.active_sensor_config_for_polling[sensor_id].get('sensor_type', sensor_id)
                # print(f"  - Sende read_sensor für: {sensor_type}") # Debug
                self.send_command({
                    "id": f"poll_{sensor_type}_{uuid.uuid4()}",
                    "command": "read_sensor",
                    "sensor": sensor_type # Sende die ID, die der Sketch erwartet (z.B. DHT11)
                })
                # Optional: Kurze Pause zwischen Abfragen, falls nötig
                # time.sleep(0.01)

    # --- Restliche Methoden wie load_saved_config, auto_save_config etc. ---
    # Wichtig: load_saved_config muss ggf. die Konfig vom BoardConfigTab laden
    # Wichtig: auto_save_config muss ggf. die Konfig vom BoardConfigTab speichern

    def load_saved_config(self):
        config = self.config_manager.load_config()
        if not config: return
        self.sequences = config.get("sequences", {})
        self.sequence_tab.update_sequence_list(self.sequences)
        if hasattr(self.dashboard_tab, 'quick_sequence_widget'): self.dashboard_tab.quick_sequence_widget.update_sequences(self.sequences)
        self.pin_control_tab.set_pin_configs(config.get("pin_configs", {}))
        self.dashboard_layouts = config.get("dashboard_layouts", {})
        if "Standard" not in self.dashboard_layouts and hasattr(self.dashboard_tab, 'get_current_layout_config'):
             self.dashboard_layouts["Standard"] = self.dashboard_tab.get_current_layout_config()
        if hasattr(self.dashboard_tab, 'update_layout_list'): self.dashboard_tab.update_layout_list(list(self.dashboard_layouts.keys()))
        if self.dashboard_layouts:
            first_layout_name = list(self.dashboard_layouts.keys())[0]
            self.load_dashboard_layout(first_layout_name)

        # Board Config laden (passiert jetzt in board_config_tab.load_config() beim Start)
        # self.board_config_tab.load_config() # Wird automatisch im Konstruktor gemacht

        if hasattr(self, 'relay_tab') and self.relay_tab:
            self.relay_tab.load_settings()
            try:
                if hasattr(self.dashboard_tab, 'relay_quick_widget'): self.dashboard_tab.relay_quick_widget.load_pin_map()
            except AttributeError as e:
                logger.debug(f"Relay quick widget nicht beim Laden verfügbar: {e}")

        # NEU: Theme laden
        saved_theme = config.get("theme", "dark")
        if saved_theme != self.current_theme:
            self.current_theme = saved_theme
            from ui.branding import get_full_stylesheet
            self.setStyleSheet(get_full_stylesheet(self.current_theme))
            logger.info(f"Theme geladen: {self.current_theme}")

        self.status_bar.showMessage("Konfiguration geladen.", 2000)


    def auto_save_config(self):
        pin_configs = self.pin_control_tab.get_pin_configs()
        current_layout_name = ""
        if hasattr(self.dashboard_tab, 'layout_combo'): current_layout_name = self.dashboard_tab.layout_combo.currentText()
        if current_layout_name and hasattr(self.dashboard_tab, 'get_current_layout_config'):
             self.dashboard_layouts[current_layout_name] = self.dashboard_tab.get_current_layout_config()

        # Board Config speichern (passiert jetzt in board_config_tab.save_config())
        # Die Methode im BoardConfigTab ruft config_manager.set auf.
        # ConfigManager speichert dann alles beim nächsten Aufruf von save_config_to_file()
        # -> save_config_to_file() muss hier oder im BoardConfigTab aufgerufen werden.

        if hasattr(self, 'relay_tab') and self.relay_tab: self.relay_tab.save_settings()

        # Speichere ALLES (inkl. Board Config, die vorher via .set() gesetzt wurde)
        self.config_manager.save_config(self.sequences, pin_configs, self.dashboard_layouts) # Diese Methode ruft intern save_config_to_file() auf

        self.status_bar.showMessage("Konfiguration automatisch gespeichert.", 2000)


    # --- Andere Methoden (clear_chart, sequence_finished, start/stop sequence/test, etc.) ---
    # bleiben weitgehend unverändert, ggf. Prüfungen auf hasattr hinzufügen
    def clear_chart(self): # Unverändert
        self.chart_tab.clear()
        try: self.dashboard_tab.live_chart_widget.clear()
        except AttributeError: pass
        self.chart_start_time = time.time()
        self.status_bar.showMessage("Live-Diagramme zurückgesetzt.", 2000)

    def sequence_finished(self, cycles, status, event_log): # Unverändert von letzter Version
        self.sequence_tab.set_running_state(False); self.sequence_tab.highlight_step(-1)
        if hasattr(self.dashboard_tab, 'sequence_info_widget'): self.dashboard_tab.sequence_info_widget.set_stopped_state()
        if hasattr(self.dashboard_tab, 'activity_widget'): self.dashboard_tab.activity_widget.add_entry(f"Sequenz beendet: {status}")
        if event_log:
            analysis = TrendAnalyzer.analyze_timing(event_log)
            self.sequence_tab.update_trend_info(analysis)
            if hasattr(self.dashboard_tab, 'sequence_info_widget'): self.dashboard_tab.sequence_info_widget.update_trend_info(analysis)
        if self.current_test_id:
            sensor_stats = {};
            temps = [s['value'] for s in self.sensor_log if s.get('sensor') == 'B24_TEMP' and s.get('value') is not None]
            humids = [s['value'] for s in self.sensor_log if s.get('sensor') == 'B24_HUMIDITY' and s.get('value') is not None]
            if temps: sensor_stats['temp'] = { 'min': min(temps), 'max': max(temps), 'avg': np.mean(temps) }
            if humids: sensor_stats['humid'] = { 'min': min(humids), 'max': max(humids), 'avg': np.mean(humids) }
            full_log = { 'events': event_log, 'sensors': sensor_stats, 'sensors_raw': self.sensor_log }
            self.db.update_run(self.current_test_id, cycles, status, full_log)
            QMessageBox.information(self, "Testlauf beendet", f"Daten für ID {self.current_test_id} gespeichert.")
            self.current_test_id = None; QTimer.singleShot(100, self.load_archive)
        elif status == "Abgeschlossen": QMessageBox.information(self, "Sequenz beendet", f"Sequenz nach {cycles} Zyklen abgeschlossen.")

    def start_sequence(self, seq_id): # Unverändert

        # TODO: Live-Stats starten (falls Testlauf)
        # if hasattr(self, "live_stats_widget"):
        #     self.live_stats_widget.start_monitoring(total_cycles)

        if not self.worker.is_connected(): QMessageBox.warning(self, "Fehler", "Bitte zuerst mit dem Arduino verbinden!"); return
        seq_name = self.sequences.get(seq_id, {}).get('name', 'Unbekannt')
        if hasattr(self.dashboard_tab, 'activity_widget'): self.dashboard_tab.activity_widget.add_entry(f"Sequenz '{seq_name}' gestartet.")
        self.sequence_tab.set_running_state(True); self.seq_runner.start_sequence(self.sequences[seq_id])

    def start_test_run(self, seq_id): # Unverändert

        # TODO: Live-Stats starten (falls Testlauf)
        # if hasattr(self, "live_stats_widget"):
        #     self.live_stats_widget.start_monitoring(total_cycles)

        if not self.worker.is_connected(): QMessageBox.warning(self, "Fehler", "Bitte zuerst mit dem Arduino verbinden!"); return
        seq = self.sequences[seq_id]; name, ok = QInputDialog.getText(self, "Testlauf starten", "Name für den Testlauf:", text=f"Test: {seq['name']}")
        if not ok or not name: return
        self.current_test_id = self.db.add_run(name, seq["name"]); self.test_start_time = time.time(); self.sensor_log.clear()
        if hasattr(self.dashboard_tab, 'activity_widget'): self.dashboard_tab.activity_widget.add_entry(f"Testlauf '{name}' gestartet.")
        self.sequence_tab.set_running_state(True); self.seq_runner.start_sequence(seq)

    def on_sequence_updated_from_editor(self, seq_id, updated_data): # Unverändert
        if seq_id in self.sequences: self.sequences[seq_id].update(updated_data); self.sequence_tab.update_sequence_list(self.sequences); self.auto_save_config()

    def new_sequence(self): # Unverändert
        dialog = SequenceDialog(self)
        if dialog.exec():
            seq = dialog.get_sequence();
            if not seq["name"]: QMessageBox.warning(self, "Fehler", "Eine Sequenz benötigt einen Namen!"); return
            seq_id = str(uuid.uuid4()); self.sequences[seq_id] = seq; self.sequence_tab.update_sequence_list(self.sequences)
            if hasattr(self.dashboard_tab, 'quick_sequence_widget'): self.dashboard_tab.quick_sequence_widget.update_sequences(self.sequences)
            self.auto_save_config()

    def edit_sequence(self, seq_id): # Unverändert
        if seq_id in self.sequences: self.sequence_tab.open_visual_editor_for_sequence(seq_id, self.sequences[seq_id])

    def delete_sequence(self, seq_id): # Unverändert
        reply = QMessageBox.question(self, "Löschen", f"Soll die Sequenz '{self.sequences[seq_id]['name']}' wirklich gelöscht werden?")
        if reply == QMessageBox.StandardButton.Yes:
            del self.sequences[seq_id]; self.sequence_tab.update_sequence_list(self.sequences)
            if hasattr(self.dashboard_tab, 'quick_sequence_widget'): self.dashboard_tab.quick_sequence_widget.update_sequences(self.sequences)
            self.auto_save_config()

    def toggle_favorite(self, seq_id):
        """NEU: Togglet den Favoriten-Status einer Sequenz"""
        if seq_id in self.sequences:
            current = self.sequences[seq_id].get("favorite", False)
            self.sequences[seq_id]["favorite"] = not current
            self.sequence_tab.update_sequence_list(self.sequences)
            if hasattr(self.dashboard_tab, 'quick_sequence_widget'):
                self.dashboard_tab.quick_sequence_widget.update_sequences(self.sequences)
            self.auto_save_config()

            status = "als Favorit markiert" if not current else "aus Favoriten entfernt"
            self.status_bar.showMessage(f"⭐ Sequenz '{self.sequences[seq_id]['name']}' {status}", 2000)
            logger.info(f"Sequenz {seq_id} {status}")

    def load_hardware_profile(self, profile_id: str):
        """Lädt Hardware-Profil in Board Config Tab"""
        if not HARDWARE_PROFILE_AVAILABLE:
            QMessageBox.warning(self, "Fehler", "Hardware Profile Manager nicht verfügbar")
            return

        try:
            # Hole Profil-Manager aus Hardware Profile Tab
            profile_manager = self.hardware_profile_tab.profile_manager
            profile = profile_manager.get_profile(profile_id)

            if not profile:
                QMessageBox.warning(self, "Fehler", f"Profil mit ID '{profile_id}' nicht gefunden")
                return

            # Lade Pin-Konfiguration in Board Config Tab
            if hasattr(self.board_config_tab, 'pin_widgets'):
                for pin_name, function in profile.pin_config.items():
                    if pin_name in self.board_config_tab.pin_widgets:
                        widget = self.board_config_tab.pin_widgets[pin_name]
                        # Prüfe ob Funktion verfügbar ist
                        for i in range(widget.combo.count()):
                            if widget.combo.itemText(i) == function:
                                widget.set_config(function)
                                break

            # Wechsle zu Board Config Tab
            self.tabs.setCurrentWidget(self.board_config_tab)

            self.status_bar.showMessage(f"✅ Profil '{profile.name}' geladen", 3000)
            logger.info(f"Hardware-Profil '{profile.name}' geladen")

        except Exception as e:
            logger.error(f"Fehler beim Laden des Hardware-Profils: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden des Profils:\n{str(e)}")

    def save_dashboard_layout(self, name, layout_config): # Unverändert
        self.dashboard_layouts[name] = layout_config
        if hasattr(self.dashboard_tab, 'update_layout_list'): self.dashboard_tab.update_layout_list(list(self.dashboard_layouts.keys()))
        if hasattr(self.dashboard_tab, 'layout_combo'): self.dashboard_tab.layout_combo.setCurrentText(name)
        self.auto_save_config(); self.status_bar.showMessage(f"Layout '{name}' gespeichert.", 2000)

    def delete_dashboard_layout(self, name): # Unverändert
        if name in self.dashboard_layouts:
            del self.dashboard_layouts[name]
            if hasattr(self.dashboard_tab, 'update_layout_list'): self.dashboard_tab.update_layout_list(list(self.dashboard_layouts.keys()))
            self.auto_save_config(); self.status_bar.showMessage(f"Layout '{name}' gelöscht.", 2000)

    def load_dashboard_layout(self, name): # Unverändert
        layout_config = self.dashboard_layouts.get(name)
        if layout_config and hasattr(self.dashboard_tab, 'apply_layout'):
             self.dashboard_tab.apply_layout(layout_config); self.status_bar.showMessage(f"Layout '{name}' geladen.", 2000)

    def load_archive(self): # Unverändert
        runs = self.db.get_all_runs(); self.archive_tab.update_archive_list(runs)

    def export_pdf(self, run_id): # Unverändert
        run_details = self.db.get_run_details(run_id);
        if not run_details: return
        file_path, _ = QFileDialog.getSaveFileName(self, "PDF exportieren", f"Bericht_{run_id}.pdf", "PDF (*.pdf)")
        if file_path:
            try: ReportGenerator.generate_pdf(run_details, file_path); QMessageBox.information(self, "Erfolg", "PDF-Bericht erfolgreich exportiert!")
            except Exception as e: QMessageBox.critical(self, "Export-Fehler", f"PDF konnte nicht erstellt werden:\n{e}")

    def export_excel(self, run_id): # Unverändert
        run_details = self.db.get_run_details(run_id);
        if not run_details: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Excel exportieren", f"Bericht_{run_id}.xlsx", "Excel (*.xlsx)")
        if file_path:
            try: ReportGenerator.generate_excel(run_details, file_path); QMessageBox.information(self, "Erfolg", "Excel-Bericht erfolgreich exportiert!")
            except Exception as e: QMessageBox.critical(self, "Export-Fehler", f"Excel konnte nicht erstellt werden:\n{e}")

    def export_csv(self, run_id):
        """NEU: Exportiert einen Testlauf als CSV-Datei."""
        run_details = self.db.get_run_details(run_id)
        if not run_details:
            return

        # Analyse durchführen (wie bei anderen Exports)
        event_log = run_details.get('log', {}).get('events', [])
        analysis = TrendAnalyzer.analyze_timing(event_log)

        # Datei-Dialog
        default_name = f"Bericht_{run_id}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV exportieren", default_name, "CSV (*.csv)")

        if file_path:
            try:
                # Verwende ExportManager für CSV-Export
                success = ExportManager.export_csv(run_details, analysis, file_path)
                if success:
                    QMessageBox.information(self, "Erfolg", f"✅ CSV-Bericht erfolgreich exportiert!\n{file_path}")
                    logger.info(f"CSV-Export erfolgreich: {file_path}")
                else:
                    QMessageBox.warning(self, "Warnung", "CSV-Export war nicht vollständig erfolgreich.")
            except Exception as e:
                logger.error(f"CSV-Export fehlgeschlagen: {e}")
                QMessageBox.critical(self, "Export-Fehler", f"CSV konnte nicht erstellt werden:\n{e}")

    def show_report_viewer(self, run_id):
        run_details = self.db.get_run_details(run_id);
        if not run_details: return
        event_log = run_details.get('log', {}).get('events', [])
        analysis = TrendAnalyzer.analyze_timing(event_log)
        report_html = ReportGenerator.generate_html(run_details, analysis)
        sensors_raw = run_details.get('log', {}).get('sensors_raw')
        chart_buffers = ReportGenerator._create_charts(analysis, sensors_raw)
        charts_base64 = [base64.b64encode(buf.getvalue()).decode('utf-8') for buf in chart_buffers]
        for buf in chart_buffers: buf.close()
        dialog = ReportViewerDialog(report_html, charts_base64, run_details, analysis, self); dialog.exec()


    def show_trend_analysis(self, run_id): # Unverändert
        run_details = self.db.get_run_details(run_id)
        event_log = run_details.get('log', {}).get('events', [])
        if not event_log: QMessageBox.warning(self, "Fehler", "Keine Log-Daten für die Analyse gefunden."); return
        analysis = TrendAnalyzer.analyze_timing(event_log)
        dialog = QDialog(self); dialog.setWindowTitle(f"Analyse: {run_details['name']}"); dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog); text_edit = QTextEdit(); text_edit.setReadOnly(True)
        stats_html = f"<h3>Zyklus-Analyse</h3><p>Ø Zykluszeit: <b>{analysis['cycle_analysis'].get('avg', 0):.2f} ms</b></p><p>Stabilität: <b>{analysis['cycle_analysis'].get('stability', 0):.1f}%</b></p><p>Anomalien: <b>{len(analysis['cycle_analysis'].get('anomalies', []))}</b></p>"
        text_edit.setHtml(stats_html); layout.addWidget(text_edit); dialog.exec()


    def show_comparison_report(self, run_ids):
        if len(run_ids) < 2: QMessageBox.information(self, "Hinweis", "Bitte mindestens zwei Testläufe für einen Vergleich auswählen."); return
        run_details_list = [self.db.get_run_details(rid) for rid in run_ids]
        analysis_results = [TrendAnalyzer.analyze_timing(rd.get('log', {}).get('events', [])) for rd in run_details_list]
        comparison_html = ReportGenerator.generate_comparison_html(run_details_list, analysis_results)
        chart_buffer = ReportGenerator.create_comparison_chart(run_details_list, analysis_results)
        charts_base64 = [base64.b64encode(chart_buffer.getvalue()).decode('utf-8')] if chart_buffer else []
        if chart_buffer: chart_buffer.close()
        dialog = ComparisonViewerDialog(comparison_html, charts_base64, run_details_list, analysis_results, self); dialog.exec()


    def register_data_handler(self, handler): # Unverändert
        self.data_handlers.append(handler)

    def refresh_ports(self): # Unverändert
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.clear(); self.port_combo.addItems(ports)
        if hasattr(self.dashboard_tab, 'connection_widget'): self.dashboard_tab.connection_widget.update_ports(ports)

    def _process_command_queue(self):
        """Verarbeitet Command Queue ohne UI zu blockieren."""
        if not self.command_queue:
            self.command_timer.stop()
            return

        cmd = self.command_queue.pop(0)
        self.send_command(cmd)

        # Wenn noch Befehle in Queue, Timer weiterlaufen lassen
        if not self.command_queue:
            self.command_timer.stop()

    def _queue_commands(self, commands, interval_ms=10):
        """Fügt Befehle zur Queue hinzu und startet Timer.

        Args:
            commands: Liste von Command-Dicts
            interval_ms: Intervall zwischen Befehlen in Millisekunden
        """
        self.command_queue.extend(commands)
        if not self.command_timer.isActive():
            self.command_timer.start(interval_ms)

    def closeEvent(self, event):
        """Sauberer Shutdown mit Thread-Cleanup und Ressourcen-Freigabe."""
        logger.info("Anwendung wird beendet...")

        # 1. Konfiguration speichern
        try:
            self.auto_save_config()
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}")

        # 2. Alle Timer stoppen
        if hasattr(self, 'sensor_poll_timer'):
            self.sensor_poll_timer.stop()
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        if hasattr(self, 'command_timer'):
            self.command_timer.stop()
        if hasattr(self, 'oscilloscope_update_timer'):
            self.oscilloscope_update_timer.stop()

        # 3. Sequenz-Runner stoppen
        if hasattr(self, 'seq_runner'):
            self.seq_runner.stop_sequence()
            # Warte bis Thread beendet ist
            if not self.seq_runner.wait(3000):
                logger.warning("SequenceRunner konnte nicht sauber beendet werden")
                self.seq_runner.terminate()

        # 4. Serial-Verbindung trennen
        if hasattr(self, 'worker'):
            self.worker.disconnect_serial()
            # Warte bis Serial-Worker beendet ist
            if self.worker.isRunning():
                if not self.worker.wait(2000):
                    logger.warning("SerialWorker konnte nicht sauber beendet werden")
                    self.worker.terminate()

        # 5. Datenbank-Thread beenden
        if hasattr(self, 'db_thread'):
            self.db_thread.quit()
            if not self.db_thread.wait(3000):
                logger.error("DB-Thread konnte nicht beendet werden, erzwinge Terminierung")
                self.db_thread.terminate()
                self.db_thread.wait(1000)

        logger.info("Anwendung sauber beendet")
        event.accept()

# --- Main execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not os.path.exists("assets"): print("WARNUNG: 'assets'-Ordner nicht gefunden...")
    # Optional: Lade Stylesheet
    try: from ui.branding import get_full_stylesheet; app.setStyleSheet(get_full_stylesheet())
    except ImportError: pass
    window = MainWindow()
    window.show()

    # === NEUE METHODEN ===

    def toggle_simulator(self):
        """Wechselt zwischen Simulator und echtem Arduino."""
        if not SIMULATOR_AVAILABLE:
            QMessageBox.warning(self, 'Nicht verfügbar', 
                               'Hardware-Simulator ist nicht installiert.\n'
                               'Lade hardware_simulator.py herunter.')
            return
        
        # Trenne aktuelle Verbindung
        if hasattr(self.worker, 'disconnect'):
            self.worker.disconnect()
        
        # Toggle
        self.use_simulator = not self.use_simulator
        
        if self.use_simulator:
            # Wechsel zu Simulator
            self.simulator = create_simulator('UNO')
            self.worker = self.simulator
            
            # Verbinde Signals
            self.setup_connections()  # Re-connect signals
            
            # Auto-Connect
            self.worker.connect('SIM')
            
            self.status_bar.showMessage('🎮 Simulator-Modus aktiviert')
            print('🎮 Simulator-Modus aktiviert')
        else:
            # Zurück zu echtem Arduino
            self.worker = SerialWorker()
            self.setup_connections()
            self.status_bar.showMessage('🔌 Arduino-Modus aktiviert')
            print('🔌 Arduino-Modus aktiviert')

    def change_theme(self, theme_name: str):
        """Ändert das UI-Theme."""
        if not THEME_MANAGER_AVAILABLE:
            return
        
        self.theme_manager.apply_theme(theme_name)
        self.status_bar.showMessage(f'Theme geändert: {theme_name}')
        print(f'🎨 Theme gewechselt zu: {theme_name}')

    def toggle_fullscreen(self):
        """Wechselt zwischen Fullscreen und Normal."""
        if self.isFullScreen():
            self.showNormal()
            self.menuBar().show()
            self.status_bar.showMessage('Fullscreen deaktiviert')
        else:
            self.showFullScreen()
            self.menuBar().hide()
            self.status_bar.showMessage('Fullscreen aktiviert (F11 zum Beenden)')

    def show_simulator_config(self):
        """Zeigt Simulator-Konfiguration."""
        if not self.use_simulator:
            QMessageBox.information(self, 'Nicht im Simulator-Modus',
                                   'Aktiviere zuerst den Simulator-Modus.')
            return
        
        # Zeige Config-Dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Simulator-Konfiguration')
        layout = QVBoxLayout(dialog)
        
        # Latenz
        layout.addWidget(QLabel('Latenz (ms):'))
        latency_spin = QSpinBox()
        latency_spin.setRange(0, 1000)
        latency_spin.setValue(self.simulator.config['latency_ms'])
        layout.addWidget(latency_spin)
        
        # Fehlerrate
        layout.addWidget(QLabel('Fehlerrate (%):'))
        error_spin = QDoubleSpinBox()
        error_spin.setRange(0, 100)
        error_spin.setValue(self.simulator.config['error_rate'] * 100)
        layout.addWidget(error_spin)
        
        # Buttons
        apply_btn = QPushButton('Übernehmen')
        apply_btn.clicked.connect(lambda: [
            self.simulator.set_latency(latency_spin.value()),
            self.simulator.set_error_rate(error_spin.value() / 100),
            dialog.accept()
        ])
        layout.addWidget(apply_btn)
        
        dialog.exec()


    # === NEUE METHODEN ===

    def toggle_simulator(self):
        """Wechselt zwischen Simulator und echtem Arduino."""
        if not SIMULATOR_AVAILABLE:
            QMessageBox.warning(self, 'Nicht verfügbar', 
                               'Hardware-Simulator ist nicht installiert.\n'
                               'Lade hardware_simulator.py herunter.')
            return
        
        # Trenne aktuelle Verbindung
        if hasattr(self.worker, 'disconnect'):
            self.worker.disconnect()
        
        # Toggle
        self.use_simulator = not self.use_simulator
        
        if self.use_simulator:
            # Wechsel zu Simulator
            self.simulator = create_simulator('UNO')
            self.worker = self.simulator
            
            # Verbinde Signals
            self.setup_connections()  # Re-connect signals
            
            # Auto-Connect
            self.worker.connect('SIM')
            
            self.status_bar.showMessage('🎮 Simulator-Modus aktiviert')
            print('🎮 Simulator-Modus aktiviert')
        else:
            # Zurück zu echtem Arduino
            self.worker = SerialWorker()
            self.setup_connections()
            self.status_bar.showMessage('🔌 Arduino-Modus aktiviert')
            print('🔌 Arduino-Modus aktiviert')

    def change_theme(self, theme_name: str):
        """Ändert das UI-Theme."""
        if not THEME_MANAGER_AVAILABLE:
            return
        
        self.theme_manager.apply_theme(theme_name)
        self.status_bar.showMessage(f'Theme geändert: {theme_name}')
        print(f'🎨 Theme gewechselt zu: {theme_name}')

    def toggle_fullscreen(self):
        """Wechselt zwischen Fullscreen und Normal."""
        if self.isFullScreen():
            self.showNormal()
            self.menuBar().show()
            self.status_bar.showMessage('Fullscreen deaktiviert')
        else:
            self.showFullScreen()
            self.menuBar().hide()
            self.status_bar.showMessage('Fullscreen aktiviert (F11 zum Beenden)')

    def show_simulator_config(self):
        """Zeigt Simulator-Konfiguration."""
        if not self.use_simulator:
            QMessageBox.information(self, 'Nicht im Simulator-Modus',
                                   'Aktiviere zuerst den Simulator-Modus.')
            return
        
        # Zeige Config-Dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Simulator-Konfiguration')
        layout = QVBoxLayout(dialog)
        
        # Latenz
        layout.addWidget(QLabel('Latenz (ms):'))
        latency_spin = QSpinBox()
        latency_spin.setRange(0, 1000)
        latency_spin.setValue(self.simulator.config['latency_ms'])
        layout.addWidget(latency_spin)

        """Fügt Live-Stats als Dock-Widget hinzu (Fallback)."""
        from PyQt6.QtWidgets import QDockWidget
        from PyQt6.QtCore import Qt
        
        self.live_stats_dock = QDockWidget("📊 Live-Statistiken", self)
        self.live_stats_dock.setWidget(self.live_stats_widget)
        self.live_stats_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.live_stats_dock)
        print("✅ Live-Stats als Dock-Widget hinzugefügt (Fallback)")

        
        # Fehlerrate
        layout.addWidget(QLabel('Fehlerrate (%):'))
        error_spin = QDoubleSpinBox()
        error_spin.setRange(0, 100)
        error_spin.setValue(self.simulator.config['error_rate'] * 100)
        layout.addWidget(error_spin)
        
        # Buttons
        apply_btn = QPushButton('Übernehmen')
        apply_btn.clicked.connect(lambda: [
            self.simulator.set_latency(latency_spin.value()),
            self.simulator.set_error_rate(error_spin.value() / 100),
            dialog.accept()
        ])
        layout.addWidget(apply_btn)
        
        dialog.exec()

    sys.exit(app.exec())