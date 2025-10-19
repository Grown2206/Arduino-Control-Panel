import sqlite3
import json
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSlot

class DatabaseWorker(QObject):
    """
    Ein Worker-Objekt, das in einem separaten Thread läuft, um
    blockierende Datenbankoperationen auszuführen.
    """
    def __init__(self, db_file="arduino_tests.db"):
        super().__init__()
        self.db_file = db_file
        print(f"DatabaseWorker initialisiert für: {self.db_file}")

    @pyqtSlot(str, str)
    def add_run(self, name, sequence_name):
        """
        Fügt einen neuen Testlauf in die Datenbank ein. Dieser Slot wird per Signal aufgerufen.
        Gibt die ID des neuen Eintrags über das Signal `run_added_signal` zurück.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                start_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                c.execute("INSERT INTO test_runs (name, sequence_name, start_time, status) VALUES (?, ?, ?, ?)",
                          (name, sequence_name, start_time, "Running"))
                conn.commit()
                # Da wir in einem anderen Thread sind, können wir die ID nicht direkt zurückgeben.
                # Das MainWindow muss die ID selbst verwalten, falls benötigt.
                print(f"Neuer Testlauf '{name}' in DB hinzugefügt.")
        except Exception as e:
            print(f"DB Worker Fehler (add_run): {e}")

    @pyqtSlot(int, int, str, dict)
    def update_run(self, run_id, cycles, status, log_data):
        """
        Aktualisiert einen bestehenden Testlauf. Dieser Slot wird per Signal aufgerufen.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                end_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                
                c.execute("SELECT start_time FROM test_runs WHERE id=?", (run_id,))
                result = c.fetchone()
                if not result:
                    print(f"DB Worker FEHLER: Konnte Testlauf-ID {run_id} nicht finden.")
                    return

                start_str = result[0]
                duration = (datetime.now() - datetime.strptime(start_str, "%d.%m.%Y %H:%M:%S")).total_seconds()
                log_json = json.dumps(log_data)
                
                c.execute("UPDATE test_runs SET end_time=?, duration=?, cycles=?, status=?, log=? WHERE id=?",
                          (end_time, duration, cycles, status, log_json, run_id))
                conn.commit()
                print(f"Testlauf-ID {run_id} in DB aktualisiert.")
        except Exception as e:
            print(f"DB Worker FEHLER (update_run) für ID {run_id}: {e}")
