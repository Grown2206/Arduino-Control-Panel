import numpy as np
from collections import defaultdict

class TrendAnalyzer:
    """Analysiert Trends in Schaltzeiten von Zyklus- und Einzelschritten."""

    @staticmethod
    def analyze_timing(event_log):
        """
        Führt eine vollständige Analyse des Event-Logs durch.
        Gibt immer eine vollständige, konsistente Datenstruktur mit Standard-Python-Datentypen zurück.
        """
        analysis_result = {
            'cycle_analysis': {'avg': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'stability': 0.0, 'trend': 'N/A', 'anomalies': []},
            'step_analysis': {},
            'raw_cycle_times': [],
            'raw_step_times': defaultdict(list),
            'raw_step_deltas': []
        }

        if not event_log or len(event_log) < 2:
            return analysis_result

        # --- 1. Rohdaten berechnen (Zeitdeltas zwischen jedem Schritt) ---
        for i in range(1, len(event_log)):
            time_current = event_log[i].get('time', 0)
            time_prev = event_log[i-1].get('time', 0)
            analysis_result['raw_step_deltas'].append(time_current - time_prev)

        # --- 2. Zyklen und Schritte gruppieren ---
        cycles = defaultdict(list)
        for entry in event_log:
            cycles[entry.get('cycle', 0)].append(entry.get('time', 0))
        
        for i in range(1, len(event_log)):
            prev_event = event_log[i-1]
            # Schlüssel für Schritte definieren, um sie zu gruppieren
            key = f"Schritt {i % len(cycles[0]) if len(cycles.get(0,[])) > 0 else i}: {prev_event.get('action', '?')} -> {event_log[i].get('action', '?')}"
            analysis_result['raw_step_times'][key].append(analysis_result['raw_step_deltas'][i-1])

        # --- 3. Zyklus-Analyse ---
        raw_cycle_times = [max(times) - min(times) for times in cycles.values() if len(times) > 1]
        analysis_result['raw_cycle_times'] = raw_cycle_times

        if len(raw_cycle_times) >= 2:
            avg_ct = float(np.mean(raw_cycle_times))
            std_ct = float(np.std(raw_cycle_times))
            slope = np.polyfit(np.arange(len(raw_cycle_times)), raw_cycle_times, 1)[0]
            
            trend = "stable"
            # Trend wird als signifikant angesehen, wenn die Steigung > 5% des Mittelwerts beträgt
            if slope > avg_ct * 0.05: trend = "increasing" 
            if slope < -avg_ct * 0.05: trend = "decreasing"
            
            stability = max(0, 100 - (std_ct / avg_ct * 100 if avg_ct > 0 else 100))
            
            anomalies_ct = []
            threshold = avg_ct + 2 * std_ct # Ausreißer sind mehr als 2 Standardabweichungen entfernt
            for i, ct in enumerate(raw_cycle_times):
                if ct > threshold:
                    deviation = (ct / avg_ct - 1) * 100 if avg_ct > 0 else 0
                    anomalies_ct.append({'cycle': i, 'time': float(ct), 'deviation': float(deviation)})

            analysis_result['cycle_analysis'] = {
                'avg': avg_ct, 'std': std_ct, 'min': float(min(raw_cycle_times)), 
                'max': float(max(raw_cycle_times)), 'stability': float(stability), 
                'trend': trend, 'anomalies': anomalies_ct
            }

        # --- 4. Schritt-Analyse (Jitter) ---
        for key, times in analysis_result['raw_step_times'].items():
            if len(times) >= 2:
                avg_st = float(np.mean(times))
                std_st = float(np.std(times))
                analysis_result['step_analysis'][key] = {
                    'avg': avg_st, 'std': std_st, 'min': float(min(times)), 'max': float(max(times))
                }

        return analysis_result

