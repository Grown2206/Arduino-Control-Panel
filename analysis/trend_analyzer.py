import numpy as np
from collections import defaultdict

class TrendAnalyzer:
    """Analysiert Trends in Schaltzeiten von Zyklus- und Einzelschritten."""

    @staticmethod
    def analyze_timing(event_log):
        """
        Führt eine vollständige Analyse des Event-Logs durch mit erweiterten Metriken.
        """
        analysis_result = {
            'cycle_analysis': {'avg': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'stability': 0.0, 'trend': 'N/A', 'anomalies': []},
            'step_analysis': {},
            'raw_cycle_times': [],
            'raw_step_times': defaultdict(list),
            'raw_step_deltas': []
        }

        if not event_log or len(event_log) < 2:
            return TrendAnalyzer._add_enhanced_metrics(analysis_result)

        # Rohdaten berechnen
        for i in range(1, len(event_log)):
            time_current = event_log[i].get('time', 0)
            time_prev = event_log[i-1].get('time', 0)
            analysis_result['raw_step_deltas'].append(time_current - time_prev)

        # Zyklen gruppieren
        cycles = defaultdict(list)
        for entry in event_log:
            cycles[entry.get('cycle', 0)].append(entry.get('time', 0))
        
        # Schritte gruppieren
        for i in range(1, len(event_log)):
            prev_event = event_log[i-1]
            key = f"{prev_event.get('action', '?')} → {event_log[i].get('action', '?')}"
            analysis_result['raw_step_times'][key].append(analysis_result['raw_step_deltas'][i-1])

        # Zyklus-Analyse
        raw_cycle_times = [max(times) - min(times) for times in cycles.values() if len(times) > 1]
        analysis_result['raw_cycle_times'] = raw_cycle_times

        if len(raw_cycle_times) >= 2:
            avg_ct = float(np.mean(raw_cycle_times))
            std_ct = float(np.std(raw_cycle_times))
            slope = np.polyfit(np.arange(len(raw_cycle_times)), raw_cycle_times, 1)[0]
            
            trend = "stable"
            if slope > avg_ct * 0.05: trend = "increasing" 
            if slope < -avg_ct * 0.05: trend = "decreasing"
            
            stability = max(0, 100 - (std_ct / avg_ct * 100 if avg_ct > 0 else 100))
            
            anomalies_ct = []
            threshold = avg_ct + 2 * std_ct
            for i, ct in enumerate(raw_cycle_times):
                if ct > threshold:
                    deviation = (ct / avg_ct - 1) * 100 if avg_ct > 0 else 0
                    anomalies_ct.append({'cycle': i, 'time': float(ct), 'deviation': float(deviation)})

            analysis_result['cycle_analysis'] = {
                'avg': avg_ct, 'std': std_ct, 'min': float(min(raw_cycle_times)), 
                'max': float(max(raw_cycle_times)), 'stability': float(stability), 
                'trend': trend, 'anomalies': anomalies_ct
            }

        # Schritt-Analyse
        for key, times in analysis_result['raw_step_times'].items():
            if len(times) >= 2:
                avg_st = float(np.mean(times))
                std_st = float(np.std(times))
                analysis_result['step_analysis'][key] = {
                    'avg': avg_st, 'std': std_st, 'min': float(min(times)), 'max': float(max(times))
                }

        return TrendAnalyzer._add_enhanced_metrics(analysis_result)
    
    @staticmethod
    def _add_enhanced_metrics(analysis_result):
        """Berechnet erweiterte Qualitätsmetriken."""
        cycle_analysis = analysis_result.get('cycle_analysis', {})
        
        stability = cycle_analysis.get('stability', 0)
        anomaly_count = len(cycle_analysis.get('anomalies', []))
        avg_time = cycle_analysis.get('avg', 0)
        std_time = cycle_analysis.get('std', 0)
        
        # === QUALITY METRICS ===
        quality_metrics = {
            'consistency_score': stability,
            'reliability_score': max(50.0, 100.0 - (anomaly_count * 2.0)) if anomaly_count > 0 else 100.0,
            'jitter_score': max(0, 100.0 - ((std_time / avg_time) * 100)) if avg_time > 0 else 0.0,
        }
        
        total_cycles = len(analysis_result.get('raw_cycle_times', []))
        quality_metrics['anomaly_rate'] = (anomaly_count / total_cycles * 100) if total_cycles > 0 else 0.0
        
        quality_metrics['overall_score'] = (
            quality_metrics['consistency_score'] * 0.4 +
            quality_metrics['reliability_score'] * 0.3 +
            quality_metrics['jitter_score'] * 0.3
        )
        
        # Empfehlungen
        recommendations = []
        if stability < 80:
            recommendations.append("⚠️ Stabilität unter 80% - System prüfen")
        if anomaly_count > 5:
            recommendations.append(f"❌ {anomaly_count} Anomalien gefunden")
        if quality_metrics['jitter_score'] < 70:
            recommendations.append("⚡ Hoher Jitter - Optimierung empfohlen")
        if not recommendations:
            recommendations.append("✅ Exzellente Performance")
        
        quality_metrics['recommendations'] = recommendations
        
        # === PERFORMANCE RATING ===
        overall = quality_metrics['overall_score']
        if overall >= 95:
            rating, stars = "Exzellent", 5
        elif overall >= 90:
            rating, stars = "Exzellent", 4
        elif overall >= 80:
            rating, stars = "Sehr Gut", 4
        elif overall >= 70:
            rating, stars = "Gut", 3
        elif overall >= 60:
            rating, stars = "Befriedigend", 2
        else:
            rating, stars = "Mangelhaft", 1
        
        performance_rating = {
            'rating': rating,
            'star_rating': stars,
            'pass_fail': "BESTANDEN" if overall >= 70 else "NICHT BESTANDEN"
        }
        
        # === ERWEITERTE ZYKLUSSTATISTIKEN ===
        raw_cycles = analysis_result.get('raw_cycle_times', [])
        if len(raw_cycles) > 0:
            cycle_analysis['median'] = float(np.median(raw_cycles))
            cycle_analysis['iqr'] = float(np.percentile(raw_cycles, 75) - np.percentile(raw_cycles, 25))
            cycle_analysis['cv'] = (std_time / avg_time * 100) if avg_time > 0 else 0
            
            if len(raw_cycles) >= 3:
                x = np.arange(len(raw_cycles))
                y = np.array(raw_cycles)
                coeffs = np.polyfit(x, y, 1)
                p = np.poly1d(coeffs)
                y_pred = p(x)
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                cycle_analysis['r_squared'] = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            trend = cycle_analysis.get('trend', 'stable')
            if trend == 'stable':
                cycle_analysis['trend'] = 'STABIL'
            elif trend == 'increasing':
                cycle_analysis['trend'] = 'STEIGEND'
            elif trend == 'decreasing':
                cycle_analysis['trend'] = 'FALLEND'
        
        # === ANOMALIE-DETAILS ===
        anomaly_details = {
            'total_anomalies': anomaly_count,
            'cycle_anomalies': anomaly_count,
            'step_anomalies': 0,
            'anomaly_rate': quality_metrics['anomaly_rate']
        }
        
        # === STATISTISCHE ZUSAMMENFASSUNG ===
        # KORREKTUR: 'raw_cycles' (list) muss für vektorisierte Berechnungen (skew/kurtosis)
        # in ein NumPy-Array umgewandelt werden.
        raw_cycles_np = np.array(raw_cycles)

        statistical_summary = {
            'sample_size': len(raw_cycles_np),
            'skewness': float(np.mean(((raw_cycles_np - avg_time) / std_time) ** 3)) if std_time > 0 and len(raw_cycles_np) > 0 else 0,
            'kurtosis': float(np.mean(((raw_cycles_np - avg_time) / std_time) ** 4)) if std_time > 0 and len(raw_cycles_np) > 0 else 0,
            'variance': float(std_time ** 2)
        }
        
        if len(raw_cycles_np) > 0:
            statistical_summary['percentiles'] = {
                10: float(np.percentile(raw_cycles_np, 10)),
                25: float(np.percentile(raw_cycles_np, 25)),
                50: float(np.percentile(raw_cycles_np, 50)),
                75: float(np.percentile(raw_cycles_np, 75)),
                90: float(np.percentile(raw_cycles_np, 90)),
                95: float(np.percentile(raw_cycles_np, 95)),
                99: float(np.percentile(raw_cycles_np, 99))
            }
        
        analysis_result['quality_metrics'] = quality_metrics
        analysis_result['performance_rating'] = performance_rating
        analysis_result['anomaly_details'] = anomaly_details
        analysis_result['statistical_summary'] = statistical_summary
        analysis_result['cycle_analysis'] = cycle_analysis
        
        return analysis_result
