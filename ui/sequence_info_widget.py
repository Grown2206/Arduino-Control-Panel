# -*- coding: utf-8 -*-
"""
ui/sequence_info_widget.py
Ein Dashboard-Widget, das die Live-Laufzeitinformationen und 
die Analyse einer laufenden Sequenz anzeigt.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, 
                             QGroupBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSlot

class SequenceInfoWidget(QWidget):
    """Ein Dashboard-Widget, das die Live-Laufzeitinformationen einer Sequenz anzeigt."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Initialisiert die UI-Komponenten."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        info_group = self._create_info_group()
        trend_group = self._create_trend_group()
        
        main_layout.addWidget(info_group)
        main_layout.addWidget(trend_group)
        main_layout.addStretch()

    def _create_info_group(self):
        """Erstellt die GroupBox für Laufzeit-Informationen."""
        group = QGroupBox("Laufzeit-Informationen")
        layout = QGridLayout(group)
        
        # Labels im Widget speichern
        self.info_labels = {
            "status": QLabel("Bereit"), "cycle": QLabel("- / -"), "step": QLabel("- / -"),
            "elapsed": QLabel("00:00"), "eta": QLabel("00:00"),
            "speed": QLabel("0.0 Zyklen/s"), "avg_time": QLabel("0.0 ms")
        }
        
        layout.addWidget(QLabel("Status:"), 0, 0); layout.addWidget(self.info_labels["status"], 0, 1)
        layout.addWidget(QLabel("Zyklus:"), 1, 0); layout.addWidget(self.info_labels["cycle"], 1, 1)
        layout.addWidget(QLabel("Schritt:"), 2, 0); layout.addWidget(self.info_labels["step"], 2, 1)
        layout.addWidget(QLabel("Laufzeit:"), 3, 0); layout.addWidget(self.info_labels["elapsed"], 3, 1)
        layout.addWidget(QLabel("Restzeit (ETA):"), 4, 0); layout.addWidget(self.info_labels["eta"], 4, 1)
        layout.addWidget(QLabel("Ø Zyklen/s:"), 5, 0); layout.addWidget(self.info_labels["speed"], 5, 1)
        layout.addWidget(QLabel("Ø Zykluszeit:"), 6, 0); layout.addWidget(self.info_labels["avg_time"], 6, 1)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar, 7, 0, 1, 2)
        
        return group

    def _create_trend_group(self):
        """Erstellt die GroupBox für die Live-Analyse."""
        group = QGroupBox("Live-Analyse (Zykluszeiten)")
        layout = QVBoxLayout(group)
        
        self.trend_labels = {
            "trend": QLabel("Trend: -"), 
            "stability": QLabel("Stabilität: -"), 
            "anomalies": QLabel("Anomalien: -")
        }
        
        for label in self.trend_labels.values():
            layout.addWidget(label)
            
        return group
    
    @pyqtSlot(dict)
    def update_sequence_info(self, info):
        """Slot zum Aktualisieren der Laufzeit-Infos."""
        self.info_labels["status"].setText("Läuft...")
        self.info_labels["status"].setStyleSheet("color: #2ecc71;") # Grün
        
        self.info_labels["cycle"].setText(f"{info['cycle']} / {info['max_cycles'] if info['max_cycles'] > 0 else '∞'}")
        self.info_labels["step"].setText(f"{info['step']} / {info['total_steps']}")
        
        elapsed_str = f"{int(info['elapsed']//60)}:{int(info['elapsed']%60):02d}"
        self.info_labels["elapsed"].setText(elapsed_str)
        
        eta_str = f"{int(info['eta']//60)}:{int(info['eta']%60):02d}" if info['eta'] > 0 else "-:--"
        self.info_labels["eta"].setText(eta_str)
        
        self.info_labels["speed"].setText(f"{info['cycles_per_sec']:.2f} Zyklen/s")
        
        avg_cycle_time_ms = info.get('avg_cycle_time', 0) * 1000
        self.info_labels["avg_time"].setText(f"{avg_cycle_time_ms:.2f} ms")
        
        self.progress_bar.setValue(int(info.get('progress_percent', 0)))

    @pyqtSlot(dict)
    def update_trend_info(self, analysis):
        """Slot zum Aktualisieren der Trend-Infos."""
        cycle_analysis = analysis.get('cycle_analysis', {})
        trend = cycle_analysis.get('trend', 'insufficient_data')
        stability = cycle_analysis.get('stability', 0)
        anomalies = cycle_analysis.get('anomalies', [])

        trend_icons = {"stable": "➡️", "increasing": "⬆️", "decreasing": "⬇️"}
        self.trend_labels["trend"].setText(f"Trend: {trend_icons.get(trend, '⏳')} {trend}")
        
        stab_color = "#2ecc71" if stability > 90 else ("#f39c12" if stability > 70 else "#e74c3c")
        self.trend_labels["stability"].setText(f"Stabilität: <span style='color: {stab_color};'>{stability:.1f}%</span>")
        
        anom_color = "#e74c3c" if anomalies else "#2ecc71"
        self.trend_labels["anomalies"].setText(f"Anomalien: <span style='color: {anom_color};'>{len(anomalies)}</span>")

    @pyqtSlot()
    def set_stopped_state(self):
        """Slot, um den Zustand 'Gestoppt' oder 'Bereit' anzuzeigen."""
        self.info_labels["status"].setText("Gestoppt")
        self.info_labels["status"].setStyleSheet("color: #e74c3c;") # Rot
        self.progress_bar.setValue(0)
        
        # Reset labels
        self.info_labels["cycle"].setText("- / -")
        self.info_labels["step"].setText("- / -")
        self.info_labels["elapsed"].setText("00:00")
        self.info_labels["eta"].setText("00:00")
        self.info_labels["speed"].setText("0.0 Zyklen/s")
        self.info_labels["avg_time"].setText("0.0 ms")
        
        self.trend_labels["trend"].setText("Trend: -")
        self.trend_labels["stability"].setText("Stabilität: -")
        self.trend_labels["anomalies"].setText("Anomalien: -")