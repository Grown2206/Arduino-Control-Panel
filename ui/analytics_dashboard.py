# -*- coding: utf-8 -*-
"""
ui/analytics_dashboard.py
Analytics Dashboard mit KPIs, Heatmaps und Korrelations-Analysen
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QFrame, QGridLayout, QSpinBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QProgressBar, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

# Import der Analysis-Module
try:
    from analysis.advanced_stats import AdvancedStats
    from analysis.prediction_model import PredictionModel
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("⚠️ Analytics Module nicht verfügbar")


class KPIWidget(QFrame):
    """Einzelnes KPI-Widget für Dashboard"""

    def __init__(self, title: str, value: str = "N/A", unit: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            KPIWidget {
                background-color: rgba(50, 50, 70, 0.8);
                border: 2px solid #27ae60;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)

        # Titel
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 12px; color: #aaa; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Wert
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24px; color: #27ae60; font-weight: bold;")
        layout.addWidget(self.value_label)

        # Einheit
        if unit:
            self.unit_label = QLabel(unit)
            self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.unit_label.setStyleSheet("font-size: 10px; color: #888;")
            layout.addWidget(self.unit_label)

    def update_value(self, value: str, color: str = "#27ae60"):
        """Aktualisiert den KPI-Wert"""
        self.value_label.setText(value)
        self.value_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")


class AnalyticsDashboardTab(QWidget):
    """
    Hauptdashboard für erweiterte Analytics
    """

    def __init__(self, db_file: str = "arduino_tests.db", parent=None):
        super().__init__(parent)
        self.db_file = db_file

        if not ANALYTICS_AVAILABLE:
            self.show_error_layout()
            return

        self.setup_ui()
        self.load_initial_data()

    def show_error_layout(self):
        """Zeigt Fehler-Layout wenn Module nicht verfügbar"""
        layout = QVBoxLayout(self)
        error_label = QLabel("⚠️ Analytics Module nicht verfügbar\n\nBitte installieren Sie die benötigten Module:\n- numpy\n- matplotlib\n- seaborn")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("font-size: 14px; color: #e74c3c;")
        layout.addWidget(error_label)

    def setup_ui(self):
        """Erstellt die UI-Komponenten"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)

        # Tab Widget für verschiedene Analytics-Bereiche
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: KPIs & Übersicht
        self.overview_tab = self.create_overview_tab()
        self.tabs.addTab(self.overview_tab, "📊 Übersicht")

        # Tab 2: Langzeit-Trends
        self.trends_tab = self.create_trends_tab()
        self.tabs.addTab(self.trends_tab, "📈 Trends")

        # Tab 3: Vergleichs-Analysen
        self.comparison_tab = self.create_comparison_tab()
        self.tabs.addTab(self.comparison_tab, "⚖️ Vergleich")

        # Tab 4: Vorhersagen
        self.prediction_tab = self.create_prediction_tab()
        self.tabs.addTab(self.prediction_tab, "🔮 Vorhersage")

        # Tab 5: Korrelationen
        self.correlation_tab = self.create_correlation_tab()
        self.tabs.addTab(self.correlation_tab, "🔗 Korrelation")

    def create_toolbar(self) -> QWidget:
        """Erstellt die Toolbar"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar.setStyleSheet("background-color: rgba(40, 40, 50, 0.9);")

        layout = QHBoxLayout(toolbar)

        # Titel
        title = QLabel("📊 Analytics Dashboard")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        layout.addWidget(title)

        layout.addStretch()

        # Zeitraum-Auswahl
        layout.addWidget(QLabel("Zeitraum:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 Tage", "30 Tage", "90 Tage", "365 Tage"])
        self.period_combo.setCurrentText("30 Tage")
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        layout.addWidget(self.period_combo)

        # Refresh Button
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self.refresh_all_data)
        layout.addWidget(refresh_btn)

        return toolbar

    def create_overview_tab(self) -> QWidget:
        """Erstellt das Übersichts-Tab mit KPIs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # KPI-Grid
        kpi_group = QGroupBox("Key Performance Indicators")
        kpi_layout = QGridLayout(kpi_group)

        # Erstelle KPI-Widgets
        self.kpi_total_runs = KPIWidget("Gesamt-Läufe", "0")
        self.kpi_success_rate = KPIWidget("Erfolgsrate", "0%")
        self.kpi_avg_cycle_time = KPIWidget("Ø Zykluszeit", "0 ms")
        self.kpi_stability = KPIWidget("Stabilität", "0%")

        kpi_layout.addWidget(self.kpi_total_runs, 0, 0)
        kpi_layout.addWidget(self.kpi_success_rate, 0, 1)
        kpi_layout.addWidget(self.kpi_avg_cycle_time, 0, 2)
        kpi_layout.addWidget(self.kpi_stability, 0, 3)

        self.kpi_degradation = KPIWidget("Degradation", "0%")
        self.kpi_anomaly_rate = KPIWidget("Anomalie-Rate", "0%")
        self.kpi_best_performance = KPIWidget("Best Performance", "N/A")
        self.kpi_risk_score = KPIWidget("Risiko-Score", "0/100")

        kpi_layout.addWidget(self.kpi_degradation, 1, 0)
        kpi_layout.addWidget(self.kpi_anomaly_rate, 1, 1)
        kpi_layout.addWidget(self.kpi_best_performance, 1, 2)
        kpi_layout.addWidget(self.kpi_risk_score, 1, 3)

        layout.addWidget(kpi_group)

        # Performance-Timeline Chart
        timeline_group = QGroupBox("Performance Timeline")
        timeline_layout = QVBoxLayout(timeline_group)

        self.timeline_canvas = FigureCanvas(Figure(figsize=(10, 4)))
        timeline_layout.addWidget(self.timeline_canvas)

        layout.addWidget(timeline_group)

        # Degradation Alerts
        alerts_group = QGroupBox("🚨 Degradation Alerts")
        alerts_layout = QVBoxLayout(alerts_group)

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels(["Sequenz", "Typ", "Änderung", "Nachricht"])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        alerts_layout.addWidget(self.alerts_table)

        layout.addWidget(alerts_group)

        return widget

    def create_trends_tab(self) -> QWidget:
        """Erstellt das Trends-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Trend-Chart
        trend_group = QGroupBox("Langzeit-Trend-Analyse")
        trend_layout = QVBoxLayout(trend_group)

        self.trend_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        trend_layout.addWidget(self.trend_canvas)

        layout.addWidget(trend_group)

        # Trend-Statistiken
        stats_group = QGroupBox("Trend-Statistiken")
        stats_layout = QVBoxLayout(stats_group)

        self.trend_stats_label = QLabel("Klicken Sie auf 'Aktualisieren' um Daten zu laden")
        self.trend_stats_label.setWordWrap(True)
        stats_layout.addWidget(self.trend_stats_label)

        layout.addWidget(stats_group)

        return widget

    def create_comparison_tab(self) -> QWidget:
        """Erstellt das Vergleichs-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel("⚖️ Vergleichs-Analysen\n\nWählen Sie Testläufe im Archiv-Tab aus und verwenden Sie die Vergleichsfunktion.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Comparison Chart
        self.comparison_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        layout.addWidget(self.comparison_canvas)

        return widget

    def create_prediction_tab(self) -> QWidget:
        """Erstellt das Vorhersage-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Steuerung
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Sequenz:"))

        self.prediction_sequence_combo = QComboBox()
        control_layout.addWidget(self.prediction_sequence_combo)

        control_layout.addWidget(QLabel("Tage voraus:"))
        self.prediction_days_spin = QSpinBox()
        self.prediction_days_spin.setRange(1, 90)
        self.prediction_days_spin.setValue(7)
        control_layout.addWidget(self.prediction_days_spin)

        predict_btn = QPushButton("🔮 Vorhersage berechnen")
        predict_btn.clicked.connect(self.calculate_prediction)
        control_layout.addWidget(predict_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Prediction Chart
        self.prediction_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        layout.addWidget(self.prediction_canvas)

        # Prediction Stats
        self.prediction_stats_label = QLabel("Keine Vorhersage berechnet")
        self.prediction_stats_label.setWordWrap(True)
        layout.addWidget(self.prediction_stats_label)

        return widget

    def create_correlation_tab(self) -> QWidget:
        """Erstellt das Korrelations-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Steuerung
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Sequenz (leer = alle):"))

        self.correlation_sequence_combo = QComboBox()
        self.correlation_sequence_combo.addItem("Alle Sequenzen", None)
        control_layout.addWidget(self.correlation_sequence_combo)

        analyze_btn = QPushButton("🔗 Korrelation berechnen")
        analyze_btn.clicked.connect(self.calculate_correlation)
        control_layout.addWidget(analyze_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Heatmap
        heatmap_group = QGroupBox("Korrelations-Heatmap")
        heatmap_layout = QVBoxLayout(heatmap_group)

        self.heatmap_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        heatmap_layout.addWidget(self.heatmap_canvas)

        layout.addWidget(heatmap_group)

        # Starke Korrelationen
        corr_group = QGroupBox("Starke Korrelationen")
        corr_layout = QVBoxLayout(corr_group)

        self.correlation_table = QTableWidget()
        self.correlation_table.setColumnCount(3)
        self.correlation_table.setHorizontalHeaderLabels(["Variable 1", "Variable 2", "Korrelation"])
        self.correlation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        corr_layout.addWidget(self.correlation_table)

        layout.addWidget(corr_group)

        return widget

    def load_initial_data(self):
        """Lädt initiale Daten"""
        self.refresh_all_data()

    def get_period_days(self) -> int:
        """Gibt die gewählte Periodenanzahl zurück"""
        period_text = self.period_combo.currentText()
        return int(period_text.split()[0])

    def on_period_changed(self):
        """Wird aufgerufen wenn Zeitraum geändert wird"""
        self.refresh_all_data()

    def refresh_all_data(self):
        """Aktualisiert alle Daten"""
        days = self.get_period_days()

        try:
            # Langzeit-Trends laden
            trends = AdvancedStats.analyze_longterm_trends(self.db_file, days)

            if trends['status'] == 'success':
                self.update_kpis(trends)
                self.update_timeline_chart(trends)
                self.update_alerts_table(trends)
                self.update_trends_tab(trends)

                # Sequenz-Liste aktualisieren
                sequences = list(trends['sequence_performance'].keys())
                self.prediction_sequence_combo.clear()
                self.prediction_sequence_combo.addItems(sequences)

                self.correlation_sequence_combo.clear()
                self.correlation_sequence_combo.addItem("Alle Sequenzen", None)
                for seq in sequences:
                    self.correlation_sequence_combo.addItem(seq, seq)

            else:
                QMessageBox.information(self, "Keine Daten", trends.get('message', 'Keine Daten verfügbar'))

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Daten:\n{str(e)}")

    def update_kpis(self, trends: dict):
        """Aktualisiert KPI-Widgets"""
        # Total Runs
        total_runs = trends.get('total_runs', 0)
        self.kpi_total_runs.update_value(str(total_runs))

        # Success Rate
        daily_summary = trends.get('daily_summary', [])
        if daily_summary:
            avg_success_rate = np.mean([d['success_rate'] for d in daily_summary])
            color = "#27ae60" if avg_success_rate >= 90 else ("#f39c12" if avg_success_rate >= 70 else "#e74c3c")
            self.kpi_success_rate.update_value(f"{avg_success_rate:.1f}%", color)
        else:
            self.kpi_success_rate.update_value("N/A")

        # Avg Cycle Time
        timeline = trends.get('timeline', [])
        cycle_times = [t['avg_cycle_time'] for t in timeline if t['avg_cycle_time'] > 0]
        if cycle_times:
            avg_ct = np.mean(cycle_times)
            self.kpi_avg_cycle_time.update_value(f"{avg_ct:.1f} ms")
        else:
            self.kpi_avg_cycle_time.update_value("N/A")

        # Stability
        trend_data = trends.get('trends', {})
        if trend_data.get('status') == 'calculated':
            stability = 100 - (trend_data.get('std_cycle_time', 0) / trend_data.get('avg_cycle_time', 1) * 100)
            color = "#27ae60" if stability >= 80 else ("#f39c12" if stability >= 60 else "#e74c3c")
            self.kpi_stability.update_value(f"{stability:.1f}%", color)
        else:
            self.kpi_stability.update_value("N/A")

        # Degradation
        if trend_data.get('status') == 'calculated':
            rel_slope = trend_data.get('relative_slope_percent', 0)
            color = "#e74c3c" if rel_slope > 5 else ("#f39c12" if rel_slope > 2 else "#27ae60")
            sign = "+" if rel_slope > 0 else ""
            self.kpi_degradation.update_value(f"{sign}{rel_slope:.1f}%", color)
        else:
            self.kpi_degradation.update_value("N/A")

        # Anomaly Rate
        alerts = trends.get('degradation_alerts', [])
        degradation_alerts = [a for a in alerts if a['type'] == 'degradation']
        if timeline:
            anomaly_rate = len(degradation_alerts) / len(trends['sequence_performance']) * 100 if trends['sequence_performance'] else 0
            color = "#e74c3c" if anomaly_rate > 20 else ("#f39c12" if anomaly_rate > 10 else "#27ae60")
            self.kpi_anomaly_rate.update_value(f"{anomaly_rate:.1f}%", color)
        else:
            self.kpi_anomaly_rate.update_value("N/A")

    def update_timeline_chart(self, trends: dict):
        """Aktualisiert Timeline-Chart"""
        timeline = trends.get('timeline', [])
        if not timeline:
            return

        fig = self.timeline_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Extrahiere Daten
        timestamps = [datetime.fromisoformat(t['timestamp']) for t in timeline]
        cycle_times = [t['avg_cycle_time'] for t in timeline]

        # Plot
        ax.plot(timestamps, cycle_times, marker='o', linestyle='-', linewidth=2, markersize=4, color='#27ae60')
        ax.set_xlabel('Zeitpunkt')
        ax.set_ylabel('Durchschnittliche Zykluszeit (ms)')
        ax.set_title('Performance Timeline')
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        self.timeline_canvas.draw()

    def update_alerts_table(self, trends: dict):
        """Aktualisiert Alerts-Tabelle"""
        alerts = trends.get('degradation_alerts', [])

        self.alerts_table.setRowCount(len(alerts))

        for i, alert in enumerate(alerts):
            self.alerts_table.setItem(i, 0, QTableWidgetItem(alert['sequence']))
            self.alerts_table.setItem(i, 1, QTableWidgetItem(alert['type'].upper()))

            change = f"{alert['change_percent']:.1f}%"
            change_item = QTableWidgetItem(change)
            if alert['type'] == 'degradation':
                change_item.setBackground(QColor("#e74c3c"))
            else:
                change_item.setBackground(QColor("#27ae60"))
            self.alerts_table.setItem(i, 2, change_item)

            self.alerts_table.setItem(i, 3, QTableWidgetItem(alert['message']))

    def update_trends_tab(self, trends: dict):
        """Aktualisiert Trends-Tab"""
        trend_data = trends.get('trends', {})

        if trend_data.get('status') != 'calculated':
            self.trend_stats_label.setText("Nicht genug Daten für Trend-Analyse")
            return

        # Statistik-Text
        stats_text = f"""
        <b>Trend-Analyse:</b><br>
        • Trend-Richtung: <b>{trend_data['trend_direction'].upper()}</b><br>
        • Schweregrad: <b>{trend_data['trend_severity'].upper()}</b><br>
        • Relative Änderung: <b>{trend_data['relative_slope_percent']:.2f}%</b><br>
        • R² (Modell-Güte): <b>{trend_data['r_squared']:.3f}</b><br>
        • Ø Zykluszeit: <b>{trend_data['avg_cycle_time']:.2f} ms</b><br>
        • Standardabweichung: <b>{trend_data['std_cycle_time']:.2f} ms</b>
        """

        self.trend_stats_label.setText(stats_text)

        # Trend-Chart
        timeline = trends.get('timeline', [])
        if timeline:
            fig = self.trend_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)

            timestamps = [datetime.fromisoformat(t['timestamp']) for t in timeline]
            cycle_times = [t['avg_cycle_time'] for t in timeline]

            # Plot Daten
            ax.scatter(range(len(cycle_times)), cycle_times, alpha=0.6, label='Messwerte')

            # Trend-Linie
            x = np.arange(len(cycle_times))
            z = np.polyfit(x, cycle_times, 1)
            p = np.poly1d(z)
            ax.plot(x, p(x), "r--", linewidth=2, label='Trend')

            ax.set_xlabel('Testlauf-Nummer')
            ax.set_ylabel('Zykluszeit (ms)')
            ax.set_title('Langzeit-Trend')
            ax.legend()
            ax.grid(True, alpha=0.3)

            fig.tight_layout()
            self.trend_canvas.draw()

    def calculate_prediction(self):
        """Berechnet Vorhersage"""
        sequence = self.prediction_sequence_combo.currentText()
        days_ahead = self.prediction_days_spin.value()

        if not sequence:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie eine Sequenz aus")
            return

        try:
            prediction = PredictionModel.predict_next_performance(
                self.db_file, sequence, days_ahead
            )

            if prediction['status'] == 'success':
                self.update_prediction_chart(prediction)
                self.update_prediction_stats(prediction)
            else:
                QMessageBox.information(self, "Keine Daten", prediction.get('message', 'Vorhersage nicht möglich'))

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei Vorhersage:\n{str(e)}")

    def update_prediction_chart(self, prediction: dict):
        """Aktualisiert Vorhersage-Chart"""
        predictions = prediction.get('predictions', [])
        if not predictions:
            return

        fig = self.prediction_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Extrahiere Daten
        dates = [datetime.fromisoformat(p['date']) for p in predictions]
        predicted = [p['predicted_cycle_time'] for p in predictions]
        lower = [p['lower_bound'] for p in predictions]
        upper = [p['upper_bound'] for p in predictions]

        # Plot
        ax.plot(dates, predicted, 'b-', linewidth=2, label='Vorhersage')
        ax.fill_between(dates, lower, upper, alpha=0.3, label='95% Konfidenzintervall')

        ax.set_xlabel('Datum')
        ax.set_ylabel('Zykluszeit (ms)')
        ax.set_title(f'Performance-Vorhersage: {prediction["sequence"]}')
        ax.legend()
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        self.prediction_canvas.draw()

    def update_prediction_stats(self, prediction: dict):
        """Aktualisiert Vorhersage-Statistiken"""
        model_quality = prediction.get('model_quality', {})
        current_perf = prediction.get('current_performance', {})
        degradation = prediction.get('degradation_forecast', {})
        warning = degradation.get('warning')

        stats_text = f"""
        <b>Vorhersage-Modell:</b><br>
        • Modell-Typ: <b>{model_quality.get('model_type', 'N/A')}</b><br>
        • R² (Güte): <b>{model_quality.get('r_squared', 0):.3f}</b><br>
        • Datenpunkte: <b>{model_quality.get('data_points', 0)}</b><br>
        <br>
        <b>Aktuelle Performance:</b><br>
        • Ø Zykluszeit: <b>{current_perf.get('avg_cycle_time', 0):.2f} ms</b><br>
        • Trend: <b>{current_perf.get('trend', 'N/A').upper()}</b><br>
        <br>
        <b>Vorhersage:</b><br>
        • Erwartete Änderung: <b>{degradation.get('percent_change', 0):.1f}%</b><br>
        """

        if warning:
            stats_text += f"""
        <br>
        <b style="color: {'#e74c3c' if warning['level'] == 'high' else '#f39c12'};">⚠️ WARNUNG:</b><br>
        • Level: <b>{warning['level'].upper()}</b><br>
        • {warning['message']}<br>
        • Empfehlung: <b>{warning['recommendation']}</b>
        """

        self.prediction_stats_label.setText(stats_text)

    def calculate_correlation(self):
        """Berechnet Korrelations-Matrix"""
        sequence = self.correlation_sequence_combo.currentData()

        try:
            correlation = AdvancedStats.generate_correlation_matrix(
                self.db_file, sequence
            )

            if correlation['status'] == 'success':
                self.update_correlation_heatmap(correlation)
                self.update_correlation_table(correlation)
            else:
                QMessageBox.information(self, "Keine Daten", correlation.get('message', 'Korrelation nicht möglich'))

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei Korrelation:\n{str(e)}")

    def update_correlation_heatmap(self, correlation: dict):
        """Aktualisiert Korrelations-Heatmap"""
        matrix = np.array(correlation['correlation_matrix'])
        variables = correlation['variables']

        fig = self.heatmap_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Heatmap erstellen
        sns.heatmap(
            matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            linewidths=1,
            cbar_kws={"shrink": 0.8},
            xticklabels=variables,
            yticklabels=variables,
            ax=ax
        )

        ax.set_title('Korrelations-Matrix')

        fig.tight_layout()
        self.heatmap_canvas.draw()

    def update_correlation_table(self, correlation: dict):
        """Aktualisiert Korrelations-Tabelle"""
        strong_corr = correlation.get('strong_correlations', [])

        self.correlation_table.setRowCount(len(strong_corr))

        for i, corr in enumerate(strong_corr):
            self.correlation_table.setItem(i, 0, QTableWidgetItem(corr['variable1']))
            self.correlation_table.setItem(i, 1, QTableWidgetItem(corr['variable2']))

            corr_value = f"{corr['correlation']:.3f}"
            corr_item = QTableWidgetItem(corr_value)

            # Farbcodierung
            if abs(corr['correlation']) > 0.9:
                corr_item.setBackground(QColor("#27ae60"))
            else:
                corr_item.setBackground(QColor("#f39c12"))

            self.correlation_table.setItem(i, 2, corr_item)
