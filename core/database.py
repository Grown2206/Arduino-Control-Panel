import sqlite3
import json
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class Database(QObject):
    """
    Verwaltet alle Interaktionen mit der SQLite-Datenbank.
    Schreibvorgänge werden an einen Worker-Thread delegiert.
    """
    # Signale, die an den DatabaseWorker gesendet werden
    add_run_requested = pyqtSignal(str, str)
    update_run_requested = pyqtSignal(int, int, str, dict)

    def __init__(self, db_file="arduino_tests.db"):
        super().__init__()
        self.db_file = db_file
        self._last_inserted_id = None
        self.init_db()
    
    def init_db(self):
        """Erstellt die Tabelle 'test_runs', falls sie nicht existiert."""
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, sequence_name TEXT,
                    start_time TEXT, end_time TEXT, duration REAL, cycles INTEGER, status TEXT, log TEXT
                )''')
            # Hole die zuletzt verwendete ID, um den Zähler zu initialisieren
            c.execute("SELECT seq FROM sqlite_sequence WHERE name='test_runs'")
            result = c.fetchone()
            self._last_inserted_id = result[0] if result else 0

    def add_run(self, name, sequence_name):
        """Sendet ein Signal, um einen neuen Testlauf hinzuzufügen."""
        self._last_inserted_id += 1
        self.add_run_requested.emit(name, sequence_name)
        return self._last_inserted_id
    
    def update_run(self, run_id, cycles, status, log_data):
        """Sendet ein Signal, um einen bestehenden Testlauf zu aktualisieren."""
        self.update_run_requested.emit(run_id, cycles, status, log_data)
    
    def get_all_runs(self):
        """Ruft alle Testläufe zur Anzeige im Archiv ab (Lesevorgang, bleibt im Hauptthread)."""
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, sequence_name, start_time, duration, cycles, status FROM test_runs ORDER BY id DESC")
            return c.fetchall()
    
    def get_run_details(self, run_id):
        """Ruft alle Details für einen einzelnen Testlauf ab (Lesevorgang, bleibt im Hauptthread)."""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM test_runs WHERE id=?", (run_id,))
            run = c.fetchone()
            if run:
                details = dict(run)
                raw_log = details.get('log')
                if raw_log:
                    try:
                        parsed_log = json.loads(raw_log)
                        if isinstance(parsed_log, list):
                            details['log'] = {'events': parsed_log, 'sensors': {}}
                        else:
                            details['log'] = parsed_log
                    except json.JSONDecodeError:
                        details['log'] = {'events': [], 'sensors': {}}
                else:
                    details['log'] = {'events': [], 'sensors': {}}
                return details
            return None
