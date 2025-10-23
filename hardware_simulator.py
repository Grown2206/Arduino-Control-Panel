"""
Hardware-Simulation Modul
Simuliert Arduino ohne echte Hardware - perfekt für Entwicklung, Testing und Training

Features:
- Vollständige Pin-Simulation (Digital + Analog)
- Realistische Delays und Timing
- Sensor-Simulation (DHT11, HC-SR04, Vibration)
- Fehler-Simulation (konfigurierbar)
- Identische Schnittstelle wie SerialWorker
"""

import time
import random
import json
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Optional


class ArduinoSimulator(QObject):
    """
    Simuliert einen Arduino Uno mit allen Features.
    Kann als Drop-in-Replacement für SerialWorker verwendet werden.
    """
    
    # Gleiche Signals wie SerialWorker
    data_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Simulationskonfiguration
        self.config = {
            'latency_ms': 10,           # Simulated command latency
            'error_rate': 0.0,          # 0.0 = keine Fehler, 0.05 = 5% Fehlerrate
            'noise_amplitude': 0.05,    # Rauschen auf Analog-Pins (±5%)
            'realistic_timing': True,   # Realistische Delays simulieren
            'board_type': 'UNO',        # UNO, MEGA, ESP32
        }
        
        # Pin-Zustände
        self.digital_pins = {f'D{i}': {'mode': 'INPUT', 'value': 0} for i in range(14)}
        self.analog_pins = {f'A{i}': {'mode': 'ANALOG_INPUT', 'value': 0} for i in range(6)}
        
        # Sensor-Simulation
        self.sensors = {
            'B24_TEMP': {
                'base_value': 23.5,
                'range': (18.0, 32.0),
                'drift_rate': 0.01,  # Langsame Drift
                'noise': 0.2
            },
            'B24_HUMIDITY': {
                'base_value': 45.0,
                'range': (30.0, 70.0),
                'drift_rate': 0.02,
                'noise': 1.0
            },
            'VIBRATION': {
                'base_value': 0,
                'spike_probability': 0.05,  # 5% Chance auf Spike
                'spike_duration_ms': 50
            },
            'ULTRASONIC': {
                'base_value': 150,  # cm
                'range': (2, 400),
                'noise': 2.0
            }
        }
        
        # Laufzeitvariablen
        self.is_connected = False
        self.command_counter = 0
        self.start_time = 0
        
        # Timer für Sensor-Updates
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self._update_sensors)
        self.sensor_timer.setInterval(1000)  # Jede Sekunde
        
        print("🎮 Arduino-Simulator initialisiert")
    
    # === PUBLIC API (kompatibel mit SerialWorker) ===
    
    def connect(self, port: str = "SIM", baudrate: int = 115200) -> bool:
        """
        Simuliert Verbindungsaufbau.
        
        Args:
            port: Wird ignoriert (immer "SIM")
            baudrate: Wird ignoriert
            
        Returns:
            True (Simulation verbindet immer erfolgreich)
        """
        print(f"🎮 Verbinde mit simuliertem Arduino...")
        
        # Simuliere Verbindungs-Delay
        time.sleep(0.5)
        
        self.is_connected = True
        self.start_time = time.time()
        
        # Starte Sensor-Simulation
        self.sensor_timer.start()
        
        # Sende Success-Message
        self._send_response({
            'type': 'status',
            'message': 'Arduino Simulator v1.0 bereit',
            'board': self.config['board_type'],
            'timestamp': time.time() * 1000
        })
        
        self.connected.emit()
        print("✅ Verbindung zu Simulator hergestellt")
        return True
    
    def disconnect(self):
        """Trennt Verbindung."""
        if not self.is_connected:
            return
        
        self.is_connected = False
        self.sensor_timer.stop()
        
        self._send_response({
            'type': 'status',
            'message': 'Simulator getrennt'
        })
        
        self.disconnected.emit()
        print("🔌 Simulator getrennt")
    
    def send_command(self, command: dict):
        """
        Verarbeitet Kommandos wie echter Arduino.
        
        Args:
            command: Command-Dict mit 'command', 'id', und Parameters
        """
        if not self.is_connected:
            print("⚠️ Simulator nicht verbunden")
            return
        
        # Simuliere Latency
        if self.config['realistic_timing']:
            time.sleep(self.config['latency_ms'] / 1000.0)
        
        # Simuliere Fehlerrate
        if random.random() < self.config['error_rate']:
            self._send_error(command.get('id', ''), "Simulated error")
            return
        
        # Verarbeite Command
        cmd_type = command.get('command', '')
        
        if cmd_type == 'pin_mode':
            self._handle_pin_mode(command)
        elif cmd_type == 'digital_write':
            self._handle_digital_write(command)
        elif cmd_type == 'digital_read':
            self._handle_digital_read(command)
        elif cmd_type == 'analog_read':
            self._handle_analog_read(command)
        elif cmd_type == 'sensor_read':
            self._handle_sensor_read(command)
        elif cmd_type == 'ping':
            self._handle_ping(command)
        else:
            self._send_error(command.get('id', ''), f"Unknown command: {cmd_type}")
        
        self.command_counter += 1
    
    # === COMMAND HANDLERS ===
    
    def _handle_pin_mode(self, cmd: dict):
        """Setzt Pin-Modus."""
        pin_name = cmd.get('pin', '')
        mode = cmd.get('mode', 'INPUT')
        msg_id = cmd.get('id', '')
        
        if pin_name in self.digital_pins:
            self.digital_pins[pin_name]['mode'] = mode
            self._send_success(msg_id, f"Pin {pin_name} mode set to {mode}")
        elif pin_name in self.analog_pins:
            self.analog_pins[pin_name]['mode'] = mode
            self._send_success(msg_id, f"Pin {pin_name} mode set to {mode}")
        else:
            self._send_error(msg_id, f"Invalid pin: {pin_name}")
    
    def _handle_digital_write(self, cmd: dict):
        """Schreibt Digital-Pin."""
        pin_name = cmd.get('pin', '')
        value = cmd.get('value', 0)
        msg_id = cmd.get('id', '')
        
        if pin_name not in self.digital_pins:
            self._send_error(msg_id, f"Invalid pin: {pin_name}")
            return
        
        # Prüfe ob Pin als OUTPUT konfiguriert
        if self.digital_pins[pin_name]['mode'] != 'OUTPUT':
            self._send_error(msg_id, f"Pin {pin_name} not in OUTPUT mode")
            return
        
        self.digital_pins[pin_name]['value'] = value
        self._send_success(msg_id, f"Pin {pin_name} set to {value}")
        
        # Sende Pin-Update
        self._send_response({
            'type': 'pin_update',
            'pin_name': pin_name,
            'value': value,
            'timestamp': time.time() * 1000
        })
    
    def _handle_digital_read(self, cmd: dict):
        """Liest Digital-Pin."""
        pin_name = cmd.get('pin', '')
        msg_id = cmd.get('id', '')
        
        if pin_name not in self.digital_pins:
            self._send_error(msg_id, f"Invalid pin: {pin_name}")
            return
        
        # Simuliere INPUT-Wert (random für Demo)
        if self.digital_pins[pin_name]['mode'] == 'INPUT':
            value = random.choice([0, 1]) if random.random() < 0.3 else 0
            self.digital_pins[pin_name]['value'] = value
        else:
            value = self.digital_pins[pin_name]['value']
        
        self._send_response({
            'type': 'digital_read',
            'id': msg_id,
            'pin': pin_name,
            'value': value,
            'timestamp': time.time() * 1000
        })
    
    def _handle_analog_read(self, cmd: dict):
        """Liest Analog-Pin."""
        pin_name = cmd.get('pin', '')
        msg_id = cmd.get('id', '')
        
        if pin_name not in self.analog_pins:
            self._send_error(msg_id, f"Invalid pin: {pin_name}")
            return
        
        # Simuliere Analog-Wert mit Noise
        base_value = self.analog_pins[pin_name]['value']
        
        if base_value == 0:
            # Generiere realistischen Wert
            base_value = random.randint(0, 1023)
        
        # Addiere Noise
        noise = random.uniform(-self.config['noise_amplitude'], 
                              self.config['noise_amplitude'])
        value = int(base_value * (1 + noise))
        value = max(0, min(1023, value))  # Clamp
        
        self.analog_pins[pin_name]['value'] = value
        
        self._send_response({
            'type': 'analog_read',
            'id': msg_id,
            'pin': pin_name,
            'value': value,
            'timestamp': time.time() * 1000
        })
    
    def _handle_sensor_read(self, cmd: dict):
        """Liest Sensor-Wert."""
        sensor_type = cmd.get('sensor', '')
        msg_id = cmd.get('id', '')
        
        if sensor_type not in self.sensors:
            self._send_error(msg_id, f"Unknown sensor: {sensor_type}")
            return
        
        # Generiere Sensor-Wert
        sensor_cfg = self.sensors[sensor_type]
        
        if sensor_type in ['B24_TEMP', 'B24_HUMIDITY']:
            # Temperatur/Humidity mit Drift und Noise
            base = sensor_cfg['base_value']
            noise = random.uniform(-sensor_cfg['noise'], sensor_cfg['noise'])
            value = base + noise
            
            # Clamp zu Range
            value = max(sensor_cfg['range'][0], min(sensor_cfg['range'][1], value))
            
            # Langsame Drift simulieren
            sensor_cfg['base_value'] += random.uniform(-sensor_cfg['drift_rate'], 
                                                       sensor_cfg['drift_rate'])
        
        elif sensor_type == 'VIBRATION':
            # Vibration mit Spikes
            if random.random() < sensor_cfg['spike_probability']:
                value = random.randint(800, 1023)  # Spike!
            else:
                value = random.randint(0, 50)  # Ruhe
        
        elif sensor_type == 'ULTRASONIC':
            # Ultraschall mit Noise
            base = sensor_cfg['base_value']
            noise = random.uniform(-sensor_cfg['noise'], sensor_cfg['noise'])
            value = base + noise
            value = max(sensor_cfg['range'][0], min(sensor_cfg['range'][1], value))
        
        else:
            value = 0
        
        self._send_response({
            'type': 'sensor_data',
            'id': msg_id,
            'sensor': sensor_type,
            'value': round(value, 2),
            'timestamp': time.time() * 1000
        })
    
    def _handle_ping(self, cmd: dict):
        """Antwortet auf Ping."""
        msg_id = cmd.get('id', '')
        
        self._send_response({
            'type': 'pong',
            'id': msg_id,
            'timestamp': time.time() * 1000,
            'uptime': int((time.time() - self.start_time) * 1000)
        })
    
    # === SENSOR-UPDATES ===
    
    def _update_sensors(self):
        """Sendet periodische Sensor-Updates (wie echter Arduino)."""
        if not self.is_connected:
            return
        
        # DHT11 Update
        for sensor in ['B24_TEMP', 'B24_HUMIDITY']:
            if sensor in self.sensors:
                cfg = self.sensors[sensor]
                base = cfg['base_value']
                noise = random.uniform(-cfg['noise'], cfg['noise'])
                value = base + noise
                value = max(cfg['range'][0], min(cfg['range'][1], value))
                
                self._send_response({
                    'type': 'sensor_data',
                    'sensor': sensor,
                    'value': round(value, 2),
                    'timestamp': time.time() * 1000
                })
    
    # === HELPER METHODS ===
    
    def _send_response(self, data: dict):
        """Sendet Daten an GUI."""
        self.data_received.emit(data)
    
    def _send_success(self, msg_id: str, message: str):
        """Sendet Success-Response."""
        self._send_response({
            'type': 'success',
            'id': msg_id,
            'message': message,
            'timestamp': time.time() * 1000
        })
    
    def _send_error(self, msg_id: str, error: str):
        """Sendet Error-Response."""
        self._send_response({
            'type': 'error',
            'id': msg_id,
            'error': error,
            'timestamp': time.time() * 1000
        })
    
    # === CONFIGURATION ===
    
    def set_latency(self, ms: int):
        """Setzt simulierte Latenz."""
        self.config['latency_ms'] = ms
        print(f"🎮 Latenz auf {ms}ms gesetzt")
    
    def set_error_rate(self, rate: float):
        """Setzt Fehlerrate (0.0 - 1.0)."""
        self.config['error_rate'] = max(0.0, min(1.0, rate))
        print(f"🎮 Fehlerrate auf {rate*100:.1f}% gesetzt")
    
    def set_noise(self, amplitude: float):
        """Setzt Noise-Amplitude."""
        self.config['noise_amplitude'] = amplitude
        print(f"🎮 Noise auf ±{amplitude*100:.1f}% gesetzt")
    
    def get_stats(self) -> dict:
        """Gibt Simulator-Statistiken zurück."""
        return {
            'connected': self.is_connected,
            'uptime': int((time.time() - self.start_time) * 1000) if self.is_connected else 0,
            'commands_processed': self.command_counter,
            'digital_pins': len(self.digital_pins),
            'analog_pins': len(self.analog_pins),
            'sensors': list(self.sensors.keys()),
            'config': self.config.copy()
        }


