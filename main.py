import sys
import os
import uuid
import serial.tools.list_ports
import time
import numpy as np
import base64

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QPushButton, QCheckBox, QStatusBar, QTabWidget,
                             QInputDialog, QMessageBox, QDialog, QTextEdit, QListWidget, QFileDialog,
                             QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPixmap

# === CORE MODULE ===
from core.database import Database
from core.database_worker import DatabaseWorker
from core.config_manager import ConfigManager
from core.serial_worker import SerialWorker
from core.sequence_runner import SequenceRunner

# === ANALYSIS MODULE ===
from analysis.trend_analyzer import TrendAnalyzer
from analysis.report_generator import ReportGenerator
from analysis.report_viewer import ReportViewerDialog
from analysis.comparison_viewer import ComparisonViewerDialog

# === UI MODULE (Basis-Tabs) ===
from ui.pin_tab import PinTab
from ui.pin_overview_widget import PinOverviewWidget
from ui.sequence_tab import SequenceTab
from ui.archive_tab import ArchiveTab
from ui.live_chart_widget import LiveChartWidget
from ui.sequence_dialog import SequenceDialog
from ui.sensor_tab import SensorTab
from ui.enhanced_dashboard_tab import EnhancedDashboardTab
from ui.branding import get_full_stylesheet, LOGO_PATH

# === OPTIONALE ERWEITERTE FEATURES ===
# Diese werden NICHT hier importiert, sondern in _add_optional_tabs()!
# Dadurch läuft die App auch, wenn neue Features noch nicht erstellt wurden.

# === ADVANCED FEATURES (falls vorhanden) ===
try:
    from advanced_features_fixed import integrate_advanced_features
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

