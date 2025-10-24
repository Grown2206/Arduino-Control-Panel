# -*- coding: utf-8 -*-
"""
api/rest_server.py
Flask REST API Server mit Swagger Dokumentation
"""
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("REST_API")


class ArduinoRestAPI:
    """
    REST API Server für Arduino Control Panel
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS für Cross-Origin Requests

        # SocketIO für WebSocket Support
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # Flask-RESTX API mit Swagger
        self.api = Api(
            self.app,
            version='1.0',
            title='Arduino Control Panel API',
            description='REST API für Arduino Control Panel - Steuerung, Monitoring und Automatisierung',
            doc='/api/docs',  # Swagger UI unter /api/docs
            prefix='/api'
        )

        # Referenz zum Main-Window (wird später gesetzt)
        self.main_window = None

        # API Keys für Authentication
        self.api_keys = set()
        self.load_api_keys()

        # Server-Thread
        self.server_thread = None
        self.is_running = False

        # Setup Namespaces und Endpoints
        self.setup_namespaces()
        self.setup_endpoints()
        self.setup_websocket()

    def set_main_window(self, main_window):
        """Setzt Referenz zum Main Window"""
        self.main_window = main_window
        logger.info("Main Window Referenz gesetzt")

    def load_api_keys(self):
        """Lädt API Keys aus Datei"""
        try:
            with open('api_keys.json', 'r') as f:
                data = json.load(f)
                self.api_keys = set(data.get('keys', []))
            logger.info(f"✅ {len(self.api_keys)} API Keys geladen")
        except FileNotFoundError:
            # Erstelle Default API Key
            self.api_keys.add("default-api-key-change-me")
            self.save_api_keys()
            logger.warning("⚠️ Keine API Keys gefunden - Default Key erstellt")

    def save_api_keys(self):
        """Speichert API Keys"""
        with open('api_keys.json', 'w') as f:
            json.dump({'keys': list(self.api_keys)}, f, indent=2)

    def check_api_key(self):
        """Prüft API Key im Request Header"""
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in self.api_keys:
            return False
        return True

    def require_api_key(self, func):
        """Decorator für API Key Authentifizierung"""
        def wrapper(*args, **kwargs):
            if not self.check_api_key():
                return {'error': 'Invalid or missing API key'}, 401
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper

    def setup_namespaces(self):
        """Erstellt API Namespaces"""
        self.ns_system = self.api.namespace('system', description='System-Informationen und Status')
        self.ns_pins = self.api.namespace('pins', description='Pin-Steuerung')
        self.ns_sensors = self.api.namespace('sensors', description='Sensor-Daten')
        self.ns_sequences = self.api.namespace('sequences', description='Sequenz-Verwaltung')
        self.ns_archive = self.api.namespace('archive', description='Test-Archiv')
        self.ns_calibration = self.api.namespace('calibration', description='Sensor-Kalibrierung')

    def setup_endpoints(self):
        """Registriert alle API Endpoints"""
        self.setup_system_endpoints()
        self.setup_pin_endpoints()
        self.setup_sensor_endpoints()
        self.setup_sequence_endpoints()
        self.setup_archive_endpoints()
        self.setup_calibration_endpoints()

    def setup_system_endpoints(self):
        """System Status Endpoints"""

        @self.ns_system.route('/status')
        class SystemStatus(Resource):
            def get(self):
                """System-Status abrufen"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                return {
                    'status': 'online',
                    'version': '1.0.0',
                    'connected': self.parent.main_window.worker.is_connected() if hasattr(self.parent.main_window, 'worker') else False,
                    'timestamp': datetime.now().isoformat()
                }

        # Bind parent reference
        SystemStatus.parent = self

        @self.ns_system.route('/info')
        class SystemInfo(Resource):
            def get(self):
                """Detaillierte System-Informationen"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                mw = self.parent.main_window
                return {
                    'application': 'Arduino Control Panel',
                    'version': '1.0.0',
                    'features': {
                        'analytics': hasattr(mw, 'analytics_tab'),
                        'hardware_profiles': hasattr(mw, 'hardware_profile_tab'),
                        'calibration': True
                    },
                    'statistics': {
                        'sequences': len(mw.sequences) if hasattr(mw, 'sequences') else 0,
                        'profiles': len(mw.hardware_profile_tab.profile_manager.profiles) if hasattr(mw, 'hardware_profile_tab') else 0
                    }
                }

        SystemInfo.parent = self

    def setup_pin_endpoints(self):
        """Pin Control Endpoints"""

        pin_model = self.api.model('Pin', {
            'pin': fields.String(required=True, description='Pin Name (z.B. D13, A0)'),
            'value': fields.Integer(required=True, description='Pin Wert (0 oder 1 für digital)')
        })

        @self.ns_pins.route('/')
        class PinList(Resource):
            @self.api.doc(security='apikey')
            def get(self):
                """Liste aller Pins und deren Status"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                # Hole Pin-Status aus Pin Overview
                pins = {}
                if hasattr(self.parent.main_window, 'pin_overview_tab'):
                    overview = self.parent.main_window.pin_overview_tab
                    # Extrahiere Pin-States
                    for pin_name, widget in overview.pin_widgets.items():
                        pins[pin_name] = {
                            'name': pin_name,
                            'mode': widget.mode,
                            'value': widget.value
                        }

                return {'pins': pins}

        PinList.parent = self

        @self.ns_pins.route('/<string:pin_name>')
        class Pin(Resource):
            @self.api.doc(security='apikey')
            def get(self, pin_name):
                """Pin-Status abrufen"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                if hasattr(self.parent.main_window, 'pin_overview_tab'):
                    overview = self.parent.main_window.pin_overview_tab
                    if pin_name in overview.pin_widgets:
                        widget = overview.pin_widgets[pin_name]
                        return {
                            'pin': pin_name,
                            'mode': widget.mode,
                            'value': widget.value
                        }

                return {'error': f'Pin {pin_name} not found'}, 404

            @self.api.expect(pin_model)
            @self.api.doc(security='apikey')
            def post(self, pin_name):
                """Pin-Wert setzen"""
                if not self.parent.check_api_key():
                    return {'error': 'Invalid API key'}, 401

                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                data = request.json
                value = data.get('value', 0)

                # Sende Command
                command = {
                    'id': f'api_{datetime.now().timestamp()}',
                    'command': 'digital_write',
                    'pin': pin_name,
                    'value': int(value)
                }

                self.parent.main_window.send_command(command)

                return {
                    'success': True,
                    'pin': pin_name,
                    'value': value
                }

        Pin.parent = self

    def setup_sensor_endpoints(self):
        """Sensor Data Endpoints"""

        @self.ns_sensors.route('/')
        class SensorList(Resource):
            def get(self):
                """Liste aller Sensoren"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                sensors = {}
                if hasattr(self.parent.main_window, 'sensor_tab'):
                    sensor_tab = self.parent.main_window.sensor_tab
                    # B24 Sensor
                    sensors['B24_TEMP'] = {
                        'name': 'Temperatur (B24)',
                        'value': float(sensor_tab.b24_sensor.temp_value.text().replace('°C', '').replace('--', '0')),
                        'unit': '°C',
                        'min': sensor_tab.b24_sensor.temp_min,
                        'max': sensor_tab.b24_sensor.temp_max
                    }
                    sensors['B24_HUMIDITY'] = {
                        'name': 'Luftfeuchtigkeit (B24)',
                        'value': float(sensor_tab.b24_sensor.humid_value.text().replace('%', '').replace('--', '0')),
                        'unit': '%',
                        'min': sensor_tab.b24_sensor.humid_min,
                        'max': sensor_tab.b24_sensor.humid_max
                    }

                return {'sensors': sensors}

        SensorList.parent = self

        @self.ns_sensors.route('/<string:sensor_id>')
        class Sensor(Resource):
            def get(self, sensor_id):
                """Sensor-Daten abrufen"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                if hasattr(self.parent.main_window, 'sensor_tab'):
                    sensor_tab = self.parent.main_window.sensor_tab

                    if sensor_id == 'B24_TEMP':
                        return {
                            'sensor_id': sensor_id,
                            'name': 'Temperatur (B24)',
                            'value': float(sensor_tab.b24_sensor.temp_value.text().replace('°C', '').replace('--', '0')),
                            'unit': '°C',
                            'calibrated': sensor_tab.b24_sensor.temp_calibration_active if hasattr(sensor_tab.b24_sensor, 'temp_calibration_active') else False
                        }
                    elif sensor_id == 'B24_HUMIDITY':
                        return {
                            'sensor_id': sensor_id,
                            'name': 'Luftfeuchtigkeit (B24)',
                            'value': float(sensor_tab.b24_sensor.humid_value.text().replace('%', '').replace('--', '0')),
                            'unit': '%',
                            'calibrated': sensor_tab.b24_sensor.humid_calibration_active if hasattr(sensor_tab.b24_sensor, 'humid_calibration_active') else False
                        }

                return {'error': f'Sensor {sensor_id} not found'}, 404

        Sensor.parent = self

    def setup_sequence_endpoints(self):
        """Sequence Management Endpoints"""

        @self.ns_sequences.route('/')
        class SequenceList(Resource):
            def get(self):
                """Liste aller Sequenzen"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                sequences = {}
                if hasattr(self.parent.main_window, 'sequences'):
                    for seq_id, seq_data in self.parent.main_window.sequences.items():
                        sequences[seq_id] = {
                            'id': seq_id,
                            'name': seq_data.get('name'),
                            'cycles': seq_data.get('cycles', 1),
                            'steps': len(seq_data.get('steps', [])),
                            'favorite': seq_data.get('favorite', False)
                        }

                return {'sequences': sequences}

        SequenceList.parent = self

        @self.ns_sequences.route('/<string:seq_id>')
        class Sequence(Resource):
            def get(self, seq_id):
                """Sequenz-Details abrufen"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                if hasattr(self.parent.main_window, 'sequences'):
                    if seq_id in self.parent.main_window.sequences:
                        return self.parent.main_window.sequences[seq_id]

                return {'error': f'Sequence {seq_id} not found'}, 404

        Sequence.parent = self

        @self.ns_sequences.route('/<string:seq_id>/start')
        class SequenceStart(Resource):
            @self.api.doc(security='apikey')
            def post(self, seq_id):
                """Sequenz starten"""
                if not self.parent.check_api_key():
                    return {'error': 'Invalid API key'}, 401

                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                if hasattr(self.parent.main_window, 'sequences'):
                    if seq_id in self.parent.main_window.sequences:
                        # Starte Sequenz
                        self.parent.main_window.start_sequence(seq_id)
                        return {
                            'success': True,
                            'sequence_id': seq_id,
                            'message': 'Sequence started'
                        }

                return {'error': f'Sequence {seq_id} not found'}, 404

        SequenceStart.parent = self

    def setup_archive_endpoints(self):
        """Archive Endpoints"""

        @self.ns_archive.route('/')
        class ArchiveList(Resource):
            def get(self):
                """Liste aller Test-Läufe"""
                if not self.parent.main_window:
                    return {'error': 'Main window not initialized'}, 503

                runs = []
                if hasattr(self.parent.main_window, 'db'):
                    all_runs = self.parent.main_window.db.get_all_runs()
                    for run in all_runs:
                        runs.append({
                            'id': run[0],
                            'name': run[1],
                            'sequence': run[2],
                            'start_time': run[3],
                            'duration': run[4],
                            'cycles': run[5],
                            'status': run[6]
                        })

                return {'runs': runs}

        ArchiveList.parent = self

    def setup_calibration_endpoints(self):
        """Calibration Endpoints"""

        @self.ns_calibration.route('/')
        class CalibrationList(Resource):
            def get(self):
                """Liste aller Kalibrierungen"""
                calibrations = {}
                try:
                    from core.calibration_manager import CalibrationManager
                    manager = CalibrationManager()

                    for sensor_id, cal in manager.calibrations.items():
                        calibrations[sensor_id] = {
                            'sensor_id': sensor_id,
                            'type': cal.calibration_type,
                            'quality': cal.quality_score,
                            'active': cal.is_active,
                            'created': cal.created_at
                        }
                except ImportError:
                    pass

                return {'calibrations': calibrations}

        CalibrationList.parent = self

    def setup_websocket(self):
        """Setup WebSocket für Live-Daten"""

        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"✅ WebSocket Client verbunden: {request.sid}")
            emit('message', {'data': 'Connected to Arduino Control Panel WebSocket'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"❌ WebSocket Client getrennt: {request.sid}")

        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Client abonniert Daten-Typ"""
            data_type = data.get('type', 'all')
            logger.info(f"Client {request.sid} abonniert: {data_type}")
            emit('subscribed', {'type': data_type})

    def broadcast_sensor_data(self, data: Dict[str, Any]):
        """Sendet Sensor-Daten an alle WebSocket Clients"""
        self.socketio.emit('sensor_data', data)

    def broadcast_pin_update(self, data: Dict[str, Any]):
        """Sendet Pin-Update an alle WebSocket Clients"""
        self.socketio.emit('pin_update', data)

    def start(self):
        """Startet den API Server in eigenem Thread"""
        if self.is_running:
            logger.warning("API Server läuft bereits")
            return

        def run_server():
            logger.info(f"🚀 REST API Server startet auf http://{self.host}:{self.port}")
            logger.info(f"📚 Swagger Dokumentation: http://{self.host}:{self.port}/api/docs")
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False, use_reloader=False)

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True

        logger.info("✅ REST API Server Thread gestartet")

    def stop(self):
        """Stoppt den API Server"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("🛑 REST API Server gestoppt")
