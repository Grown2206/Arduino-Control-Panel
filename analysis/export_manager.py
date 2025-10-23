#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analysis/export_manager.py
Export-Manager für Testergebnisse
Unterstützt: CSV, JSON, Excel (Batch & Einzeln)
"""

import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os


class ExportManager:
    """Manager für Datenexporte in verschiedene Formate."""
    
    @staticmethod
    def export_csv(run_details: Dict[str, Any], analysis: Dict[str, Any], file_path: str) -> bool:
        """
        Exportiert einen einzelnen Testlauf als CSV, inklusive aller Analyse-Metriken.
        
        Args:
            run_details: Dictionary mit Testlauf-Details
            analysis: Dictionary mit Analyse-Ergebnissen
            file_path: Ziel-Dateipfad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            quality = analysis.get('quality_metrics', {})
            perf_rating = analysis.get('performance_rating', {})
            cycle_stats = analysis.get('cycle_analysis', {})
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Header: Grundinformationen
                writer.writerow(['=== TESTLAUF INFORMATION ==='])
                writer.writerow(['ID', run_details.get('id', '-')])
                writer.writerow(['Name', run_details.get('name', '-')])
                writer.writerow(['Sequenz', run_details.get('sequence_name', '-')])
                writer.writerow(['Start', run_details.get('start_time', '-')])
                writer.writerow(['Ende', run_details.get('end_time', '-')])
                writer.writerow(['Dauer (s)', f"{run_details.get('duration', 0):.2f}"])
                writer.writerow(['Zyklen', run_details.get('cycles', 0)])
                writer.writerow(['Status', run_details.get('status', '-')])
                writer.writerow([])

                # Performance Rating
                writer.writerow(['=== PERFORMANCE RATING ==='])
                writer.writerow(['Gesamt-Score', f"{quality.get('overall_score', 0):.1f}"])
                writer.writerow(['Rating', perf_rating.get('rating', 'N/A')])
                writer.writerow(['Ergebnis', perf_rating.get('pass_fail', 'N/A')])
                writer.writerow([])

                # Qualitätsmetriken
                writer.writerow(['=== QUALITÄTSMETRIKEN ==='])
                writer.writerow(['Konsistenz (%)', f"{quality.get('consistency_score', 0):.1f}"])
                writer.writerow(['Zuverlässigkeit (%)', f"{quality.get('reliability_score', 0):.1f}"])
                writer.writerow(['Präzision (Jitter) (%)', f"{quality.get('jitter_score', 0):.1f}"])
                writer.writerow(['Anomalierate (%)', f"{quality.get('anomaly_rate', 0):.1f}"])
                writer.writerow([])

                # Zykluszeit-Analyse
                writer.writerow(['=== ZYKLUSZEIT-ANALYSE ==='])
                writer.writerow(['Metrik', 'Wert (ms)'])
                writer.writerow(['Durchschnitt', f"{cycle_stats.get('avg', 0):.2f}"])
                writer.writerow(['Median', f"{cycle_stats.get('median', 0):.2f}"])
                writer.writerow(['Minimum', f"{cycle_stats.get('min', 0):.2f}"])
                writer.writerow(['Maximum', f"{cycle_stats.get('max', 0):.2f}"])
                writer.writerow(['Standardabweichung', f"{cycle_stats.get('std', 0):.2f}"])
                writer.writerow(['Stabilität (%)', f"{cycle_stats.get('stability', 0):.1f}"])
                writer.writerow(['Anomalien (Anzahl)', len(cycle_stats.get('anomalies', []))])
                writer.writerow([])
                
                # Events
                log_data = run_details.get('log', {})
                events = log_data.get('events', [])
                
                if events:
                    writer.writerow(['=== EVENTS ==='])
                    writer.writerow(['Zeit (ms)', 'Pin', 'Aktion', 'Zyklus'])
                    for event in events:
                        writer.writerow([
                            f"{event.get('time', 0):.2f}",
                            event.get('pin', '-'),
                            event.get('action', '-'),
                            event.get('cycle', '-')
                        ])
                    writer.writerow([])
                
                # Sensor-Statistiken
                sensors = log_data.get('sensors', {})
                if sensors:
                    writer.writerow(['=== SENSOR STATISTIKEN ==='])
                    writer.writerow(['Sensor', 'Min', 'Max', 'Durchschnitt'])
                    
                    if 'temp' in sensors:
                        temp = sensors['temp']
                        writer.writerow([
                            'Temperatur (°C)',
                            f"{temp.get('min', 0):.1f}",
                            f"{temp.get('max', 0):.1f}",
                            f"{temp.get('avg', 0):.1f}"
                        ])
                    
                    if 'humid' in sensors:
                        humid = sensors['humid']
                        writer.writerow([
                            'Luftfeuchtigkeit (%)',
                            f"{humid.get('min', 0):.1f}",
                            f"{humid.get('max', 0):.1f}",
                            f"{humid.get('avg', 0):.1f}"
                        ])
                    writer.writerow([])
                
                # Raw Sensor-Daten
                sensors_raw = log_data.get('sensors_raw', [])
                if sensors_raw:
                    writer.writerow(['=== RAW SENSOR DATEN ==='])
                    writer.writerow(['Zeit (ms)', 'Sensor', 'Wert'])
                    for entry in sensors_raw:
                        writer.writerow([
                            entry.get('time_ms', '-'), # Geändert von 'timestamp'
                            entry.get('sensor', '-'),
                            entry.get('value', '-')
                        ])
                
            return True
            
        except Exception as e:
            print(f"❌ CSV-Export fehlgeschlagen: {e}")
            return False
    
    @staticmethod
    def export_json(run_details: Dict[str, Any], analysis: Dict[str, Any], file_path: str) -> bool:
        """
        Exportiert einen einzelnen Testlauf als JSON, inklusive Analyse.
        
        Args:
            run_details: Dictionary mit Testlauf-Details
            analysis: Dictionary mit Analyse-Ergebnissen
            file_path: Ziel-Dateipfad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Bereite Daten für JSON-Export vor
            export_data = {
                'metadata': {
                    'id': run_details.get('id'),
                    'name': run_details.get('name'),
                    'sequence_name': run_details.get('sequence_name'),
                    'start_time': run_details.get('start_time'),
                    'end_time': run_details.get('end_time'),
                    'duration': run_details.get('duration'),
                    'cycles': run_details.get('cycles'),
                    'status': run_details.get('status')
                },
                'analysis': analysis, # Füge komplettes Analyse-Objekt hinzu
                'log': run_details.get('log', {})
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ JSON-Export fehlgeschlagen: {e}")
            return False
    
    @staticmethod
    def export_batch_csv(runs_list: List[Dict[str, Any]], 
                         analysis_results: List[Dict[str, Any]], 
                         file_path: str) -> bool:
        """
        Exportiert mehrere Testläufe als CSV, inkl. Analyse-Übersicht.
        
        Args:
            runs_list: Liste von Testlauf-Details
            analysis_results: Liste von Analyse-Ergebnissen
            file_path: Ziel-Dateipfad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if len(runs_list) != len(analysis_results):
            print("❌ Batch CSV-Export: Listenlänge stimmt nicht überein!")
            return False
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Header
                writer.writerow(['=== BATCH EXPORT ==='])
                writer.writerow(['Anzahl Testläufe', len(runs_list)])
                writer.writerow(['Exportiert am', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                
                # Übersichtstabelle (mit Analyse-Daten)
                writer.writerow(['=== ÜBERSICHT ==='])
                writer.writerow([
                    'ID', 'Name', 'Sequenz', 'Status', 'Dauer (s)', 'Zyklen', 
                    'Gesamt-Score', 'Rating', 'Ergebnis', 
                    'Ø Zykluszeit (ms)', 'Stabilität (%)', 'Anomalien'
                ])
                
                for run, analysis in zip(runs_list, analysis_results):
                    quality = analysis.get('quality_metrics', {})
                    perf_rating = analysis.get('performance_rating', {})
                    cycle_stats = analysis.get('cycle_analysis', {})
                    
                    writer.writerow([
                        run.get('id', '-'),
                        run.get('name', '-'),
                        run.get('sequence_name', '-'),
                        run.get('status', '-'),
                        f"{run.get('duration', 0):.2f}",
                        run.get('cycles', 0),
                        f"{quality.get('overall_score', 0):.1f}",
                        perf_rating.get('rating', 'N/A'),
                        perf_rating.get('pass_fail', 'N/A'),
                        f"{cycle_stats.get('avg', 0):.2f}",
                        f"{cycle_stats.get('stability', 0):.1f}",
                        len(cycle_stats.get('anomalies', []))
                    ])
                
                writer.writerow([])
                writer.writerow(['=== DETAILLIERTE EVENT-LOGS ==='])
                writer.writerow([])
                
                # Detaillierte Daten für jeden Testlauf
                for i, run in enumerate(runs_list, 1):
                    writer.writerow([f'--- Testlauf {i}: {run.get("name", "-")} (ID: {run.get("id")}) ---'])
                    
                    # Events
                    log_data = run.get('log', {})
                    events = log_data.get('events', [])
                    
                    if events:
                        writer.writerow(['Zeit (ms)', 'Pin', 'Aktion', 'Zyklus'])
                        for event in events:
                            writer.writerow([
                                f"{event.get('time', 0):.2f}",
                                event.get('pin', '-'),
                                event.get('action', '-'),
                                event.get('cycle', '-')
                            ])
                    
                    writer.writerow([])
            
            return True
            
        except Exception as e:
            print(f"❌ Batch CSV-Export fehlgeschlagen: {e}")
            return False
    
    @staticmethod
    def export_batch_json(runs_list: List[Dict[str, Any]], 
                          analysis_results: List[Dict[str, Any]], 
                          file_path: str) -> bool:
        """
        Exportiert mehrere Testläufe als JSON, inkl. Analysen.
        
        Args:
            runs_list: Liste von Testlauf-Details
            analysis_results: Liste von Analyse-Ergebnissen
            file_path: Ziel-Dateipfad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if len(runs_list) != len(analysis_results):
            print("❌ Batch JSON-Export: Listenlänge stimmt nicht überein!")
            return False
            
        try:
            export_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_runs': len(runs_list)
                },
                'runs': []
            }
            
            for run, analysis in zip(runs_list, analysis_results):
                export_data['runs'].append({
                    'id': run.get('id'),
                    'name': run.get('name'),
                    'sequence_name': run.get('sequence_name'),
                    'start_time': run.get('start_time'),
                    'end_time': run.get('end_time'),
                    'duration': run.get('duration'),
                    'cycles': run.get('cycles'),
                    'status': run.get('status'),
                    'analysis': analysis, # Füge Analyse-Objekt hinzu
                    'log': run.get('log', {})
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Batch JSON-Export fehlgeschlagen: {e}")
            return False
    
    @staticmethod
    def get_default_filename(run_name, extension, batch=False):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Bereinige den Namen für Dateisysteme
        safe_name = "".join([c for c in run_name if c.isalpha() or c.isdigit() or c=='_']).rstrip()
        prefix = 'batch' if batch else (safe_name if safe_name else 'bericht')
        return f"{prefix}_{timestamp}.{extension}"