class MainWindow(QMainWindow):
    # ... (init and other methods unchanged) ...
    pin_update_for_runner = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drexler Dynamics - Arduino Control Panel")
        self.setGeometry(100, 100, 1600, 950)

        if os.path.exists(LOGO_PATH):
            self.setWindowIcon(QIcon(LOGO_PATH))

        print("Starte Arduino Control Panel...")

        self.data_handlers = []
        self.sequences = {}
        self.dashboard_layouts = {} 

        self.db = Database(db_file="arduino_tests.db")
        self.db_thread = QThread()
        self.db_worker = DatabaseWorker(db_file="arduino_tests.db")
        self.db_worker.moveToThread(self.db_thread)
        self.db_thread.start()
        print("Asynchroner Datenbank-Worker gestartet.")

        self.config_manager = ConfigManager(config_file="arduino_config.json")
        self.worker = SerialWorker()
        self.seq_runner = SequenceRunner()

        self.current_test_id = None
        self.sensor_log = []
        self.test_start_time = 0
        self.chart_start_time = time.time()

        self.setup_ui()
        self.setup_connections()
        self.setStyleSheet(get_full_stylesheet())
        self.load_saved_config()

        if ADVANCED_FEATURES_AVAILABLE:
            print("\n🔧 Integriere Advanced Features...")
            integrate_advanced_features(self)
            print("✅ Advanced Features erfolgreich integriert!")

        self.auto_save_timer = QTimer(self, timeout=self.auto_save_config, interval=30000)
        self.auto_save_timer.start()

        self.sensor_poll_timer = QTimer(self, timeout=self.poll_sensors)
        print("\nAnwendung bereit.")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        
        # === BESTEHENDE TABS (Immer vorhanden) ===
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
        
        # === NEUE TABS (Optional mit Fehlerbehandlung) ===
        self._add_optional_tabs()
        self._add_optional_tabs_to_dashboard()

        main_layout.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bereit")

    def _add_optional_tabs(self):
        """Fügt optionale Tabs hinzu, falls verfügbar"""
        
        # Data Logger
        try:
            from ui.data_logger_widget import DataLoggerWidget
            self.data_logger_tab = DataLoggerWidget()
            self.tabs.addTab(self.data_logger_tab, "📊 Data Logger")
            print("✅ Data Logger geladen")
        except Exception as e:
            print(f"⚠️ Data Logger nicht verfügbar: {e}")
            self.data_logger_tab = None
        
        # LED Matrix Simulator
        try:
            from ui.led_matrix_simulator import LEDMatrixSimulator
            self.led_matrix_tab = LEDMatrixSimulator()
            self.tabs.addTab(self.led_matrix_tab, "💡 LED Matrix")
            print("✅ LED Matrix Simulator geladen")
        except Exception as e:
            print(f"⚠️ LED Matrix Simulator nicht verfügbar: {e}")
            self.led_matrix_tab = None
        
        # Oszilloskop
        try:
            from ui.oscilloscope_widget import OscilloscopeWidget
            self.oscilloscope_tab = OscilloscopeWidget()
            self.tabs.addTab(self.oscilloscope_tab, "📡 Oszilloskop")
            print("✅ Oszilloskop geladen")
        except Exception as e:
            print(f"⚠️ Oszilloskop nicht verfügbar: {e}")
            self.oscilloscope_tab = None
        
        # PWM/Servo Steuerung
        try:
            from ui.pwm_servo_control import PWMServoControl
            self.pwm_servo_tab = PWMServoControl()
            self.tabs.addTab(self.pwm_servo_tab, "⚡ PWM/Servo")
            print("✅ PWM/Servo Steuerung geladen")
        except Exception as e:
            print(f"⚠️ PWM/Servo Steuerung nicht verfügbar: {e}")
            self.pwm_servo_tab = None
        
        # Makro-Recorder
        try:
            from ui.macro_system import MacroRecorder
            self.macro_tab = MacroRecorder()
            self.tabs.addTab(self.macro_tab, "🤖 Makros")
            print("✅ Makro-Recorder geladen")
        except Exception as e:
            print(f"⚠️ Makro-Recorder nicht verfügbar: {e}")
            self.macro_tab = None
        
        # Sensor-Konfiguration
        try:
            from ui.sensor_config_tab import SensorConfigTab
            self.sensor_config_tab = SensorConfigTab()
            self.tabs.addTab(self.sensor_config_tab, "🔧 Sensor-Setup")
            print("✅ Sensor-Konfiguration geladen")
        except Exception as e:
            print(f"⚠️ Sensor-Konfiguration nicht verfügbar: {e}")
            self.sensor_config_tab = None    

    def _add_optional_tabs_to_dashboard(self):
        """Fügt neue Feature-Widgets zum Dashboard hinzu"""
        
        # Data Logger
        if hasattr(self, 'data_logger_tab') and self.data_logger_tab:
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
            
            # Synchronisiere mit Haupt-Logger
            def sync_logger(data):
                if data.get('type') == 'pin_update':
                    pin = data.get('pin_name')
                    value = data.get('value')
                    if pin and value is not None:
                        dashboard_logger.log_pin_value(pin, value)
            
            self.worker.data_received.connect(sync_logger)
        
        # LED Matrix Simulator (Mini)
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
        
        # Oszilloskop Kompakt
        if hasattr(self, 'oscilloscope_tab') and self.oscilloscope_tab:
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
            
            # Nur A0 und A1
            def forward_to_dash_scope(data):
                if data.get('type') == 'pin_update':
                    pin = data.get('pin_name')
                    value = data.get('value')
                    if pin in ['A0', 'A1'] and value is not None:
                        dashboard_scope.add_data_point(pin, value, time.time())
            
            self.worker.data_received.connect(forward_to_dash_scope)
        
        # PWM Schnellzugriff
        if hasattr(self, 'pwm_servo_tab') and self.pwm_servo_tab:
            from ui.pwm_quick_widget import PWMQuickWidget
            
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
            from ui.macro_quick_widget import MacroQuickWidget
            
            dashboard_macros = MacroQuickWidget()
            
            self.dashboard_tab.add_optional_widget(
                widget_id='macro_quick',
                title='Makro Schnellstart',
                icon='🤖',
                widget_instance=dashboard_macros,
                geometry=(1270, 220, 280, 200),
                category='Automatisierung'
            )

    def _create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Datei")
        save_action = file_menu.addAction("💾 Speichern")
        save_action.triggered.connect(self.auto_save_config)
        save_action.setShortcut("Ctrl+S")
        load_action = file_menu.addAction("📂 Laden")
        load_action.triggered.connect(self.load_saved_config)
        load_action.setShortcut("Ctrl+O")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("❌ Beenden")
        exit_action.triggered.connect(self.close)

    def _create_connection_bar(self):
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        conn_layout.addWidget(self.port_combo)
        refresh_btn = QPushButton("↻")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self.refresh_ports)
        conn_layout.addWidget(refresh_btn)
        self.sim_check = QCheckBox("Simulation")
        conn_layout.addWidget(self.sim_check)
        self.connect_btn = QPushButton("Verbinden")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addStretch()
        return conn_layout

    def setup_connections(self):
        """Verbindet alle Signale und Slots - Basis-Tabs + Optionale neue Tabs"""
        
        # =========================================================================
        # CORE CONNECTIONS - Serial Worker & Database
        # =========================================================================
        
        self.worker.data_received.connect(self.handle_data)
        self.worker.status_changed.connect(self.update_status)
        
        self.db.add_run_requested.connect(self.db_worker.add_run)
        self.db.update_run_requested.connect(self.db_worker.update_run)
        
        # =========================================================================
        # PIN CONTROL TAB
        # =========================================================================
        
        self.pin_control_tab.command_signal.connect(self.send_command)
        
        # =========================================================================
        # SEQUENCE RUNNER & SEQUENCE TAB
        # =========================================================================
        
        # Sequence Runner -> Commands & Updates
        self.seq_runner.command_signal.connect(self.send_command)
        self.seq_runner.step_update.connect(self.sequence_tab.update_sequence_info)
        self.seq_runner.step_highlight_signal.connect(self.sequence_tab.highlight_step)
        self.seq_runner.finished.connect(self.sequence_finished)
        self.pin_update_for_runner.connect(self.seq_runner.on_pin_update)
        
        # Sequence Tab -> Actions
        self.sequence_tab.start_sequence_signal.connect(self.start_sequence)
        self.sequence_tab.start_test_run_signal.connect(self.start_test_run)
        self.sequence_tab.stop_sequence_signal.connect(self.seq_runner.stop_sequence)
        self.sequence_tab.pause_sequence_signal.connect(self.seq_runner.pause_sequence)
        self.sequence_tab.new_sequence_signal.connect(self.new_sequence)
        self.sequence_tab.edit_sequence_signal.connect(self.edit_sequence)
        self.sequence_tab.delete_sequence_signal.connect(self.delete_sequence)
        self.sequence_tab.sequence_updated_signal.connect(self.on_sequence_updated_from_editor)
        
        # =========================================================================
        # ARCHIVE TAB
        # =========================================================================
        
        self.archive_tab.refresh_signal.connect(self.load_archive)
        self.archive_tab.export_pdf_signal.connect(self.export_pdf)
        self.archive_tab.export_excel_signal.connect(self.export_excel)
        self.archive_tab.show_analysis_signal.connect(self.show_trend_analysis)
        self.archive_tab.show_report_signal.connect(self.show_report_viewer)
        self.archive_tab.compare_runs_signal.connect(self.show_comparison_report)
        
        # =========================================================================
        # SENSOR TAB
        # =========================================================================
        
        self.sensor_tab.poll_interval_changed.connect(self.update_poll_interval)
        
        # =========================================================================
        # CHART TAB
        # =========================================================================
        
        self.chart_tab.clear_button_pressed.connect(self.clear_chart)
        
        # =========================================================================
        # TAB WIDGET
        # =========================================================================
        
        # Lädt Archiv automatisch beim Wechsel zum Archive-Tab
        self.tabs.currentChanged.connect(
            lambda i: self.load_archive() if self.tabs.widget(i) == self.archive_tab else None
        )
        
        # =========================================================================
        # DASHBOARD TAB
        # =========================================================================
        
        self.dashboard_tab.connect_requested.connect(self.handle_dashboard_connect)
        self.dashboard_tab.disconnect_requested.connect(self.toggle_connection)
        self.dashboard_tab.refresh_ports_requested.connect(self.refresh_ports)
        self.dashboard_tab.start_sequence_signal.connect(self.start_sequence)
        self.dashboard_tab.start_test_run_signal.connect(self.start_test_run)
        self.dashboard_tab.live_chart_widget.clear_button_pressed.connect(self.clear_chart)
        self.dashboard_tab.layout_save_requested.connect(self.save_dashboard_layout)
        self.dashboard_tab.layout_delete_requested.connect(self.delete_dashboard_layout)
        self.dashboard_tab.layout_load_requested.connect(self.load_dashboard_layout)
        
        # =========================================================================
        # NEUE TABS (OPTIONAL) - Werden nur verbunden, wenn vorhanden
        # =========================================================================
        
        # -------------------------------------------------------------------------
        # DATA LOGGER TAB
        # -------------------------------------------------------------------------
        if hasattr(self, 'data_logger_tab') and self.data_logger_tab:
            print("🔗 Verbinde Data Logger...")
            
            # Pin-Updates an Data Logger weiterleiten
            def forward_to_data_logger(data):
                if data.get('type') == 'pin_update':
                    pin = data.get('pin_name')
                    value = data.get('value')
                    if pin and value is not None:
                        self.data_logger_tab.log_pin_value(pin, value)
            
            self.worker.data_received.connect(forward_to_data_logger)
        
        # -------------------------------------------------------------------------
        # LED MATRIX SIMULATOR
        # -------------------------------------------------------------------------
        if hasattr(self, 'led_matrix_tab') and self.led_matrix_tab:
            print("🔗 Verbinde LED Matrix Simulator...")
            
            # Commands vom Matrix-Widget an Arduino
            # (Falls du später LED-Matrix-Befehle implementierst)
            # self.led_matrix_tab.command_signal.connect(self.send_command)
        
        # -------------------------------------------------------------------------
        # OSZILLOSKOP TAB
        # -------------------------------------------------------------------------
        if hasattr(self, 'oscilloscope_tab') and self.oscilloscope_tab:
            print("🔗 Verbinde Oszilloskop...")
            
            # Analog-Werte an Oszilloskop weiterleiten
            def forward_to_oscilloscope(data):
                if data.get('type') == 'pin_update':
                    pin = data.get('pin_name')
                    value = data.get('value')
                    if pin and value is not None:
                        # Nur Analog-Pins (A0-A5) ans Oszilloskop
                        if pin.startswith('A'):
                            self.oscilloscope_tab.add_sample(pin, value)
            
            self.worker.data_received.connect(forward_to_oscilloscope)
            
            # Plot regelmäßig aktualisieren
            self.oscilloscope_update_timer = QTimer(self)
            self.oscilloscope_update_timer.timeout.connect(self.oscilloscope_tab.update_plot)
            self.oscilloscope_update_timer.start(100)  # 10 Hz Update
        
        # -------------------------------------------------------------------------
        # PWM/SERVO CONTROL TAB
        # -------------------------------------------------------------------------
        if hasattr(self, 'pwm_servo_tab') and self.pwm_servo_tab:
            print("🔗 Verbinde PWM/Servo Control...")
            
            # PWM/Servo-Commands an Arduino weiterleiten
            self.pwm_servo_tab.command_signal.connect(self.send_command)
        
        # -------------------------------------------------------------------------
        # MAKRO-RECORDER TAB
        # -------------------------------------------------------------------------
        if hasattr(self, 'macro_tab') and self.macro_tab:
            print("🔗 Verbinde Makro-Recorder...")
            
            # Makro-Commands an Arduino
            self.macro_tab.command_signal.connect(self.send_command)
            
            # Pin-Aktionen aufzeichnen wenn Recording aktiv
            def record_pin_action(data):
                if not self.macro_tab.recording:
                    return
                
                msg_type = data.get('type')
                
                # Digital Write aufzeichnen
                if msg_type == 'response' and data.get('status') == 'ok':
                    # Hier könnte man den Original-Command tracken
                    pass
                
                # Pin-Updates aufzeichnen
                elif msg_type == 'pin_update':
                    pin = data.get('pin_name')
                    value = data.get('value')
                    if pin and value is not None:
                        self.macro_tab.record_action(
                            action_type='pin_write' if pin.startswith('D') else 'analog_write',
                            parameters={'pin': pin, 'value': value},
                            description=f"{pin} → {value}"
                        )
            
            self.worker.data_received.connect(record_pin_action)
        
        # -------------------------------------------------------------------------
        # SENSOR CONFIG TAB
        # -------------------------------------------------------------------------
        if hasattr(self, 'sensor_config_tab') and self.sensor_config_tab:
            print("🔗 Verbinde Sensor-Konfiguration...")
            
            # Sensor-Updates an Config-Tab weiterleiten
            def forward_to_sensor_config(data):
                if data.get('type') == 'sensor_update':
                    # Hier könnte man Live-Updates an die Sensor-Cards senden
                    pass
            
            self.worker.data_received.connect(forward_to_sensor_config)


    # =========================================================================
    # HILFSMETHODEN für neue Tabs
    # =========================================================================

    def update_oscilloscope(self, data):
        """
        Legacy-Methode - Wird jetzt direkt in setup_connections() gehandhabt
        Kann entfernt werden, falls nicht mehr verwendet
        """
        if not hasattr(self, 'oscilloscope_tab') or not self.oscilloscope_tab:
            return
        
        if data.get('type') == 'pin_update':
            pin = data.get('pin_name')
            value = data.get('value')
            if pin and value is not None and pin.startswith('A'):
                self.oscilloscope_tab.add_sample(pin, value)
                
    def handle_dashboard_connect(self, port):
        """Verbindet über das Dashboard"""
        self.port_combo.setCurrentText(port)
        self.toggle_connection()

    def send_command(self, command):
        """Sendet einen Befehl an den Arduino"""
        if self.worker.is_connected():
            self.worker.send_command(command)
        else:
            print(f"⚠️ Nicht verbunden - Befehl ignoriert: {command}")
            
    def handle_data(self, data):
        """Verarbeitet eingehende Daten vom Arduino"""
        msg_type = data.get("type")
        
        # === DEBUG ===
        print(f"📨 Daten empfangen: {msg_type}")
        
        # Response-Feedback
        if msg_type == "response":
            if data.get("status") == "ok":
                QTimer.singleShot(0, lambda: self.status_bar.setStyleSheet("background-color: #27ae60;"))
                QTimer.singleShot(1000, lambda: self.status_bar.setStyleSheet(""))
        
        # Pin-Updates
        elif msg_type == "pin_update":
            pin = data.get("pin_name")
            value = data.get("value")
            print(f"📍 Pin-Update: {pin} = {value}")  # ← DEBUG
            
            if pin is not None and value is not None:
                current_time = time.time() - self.chart_start_time
                
                # An UI-Widgets weiterleiten
                self.pin_control_tab.update_pin_value(pin, value)
                self.pin_overview_tab.update_pin_state(pin, value)
                self.chart_tab.add_data_point(pin, value, current_time)
                
                # === DASHBOARD - PRÜFEN ===
                try:
                    self.dashboard_tab.pin_overview_widget.update_pin_state(pin, value)
                    print(f"✅ Dashboard Pin-Übersicht aktualisiert")
                except Exception as e:
                    print(f"❌ Dashboard Pin-Übersicht Fehler: {e}")
                
                try:
                    self.dashboard_tab.live_chart_widget.add_data_point(pin, value, current_time)
                    print(f"✅ Dashboard Chart aktualisiert")
                except Exception as e:
                    print(f"❌ Dashboard Chart Fehler: {e}")
                
                # An Sequence Runner weiterleiten
                self.pin_update_for_runner.emit(pin, value)
        
        # Sensor-Updates
        elif msg_type == "sensor_update":
            print(f"🌡️ Sensor-Update: {data.get('sensor')}")  # ← DEBUG
            
            # Log für Testläufe
            if self.current_test_id is not None:
                data['time_ms'] = (time.time() - self.test_start_time) * 1000
                self.sensor_log.append(data)
            
            # An Sensor-Tab weiterleiten
            self.sensor_tab.handle_sensor_data(data)
            
            # === DASHBOARD - PRÜFEN ===
            try:
                if data.get("sensor") == "B24_TEMP":
                    self.dashboard_tab.sensor_display_widget.update_temperature(data.get("value", 0))
                    print(f"✅ Dashboard Temperatur aktualisiert: {data.get('value')}°C")
                elif data.get("sensor") == "B24_HUMIDITY":
                    self.dashboard_tab.sensor_display_widget.update_humidity(data.get("value", 0))
                    print(f"✅ Dashboard Luftfeuchtigkeit aktualisiert: {data.get('value')}%")
            except Exception as e:
                print(f"❌ Dashboard Sensor Fehler: {e}")
        
        # An registrierte Handler weiterleiten
        for handler in self.data_handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"❌ Handler-Fehler: {e}")
    
    def update_status(self, message):
        """Aktualisiert die Statusleiste"""
        self.status_bar.showMessage(message)
        
        # Dashboard-Status aktualisieren
        is_connected = "Verbunden" in message or "Simulation" in message
        port_name = ""
        if is_connected:
            try:
                port_name = message.split(':')[1].strip()
            except IndexError:
                port_name = "Simulation"
        
        self.dashboard_tab.connection_widget.update_status(is_connected, port_name)
        self.dashboard_tab.activity_widget.add_entry(message)
        
        
    def update_poll_interval(self, interval_ms):
        """Aktualisiert das Sensor-Polling-Intervall"""
        self.sensor_poll_timer.setInterval(interval_ms)
        if self.sensor_poll_timer.isActive():
            self.sensor_poll_timer.start()
        self.status_bar.showMessage(f"Sensor-Intervall auf {interval_ms} ms gesetzt.", 2000)
    
    def clear_chart(self):
        """Löscht alle Chart-Daten"""
        self.chart_tab.clear()
        self.dashboard_tab.live_chart_widget.clear()
        self.chart_start_time = time.time()
        self.status_bar.showMessage("Live-Diagramme zurückgesetzt.", 2000)
    
    def toggle_connection(self):
        """Verbindet/Trennt die Verbindung zum Arduino"""
        if self.worker.is_connected():
            # Trennen
            self.sensor_poll_timer.stop()
            self.worker.disconnect_serial()
        else:
            # Verbinden
            self.sensor_poll_timer.setInterval(self.sensor_tab.get_poll_interval())
            
            if self.sim_check.isChecked():
                # Simulation starten
                self.worker.connect_simulation()
            elif self.port_combo.currentText():
                # Echte Verbindung
                self.worker.connect_serial(self.port_combo.currentText())
            else:
                QMessageBox.warning(self, "Fehler", "Kein Port ausgewählt!")
                return
            
            self.sensor_poll_timer.start()
        
        # Button-Text aktualisieren
        is_connected = self.worker.is_connected()
        self.connect_btn.setText("Trennen" if is_connected else "Verbinden")
    
    def sequence_finished(self, cycles, status, event_log):
            """Wird aufgerufen, wenn eine Sequenz beendet wurde"""
            self.sequence_tab.set_running_state(False)
            self.sequence_tab.highlight_step(-1)
            self.dashboard_tab.activity_widget.add_entry(f"Sequenz beendet: {status}")
            
            # Trend-Analyse
            if event_log:
                analysis = TrendAnalyzer.analyze_timing(event_log)
                self.sequence_tab.update_trend_info(analysis)
            
            # Testlauf abschließen (falls aktiv)
            if self.current_test_id:
                # Sensor-Statistiken berechnen
                sensor_stats = {}
                temps = [s['value'] for s in self.sensor_log if s.get('sensor') == 'B24_TEMP' and s.get('value') is not None]
                humids = [s['value'] for s in self.sensor_log if s.get('sensor') == 'B24_HUMIDITY' and s.get('value') is not None]
                
                if temps:
                    sensor_stats['temp'] = {
                        'min': min(temps),
                        'max': max(temps),
                        'avg': np.mean(temps)
                    }
                
                if humids:
                    sensor_stats['humid'] = {
                        'min': min(humids),
                        'max': max(humids),
                        'avg': np.mean(humids)
                    }
                
                # Log zusammenstellen
                full_log = {
                    'events': event_log,
                    'sensors': sensor_stats,
                    'sensors_raw': self.sensor_log
                }
                
                # In Datenbank speichern
                self.db.update_run(self.current_test_id, cycles, status, full_log)
                
                QMessageBox.information(
                    self, "Testlauf beendet",
                    f"Daten für ID {self.current_test_id} gespeichert."
                )
                
                self.current_test_id = None
                QTimer.singleShot(100, self.load_archive)
            
            elif status == "Abgeschlossen":
                QMessageBox.information(
                    self, "Sequenz beendet",
                    f"Sequenz nach {cycles} Zyklen abgeschlossen."
                )
                    
    def start_sequence(self, seq_id):
        """Startet eine Sequenz"""
        if not self.worker.is_connected():
            QMessageBox.warning(self, "Fehler", "Bitte zuerst mit dem Arduino verbinden!")
            return
        
        seq_name = self.sequences.get(seq_id, {}).get('name', 'Unbekannt')
        self.dashboard_tab.activity_widget.add_entry(f"Sequenz '{seq_name}' gestartet.")
        self.sequence_tab.set_running_state(True)
        self.seq_runner.start_sequence(self.sequences[seq_id])
    
    def start_test_run(self, seq_id):
        """Startet einen Testlauf (mit Datenbank-Logging)"""
        if not self.worker.is_connected():
            QMessageBox.warning(self, "Fehler", "Bitte zuerst mit dem Arduino verbinden!")
            return
        
        seq = self.sequences[seq_id]
        name, ok = QInputDialog.getText(
            self, "Testlauf starten",
            "Name für den Testlauf:",
            text=f"Test: {seq['name']}"
        )
        
        if not ok or not name:
            return
        
        # Testlauf in DB erstellen
        self.current_test_id = self.db.add_run(name, seq["name"])
        self.test_start_time = time.time()
        self.sensor_log.clear()
        
        self.dashboard_tab.activity_widget.add_entry(f"Testlauf '{name}' gestartet.")
        self.sequence_tab.set_running_state(True)
        self.seq_runner.start_sequence(seq)
    
            
    def on_sequence_updated_from_editor(self, seq_id, updated_data):
        if seq_id in self.sequences:
            self.sequences[seq_id].update(updated_data)
            self.sequence_tab.update_sequence_list(self.sequences)
            self.auto_save_config()
    def new_sequence(self):
        dialog = SequenceDialog(self)
        if dialog.exec():
            seq = dialog.get_sequence()
            if not seq["name"]: QMessageBox.warning(self, "Fehler", "Eine Sequenz benötigt einen Namen!"); return
            seq_id = str(uuid.uuid4())
            self.sequences[seq_id] = seq
            self.sequence_tab.update_sequence_list(self.sequences)
            self.dashboard_tab.quick_sequence_widget.update_sequences(self.sequences)
            self.auto_save_config()
    def edit_sequence(self, seq_id):
        if seq_id in self.sequences:
            sequence_data = self.sequences[seq_id]
            self.sequence_tab.open_visual_editor_for_sequence(seq_id, sequence_data)
    def delete_sequence(self, seq_id):
        reply = QMessageBox.question(self, "Löschen", f"Soll die Sequenz '{self.sequences[seq_id]['name']}' wirklich gelöscht werden?")
        if reply == QMessageBox.StandardButton.Yes:
            del self.sequences[seq_id]
            self.sequence_tab.update_sequence_list(self.sequences)
            self.dashboard_tab.quick_sequence_widget.update_sequences(self.sequences)
            self.auto_save_config()
    def save_dashboard_layout(self, name, layout_config):
        self.dashboard_layouts[name] = layout_config
        self.dashboard_tab.update_layout_list(list(self.dashboard_layouts.keys()))
        self.dashboard_tab.layout_combo.setCurrentText(name)
        self.auto_save_config()
        self.status_bar.showMessage(f"Layout '{name}' gespeichert.", 2000)
    def delete_dashboard_layout(self, name):
        if name in self.dashboard_layouts:
            del self.dashboard_layouts[name]
            self.dashboard_tab.update_layout_list(list(self.dashboard_layouts.keys()))
            self.auto_save_config()
            self.status_bar.showMessage(f"Layout '{name}' gelöscht.", 2000)
    def load_dashboard_layout(self, name):
        layout_config = self.dashboard_layouts.get(name)
        if layout_config:
            self.dashboard_tab.apply_layout(layout_config)
            self.status_bar.showMessage(f"Layout '{name}' geladen.", 2000)
    def load_saved_config(self):
        config = self.config_manager.load_config()
        if not config:
            return
        self.sequences = config.get("sequences", {})
        self.sequence_tab.update_sequence_list(self.sequences)
        self.dashboard_tab.quick_sequence_widget.update_sequences(self.sequences)
        self.pin_control_tab.set_pin_configs(config.get("pin_configs", {}))
        self.dashboard_layouts = config.get("dashboard_layouts", {})
        if "Standard" not in self.dashboard_layouts:
            self.dashboard_layouts["Standard"] = self.dashboard_tab.get_current_layout_config()
        self.dashboard_tab.update_layout_list(list(self.dashboard_layouts.keys()))
        if self.dashboard_layouts:
            first_layout_name = list(self.dashboard_layouts.keys())[0]
            self.load_dashboard_layout(first_layout_name)
            self.dashboard_tab.layout_combo.setCurrentText(first_layout_name)
        self.status_bar.showMessage("Konfiguration geladen.", 2000)
    def auto_save_config(self):
        pin_configs = self.pin_control_tab.get_pin_configs()
        current_layout_name = self.dashboard_tab.layout_combo.currentText()
        if current_layout_name:
            self.dashboard_layouts[current_layout_name] = self.dashboard_tab.get_current_layout_config()
        self.config_manager.save_config(self.sequences, pin_configs, self.dashboard_layouts)
        self.status_bar.showMessage("Konfiguration automatisch gespeichert.", 2000)
    def load_archive(self):
        runs = self.db.get_all_runs()
        self.archive_tab.update_archive_list(runs)
    def export_pdf(self, run_id):
        run_details = self.db.get_run_details(run_id)
        if not run_details: return
        file_path, _ = QFileDialog.getSaveFileName(self, "PDF exportieren", f"Bericht_{run_id}.pdf", "PDF (*.pdf)")
        if file_path:
            try:
                ReportGenerator.generate_pdf(run_details, file_path)
                QMessageBox.information(self, "Erfolg", "PDF-Bericht erfolgreich exportiert!")
            except Exception as e: QMessageBox.critical(self, "Export-Fehler", f"PDF konnte nicht erstellt werden:\n{e}")
    def export_excel(self, run_id):
        run_details = self.db.get_run_details(run_id)
        if not run_details: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Excel exportieren", f"Bericht_{run_id}.xlsx", "Excel (*.xlsx)")
        if file_path:
            try:
                ReportGenerator.generate_excel(run_details, file_path)
                QMessageBox.information(self, "Erfolg", "Excel-Bericht erfolgreich exportiert!")
            except Exception as e: QMessageBox.critical(self, "Export-Fehler", f"Excel konnte nicht erstellt werden:\n{e}")

    def show_report_viewer(self, run_id):
        # ... (code unchanged) ...
        run_details = self.db.get_run_details(run_id)
        if not run_details: return
        event_log = run_details.get('log', {}).get('events', [])
        analysis = TrendAnalyzer.analyze_timing(event_log)
        report_html = ReportGenerator.generate_html(run_details, analysis)
        sensors_raw = run_details.get('log', {}).get('sensors_raw')
        chart_buffers = ReportGenerator._create_charts(analysis, sensors_raw)
        charts_base64 = [base64.b64encode(buf.getvalue()).decode('utf-8') for buf in chart_buffers]
        for buf in chart_buffers: buf.close()
        dialog = ReportViewerDialog(report_html, charts_base64, self)
        dialog.exec()
        
    def show_trend_analysis(self, run_id):
        # ... (code unchanged) ...
        run_details = self.db.get_run_details(run_id)
        event_log = run_details.get('log', {}).get('events', [])
        if not event_log:
            QMessageBox.warning(self, "Fehler", "Keine Log-Daten für die Analyse gefunden.")
            return
        analysis = TrendAnalyzer.analyze_timing(event_log)
        dialog = QDialog(self); dialog.setWindowTitle(f"Analyse: {run_details['name']}"); dialog.setMinimumSize(500, 400)
        layout = QVBoxLayout(dialog); text_edit = QTextEdit(); text_edit.setReadOnly(True)
        stats_html = f"""<h3>Zyklus-Analyse</h3>
        <p>Ø Zykluszeit: <b>{analysis['cycle_analysis'].get('avg', 0):.2f} ms</b></p>
        <p>Stabilität: <b>{analysis['cycle_analysis'].get('stability', 0):.1f}%</b></p>
        <p>Anomalien: <b>{len(analysis['cycle_analysis'].get('anomalies', []))}</b></p>"""
        text_edit.setHtml(stats_html); layout.addWidget(text_edit); dialog.exec()

    # NEUE Methode zur Anzeige des Vergleichsberichts
    def show_comparison_report(self, run_ids):
        if len(run_ids) < 2:
            QMessageBox.information(self, "Hinweis", "Bitte mindestens zwei Testläufe für einen Vergleich auswählen.")
            return

        run_details_list = [self.db.get_run_details(rid) for rid in run_ids]
        analysis_results = [TrendAnalyzer.analyze_timing(rd.get('log', {}).get('events', [])) for rd in run_details_list]

        # HTML-Teil generieren
        comparison_html = ReportGenerator.generate_comparison_html(run_details_list, analysis_results)

        # Diagramm-Teil generieren
        chart_buffer = ReportGenerator.create_comparison_chart(run_details_list, analysis_results)
        charts_base64 = []
        if chart_buffer:
            charts_base64.append(base64.b64encode(chart_buffer.getvalue()).decode('utf-8'))
            chart_buffer.close()

        # Dialog anzeigen
        dialog = ComparisonViewerDialog(comparison_html, charts_base64, self)
        dialog.exec()

    def register_data_handler(self, handler):
        """Registriert einen zusätzlichen Daten-Handler"""
        self.data_handlers.append(handler)
        
        
    def refresh_ports(self):
        """Aktualisiert die Liste der verfügbaren COM-Ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        
        if hasattr(self, 'dashboard_tab'):
            self.dashboard_tab.connection_widget.update_ports(ports)
    
    
    def poll_sensors(self):
            """Fragt alle Sensoren ab"""
            if self.worker.is_connected():
                self.send_command({
                    "id": str(uuid.uuid4()),
                    "command": "read_sensor",
                    "sensor": "B24_TEMP_HUMIDITY"
                })
                
    def closeEvent(self, event):
        """Wird beim Schließen der Anwendung aufgerufen - Aufräumen!"""
        print("\n🛑 Anwendung wird beendet...")
        
        # Konfiguration speichern
        self.auto_save_config()
        
        # Sequenzen stoppen
        self.seq_runner.stop_sequence()
        
        # Serial-Verbindung trennen
        self.worker.disconnect_serial()
        
        # Sensor-Polling stoppen
        self.sensor_poll_timer.stop()
        
        # Oszilloskop-Timer stoppen (falls vorhanden)
        if hasattr(self, 'oscilloscope_update_timer'):
            self.oscilloscope_update_timer.stop()
        
        # Database-Thread beenden
        self.db_thread.quit()
        self.db_thread.wait(2000)  # Max 2 Sekunden warten
        
        print("✅ Anwendung sauber beendet.")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not os.path.exists("assets"): print("WARNUNG: 'assets'-Ordner nicht gefunden. Logo und Hintergrund werden nicht geladen.")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

