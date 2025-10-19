import json
import serial
import serial.tools.list_ports
import time
from collections import deque
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker, QTimer

# ==================== ENHANCED SERIAL WORKER ====================
class SerialWorker(QThread):
    data_received = pyqtSignal(dict)
    status_changed = pyqtSignal(str)
    stats_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.serial = None
        self.running = False
        self.simulation = False
        self.sim_pins = {}
        self.lock = QMutex()
        self._stop_requested = False
        
        self.command_queue = deque()
        self.burst_mode = False
        self.burst_delay = 10
        
        self.stats = {
            'commands_sent': 0, 'responses_received': 0,
            'errors': 0, 'avg_response_time': 0
        }
        self.response_times = deque(maxlen=100)
    
    def connect_serial(self, port, baud=115200):
        try:
            self.serial = serial.Serial(port, baud, timeout=0.1)
            time.sleep(0.5)
            self.running = True
            self.simulation = False
            self._stop_requested = False
            self.status_changed.emit(f"Verbunden: {port}")
            self.start()
        except Exception as e:
            self.status_changed.emit(f"Fehler: {e}")
    
    def connect_simulation(self):
        self.simulation = True
        self.running = True
        self.sim_pins = {}
        self._stop_requested = False
        self.status_changed.emit("Simulation aktiv")
        self.start()
    
    def disconnect_serial(self):
        self._stop_requested = True
        self.running = False
        if self.serial and self.serial.is_open:
            try: self.serial.close()
            except: pass
        self.wait(2000)
        self.status_changed.emit("Getrennt")
    
    def is_connected(self):
        return self.running and not self._stop_requested
    
    def set_burst_mode(self, enabled, delay_ms=10):
        self.burst_mode = enabled
        self.burst_delay = delay_ms
    
    def run(self):
        while self.running and not self._stop_requested:
            try:
                # KORREKTUR: 'QMutexLocker' wird hier korrekt verwendet.
                # Es stellt sicher, dass der Zugriff auf die 'command_queue' threadsicher ist.
                command = None
                with QMutexLocker(self.lock):
                    if self.command_queue:
                        command = self.command_queue.popleft()

                if command:
                    self._send_command_internal(command)

                    if self.burst_mode:
                        self.msleep(self.burst_delay)
                
                if self.simulation:
                    self.msleep(100)
                    continue
                
                if self.serial and self.serial.is_open and self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.data_received.emit(data)
                            if data.get('type') == 'response':
                                self.stats['responses_received'] += 1
                        except json.JSONDecodeError:
                            # Ignoriere fehlerhafte JSON-Daten vom Arduino
                            pass
                
                self.msleep(10 if self.burst_mode else 50)
                
                if self.stats['commands_sent'] > 0 and self.stats['commands_sent'] % 20 == 0:
                    self.stats_updated.emit(self.stats.copy())
                
            except Exception as e:
                if self.running:
                    # Der Fehler wird jetzt in der Konsole ausgegeben, um das Problem zu identifizieren.
                    print(f"Serial Worker Error: {e}")
                    self.stats['errors'] += 1
                self.msleep(100)
    
    def send_command(self, command):
        if not self.is_connected(): return
        with QMutexLocker(self.lock):
            self.command_queue.append(command)
        self.stats['commands_sent'] += 1
    
    def _send_command_internal(self, command):
        try:
            if self.simulation:
                QTimer.singleShot(10, lambda: self._exec_simulation(command))
            elif self.serial and self.serial.is_open:
                send_time = time.time()
                cmd_json = json.dumps(command) + '\n'
                self.serial.write(cmd_json.encode('utf-8'))
                self.serial.flush()
                
                response_time = (time.time() - send_time) * 1000
                self.response_times.append(response_time)
                self.stats['avg_response_time'] = sum(self.response_times) / len(self.response_times)
        except Exception as e:
            print(f"Send Error: {e}")
            self.stats['errors'] += 1
    
    def _exec_simulation(self, command):
        cmd_type = command.get("command")
        pin = command.get("pin", "")
        msg_id = command.get("id", "")
        response = {"type": "response", "status": "ok", "response_to": msg_id}
        
        if cmd_type == "digital_write":
            value = command.get("value", 0)
            self.sim_pins[pin] = value
            self.data_received.emit(response)
            self.data_received.emit({"type": "pin_update", "pin_name": pin, "value": value})
        
        elif cmd_type in ["analog_read", "digital_read"]:
            import random
            value = random.randint(0, 1023) if 'analog' in cmd_type else self.sim_pins.get(pin, 0)
            response["value"] = value
            self.data_received.emit(response)
            self.data_received.emit({"type": "pin_update", "pin_name": pin, "value": value})

        elif cmd_type == "read_sensor":
            import random
            if command.get("sensor") == "B24_TEMP_HUMIDITY":
                temp = 22.5 + (random.random() - 0.5)
                humid = 45.0 + (random.random() - 0.5) * 5
                self.data_received.emit({"type": "sensor_update", "sensor": "B24_TEMP", "value": temp})
                self.data_received.emit({"type": "sensor_update", "sensor": "B24_HUMIDITY", "value": humid})
            self.data_received.emit(response)
        else:
            self.data_received.emit(response)

