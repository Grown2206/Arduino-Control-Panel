"""
Live-Statistik-Widget
Zeigt Echtzeit-Statistiken während laufender Tests

Features:
- Echtzeit-Update (500ms)
- Ø Zykluszeit, Min/Max, Std, Trend
- Stabilität mit Progress-Bar
- Anomalien-Counter
- Mini-Chart (letzte 50 Zyklen)
- Farbcodierung (Grün/Gelb/Rot)
"""

import time
from typing import List, Optional
from collections import deque

import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False


class MiniChartWidget(QWidget):
    """
    Mini-Chart für die letzten N Zyklen.
    Zeigt Linienverlauf mit Anomalie-Markierungen.
    """
    
    def __init__(self, max_points: int = 50):
        super().__init__()
        self.max_points = max_points
        self.data = deque(maxlen=max_points)
        self.anomalies = deque(maxlen=max_points)
        self.avg_line = None
        
        self.setMinimumHeight(80)
        self.setMinimumWidth(250)
        
        # Farben
        self.bg_color = QColor('#2c3e50')
        self.line_color = QColor('#3498db')
        self.avg_color = QColor('#2ecc71')
        self.anomaly_color = QColor('#e74c3c')
        self.grid_color = QColor('#34495e')
    
    def add_point(self, value: float, is_anomaly: bool = False):
        """Fügt neuen Datenpunkt hinzu."""
        self.data.append(value)
        self.anomalies.append(is_anomaly)
        self.update()
    
    def set_average(self, avg: float):
        """Setzt Durchschnitts-Linie."""
        self.avg_line = avg
        self.update()
    
    def clear(self):
        """Löscht alle Daten."""
        self.data.clear()
        self.anomalies.clear()
        self.avg_line = None
        self.update()
    
    def paintEvent(self, event):
        """Zeichnet Mini-Chart."""
        if not self.data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Hintergrund
        painter.fillRect(self.rect(), self.bg_color)
        
        # Berechne Skalierung
        width = self.width()
        height = self.height()
        padding = 10
        
        data_list = list(self.data)
        min_val = min(data_list)
        max_val = max(data_list)
        value_range = max_val - min_val if max_val != min_val else 1
        
        # Grid zeichnen
        painter.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            y = padding + (height - 2 * padding) * i / 4
            painter.drawLine(padding, int(y), width - padding, int(y))
        
        # Durchschnitts-Linie
        if self.avg_line is not None:
            y_avg = height - padding - ((self.avg_line - min_val) / value_range) * (height - 2 * padding)
            painter.setPen(QPen(self.avg_color, 2, Qt.PenStyle.DashLine))
            painter.drawLine(padding, int(y_avg), width - padding, int(y_avg))
        
        # Daten-Linie
        painter.setPen(QPen(self.line_color, 2))
        points = []
        
        for i, value in enumerate(data_list):
            x = padding + (width - 2 * padding) * i / max(len(data_list) - 1, 1)
            y = height - padding - ((value - min_val) / value_range) * (height - 2 * padding)
            points.append((x, y))
        
        # Zeichne Linie
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]), 
                           int(points[i+1][0]), int(points[i+1][1]))
        
        # Anomalie-Marker
        painter.setPen(QPen(self.anomaly_color, 3))
        painter.setBrush(self.anomaly_color)
        
        for i, (x, y) in enumerate(points):
            if i < len(self.anomalies) and self.anomalies[i]:
                painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)


