# -*- coding: utf-8 -*-
"""
Example Plugin: CSV Data Export
Zeigt, wie man ein Export-Plugin erstellt
"""
from plugins import (
    PluginInterface, PluginMetadata, PluginType,
    PluginPriority, PluginCapability, ApplicationContext
)
import csv
import os
from datetime import datetime
from typing import List


class CSVExportPlugin(PluginInterface):
    """
    Beispiel-Plugin für CSV-Export von Testdaten.

    Dieses Plugin demonstriert:
    - Plugin-Metadaten definieren
    - Capabilities spezifizieren
    - Mit dem ApplicationContext arbeiten
    - Daten exportieren
    """

    def __init__(self):
        super().__init__()
        self.export_dir = "exports/csv"

    def get_metadata(self) -> PluginMetadata:
        """Plugin-Metadaten"""
        return PluginMetadata(
            id="com.drexlerdynamics.csv_export",
            name="CSV Data Exporter",
            version="1.0.0",
            author="Drexler Dynamics",
            description="Exportiert Testdaten in CSV-Format mit erweiterten Optionen",
            plugin_type=PluginType.EXPORT,
            priority=PluginPriority.NORMAL,
            dependencies=[],
            min_app_version="1.0.0",
            website="https://github.com/Grown2206/Arduino-Control-Panel",
            license="MIT"
        )

    def get_capabilities(self) -> List[PluginCapability]:
        """Plugin-Fähigkeiten"""
        return [
            PluginCapability.EXPORT_DATA,
            PluginCapability.FILE_ACCESS,
            PluginCapability.DATABASE_ACCESS
        ]

    def initialize(self, app_context: ApplicationContext) -> bool:
        """
        Initialisiert das Plugin.

        Args:
            app_context: Anwendungskontext

        Returns:
            bool: True bei Erfolg
        """
        try:
            self._app_context = app_context

            # Erstelle Export-Verzeichnis
            os.makedirs(self.export_dir, exist_ok=True)

            # Registriere Export-Funktion
            # (Könnte später an einen Menü-Button gebunden werden)
            print(f"✅ {self.get_metadata().name} initialisiert")
            return True

        except Exception as e:
            print(f"❌ Fehler bei Plugin-Initialisierung: {e}")
            return False

    def shutdown(self) -> bool:
        """Fährt das Plugin herunter"""
        print(f"Plugin {self.get_metadata().name} heruntergefahren")
        return True

    def export_test_run(self, test_id: int, filename: str = None) -> bool:
        """
        Exportiert einen Testlauf als CSV.

        Args:
            test_id: Test-ID
            filename: Dateiname (optional)

        Returns:
            bool: True bei Erfolg
        """
        try:
            # Hole Daten aus Datenbank
            db = self._app_context.get_database()
            test_data = db.get_run_details(test_id)

            if not test_data:
                print(f"Keine Daten für Test-ID {test_id} gefunden")
                return False

            # Generiere Dateiname falls nicht angegeben
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"test_{test_id}_{timestamp}.csv"

            filepath = os.path.join(self.export_dir, filename)

            # Schreibe CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Header
                writer.writerow(['Test Information'])
                writer.writerow(['ID', test_data.get('id')])
                writer.writerow(['Name', test_data.get('name')])
                writer.writerow(['Sequence', test_data.get('sequence_name')])
                writer.writerow(['Start Time', test_data.get('start_time')])
                writer.writerow(['Duration', f"{test_data.get('duration', 0)} s"])
                writer.writerow(['Cycles', test_data.get('cycles')])
                writer.writerow(['Status', test_data.get('status')])
                writer.writerow([])  # Leerzeile

                # Sensor-Daten (wenn vorhanden)
                log_data = test_data.get('log')
                if log_data:
                    import json
                    try:
                        if isinstance(log_data, str):
                            log_data = json.loads(log_data)

                        if isinstance(log_data, dict):
                            sensors = log_data.get('sensors', {})
                            if sensors:
                                writer.writerow(['Sensor Data'])
                                writer.writerow(['Sensor', 'Values'])

                                for sensor_id, values in sensors.items():
                                    values_str = ', '.join(map(str, values))
                                    writer.writerow([sensor_id, values_str])

                                writer.writerow([])  # Leerzeile

                        # Events
                        events = log_data.get('events', []) if isinstance(log_data, dict) else log_data
                        if events and isinstance(events, list):
                            writer.writerow(['Events'])
                            writer.writerow(['Cycle', 'Time', 'Pin', 'Value'])

                            for event in events:
                                writer.writerow([
                                    event.get('cycle', ''),
                                    event.get('time', ''),
                                    event.get('pin', ''),
                                    event.get('value', '')
                                ])

                    except json.JSONDecodeError:
                        writer.writerow(['Log Data', log_data])

            print(f"✅ CSV exportiert: {filepath}")
            return True

        except Exception as e:
            print(f"❌ Fehler beim CSV-Export: {e}")
            import traceback
            traceback.print_exc()
            return False

    def export_multiple_tests(self, test_ids: List[int], filename: str = None) -> bool:
        """
        Exportiert mehrere Testläufe in eine CSV.

        Args:
            test_ids: Liste von Test-IDs
            filename: Dateiname (optional)

        Returns:
            bool: True bei Erfolg
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tests_comparison_{timestamp}.csv"

            filepath = os.path.join(self.export_dir, filename)
            db = self._app_context.get_database()

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Header
                writer.writerow(['ID', 'Name', 'Sequence', 'Start Time', 'Duration (s)', 'Cycles', 'Status'])

                # Daten
                for test_id in test_ids:
                    test_data = db.get_run_details(test_id)
                    if test_data:
                        writer.writerow([
                            test_data.get('id'),
                            test_data.get('name'),
                            test_data.get('sequence_name'),
                            test_data.get('start_time'),
                            test_data.get('duration', 0),
                            test_data.get('cycles'),
                            test_data.get('status')
                        ])

            print(f"✅ Vergleichs-CSV exportiert: {filepath}")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Vergleichs-Export: {e}")
            return False
