# -*- coding: utf-8 -*-
"""
analysis/advanced_stats.py
Erweiterte Statistik & Analytics für Langzeit-Trends und Degradations-Erkennung
"""
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Tuple
import sqlite3
import json
import logging

logger = logging.getLogger("AdvancedStats")


class AdvancedStats:
    """
    Erweiterte Statistik-Analysen für Arduino Control Panel
    - Langzeit-Trends über Wochen/Monate
    - Performance-Degradation Erkennung
    - Vergleichs-Analysen (Test A vs. Test B)
    - Hardware-Vergleiche
    """

    @staticmethod
    def analyze_longterm_trends(db_file: str, days: int = 30) -> Dict[str, Any]:
        """
        Analysiert Langzeit-Trends über einen bestimmten Zeitraum

        Args:
            db_file: Pfad zur Datenbank
            days: Anzahl der Tage für die Analyse

        Returns:
            Dict mit Trend-Analyse
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Hole alle Testläufe seit cutoff_date
            c.execute("""
                SELECT id, name, sequence_name, start_time, duration, cycles, status, log
                FROM test_runs
                WHERE start_time >= ?
                ORDER BY start_time ASC
            """, (cutoff_date.isoformat(),))

            runs = c.fetchall()

        if not runs:
            return {
                'status': 'no_data',
                'message': f'Keine Daten in den letzten {days} Tagen gefunden',
                'period_days': days
            }

        # Verarbeite Daten
        timeline_data = []
        sequence_performance = defaultdict(list)
        daily_stats = defaultdict(lambda: {'count': 0, 'success': 0, 'avg_duration': []})

        for run in runs:
            run_dict = dict(run)

            # Sichere Datums-Konvertierung
            try:
                if run_dict.get('start_time'):
                    run_date = datetime.fromisoformat(run_dict['start_time']).date()
                else:
                    # Überspringe Einträge ohne Datum
                    continue
            except (ValueError, TypeError) as e:
                # Ungültiges Datumsformat - überspringe
                logger.warning(f"Ungültiges start_time Format in Run {run_dict.get('id')}: {e}")
                continue

            # Parse log
            log_data = {}
            if run_dict.get('log'):
                try:
                    log_data = json.loads(run_dict['log'])
                    if isinstance(log_data, list):
                        log_data = {'events': log_data, 'sensors': {}}
                except json.JSONDecodeError:
                    log_data = {'events': [], 'sensors': {}}

            # Berechne Zyklus-Zeit
            avg_cycle_time = 0
            events = log_data.get('events', [])
            if events:
                cycles = defaultdict(list)
                for event in events:
                    cycles[event.get('cycle', 0)].append(event.get('time', 0))

                cycle_times = [max(times) - min(times) for times in cycles.values() if len(times) > 1]
                if cycle_times:
                    avg_cycle_time = float(np.mean(cycle_times))

            # Timeline-Datenpunkt
            timeline_data.append({
                'timestamp': run_dict['start_time'],
                'run_id': run_dict['id'],
                'sequence': run_dict['sequence_name'],
                'duration': run_dict['duration'],
                'cycles': run_dict['cycles'],
                'status': run_dict['status'],
                'avg_cycle_time': avg_cycle_time
            })

            # Sequenz-Performance
            sequence_performance[run_dict['sequence_name']].append({
                'timestamp': run_dict['start_time'],
                'avg_cycle_time': avg_cycle_time,
                'status': run_dict['status']
            })

            # Tägliche Statistiken
            daily_stats[run_date]['count'] += 1
            if run_dict['status'] in ['Abgeschlossen', 'ok', 'success']:
                daily_stats[run_date]['success'] += 1
            if run_dict['duration']:
                daily_stats[run_date]['avg_duration'].append(run_dict['duration'])

        # Berechne Trend-Metriken
        trends = AdvancedStats._calculate_trends(timeline_data)

        # Degradations-Analyse
        degradation_alerts = AdvancedStats._detect_degradation(sequence_performance)

        # Daily Summary
        daily_summary = []
        for date, stats in sorted(daily_stats.items()):
            avg_dur = np.mean(stats['avg_duration']) if stats['avg_duration'] else 0
            daily_summary.append({
                'date': date.isoformat(),
                'total_runs': stats['count'],
                'successful_runs': stats['success'],
                'success_rate': (stats['success'] / stats['count'] * 100) if stats['count'] > 0 else 0,
                'avg_duration': float(avg_dur)
            })

        return {
            'status': 'success',
            'period_days': days,
            'total_runs': len(runs),
            'timeline': timeline_data,
            'trends': trends,
            'degradation_alerts': degradation_alerts,
            'sequence_performance': dict(sequence_performance),
            'daily_summary': daily_summary
        }

    @staticmethod
    def _calculate_trends(timeline_data: List[Dict]) -> Dict[str, Any]:
        """Berechnet Trend-Metriken aus Timeline-Daten"""
        if len(timeline_data) < 2:
            return {'status': 'insufficient_data'}

        # Extrahiere Zykluszeiten über Zeit
        timestamps = [datetime.fromisoformat(d['timestamp']).timestamp() for d in timeline_data]
        cycle_times = [d['avg_cycle_time'] for d in timeline_data if d['avg_cycle_time'] > 0]

        if len(cycle_times) < 2:
            return {'status': 'insufficient_data'}

        # Linear Regression für Trend
        x = np.arange(len(cycle_times))
        coeffs = np.polyfit(x, cycle_times, 1)
        slope = coeffs[0]

        # Berechne R² für Trend-Stärke
        p = np.poly1d(coeffs)
        y_pred = p(x)
        ss_res = np.sum((np.array(cycle_times) - y_pred) ** 2)
        ss_tot = np.sum((np.array(cycle_times) - np.mean(cycle_times)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Trend-Interpretation
        avg_time = np.mean(cycle_times)
        relative_slope = (slope / avg_time * 100) if avg_time > 0 else 0

        if abs(relative_slope) < 1:
            trend_direction = 'stable'
            trend_severity = 'none'
        elif relative_slope > 0:
            trend_direction = 'degrading'
            if relative_slope > 5:
                trend_severity = 'critical'
            elif relative_slope > 2:
                trend_severity = 'moderate'
            else:
                trend_severity = 'minor'
        else:
            trend_direction = 'improving'
            if relative_slope < -5:
                trend_severity = 'significant'
            elif relative_slope < -2:
                trend_severity = 'moderate'
            else:
                trend_severity = 'minor'

        return {
            'status': 'calculated',
            'slope': float(slope),
            'relative_slope_percent': float(relative_slope),
            'r_squared': float(r_squared),
            'trend_direction': trend_direction,
            'trend_severity': trend_severity,
            'avg_cycle_time': float(avg_time),
            'std_cycle_time': float(np.std(cycle_times))
        }

    @staticmethod
    def _detect_degradation(sequence_performance: Dict[str, List[Dict]]) -> List[Dict]:
        """Erkennt Performance-Degradation in Sequenzen"""
        alerts = []

        for sequence_name, data_points in sequence_performance.items():
            if len(data_points) < 5:
                continue

            # Teile in "früh" und "spät" Zeitfenster
            split_point = len(data_points) // 2
            early_data = [d['avg_cycle_time'] for d in data_points[:split_point] if d['avg_cycle_time'] > 0]
            late_data = [d['avg_cycle_time'] for d in data_points[split_point:] if d['avg_cycle_time'] > 0]

            if not early_data or not late_data:
                continue

            early_avg = np.mean(early_data)
            late_avg = np.mean(late_data)

            # Berechne prozentuale Änderung
            change_percent = ((late_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0

            # Prüfe auf signifikante Degradation
            if change_percent > 10:  # >10% Verlangsamung
                alerts.append({
                    'sequence': sequence_name,
                    'type': 'degradation',
                    'severity': 'high' if change_percent > 25 else 'moderate',
                    'change_percent': float(change_percent),
                    'early_avg': float(early_avg),
                    'late_avg': float(late_avg),
                    'message': f'{sequence_name}: Performance verschlechtert um {change_percent:.1f}%'
                })
            elif change_percent < -10:  # >10% Verbesserung
                alerts.append({
                    'sequence': sequence_name,
                    'type': 'improvement',
                    'severity': 'info',
                    'change_percent': float(change_percent),
                    'early_avg': float(early_avg),
                    'late_avg': float(late_avg),
                    'message': f'{sequence_name}: Performance verbessert um {abs(change_percent):.1f}%'
                })

        return alerts

    @staticmethod
    def compare_test_runs(db_file: str, run_ids: List[int]) -> Dict[str, Any]:
        """
        Vergleicht mehrere Testläufe miteinander

        Args:
            db_file: Pfad zur Datenbank
            run_ids: Liste von Run-IDs zum Vergleichen

        Returns:
            Vergleichs-Analyse
        """
        if len(run_ids) < 2:
            return {'status': 'error', 'message': 'Mindestens 2 Testläufe für Vergleich benötigt'}

        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            placeholders = ','.join('?' * len(run_ids))
            c.execute(f"""
                SELECT id, name, sequence_name, start_time, duration, cycles, status, log
                FROM test_runs
                WHERE id IN ({placeholders})
            """, run_ids)

            runs = c.fetchall()

        if len(runs) != len(run_ids):
            return {'status': 'error', 'message': 'Nicht alle Run-IDs gefunden'}

        # Extrahiere Metriken
        comparison_data = []

        for run in runs:
            run_dict = dict(run)

            # Parse log
            log_data = {}
            if run_dict.get('log'):
                try:
                    log_data = json.loads(run_dict['log'])
                    if isinstance(log_data, list):
                        log_data = {'events': log_data, 'sensors': {}}
                except json.JSONDecodeError:
                    log_data = {'events': [], 'sensors': {}}

            # Berechne Metriken
            events = log_data.get('events', [])
            cycle_times = []

            if events:
                cycles = defaultdict(list)
                for event in events:
                    cycles[event.get('cycle', 0)].append(event.get('time', 0))

                cycle_times = [max(times) - min(times) for times in cycles.values() if len(times) > 1]

            comparison_data.append({
                'run_id': run_dict['id'],
                'name': run_dict['name'],
                'sequence': run_dict['sequence_name'],
                'start_time': run_dict['start_time'],
                'duration': run_dict['duration'],
                'cycles': run_dict['cycles'],
                'status': run_dict['status'],
                'avg_cycle_time': float(np.mean(cycle_times)) if cycle_times else 0,
                'std_cycle_time': float(np.std(cycle_times)) if cycle_times else 0,
                'min_cycle_time': float(min(cycle_times)) if cycle_times else 0,
                'max_cycle_time': float(max(cycle_times)) if cycle_times else 0
            })

        # Berechne Vergleichs-Metriken
        avg_cycle_times = [d['avg_cycle_time'] for d in comparison_data if d['avg_cycle_time'] > 0]

        if avg_cycle_times:
            best_idx = int(np.argmin(avg_cycle_times))
            worst_idx = int(np.argmax(avg_cycle_times))

            comparison_summary = {
                'best_run': comparison_data[best_idx],
                'worst_run': comparison_data[worst_idx],
                'performance_difference_percent': float(
                    (avg_cycle_times[worst_idx] - avg_cycle_times[best_idx]) /
                    avg_cycle_times[best_idx] * 100
                ) if avg_cycle_times[best_idx] > 0 else 0
            }
        else:
            comparison_summary = {
                'best_run': None,
                'worst_run': None,
                'performance_difference_percent': 0
            }

        return {
            'status': 'success',
            'runs': comparison_data,
            'summary': comparison_summary
        }

    @staticmethod
    def generate_correlation_matrix(db_file: str, sequence_name: str = None) -> Dict[str, Any]:
        """
        Generiert eine Korrelations-Matrix für verschiedene Metriken

        Args:
            db_file: Pfad zur Datenbank
            sequence_name: Optional - nur diese Sequenz analysieren

        Returns:
            Korrelations-Matrix und Analyse
        """
        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            if sequence_name:
                c.execute("""
                    SELECT id, duration, cycles, status, log
                    FROM test_runs
                    WHERE sequence_name = ?
                """, (sequence_name,))
            else:
                c.execute("""
                    SELECT id, duration, cycles, status, log
                    FROM test_runs
                """)

            runs = c.fetchall()

        if len(runs) < 3:
            return {'status': 'insufficient_data', 'message': 'Mindestens 3 Testläufe für Korrelation benötigt'}

        # Extrahiere Variablen
        data_matrix = {
            'duration': [],
            'cycles': [],
            'avg_cycle_time': [],
            'cycle_stability': []
        }

        for run in runs:
            run_dict = dict(run)

            # Nur erfolgreiche Läufe
            if run_dict['status'] not in ['Abgeschlossen', 'ok', 'success']:
                continue

            # Parse log
            log_data = {}
            if run_dict.get('log'):
                try:
                    log_data = json.loads(run_dict['log'])
                    if isinstance(log_data, list):
                        log_data = {'events': log_data, 'sensors': {}}
                except json.JSONDecodeError:
                    continue

            events = log_data.get('events', [])
            if not events:
                continue

            # Berechne Zyklus-Metriken
            cycles = defaultdict(list)
            for event in events:
                cycles[event.get('cycle', 0)].append(event.get('time', 0))

            cycle_times = [max(times) - min(times) for times in cycles.values() if len(times) > 1]

            if not cycle_times:
                continue

            avg_ct = np.mean(cycle_times)
            std_ct = np.std(cycle_times)
            stability = max(0, 100 - (std_ct / avg_ct * 100 if avg_ct > 0 else 100))

            data_matrix['duration'].append(run_dict['duration'] or 0)
            data_matrix['cycles'].append(run_dict['cycles'] or 0)
            data_matrix['avg_cycle_time'].append(avg_ct)
            data_matrix['cycle_stability'].append(stability)

        # Berechne Korrelations-Matrix
        variables = list(data_matrix.keys())
        n_vars = len(variables)
        correlation_matrix = np.zeros((n_vars, n_vars))

        for i, var1 in enumerate(variables):
            for j, var2 in enumerate(variables):
                if len(data_matrix[var1]) > 0 and len(data_matrix[var2]) > 0:
                    correlation_matrix[i, j] = np.corrcoef(
                        data_matrix[var1],
                        data_matrix[var2]
                    )[0, 1]

        # Finde starke Korrelationen
        strong_correlations = []
        for i, var1 in enumerate(variables):
            for j, var2 in enumerate(variables):
                if i < j:  # Nur obere Dreiecksmatrix
                    corr = correlation_matrix[i, j]
                    if abs(corr) > 0.7:  # Starke Korrelation
                        strong_correlations.append({
                            'variable1': var1,
                            'variable2': var2,
                            'correlation': float(corr),
                            'strength': 'strong' if abs(corr) > 0.9 else 'moderate'
                        })

        return {
            'status': 'success',
            'variables': variables,
            'correlation_matrix': correlation_matrix.tolist(),
            'strong_correlations': strong_correlations,
            'sample_size': len(data_matrix['cycles'])
        }