class LiveStatsWidget(QWidget):
    """
    Haupt-Widget für Live-Statistiken.
    Zeigt alle wichtigen Metriken in Echtzeit.
    """
    
    # Signals
    pause_requested = pyqtSignal()  # Nutzer will pausieren
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Daten
        self.cycle_times = []
        self.current_cycle = 0
        self.total_cycles = 0
        self.anomaly_count = 0
        self.is_running = False
        self.start_time = 0
        
        # Statistiken
        self.stats = {
            'avg': 0.0,
            'current': 0.0,
            'min': 0.0,
            'max': 0.0,
            'std': 0.0,
            'trend': 0.0,
            'stability': 0.0
        }
        
        self.setup_ui()
        
        # Update-Timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_display)
        self.update_timer.setInterval(500)  # 500ms
    
    def setup_ui(self):
        """Erstellt UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # === HEADER ===
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("📊 Live-Statistiken")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #3498db;
            }
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.cycle_label = QLabel("Zyklus 0/0")
        self.cycle_label.setStyleSheet("font-size: 11pt; color: #95a5a6;")
        header_layout.addWidget(self.cycle_label)
        
        layout.addLayout(header_layout)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #34495e;")
        layout.addWidget(line)
        
        # === METRIKEN GRID ===
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(15)
        
        # Row 0: Ø Zykluszeit + Aktuell
        self.avg_label = self.create_metric_widget("Ø Zykluszeit:", "0.0 ms")
        metrics_layout.addWidget(self.avg_label, 0, 0)
        
        self.current_label = self.create_metric_widget("Aktuell:", "0.0 ms", highlight=True)
        metrics_layout.addWidget(self.current_label, 0, 1)
        
        # Row 1: Min/Max
        self.minmax_label = self.create_metric_widget("Min / Max:", "0 / 0 ms")
        metrics_layout.addWidget(self.minmax_label, 1, 0)
        
        # Row 2: Std
        self.std_label = self.create_metric_widget("Std.abw.:", "0.0 ms")
        metrics_layout.addWidget(self.std_label, 2, 0)
        
        # Row 3: Trend
        self.trend_label = self.create_metric_widget("Trend:", "-- %")
        metrics_layout.addWidget(self.trend_label, 3, 0)
        
        layout.addLayout(metrics_layout)
        
        # === STABILITÄT ===
        stability_container = QWidget()
        stability_layout = QVBoxLayout(stability_container)
        stability_layout.setContentsMargins(0, 5, 0, 5)
        
        stability_header = QHBoxLayout()
        stability_header.addWidget(QLabel("<b>Stabilität:</b>"))
        
        self.stability_value_label = QLabel("0.0%")
        self.stability_value_label.setStyleSheet("color: #95a5a6;")
        stability_header.addWidget(self.stability_value_label)
        stability_header.addStretch()
        
        stability_layout.addLayout(stability_header)
        
        self.stability_bar = QProgressBar()
        self.stability_bar.setRange(0, 100)
        self.stability_bar.setValue(0)
        self.stability_bar.setTextVisible(False)
        self.stability_bar.setMaximumHeight(20)
        self.stability_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 5px;
                background-color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
        """)
        stability_layout.addWidget(self.stability_bar)
        
        layout.addWidget(stability_container)
        
        # === ANOMALIEN ===
        anomaly_container = QWidget()
        anomaly_layout = QHBoxLayout(anomaly_container)
        anomaly_layout.setContentsMargins(0, 0, 0, 0)
        
        anomaly_layout.addWidget(QLabel("<b>Anomalien:</b>"))
        
        self.anomaly_label = QLabel("0")
        self.anomaly_label.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                font-size: 12pt;
                font-weight: bold;
            }
        """)
        anomaly_layout.addWidget(self.anomaly_label)
        
        self.anomaly_rate_label = QLabel("(0.0%)")
        self.anomaly_rate_label.setStyleSheet("color: #95a5a6;")
        anomaly_layout.addWidget(self.anomaly_rate_label)
        
        anomaly_layout.addStretch()
        
        layout.addWidget(anomaly_container)
        
        # === MINI-CHART ===
        chart_label = QLabel("<b>Verlauf (letzte 50 Zyklen):</b>")
        layout.addWidget(chart_label)
        
        self.mini_chart = MiniChartWidget()
        layout.addWidget(self.mini_chart)
        
        layout.addStretch()
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ecf0f1;
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
            }
        """)
    
    def create_metric_widget(self, label: str, value: str, highlight: bool = False) -> QWidget:
        """Erstellt Metrik-Widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #95a5a6; font-size: 9pt;")
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        if highlight:
            value_widget.setStyleSheet("""
                font-size: 13pt; 
                font-weight: bold; 
                color: #3498db;
            """)
        else:
            value_widget.setStyleSheet("font-size: 11pt; color: #ecf0f1;")
        
        layout.addWidget(value_widget)
        
        # Speichere Value-Label für Updates
        container.value_label = value_widget
        
        return container
    
    # === PUBLIC API ===
    
    def start_monitoring(self, total_cycles: int):
        """Startet Monitoring."""
        self.is_running = True
        self.total_cycles = total_cycles
        self.current_cycle = 0
        self.cycle_times = []
        self.anomaly_count = 0
        self.start_time = time.time()
        
        self.cycle_label.setText(f"Zyklus 0/{total_cycles}")
        self.mini_chart.clear()
        
        self.update_timer.start()
        print("📊 Live-Statistik Monitoring gestartet")
    
    def stop_monitoring(self):
        """Stoppt Monitoring."""
        self.is_running = False
        self.update_timer.stop()
        print("📊 Live-Statistik Monitoring gestoppt")
    
    def add_cycle(self, cycle_time: float, is_anomaly: bool = False):
        """Fügt neuen Zyklus hinzu."""
        if not self.is_running:
            return
        
        self.cycle_times.append(cycle_time)
        self.current_cycle += 1
        
        if is_anomaly:
            self.anomaly_count += 1
        
        # Update Chart
        self.mini_chart.add_point(cycle_time, is_anomaly)
        
        # Berechne Statistiken
        self.calculate_stats()
        
        # Update Display (passiert automatisch durch Timer)
    
    def calculate_stats(self):
        """Berechnet Statistiken."""
        if not self.cycle_times:
            return
        
        times = np.array(self.cycle_times)
        
        self.stats['avg'] = float(np.mean(times))
        self.stats['current'] = float(self.cycle_times[-1])
        self.stats['min'] = float(np.min(times))
        self.stats['max'] = float(np.max(times))
        self.stats['std'] = float(np.std(times))
        
        # Trend (letzte 10 vs vorherige 10)
        if len(times) >= 20:
            recent_10 = times[-10:]
            previous_10 = times[-20:-10]
            recent_avg = np.mean(recent_10)
            previous_avg = np.mean(previous_10)
            self.stats['trend'] = ((recent_avg - previous_avg) / previous_avg) * 100
        else:
            self.stats['trend'] = 0.0
        
        # Stabilität (inverse CV)
        cv = (self.stats['std'] / self.stats['avg']) * 100 if self.stats['avg'] > 0 else 0
        self.stats['stability'] = max(0, min(100, 100 - cv))
        
        # Update Chart Average-Line
        self.mini_chart.set_average(self.stats['avg'])
    
    def refresh_display(self):
        """Aktualisiert Anzeige."""
        if not self.is_running:
            return
        
        # Cycle Counter
        self.cycle_label.setText(f"Zyklus {self.current_cycle}/{self.total_cycles}")
        
        # Metriken
        self.avg_label.value_label.setText(f"{self.stats['avg']:.1f} ms")
        
        # Current mit Status-Indicator
        current_text = f"{self.stats['current']:.1f} ms"
        if self.cycle_times:
            deviation = abs(self.stats['current'] - self.stats['avg'])
            threshold = self.stats['std'] * 2
            
            if deviation > threshold:
                current_text += " ⚠️"
                self.current_label.value_label.setStyleSheet("""
                    font-size: 13pt; 
                    font-weight: bold; 
                    color: #e74c3c;
                """)
            else:
                current_text += " ✓"
                self.current_label.value_label.setStyleSheet("""
                    font-size: 13pt; 
                    font-weight: bold; 
                    color: #2ecc71;
                """)
        
        self.current_label.value_label.setText(current_text)
        
        # Min/Max
        self.minmax_label.value_label.setText(
            f"{self.stats['min']:.0f} / {self.stats['max']:.0f} ms"
        )
        
        # Std
        self.std_label.value_label.setText(f"{self.stats['std']:.1f} ms")
        
        # Trend
        trend = self.stats['trend']
        if abs(trend) < 0.1:
            trend_text = "→ stabil"
            trend_color = "#2ecc71"
        elif trend > 0:
            trend_text = f"⬆️ +{trend:.1f}%"
            trend_color = "#e74c3c"
        else:
            trend_text = f"⬇️ {trend:.1f}%"
            trend_color = "#3498db"
        
        self.trend_label.value_label.setText(trend_text)
        self.trend_label.value_label.setStyleSheet(f"font-size: 11pt; color: {trend_color};")
        
        # Stabilität
        stability = self.stats['stability']
        self.stability_value_label.setText(f"{stability:.1f}%")
        self.stability_bar.setValue(int(stability))
        
        # Stabilität-Farbe
        if stability >= 85:
            chunk_color = "#27ae60"
        elif stability >= 70:
            chunk_color = "#f39c12"
        else:
            chunk_color = "#e74c3c"
        
        self.stability_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #34495e;
                border-radius: 5px;
                background-color: #2c3e50;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 4px;
            }}
        """)
        
        # Anomalien
        self.anomaly_label.setText(str(self.anomaly_count))
        
        anomaly_rate = (self.anomaly_count / self.current_cycle * 100) if self.current_cycle > 0 else 0
        self.anomaly_rate_label.setText(f"({anomaly_rate:.1f}%)")
        
        # Anomalien-Farbe
        if anomaly_rate < 2:
            anomaly_color = "#2ecc71"
        elif anomaly_rate < 5:
            anomaly_color = "#f39c12"
        else:
            anomaly_color = "#e74c3c"
        
        self.anomaly_label.setStyleSheet(f"""
            QLabel {{
                color: {anomaly_color};
                font-size: 12pt;
                font-weight: bold;
            }}
        """)
    
    def get_stats(self) -> dict:
        """Gibt aktuelle Statistiken zurück."""
        return {
            'cycle_times': self.cycle_times.copy(),
            'current_cycle': self.current_cycle,
            'total_cycles': self.total_cycles,
            'anomaly_count': self.anomaly_count,
            'stats': self.stats.copy(),
            'elapsed_time': time.time() - self.start_time if self.start_time > 0 else 0
        }


