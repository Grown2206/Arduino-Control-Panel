# -*- coding: utf-8 -*-
"""
Unit Tests für Database
"""
import pytest
import time
from core.database import Database


class TestDatabase:
    """Test-Suite für Database"""

    def test_init_creates_tables(self, temp_db_file):
        """Test: Datenbank-Initialisierung erstellt Tabellen"""
        db = Database(db_file=temp_db_file)

        # Prüfe ob Tabelle existiert
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_runs'")
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'test_runs'

    def test_add_run(self, temp_db_file):
        """Test: Testlauf hinzufügen"""
        db = Database(db_file=temp_db_file)

        run_id = db.add_run("Test Run 1", "Test Sequence")

        assert run_id is not None
        assert isinstance(run_id, int)

    def test_get_run_details(self, temp_db_file):
        """Test: Testlauf-Details abrufen"""
        db = Database(db_file=temp_db_file)

        # Füge Testlauf hinzu
        run_id = db.add_run("Test Run 1", "Test Sequence")

        # Rufe Details ab
        details = db.get_run_details(run_id)

        assert details is not None
        assert details['id'] == run_id
        assert details['name'] == "Test Run 1"
        assert details['sequence_name'] == "Test Sequence"
        assert details['timestamp'] is not None

    def test_update_run(self, temp_db_file):
        """Test: Testlauf aktualisieren"""
        db = Database(db_file=temp_db_file)

        # Füge Testlauf hinzu
        run_id = db.add_run("Test Run 1", "Test Sequence")

        # Aktualisiere
        log_data = {
            'events': [
                {'cycle': 1, 'duration_ms': 100},
                {'cycle': 2, 'duration_ms': 105}
            ],
            'sensors': {
                'temp': {'min': 20.0, 'max': 25.0, 'avg': 22.5}
            }
        }
        db.update_run(run_id, cycles=2, status="completed", log=log_data)

        # Prüfe Update
        details = db.get_run_details(run_id)
        assert details['cycles'] == 2
        assert details['status'] == "completed"
        assert details['log'] == log_data

    def test_get_all_runs(self, temp_db_file):
        """Test: Alle Testläufe abrufen"""
        db = Database(db_file=temp_db_file)

        # Füge mehrere Testläufe hinzu
        db.add_run("Run 1", "Seq 1")
        time.sleep(0.01)  # Ensure different timestamps
        db.add_run("Run 2", "Seq 2")
        time.sleep(0.01)
        db.add_run("Run 3", "Seq 1")

        # Rufe alle ab
        runs = db.get_all_runs()

        assert len(runs) == 3
        # Sollte nach Timestamp sortiert sein (neueste zuerst)
        assert runs[0]['name'] == "Run 3"
        assert runs[1]['name'] == "Run 2"
        assert runs[2]['name'] == "Run 1"

    def test_delete_run(self, temp_db_file):
        """Test: Testlauf löschen"""
        db = Database(db_file=temp_db_file)

        # Füge Testlauf hinzu
        run_id = db.add_run("Test Run", "Test Sequence")

        # Lösche
        db.delete_run(run_id)

        # Prüfe dass gelöscht
        details = db.get_run_details(run_id)
        assert details is None

    def test_get_runs_by_sequence(self, temp_db_file):
        """Test: Testläufe nach Sequenz filtern"""
        db = Database(db_file=temp_db_file)

        # Füge verschiedene Testläufe hinzu
        db.add_run("Run 1", "Sequence A")
        db.add_run("Run 2", "Sequence B")
        db.add_run("Run 3", "Sequence A")

        # Hole alle Runs
        all_runs = db.get_all_runs()

        # Filtere nach Sequence A
        seq_a_runs = [r for r in all_runs if r['sequence_name'] == 'Sequence A']

        assert len(seq_a_runs) == 2
        assert all(r['sequence_name'] == 'Sequence A' for r in seq_a_runs)

    def test_run_status_default(self, temp_db_file):
        """Test: Standard-Status für neuen Run"""
        db = Database(db_file=temp_db_file)

        run_id = db.add_run("Test Run", "Test Sequence")
        details = db.get_run_details(run_id)

        assert details['status'] == "pending"
        assert details['cycles'] == 0

    def test_run_with_empty_log(self, temp_db_file):
        """Test: Run mit leerem Log"""
        db = Database(db_file=temp_db_file)

        run_id = db.add_run("Test Run", "Test Sequence")
        details = db.get_run_details(run_id)

        assert details['log'] == {}

    def test_multiple_database_instances(self, temp_db_file):
        """Test: Mehrere Database-Instanzen auf gleiche Datei"""
        db1 = Database(db_file=temp_db_file)
        db2 = Database(db_file=temp_db_file)

        # Füge mit db1 hinzu
        run_id = db1.add_run("Test Run", "Test Sequence")

        # Lese mit db2
        details = db2.get_run_details(run_id)

        assert details is not None
        assert details['name'] == "Test Run"
