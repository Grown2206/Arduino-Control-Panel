import serial
import json
import time
import uuid
from PyQt6.QtCore import QThread, pyqtSignal
import random

class SerialWorker(QThread):
    """
    Handles serial communication with the Arduino in a separate thread.
    KORRIGIERT: Implementiert einen sauberen Shutdown-Mechanismus, um
    OSError unter Windows zu vermeiden.
    """
    data_received = pyqtSignal(dict)
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = False  # Flag to control the run loop

    def connect_serial(self, port, baudrate=115200):
        """Connects to the specified serial port."""
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            # Warten, bis der Arduino bereit ist
            time.sleep(2)
            self.running = True
            self.start()
            self.status_changed.emit(f"Verbunden mit: {port}")
            print(f"Verbindung zu {port} hergestellt.")
        except serial.SerialException as e:
            self.status_changed.emit(f"Fehler: {e}")
            print(f"Fehler bei der Verbindung: {e}")

    def connect_simulation(self):
        """Starts the simulation mode."""
        self.running = True
        self.ser = "SIMULATION" # Set sentinel for simulation
        self.start()
        self.status_changed.emit("Simulation gestartet")
        print("Simulationsmodus gestartet.")

    def disconnect_serial(self):
        """Gracefully disconnects from the serial port."""
        if self.running:
            self.running = False
            self.wait(2000) # Warte max. 2 Sekunden, bis der Thread beendet ist
            if self.ser and self.ser != "SIMULATION":
                self.ser.close()
            self.ser = None
            self.status_changed.emit("Verbindung getrennt")
            print("Verbindung getrennt.")

    def send_command(self, command_dict):
        """Sends a JSON command to the Arduino."""
        if self.is_connected():
            try:
                # Füge immer eine ID hinzu, falls nicht vorhanden
                if "id" not in command_dict:
                    command_dict["id"] = str(uuid.uuid4())
                
                command_str = json.dumps(command_dict) + '\n'
                
                if self.ser == "SIMULATION":
                    print(f"SIM -> Arduino: {command_str.strip()}")
                else:
                    self.ser.write(command_str.encode('utf-8'))
                
                # Sende eine "ok" Antwort in der Simulation
                if self.ser == "SIMULATION":
                    response = {"type": "response", "id": command_dict["id"], "status": "ok"}
                    self.data_received.emit(response)

            except (serial.SerialException, TypeError, AttributeError) as e:
                self.status_changed.emit(f"Sendefehler: {e}")
                print(f"Fehler beim Senden: {e}")

    def is_connected(self):
        """Checks if the connection is active."""
        return self.running and self.ser is not None

    def run(self):
        """The main loop of the thread, reads data from serial or simulates it."""
        while self.running:
            if self.ser == "SIMULATION":
                # Simuliere Pin- und Sensor-Daten
                self._run_simulation_cycle()
                time.sleep(0.1) # Simuliere Leseintervall
            elif self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line:
                            try:
                                data = json.loads(line)
                                self.data_received.emit(data)
                            except json.JSONDecodeError:
                                # Manchmal sendet der Arduino Debug-Infos
                                print(f"Ungültiges JSON empfangen: {line}")
                except serial.SerialException:
                    # Port wurde wahrscheinlich geschlossen
                    self.status_changed.emit("Fehler: Port nicht verfügbar.")
                    break
                except Exception as e:
                    print(f"Unerwarteter Fehler im Lesethread: {e}")
                    break
            else:
                # Beende den Thread, wenn keine Verbindung mehr besteht
                break
        
        # Aufräumen, falls der Thread unerwartet endet
        self.running = False
        print("Serial-Worker-Thread beendet.")
    
    def _run_simulation_cycle(self):
        """Generates a cycle of simulated data."""
        # Simuliere ein Pin-Update (z.B. ein pulsierender Analog-Pin)
        pin_update = {
            "type": "pin_update",
            "pin_name": "A0",
            "value": int(512 + 511 * (0.5 + 0.5 * random.random()))
        }
        self.data_received.emit(pin_update)
        
        # Simuliere alle paar Zyklen ein Sensor-Update
        if random.random() < 0.1: # ca. jede Sekunde
             sensor_update = {
                "type": "sensor_update",
                "sensor": "B24_TEMP",
                "value": round(20 + 5 * random.random(), 2)
            }
             self.data_received.emit(sensor_update)
             sensor_update = {
                "type": "sensor_update",
                "sensor": "B24_HUMIDITY",
                "value": round(40 + 10 * random.random(), 2)
            }
             self.data_received.emit(sensor_update)