# === BEISPIEL-VERWENDUNG ===

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
    import random
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Live-Statistik Widget Test")
            self.setGeometry(100, 100, 400, 600)
            
            # Central Widget
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            
            # Live-Stats Widget
            self.stats_widget = LiveStatsWidget()
            layout.addWidget(self.stats_widget)
            
            # Buttons
            btn_layout = QHBoxLayout()
            
            start_btn = QPushButton("Start (100 Zyklen)")
            start_btn.clicked.connect(self.start_test)
            btn_layout.addWidget(start_btn)
            
            stop_btn = QPushButton("Stop")
            stop_btn.clicked.connect(self.stop_test)
            btn_layout.addWidget(stop_btn)
            
            layout.addLayout(btn_layout)
            
            # Test-Timer
            self.test_timer = QTimer()
            self.test_timer.timeout.connect(self.simulate_cycle)
            self.test_cycle = 0
            self.base_time = 250
        
        def start_test(self):
            print("🧪 Starte Test...")
            self.test_cycle = 0
            self.stats_widget.start_monitoring(100)
            self.test_timer.start(100)  # Alle 100ms ein Zyklus
        
        def stop_test(self):
            print("🛑 Stoppe Test...")
            self.test_timer.stop()
            self.stats_widget.stop_monitoring()
        
        def simulate_cycle(self):
            if self.test_cycle >= 100:
                self.stop_test()
                return
            
            # Simuliere Zykluszeit mit Noise
            noise = random.uniform(-20, 20)
            
            # Ab und zu Anomalie
            is_anomaly = random.random() < 0.05
            if is_anomaly:
                noise += random.uniform(50, 100)
            
            cycle_time = self.base_time + noise
            
            self.stats_widget.add_cycle(cycle_time, is_anomaly)
            self.test_cycle += 1
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())