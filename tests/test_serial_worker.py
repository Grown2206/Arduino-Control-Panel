# -*- coding: utf-8 -*-
"""
Unit Tests für SerialWorker
"""
import pytest
import time
import json
from PyQt6.QtCore import QCoreApplication
from core.serial_worker import SerialWorker


@pytest.fixture
def qapp():
    """Qt Application für Signal/Slot Tests"""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


class TestSerialWorker:
    """Test-Suite für SerialWorker"""

    def test_init(self, qapp):
        """Test: SerialWorker Initialisierung"""
        worker = SerialWorker()

        assert worker.ser is None
        assert worker.running is False

    def test_connect_simulation(self, qapp):
        """Test: Simulation-Modus starten"""
        worker = SerialWorker()

        # Verbinde Signal
        status_messages = []
        worker.status_changed.connect(lambda msg: status_messages.append(msg))

        worker.connect_simulation()

        # Warte kurz
        time.sleep(0.1)
        QCoreApplication.processEvents()

        assert worker.is_connected()
        assert worker.ser == "SIMULATION"
        assert worker.running is True
        assert any("Simulation" in msg for msg in status_messages)

    def test_disconnect_serial(self, qapp):
        """Test: Verbindung trennen"""
        worker = SerialWorker()

        # Starte Simulation
        worker.connect_simulation()
        time.sleep(0.1)

        # Trenne
        worker.disconnect_serial()

        assert not worker.is_connected()
        assert worker.ser is None
        assert worker.running is False

    def test_send_command_not_connected(self, qapp):
        """Test: Command senden wenn nicht verbunden"""
        worker = SerialWorker()

        # Sollte nichts tun, nur warnen
        worker.send_command({"command": "test"})

        # Kein Fehler sollte auftreten
        assert True

    def test_send_command_adds_id(self, qapp):
        """Test: Command bekommt automatisch eine ID"""
        worker = SerialWorker()
        worker.connect_simulation()
        time.sleep(0.1)

        command = {"command": "digital_write", "pin": "D2", "value": 1}
        worker.send_command(command)

        # Original-Command sollte jetzt eine ID haben
        assert "id" in command
        assert isinstance(command["id"], str)

        worker.disconnect_serial()

    def test_simulation_sends_response(self, qapp):
        """Test: Simulation sendet ok-Response"""
        worker = SerialWorker()

        # Verbinde Signal
        received_data = []
        worker.data_received.connect(lambda data: received_data.append(data))

        worker.connect_simulation()
        time.sleep(0.1)

        # Sende Command
        worker.send_command({"id": "test-123", "command": "test"})

        # Warte und verarbeite Events
        time.sleep(0.1)
        QCoreApplication.processEvents()

        # Prüfe Response
        assert len(received_data) > 0
        response = received_data[-1]
        assert response['type'] == 'response'
        assert response['id'] == 'test-123'
        assert response['status'] == 'ok'

        worker.disconnect_serial()

    def test_simulation_generates_pin_updates(self, qapp):
        """Test: Simulation generiert Pin-Updates"""
        worker = SerialWorker()

        # Verbinde Signal
        received_data = []
        worker.data_received.connect(lambda data: received_data.append(data))

        worker.connect_simulation()

        # Warte auf Daten
        time.sleep(0.5)
        QCoreApplication.processEvents()

        # Sollte Pin-Updates empfangen haben
        pin_updates = [d for d in received_data if d.get('type') == 'pin_update']
        assert len(pin_updates) > 0

        worker.disconnect_serial()

    def test_is_connected_when_connected(self, qapp):
        """Test: is_connected() gibt True zurück wenn verbunden"""
        worker = SerialWorker()
        worker.connect_simulation()
        time.sleep(0.1)

        assert worker.is_connected() is True

        worker.disconnect_serial()

    def test_is_connected_when_disconnected(self, qapp):
        """Test: is_connected() gibt False zurück wenn getrennt"""
        worker = SerialWorker()

        assert worker.is_connected() is False

    def test_thread_stops_gracefully(self, qapp):
        """Test: Thread stoppt sauber"""
        worker = SerialWorker()
        worker.connect_simulation()
        time.sleep(0.2)

        # Thread sollte laufen
        assert worker.isRunning()

        # Trenne
        worker.disconnect_serial()

        # Thread sollte gestoppt sein
        assert not worker.isRunning()

    @pytest.mark.slow
    def test_simulation_runs_continuously(self, qapp):
        """Test: Simulation läuft kontinuierlich"""
        worker = SerialWorker()

        received_data = []
        worker.data_received.connect(lambda data: received_data.append(data))

        worker.connect_simulation()

        # Warte länger
        time.sleep(1.0)
        QCoreApplication.processEvents()

        # Sollte viele Updates erhalten haben
        assert len(received_data) > 5

        worker.disconnect_serial()
