import time
import uuid
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QEventLoop, QTimer, QMutex, QMutexLocker

class SequenceRunner(QThread):
    """Führt eine Testsequenz in einem separaten Thread aus."""
    step_update = pyqtSignal(dict)
    cycle_completed = pyqtSignal(float, bool)  # (cycle_time, is_anomaly)
    finished = pyqtSignal(int, str, list)
    command_signal = pyqtSignal(dict)
    # KORREKTUR: Fehlendes Signal hier definieren
    step_highlight_signal = pyqtSignal(int) # NEU: Signal für Live-Highlighting

    def __init__(self):
        super().__init__()
        self.sequence = None
        self.running = False
        self.paused = False
        self._stop_requested = False
        self.current_step = 0
        self.current_cycle = 0
        self.log = []
        self.start_time = 0
        self.cycle_start_times = []

        # Thread-safe flags mit Mutex
        self._wait_mutex = QMutex()
        self._is_waiting_for_pin = False
        self._wait_pin_name = None
        self._wait_target_state = None
        self._wait_success = False

    def start_sequence(self, sequence):
        self.sequence = sequence
        self.running = True
        self.paused = False
        self._stop_requested = False
        self.current_step = 0
        self.current_cycle = 0
        self.log = []
        self.start_time = time.time()
        self.cycle_start_times = [self.start_time]
        self.start()

    def on_pin_update(self, pin_name, value):
        """Thread-safe Pin-Update Handler (läuft im Main-Thread)."""
        with QMutexLocker(self._wait_mutex):
            if self._is_waiting_for_pin and pin_name == self._wait_pin_name:
                if value == self._wait_target_state:
                    self._wait_success = True
                    self._is_waiting_for_pin = False

    def pause_sequence(self):
        self.paused = not self.paused
    
    def stop_sequence(self):
        self._stop_requested = True
        self.running = False
        with QMutexLocker(self._wait_mutex):
            self._is_waiting_for_pin = False
        self.wait(2000)
    
    def run(self):
        try:
            steps = self.sequence.get("steps", [])
            if not steps:
                return 

            max_cycles = self.sequence.get("cycles", 1)
            
            while self.running and not self._stop_requested:
                if self.paused:
                    self.msleep(100)
                    continue
                
                if max_cycles > 0 and self.current_cycle >= max_cycles:
                    break
                
                if self.current_step < len(steps):
                    # Signal für das Highlighting des aktuellen Schritts senden
                    self.step_highlight_signal.emit(self.current_step)

                    step = steps[self.current_step]
                    step_executed = self.execute_step(step)

                    if not step_executed:
                        break 
                    
                    self.current_step += 1

                if self.current_step >= len(steps):
                    # Zyklus abgeschlossen
                    self.current_cycle += 1
                    self.current_step = 0
                    current_time = time.time()
                    self.cycle_start_times.append(current_time)

                    # Berechne Zyklus-Zeit
                    if len(self.cycle_start_times) >= 2:
                        cycle_time_sec = self.cycle_start_times[-1] - self.cycle_start_times[-2]
                        time_ms = cycle_time_sec * 1000

                        # Anomalie-Erkennung (einfach: > 2x Durchschnitt wenn genug Daten)
                        is_anomaly = False
                        if len(self.cycle_start_times) > 5:
                            # Berechne Durchschnitt der letzten 5 Zyklen
                            recent_times = []
                            for i in range(len(self.cycle_start_times) - 5, len(self.cycle_start_times) - 1):
                                if i > 0:
                                    recent_times.append((self.cycle_start_times[i] - self.cycle_start_times[i-1]) * 1000)

                            if recent_times:
                                avg_time = sum(recent_times) / len(recent_times)
                                is_anomaly = time_ms > (avg_time * 2)  # Mehr als 2x Durchschnitt

                        # Feuer cycle_completed Signal für Live-Stats
                        self.cycle_completed.emit(time_ms, is_anomaly)

                # Update UI periodically
                info = self.calculate_progress_info(max_cycles, len(steps))
                self.step_update.emit(info)
        finally:
            self.step_highlight_signal.emit(-1) # Highlighting aufheben
            status = "Gestoppt" if self._stop_requested else "Abgeschlossen"

            # Thread-safe Status-Check
            with QMutexLocker(self._wait_mutex):
                if not self._wait_success and self._is_waiting_for_pin:
                    status = "Timeout"
                self._is_waiting_for_pin = False

            self.finished.emit(self.current_cycle, status, self.log)


    def calculate_progress_info(self, max_cycles, total_steps):
        elapsed = time.time() - self.start_time
        avg_cycle_time = 0
        if len(self.cycle_start_times) > 1:
            cycle_times = [self.cycle_start_times[i+1] - self.cycle_start_times[i] for i in range(len(self.cycle_start_times)-1)]
            avg_cycle_time = np.mean(cycle_times) if cycle_times else 0
        
        eta_seconds = 0
        if max_cycles > 0 and avg_cycle_time > 0:
            eta_seconds = (max_cycles - self.current_cycle) * avg_cycle_time
        
        progress_percent = (self.current_cycle / max_cycles) * 100 if max_cycles > 0 else 0
        cycles_per_sec = self.current_cycle / elapsed if elapsed > 0 else 0
        
        return {
            "step": self.current_step, "cycle": self.current_cycle, "max_cycles": max_cycles,
            "total_steps": total_steps, "elapsed": elapsed, "avg_cycle_time": avg_cycle_time,
            "eta": eta_seconds, "progress_percent": progress_percent, "cycles_per_sec": cycles_per_sec
        }
    
    def execute_step(self, step):
        action = step["action"]
        pin = step.get("pin", "")
        elapsed = (time.time() - self.start_time) * 1000
        log_entry = None

        if action in ["SET_HIGH", "SET_LOW"]:
            value = 1 if action == "SET_HIGH" else 0
            self.command_signal.emit({
                "id": str(uuid.uuid4()), "command": "digital_write",
                "pin": pin, "value": value
            })
            log_entry = {"time": elapsed, "pin": pin, "action": "HIGH" if value else "LOW", "cycle": self.current_cycle}
            self.msleep(step.get("wait", 100))

        elif action == "WAIT":
            wait_time = step.get('wait', step.get('value', 100))
            log_entry = {"time": elapsed, "pin": "-", "action": f"WAIT {wait_time}ms", "cycle": self.current_cycle}
            self.msleep(wait_time)

        elif action == "WAIT_FOR_PIN":
            target_state_str = step.get("value", "HIGH")
            timeout = step.get("timeout", 5000)
            target_state = 1 if target_state_str == "HIGH" else 0

            log_entry = {"time": elapsed, "pin": pin, "action": f"WAIT_FOR_{target_state_str}", "cycle": self.current_cycle}

            # Thread-safe Flag-Initialisierung
            with QMutexLocker(self._wait_mutex):
                self._is_waiting_for_pin = True
                self._wait_pin_name = pin
                self._wait_target_state = target_state
                self._wait_success = False

            start_time = time.time()
            while True:
                # Thread-safe Flag-Check
                with QMutexLocker(self._wait_mutex):
                    if not self._is_waiting_for_pin:
                        break

                if self._stop_requested:
                    break

                if (time.time() - start_time) * 1000 > timeout:
                    print(f"TIMEOUT on pin {pin}")
                    with QMutexLocker(self._wait_mutex):
                        self._is_waiting_for_pin = False
                    self._stop_requested = True

                    # Berechne Cycle-Zeit korrekt
                    if len(self.cycle_start_times) >= 2:
                        cycle_time_sec = self.cycle_start_times[-1] - self.cycle_start_times[-2]
                        time_ms = cycle_time_sec * 1000
                        is_anomaly = True  # Timeout ist Anomalie
                        self.cycle_completed.emit(time_ms, is_anomaly)
                    return False

                self.command_signal.emit({
                    "id": str(uuid.uuid4()), "command": "digital_read", "pin": pin
                })
                self.msleep(50)

            # Thread-safe Check für Success
            with QMutexLocker(self._wait_mutex):
                success = self._wait_success

            if not success and not self._stop_requested:
                return False 
        
        if log_entry:
             self.log.append(log_entry)
        
        return True