# === SIMULATOR FACTORY ===

def create_simulator(board_type: str = 'UNO') -> ArduinoSimulator:
    """
    Factory-Funktion zum Erstellen eines konfigurierten Simulators.
    
    Args:
        board_type: 'UNO', 'MEGA', 'ESP32'
        
    Returns:
        Konfigurierter ArduinoSimulator
    """
    sim = ArduinoSimulator()
    sim.config['board_type'] = board_type
    
    # Board-spezifische Konfiguration
    if board_type == 'MEGA':
        # Mega hat mehr Pins
        for i in range(14, 54):
            sim.digital_pins[f'D{i}'] = {'mode': 'INPUT', 'value': 0}
        for i in range(6, 16):
            sim.analog_pins[f'A{i}'] = {'mode': 'ANALOG_INPUT', 'value': 0}
    
    elif board_type == 'ESP32':
        # ESP32 hat WiFi (nur simuliert)
        sim.config['has_wifi'] = True
        sim.config['latency_ms'] = 20  # WiFi-Latenz
    
    print(f"🎮 {board_type}-Simulator erstellt ({len(sim.digital_pins)}D + {len(sim.analog_pins)}A Pins)")
    return sim


# === BEISPIEL-VERWENDUNG ===

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Simulator erstellen
    sim = create_simulator('UNO')
    
    # Event-Handler
    def on_data(data):
        print(f"📨 Daten empfangen: {data}")
    
    sim.data_received.connect(on_data)
    
    # Verbinden
    sim.connect()
    
    # Test-Commands
    sim.send_command({'command': 'pin_mode', 'pin': 'D13', 'mode': 'OUTPUT', 'id': '1'})
    sim.send_command({'command': 'digital_write', 'pin': 'D13', 'value': 1, 'id': '2'})
    sim.send_command({'command': 'analog_read', 'pin': 'A0', 'id': '3'})
    sim.send_command({'command': 'sensor_read', 'sensor': 'B24_TEMP', 'id': '4'})
    
    # Stats anzeigen
    print("\n📊 Simulator-Stats:")
    for key, value in sim.get_stats().items():
        print(f"  {key}: {value}")
    
    sys.exit(app.exec())