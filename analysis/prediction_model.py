# -*- coding: utf-8 -*-
"""
analysis/prediction_model.py
Vorhersage-Modelle für Performance und Degradation
"""
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
import json
from collections import defaultdict


class PredictionModel:
    """
    Vorhersage-Modelle für Arduino Control Panel
    - Performance-Vorhersagen
    - Wartungs-Benachrichtigungen
    - Ausfallrisiko-Analyse
    """

    @staticmethod
    def predict_next_performance(
        db_file: str,
        sequence_name: str,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Sagt zukünftige Performance vorher basierend auf historischen Daten

        Args:
            db_file: Pfad zur Datenbank
            sequence_name: Name der Sequenz
            days_ahead: Tage in die Zukunft für Vorhersage

        Returns:
            Vorhersage-Daten
        """
        # Hole historische Daten
        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute("""
                SELECT id, start_time, duration, cycles, log
                FROM test_runs
                WHERE sequence_name = ? AND status IN ('Abgeschlossen', 'ok', 'success')
                ORDER BY start_time ASC
            """, (sequence_name,))

            runs = c.fetchall()

        if len(runs) < 5:
            return {
                'status': 'insufficient_data',
                'message': f'Mindestens 5 Testläufe für Vorhersage benötigt (gefunden: {len(runs)})',
                'sequence': sequence_name
            }

        # Extrahiere Zeitreihe
        timeline = []

        for run in runs:
            run_dict = dict(run)
            timestamp = datetime.fromisoformat(run_dict['start_time']).timestamp()

            # Parse log für Zyklus-Zeit
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

            # Berechne Zyklus-Zeit
            cycles = defaultdict(list)
            for event in events:
                cycles[event.get('cycle', 0)].append(event.get('time', 0))

            cycle_times = [max(times) - min(times) for times in cycles.values() if len(times) > 1]

            if not cycle_times:
                continue

            avg_cycle_time = float(np.mean(cycle_times))

            timeline.append({
                'timestamp': timestamp,
                'avg_cycle_time': avg_cycle_time
            })

        if len(timeline) < 5:
            return {
                'status': 'insufficient_data',
                'message': 'Nicht genug verwertbare Daten für Vorhersage',
                'sequence': sequence_name
            }

        # Zeitreihen-Analyse
        timestamps = np.array([d['timestamp'] for d in timeline])
        cycle_times = np.array([d['avg_cycle_time'] for d in timeline])

        # Normalisiere Zeitstempel (Tage seit Start)
        t0 = timestamps[0]
        t_normalized = (timestamps - t0) / (24 * 3600)  # In Tage umrechnen

        # Fit Polynomial (Grad 2 für nicht-linearen Trend)
        try:
            if len(t_normalized) >= 3:
                coeffs = np.polyfit(t_normalized, cycle_times, min(2, len(t_normalized) - 1))
            else:
                coeffs = np.polyfit(t_normalized, cycle_times, 1)

            poly_model = np.poly1d(coeffs)

            # Berechne R² für Modell-Güte
            y_pred = poly_model(t_normalized)
            ss_res = np.sum((cycle_times - y_pred) ** 2)
            ss_tot = np.sum((cycle_times - np.mean(cycle_times)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        except np.linalg.LinAlgError:
            return {
                'status': 'error',
                'message': 'Konnte Modell nicht fitten',
                'sequence': sequence_name
            }

        # Vorhersage für zukünftige Zeitpunkte
        last_timestamp = timestamps[-1]
        prediction_days = np.linspace(
            (last_timestamp - t0) / (24 * 3600),
            (last_timestamp - t0) / (24 * 3600) + days_ahead,
            days_ahead + 1
        )

        predicted_values = poly_model(prediction_days)

        # Berechne Konfidenzintervall (vereinfacht)
        residuals = cycle_times - poly_model(t_normalized)
        std_residual = np.std(residuals)

        predictions = []
        for i, day in enumerate(prediction_days):
            pred_timestamp = t0 + day * 24 * 3600
            pred_value = float(predicted_values[i])

            # Konfidenzintervall (±2 Standardabweichungen)
            lower_bound = max(0, pred_value - 2 * std_residual)
            upper_bound = pred_value + 2 * std_residual

            predictions.append({
                'date': datetime.fromtimestamp(pred_timestamp).isoformat(),
                'predicted_cycle_time': pred_value,
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
                'confidence': 95.0  # 95% Konfidenzintervall
            })

        # Degradations-Warnung
        current_avg = float(np.mean(cycle_times[-3:]))  # Letzte 3 Werte
        future_avg = float(np.mean(predicted_values[-3:]))  # Letzte 3 Vorhersagen

        degradation_percent = ((future_avg - current_avg) / current_avg * 100) if current_avg > 0 else 0

        warning = None
        if degradation_percent > 15:
            warning = {
                'level': 'high',
                'message': f'Erwartete Degradation: {degradation_percent:.1f}% in {days_ahead} Tagen',
                'recommendation': 'Wartung oder Optimierung empfohlen'
            }
        elif degradation_percent > 5:
            warning = {
                'level': 'moderate',
                'message': f'Leichte Degradation erwartet: {degradation_percent:.1f}%',
                'recommendation': 'System beobachten'
            }

        return {
            'status': 'success',
            'sequence': sequence_name,
            'model_quality': {
                'r_squared': float(r_squared),
                'data_points': len(timeline),
                'model_type': f'polynomial_degree_{len(coeffs) - 1}'
            },
            'current_performance': {
                'avg_cycle_time': current_avg,
                'trend': 'degrading' if degradation_percent > 2 else 'stable'
            },
            'predictions': predictions,
            'degradation_forecast': {
                'percent_change': float(degradation_percent),
                'warning': warning
            }
        }

    @staticmethod
    def estimate_maintenance_window(
        db_file: str,
        threshold_degradation: float = 20.0
    ) -> Dict[str, Any]:
        """
        Schätzt wann Wartung basierend auf Degradation nötig wird

        Args:
            db_file: Pfad zur Datenbank
            threshold_degradation: % Degradation bevor Wartung nötig

        Returns:
            Wartungs-Schätzung
        """
        # Hole alle aktiven Sequenzen
        with sqlite3.connect(db_file) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT DISTINCT sequence_name
                FROM test_runs
                WHERE status IN ('Abgeschlossen', 'ok', 'success')
            """)
            sequences = [row[0] for row in c.fetchall()]

        if not sequences:
            return {
                'status': 'no_data',
                'message': 'Keine Sequenzen gefunden'
            }

        maintenance_estimates = []

        for seq_name in sequences:
            # Vorhersage für 30 Tage
            prediction = PredictionModel.predict_next_performance(
                db_file, seq_name, days_ahead=30
            )

            if prediction['status'] != 'success':
                continue

            # Prüfe wann Threshold erreicht wird
            degradation = prediction['degradation_forecast']['percent_change']

            if degradation >= threshold_degradation:
                # Bereits kritisch
                days_to_maintenance = 0
                urgency = 'critical'
            elif degradation > 0:
                # Schätze wann Threshold erreicht wird (linear)
                days_per_percent = 30 / degradation if degradation > 0 else float('inf')
                days_to_maintenance = int(days_per_percent * threshold_degradation)
                urgency = 'high' if days_to_maintenance < 14 else 'moderate'
            else:
                days_to_maintenance = None
                urgency = 'low'

            maintenance_estimates.append({
                'sequence': seq_name,
                'current_degradation_percent': float(degradation),
                'days_to_maintenance': days_to_maintenance,
                'urgency': urgency,
                'threshold_percent': threshold_degradation
            })

        # Sortiere nach Dringlichkeit
        maintenance_estimates.sort(key=lambda x: x['days_to_maintenance'] if x['days_to_maintenance'] is not None else 9999)

        return {
            'status': 'success',
            'threshold_degradation': threshold_degradation,
            'sequences_analyzed': len(maintenance_estimates),
            'maintenance_schedule': maintenance_estimates
        }

    @staticmethod
    def analyze_failure_risk(
        db_file: str,
        sequence_name: str
    ) -> Dict[str, Any]:
        """
        Analysiert Ausfallrisiko basierend auf historischen Fehlern

        Args:
            db_file: Pfad zur Datenbank
            sequence_name: Name der Sequenz

        Returns:
            Risiko-Analyse
        """
        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Hole alle Läufe (inkl. fehlgeschlagene)
            c.execute("""
                SELECT status, start_time
                FROM test_runs
                WHERE sequence_name = ?
                ORDER BY start_time DESC
                LIMIT 50
            """, (sequence_name,))

            runs = c.fetchall()

        if len(runs) < 5:
            return {
                'status': 'insufficient_data',
                'message': 'Mindestens 5 Testläufe für Risiko-Analyse benötigt',
                'sequence': sequence_name
            }

        # Analysiere Fehlerrate
        total_runs = len(runs)
        failed_runs = sum(1 for r in runs if r['status'] not in ['Abgeschlossen', 'ok', 'success'])
        success_rate = ((total_runs - failed_runs) / total_runs * 100) if total_runs > 0 else 0

        # Analysiere zeitlichen Verlauf (letzte 10 vs. vorletzte 10)
        recent_10 = runs[:10]
        previous_10 = runs[10:20] if len(runs) >= 20 else []

        recent_failures = sum(1 for r in recent_10 if r['status'] not in ['Abgeschlossen', 'ok', 'success'])
        previous_failures = sum(1 for r in previous_10 if r['status'] not in ['Abgeschlossen', 'ok', 'success']) if previous_10 else 0

        # Trend-Berechnung
        if previous_failures > 0 and recent_failures > previous_failures:
            trend = 'increasing'
        elif recent_failures < previous_failures:
            trend = 'decreasing'
        else:
            trend = 'stable'

        # Risiko-Bewertung
        if success_rate >= 95:
            risk_level = 'low'
            risk_score = 10
        elif success_rate >= 85:
            risk_level = 'moderate'
            risk_score = 30
        elif success_rate >= 70:
            risk_level = 'high'
            risk_score = 60
        else:
            risk_level = 'critical'
            risk_score = 90

        # Erhöhe Risiko bei steigender Fehlerrate
        if trend == 'increasing':
            risk_score = min(100, risk_score + 20)
            if risk_level == 'low':
                risk_level = 'moderate'
            elif risk_level == 'moderate':
                risk_level = 'high'

        # Empfehlungen
        recommendations = []
        if risk_level in ['high', 'critical']:
            recommendations.append('🚨 System prüfen und Fehlerursachen analysieren')
            recommendations.append('📊 Detaillierte Logs für fehlgeschlagene Läufe überprüfen')
        if trend == 'increasing':
            recommendations.append('📈 Fehlerrate steigt - dringende Wartung empfohlen')
        if success_rate < 90:
            recommendations.append('🔧 Konfiguration und Hardware überprüfen')

        if not recommendations:
            recommendations.append('✅ System läuft stabil')

        return {
            'status': 'success',
            'sequence': sequence_name,
            'risk_assessment': {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'success_rate': float(success_rate),
                'failure_rate': float(100 - success_rate)
            },
            'statistics': {
                'total_runs_analyzed': total_runs,
                'failed_runs': failed_runs,
                'recent_failures': recent_failures,
                'previous_failures': previous_failures,
                'trend': trend
            },
            'recommendations': recommendations
        }

    @staticmethod
    def forecast_resource_usage(
        db_file: str,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Vorhersage der Ressourcen-Nutzung (Testläufe, Speicher, etc.)

        Args:
            db_file: Pfad zur Datenbank
            days_ahead: Tage in die Zukunft

        Returns:
            Ressourcen-Vorhersage
        """
        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Hole Läufe der letzten 30 Tage
            cutoff_date = datetime.now() - timedelta(days=30)
            c.execute("""
                SELECT start_time, duration
                FROM test_runs
                WHERE start_time >= ?
                ORDER BY start_time ASC
            """, (cutoff_date.isoformat(),))

            runs = c.fetchall()

        if len(runs) < 5:
            return {
                'status': 'insufficient_data',
                'message': 'Mindestens 5 Testläufe in den letzten 30 Tagen benötigt'
            }

        # Gruppiere nach Tagen
        daily_counts = defaultdict(int)
        for run in runs:
            date = datetime.fromisoformat(dict(run)['start_time']).date()
            daily_counts[date] += 1

        # Berechne durchschnittliche tägliche Läufe
        if daily_counts:
            avg_daily_runs = np.mean(list(daily_counts.values()))
            std_daily_runs = np.std(list(daily_counts.values()))
        else:
            avg_daily_runs = 0
            std_daily_runs = 0

        # Vorhersage
        predicted_total_runs = int(avg_daily_runs * days_ahead)

        # Schätze Speicherbedarf (Annahme: ~50KB pro Testlauf)
        avg_storage_per_run_kb = 50
        predicted_storage_mb = (predicted_total_runs * avg_storage_per_run_kb) / 1024

        return {
            'status': 'success',
            'period_analyzed_days': 30,
            'forecast_days': days_ahead,
            'current_metrics': {
                'avg_daily_runs': float(avg_daily_runs),
                'std_daily_runs': float(std_daily_runs),
                'total_runs_last_30_days': len(runs)
            },
            'predictions': {
                'estimated_total_runs': predicted_total_runs,
                'estimated_storage_mb': float(predicted_storage_mb),
                'estimated_daily_runs': float(avg_daily_runs)
            }
        }
