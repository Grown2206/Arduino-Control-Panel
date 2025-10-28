# -*- coding: utf-8 -*-
"""
ui/analytics_dashboard.py
Analytics Dashboard mit KPIs, Heatmaps und Korrelations-Analysen
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QFrame, QGridLayout, QSpinBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QProgressBar, QTabWidget,
    QDialog, QFormLayout, QCheckBox, QDoubleSpinBox, QDateEdit, QFileDialog,
    QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import csv
import json
from pathlib import Path

# Import der Analysis-Module
try:
    from analysis.advanced_stats import AdvancedStats, parse_timestamp
    from analysis.prediction_model import PredictionModel
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("⚠️ Analytics Module nicht verfügbar")


class AnalyticsSettingsDialog(QDialog):
    """Dialog für Analytics-Einstellungen"""

    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analytics Einstellungen")
        self.setMinimumWidth(500)
        self.settings = current_settings.copy()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Form Layout für Einstellungen
        form = QFormLayout()

        # Anomalie-Schwellenwert
        self.anomaly_threshold = QDoubleSpinBox()
        self.anomaly_threshold.setRange(1.0, 5.0)
        self.anomaly_threshold.setSingleStep(0.5)
        self.anomaly_threshold.setValue(self.settings.get('anomaly_threshold', 2.0))
        self.anomaly_threshold.setSuffix(" σ")
        self.anomaly_threshold.setToolTip("Anzahl der Standardabweichungen für Anomalie-Erkennung")
        form.addRow("Anomalie-Schwellenwert:", self.anomaly_threshold)

        # Degradations-Schwellenwert
        self.degradation_threshold = QDoubleSpinBox()
        self.degradation_threshold.setRange(1.0, 50.0)
        self.degradation_threshold.setSingleStep(1.0)
        self.degradation_threshold.setValue(self.settings.get('degradation_threshold', 10.0))
        self.degradation_threshold.setSuffix(" %")
        self.degradation_threshold.setToolTip("Prozentuale Änderung für Degradation-Warnung")
        form.addRow("Degradation-Schwellenwert:", self.degradation_threshold)

        # Trend-Sensitivität
        self.trend_sensitivity = QDoubleSpinBox()
        self.trend_sensitivity.setRange(0.1, 10.0)
        self.trend_sensitivity.setSingleStep(0.5)
        self.trend_sensitivity.setValue(self.settings.get('trend_sensitivity', 1.0))
        self.trend_sensitivity.setSuffix(" %")
        self.trend_sensitivity.setToolTip("Minimale prozentuale Änderung für Trend-Erkennung")
        form.addRow("Trend-Sensitivität:", self.trend_sensitivity)

        # Konfidenz-Level
        self.confidence_level = QDoubleSpinBox()
        self.confidence_level.setRange(0.80, 0.99)
        self.confidence_level.setSingleStep(0.01)
        self.confidence_level.setValue(self.settings.get('confidence_level', 0.95))
        self.confidence_level.setDecimals(2)
        self.confidence_level.setToolTip("Konfidenz-Level für Vorhersage-Intervalle")
        form.addRow("Konfidenz-Level:", self.confidence_level)

        # Auto-Refresh
        self.auto_refresh = QCheckBox()
        self.auto_refresh.setChecked(self.settings.get('auto_refresh', False))
        self.auto_refresh.setToolTip("Automatische Aktualisierung aktivieren")
        form.addRow("Auto-Refresh:", self.auto_refresh)

        # Refresh-Intervall
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(10, 300)
        self.refresh_interval.setSingleStep(10)
        self.refresh_interval.setValue(self.settings.get('refresh_interval', 60))
        self.refresh_interval.setSuffix(" Sekunden")
        self.refresh_interval.setEnabled(self.auto_refresh.isChecked())
        self.auto_refresh.toggled.connect(self.refresh_interval.setEnabled)
        form.addRow("Refresh-Intervall:", self.refresh_interval)

        # Chart-Stil
        self.chart_style = QComboBox()
        self.chart_style.addItems(["default", "seaborn", "dark_background", "ggplot", "bmh"])
        current_style = self.settings.get('chart_style', 'default')
        index = self.chart_style.findText(current_style)
        if index >= 0:
            self.chart_style.setCurrentIndex(index)
        form.addRow("Chart-Stil:", self.chart_style)

        # Min. Datenpunkte für Analyse
        self.min_data_points = QSpinBox()
        self.min_data_points.setRange(2, 100)
        self.min_data_points.setValue(self.settings.get('min_data_points', 5))
        self.min_data_points.setToolTip("Minimale Anzahl Datenpunkte für Analysen")
        form.addRow("Min. Datenpunkte:", self.min_data_points)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Standard")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def reset_to_defaults(self):
        """Setzt alle Einstellungen auf Standardwerte zurück"""
        self.anomaly_threshold.setValue(2.0)
        self.degradation_threshold.setValue(10.0)
        self.trend_sensitivity.setValue(1.0)
        self.confidence_level.setValue(0.95)
        self.auto_refresh.setChecked(False)
        self.refresh_interval.setValue(60)
        self.chart_style.setCurrentText("default")
        self.min_data_points.setValue(5)

    def get_settings(self) -> dict:
        """Gibt die aktuellen Einstellungen zurück"""
        return {
            'anomaly_threshold': self.anomaly_threshold.value(),
            'degradation_threshold': self.degradation_threshold.value(),
            'trend_sensitivity': self.trend_sensitivity.value(),
            'confidence_level': self.confidence_level.value(),
            'auto_refresh': self.auto_refresh.isChecked(),
            'refresh_interval': self.refresh_interval.value(),
            'chart_style': self.chart_style.currentText(),
            'min_data_points': self.min_data_points.value()
        }


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

        # Einstellungen
        self.settings = {
            'anomaly_threshold': 2.0,
            'degradation_threshold': 10.0,
            'trend_sensitivity': 1.0,
            'confidence_level': 0.95,
            'auto_refresh': False,
            'refresh_interval': 60,
            'chart_style': 'default',
            'min_data_points': 5
        }

        # Filter-Einstellungen
        self.filter_settings = {
            'sequence': None,
            'status': None,
            'start_date': None,
            'end_date': None
        }

        # Auto-Refresh Timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)

        # Gespeicherte Daten für Export
        self.current_data = None

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

        # Tab 6: Datenqualität
        self.quality_tab = self.create_data_quality_tab()
        self.tabs.addTab(self.quality_tab, "🎯 Datenqualität")

        # Tab 7: Statistik-Visualisierungen
        self.stats_viz_tab = self.create_stats_viz_tab()
        self.tabs.addTab(self.stats_viz_tab, "📉 Verteilungen")

        # Tab 8: Benchmarks & SLA
        self.benchmark_tab = self.create_benchmark_tab()
        self.tabs.addTab(self.benchmark_tab, "🎯 Benchmarks")

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

        # Filter Button
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.setToolTip("Filter für Daten anwenden")
        filter_btn.clicked.connect(self.show_filter_dialog)
        layout.addWidget(filter_btn)

        # Zeitraum-Auswahl
        layout.addWidget(QLabel("Zeitraum:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 Tage", "30 Tage", "90 Tage", "365 Tage", "Alle"])
        self.period_combo.setCurrentText("30 Tage")
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        layout.addWidget(self.period_combo)

        # Export Button
        export_btn = QPushButton("📥 Export")
        export_btn.setToolTip("Daten exportieren (CSV, JSON, PDF)")
        export_btn.clicked.connect(self.show_export_menu)
        layout.addWidget(export_btn)

        # Einstellungen Button
        settings_btn = QPushButton("⚙️ Einstellungen")
        settings_btn.setToolTip("Analytics-Einstellungen")
        settings_btn.clicked.connect(self.show_settings_dialog)
        layout.addWidget(settings_btn)

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

    def create_data_quality_tab(self) -> QWidget:
        """Erstellt das Datenqualitäts-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Qualitäts-Metriken
        metrics_group = QGroupBox("Datenqualitäts-Metriken")
        metrics_layout = QGridLayout(metrics_group)

        self.quality_completeness = KPIWidget("Vollständigkeit", "0%")
        self.quality_accuracy = KPIWidget("Genauigkeit", "0%")
        self.quality_consistency = KPIWidget("Konsistenz", "0%")
        self.quality_timeliness = KPIWidget("Aktualität", "0%")

        metrics_layout.addWidget(self.quality_completeness, 0, 0)
        metrics_layout.addWidget(self.quality_accuracy, 0, 1)
        metrics_layout.addWidget(self.quality_consistency, 0, 2)
        metrics_layout.addWidget(self.quality_timeliness, 0, 3)

        layout.addWidget(metrics_group)

        # Outlier-Detection
        outlier_group = QGroupBox("Ausreißer-Erkennung")
        outlier_layout = QVBoxLayout(outlier_group)

        self.outlier_table = QTableWidget()
        self.outlier_table.setColumnCount(5)
        self.outlier_table.setHorizontalHeaderLabels(["Run ID", "Sequenz", "Wert", "Abweichung", "Z-Score"])
        self.outlier_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        outlier_layout.addWidget(self.outlier_table)

        layout.addWidget(outlier_group)

        # Datenqualitäts-Report
        report_group = QGroupBox("Datenqualitäts-Report")
        report_layout = QVBoxLayout(report_group)

        self.quality_report = QTextEdit()
        self.quality_report.setReadOnly(True)
        self.quality_report.setMaximumHeight(150)
        report_layout.addWidget(self.quality_report)

        layout.addWidget(report_group)

        return widget

    def create_stats_viz_tab(self) -> QWidget:
        """Erstellt das Statistik-Visualisierungs-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Steuerung
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Visualisierung:"))

        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItems(["Histogramm", "Box-Plot", "Violin-Plot", "Scatter-Matrix"])
        self.viz_type_combo.currentTextChanged.connect(self.update_stats_visualization)
        control_layout.addWidget(self.viz_type_combo)

        control_layout.addWidget(QLabel("Sequenz:"))
        self.viz_sequence_combo = QComboBox()
        self.viz_sequence_combo.addItem("Alle Sequenzen", None)
        self.viz_sequence_combo.currentTextChanged.connect(self.update_stats_visualization)
        control_layout.addWidget(self.viz_sequence_combo)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # Splitter für mehrere Charts
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Chart 1: Hauptvisualisierung
        self.stats_viz_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        splitter.addWidget(self.stats_viz_canvas)

        # Chart 2: Zusatz-Informationen
        self.stats_viz_canvas2 = FigureCanvas(Figure(figsize=(10, 4)))
        splitter.addWidget(self.stats_viz_canvas2)

        layout.addWidget(splitter)

        return widget

    def create_benchmark_tab(self) -> QWidget:
        """Erstellt das Benchmark-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # SLA/KPI-Definition
        sla_group = QGroupBox("SLA / Benchmark-Definitionen")
        sla_layout = QVBoxLayout(sla_group)

        # SLA-Tabelle
        self.sla_table = QTableWidget()
        self.sla_table.setColumnCount(4)
        self.sla_table.setHorizontalHeaderLabels(["Metrik", "Zielwert", "Aktuell", "Status"])
        self.sla_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Beispiel-SLAs
        self.sla_table.setRowCount(5)
        sla_items = [
            ("Ø Zykluszeit", "< 100 ms", "N/A", "⏳"),
            ("Erfolgsrate", "> 95%", "N/A", "⏳"),
            ("Stabilität", "> 90%", "N/A", "⏳"),
            ("Anomalie-Rate", "< 5%", "N/A", "⏳"),
            ("Degradation", "< 3%", "N/A", "⏳")
        ]

        for i, (metric, target, current, status) in enumerate(sla_items):
            self.sla_table.setItem(i, 0, QTableWidgetItem(metric))
            self.sla_table.setItem(i, 1, QTableWidgetItem(target))
            self.sla_table.setItem(i, 2, QTableWidgetItem(current))
            self.sla_table.setItem(i, 3, QTableWidgetItem(status))

        sla_layout.addWidget(self.sla_table)

        layout.addWidget(sla_group)

        # Benchmark-Vergleich Chart
        benchmark_group = QGroupBox("Benchmark-Vergleich")
        benchmark_layout = QVBoxLayout(benchmark_group)

        self.benchmark_canvas = FigureCanvas(Figure(figsize=(10, 5)))
        benchmark_layout.addWidget(self.benchmark_canvas)

        layout.addWidget(benchmark_group)

        # Performance-Zusammenfassung
        summary_group = QGroupBox("Performance-Zusammenfassung")
        summary_layout = QVBoxLayout(summary_group)

        self.benchmark_summary = QTextEdit()
        self.benchmark_summary.setReadOnly(True)
        self.benchmark_summary.setMaximumHeight(120)
        summary_layout.addWidget(self.benchmark_summary)

        layout.addWidget(summary_group)

        return widget

    def load_initial_data(self):
        """Lädt initiale Daten"""
        # Verzögere initiales Laden um UI nicht zu blockieren
        QTimer.singleShot(500, self.refresh_all_data)

    def get_period_days(self) -> int:
        """Gibt die gewählte Periodenanzahl zurück"""
        period_text = self.period_combo.currentText()
        if period_text == "Alle":
            return 36500  # 100 Jahre - praktisch alle Daten
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
                # Speichere Daten für Export
                self.current_data = trends

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

                # Neue Tabs aktualisieren
                self.viz_sequence_combo.clear()
                self.viz_sequence_combo.addItem("Alle Sequenzen", None)
                for seq in sequences:
                    self.viz_sequence_combo.addItem(seq, seq)

                # Aktualisiere neue Features
                self.update_data_quality()
                self.update_benchmarks()
                self.update_stats_visualization()

            elif trends['status'] == 'no_data':
                # Zeige Info-Nachricht nur beim ersten Mal
                if not hasattr(self, '_no_data_shown'):
                    self._no_data_shown = True
                    QMessageBox.information(
                        self,
                        "Keine Daten",
                        f"{trends.get('message', 'Keine Daten verfügbar')}\n\n"
                        "Führen Sie erst einige Tests durch, um Analytics zu sehen."
                    )
                # Setze KPIs auf 0
                self.reset_kpis()
            else:
                # Anderer Fehler
                QMessageBox.warning(
                    self,
                    "Problem",
                    trends.get('message', 'Unbekannter Fehler beim Laden der Daten')
                )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Laden der Analytics-Daten:\n\n{str(e)}\n\n"
                "Details siehe Log-Datei."
            )
            print(f"Analytics Dashboard Error:\n{error_details}")

    def reset_kpis(self):
        """Setzt alle KPIs auf Standardwerte zurück"""
        self.kpi_total_runs.update_value("0")
        self.kpi_success_rate.update_value("N/A")
        self.kpi_avg_cycle_time.update_value("N/A")
        self.kpi_stability.update_value("N/A")
        self.kpi_degradation.update_value("N/A")
        self.kpi_anomaly_rate.update_value("N/A")
        self.kpi_best_performance.update_value("N/A")
        self.kpi_risk_score.update_value("0/100")

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

        fig = self.timeline_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if not timeline:
            # Zeige leeren Chart mit Hinweis
            ax.text(0.5, 0.5, 'Keine Daten verfügbar\n\nFühren Sie Tests durch um Daten zu sammeln',
                    ha='center', va='center', fontsize=12, color='gray',
                    transform=ax.transAxes)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            fig.tight_layout()
            self.timeline_canvas.draw()
            return

        try:
            # Extrahiere Daten
            timestamps = []
            cycle_times = []

            for t in timeline:
                try:
                    ts = parse_timestamp(t['timestamp'])
                    timestamps.append(ts)
                    cycle_times.append(t['avg_cycle_time'])
                except (ValueError, KeyError) as e:
                    # Überspringe ungültige Einträge
                    continue

            if not timestamps:
                # Keine gültigen Daten
                ax.text(0.5, 0.5, 'Keine gültigen Zeitstempel gefunden',
                        ha='center', va='center', fontsize=12, color='orange',
                        transform=ax.transAxes)
                ax.axis('off')
                fig.tight_layout()
                self.timeline_canvas.draw()
                return

            # Plot
            ax.plot(timestamps, cycle_times, marker='o', linestyle='-', linewidth=2, markersize=4, color='#27ae60')
            ax.set_xlabel('Zeitpunkt')
            ax.set_ylabel('Durchschnittliche Zykluszeit (ms)')
            ax.set_title('Performance Timeline')
            ax.grid(True, alpha=0.3)

            fig.tight_layout()
            self.timeline_canvas.draw()

        except Exception as e:
            # Fehler beim Plotten
            ax.text(0.5, 0.5, f'Fehler beim Erstellen des Charts:\n{str(e)}',
                    ha='center', va='center', fontsize=10, color='red',
                    transform=ax.transAxes)
            ax.axis('off')
            fig.tight_layout()
            self.timeline_canvas.draw()
            print(f"Timeline Chart Error: {e}")

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

            timestamps = []
            cycle_times = []
            for t in timeline:
                try:
                    timestamps.append(parse_timestamp(t['timestamp']))
                    cycle_times.append(t['avg_cycle_time'])
                except (ValueError, KeyError):
                    # Überspringe ungültige Einträge
                    continue

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
        dates = []
        predicted = []
        lower = []
        upper = []
        for p in predictions:
            try:
                dates.append(parse_timestamp(p['date']))
                predicted.append(p['predicted_cycle_time'])
                lower.append(p['lower_bound'])
                upper.append(p['upper_bound'])
            except (ValueError, KeyError):
                # Überspringe ungültige Einträge
                continue

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

    # ==================== NEUE FUNKTIONEN ====================

    def show_settings_dialog(self):
        """Zeigt den Einstellungs-Dialog"""
        dialog = AnalyticsSettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()

            # Wende neue Einstellungen an
            if self.settings['auto_refresh']:
                self.refresh_timer.start(self.settings['refresh_interval'] * 1000)
            else:
                self.refresh_timer.stop()

            # Chart-Stil anwenden
            plt.style.use(self.settings['chart_style'])

            # Daten neu laden
            self.refresh_all_data()

    def show_filter_dialog(self):
        """Zeigt den Filter-Dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Daten-Filter")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        # Sequenz-Filter
        sequence_filter = QComboBox()
        sequence_filter.addItem("Alle Sequenzen", None)
        if hasattr(self, 'prediction_sequence_combo'):
            for i in range(self.prediction_sequence_combo.count()):
                text = self.prediction_sequence_combo.itemText(i)
                sequence_filter.addItem(text, text)
        form.addRow("Sequenz:", sequence_filter)

        # Status-Filter
        status_filter = QComboBox()
        status_filter.addItems(["Alle", "Abgeschlossen", "Fehler", "Abgebrochen"])
        form.addRow("Status:", status_filter)

        # Datums-Filter
        start_date = QDateEdit()
        start_date.setCalendarPopup(True)
        start_date.setDate(QDate.currentDate().addDays(-30))
        form.addRow("Von:", start_date)

        end_date = QDateEdit()
        end_date.setCalendarPopup(True)
        end_date.setDate(QDate.currentDate())
        form.addRow("Bis:", end_date)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()

        clear_btn = QPushButton("Filter löschen")
        clear_btn.clicked.connect(lambda: self.clear_filters())
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Anwenden")
        apply_btn.clicked.connect(lambda: self.apply_filters({
            'sequence': sequence_filter.currentData(),
            'status': status_filter.currentText() if status_filter.currentText() != "Alle" else None,
            'start_date': start_date.date().toPyDate(),
            'end_date': end_date.date().toPyDate()
        }))
        apply_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def clear_filters(self):
        """Löscht alle Filter"""
        self.filter_settings = {
            'sequence': None,
            'status': None,
            'start_date': None,
            'end_date': None
        }
        self.refresh_all_data()

    def apply_filters(self, filters: dict):
        """Wendet Filter an"""
        self.filter_settings = filters
        self.refresh_all_data()

    def show_export_menu(self):
        """Zeigt Export-Optionen"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QCursor

        menu = QMenu(self)
        menu.addAction("📄 CSV Export", self.export_to_csv)
        menu.addAction("📋 JSON Export", self.export_to_json)
        menu.addAction("📊 Chart als PNG", self.export_chart_png)
        menu.addAction("📑 Vollständiger Report", self.export_full_report)

        menu.exec(QCursor.pos())

    def export_to_csv(self):
        """Exportiert Daten als CSV"""
        if not self.current_data:
            QMessageBox.warning(self, "Keine Daten", "Keine Daten zum Exportieren verfügbar")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "CSV Export", "", "CSV Dateien (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Header
                writer.writerow(['Timestamp', 'Run ID', 'Sequenz', 'Duration', 'Cycles', 'Status', 'Avg Cycle Time'])

                # Daten
                for item in self.current_data.get('timeline', []):
                    writer.writerow([
                        item.get('timestamp', ''),
                        item.get('run_id', ''),
                        item.get('sequence', ''),
                        item.get('duration', ''),
                        item.get('cycles', ''),
                        item.get('status', ''),
                        item.get('avg_cycle_time', '')
                    ])

            QMessageBox.information(self, "Export erfolgreich", f"Daten wurden nach {file_path} exportiert")

        except Exception as e:
            QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Exportieren:\n{str(e)}")

    def export_to_json(self):
        """Exportiert Daten als JSON"""
        if not self.current_data:
            QMessageBox.warning(self, "Keine Daten", "Keine Daten zum Exportieren verfügbar")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSON Export", "", "JSON Dateien (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.current_data, jsonfile, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Export erfolgreich", f"Daten wurden nach {file_path} exportiert")

        except Exception as e:
            QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Exportieren:\n{str(e)}")

    def export_chart_png(self):
        """Exportiert aktuelles Chart als PNG"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Chart Export", "", "PNG Dateien (*.png)"
        )

        if not file_path:
            return

        try:
            # Exportiere Chart vom aktiven Tab
            current_tab_index = self.tabs.currentIndex()
            canvas = None

            if current_tab_index == 0:  # Übersicht
                canvas = self.timeline_canvas
            elif current_tab_index == 1:  # Trends
                canvas = self.trend_canvas
            elif current_tab_index == 3:  # Vorhersage
                canvas = self.prediction_canvas
            elif current_tab_index == 4:  # Korrelation
                canvas = self.heatmap_canvas

            if canvas:
                canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Export erfolgreich", f"Chart wurde nach {file_path} exportiert")
            else:
                QMessageBox.warning(self, "Kein Chart", "Kein Chart zum Exportieren im aktuellen Tab")

        except Exception as e:
            QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Exportieren:\n{str(e)}")

    def export_full_report(self):
        """Erstellt einen vollständigen Analytics-Report"""
        if not self.current_data:
            QMessageBox.warning(self, "Keine Daten", "Keine Daten zum Exportieren verfügbar")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Report Export", "", "Text Dateien (*.txt)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("ANALYTICS REPORT - Arduino Control Panel\n")
                f.write("=" * 80 + "\n\n")

                f.write(f"Zeitraum: {self.period_combo.currentText()}\n")
                f.write(f"Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("-" * 80 + "\n")
                f.write("ZUSAMMENFASSUNG\n")
                f.write("-" * 80 + "\n")
                f.write(f"Gesamt-Läufe: {self.current_data.get('total_runs', 0)}\n")

                trends = self.current_data.get('trends', {})
                if trends.get('status') == 'calculated':
                    f.write(f"Trend-Richtung: {trends.get('trend_direction', 'N/A').upper()}\n")
                    f.write(f"Trend-Schweregrad: {trends.get('trend_severity', 'N/A').upper()}\n")
                    f.write(f"Relative Änderung: {trends.get('relative_slope_percent', 0):.2f}%\n")

                f.write("\n" + "-" * 80 + "\n")
                f.write("DEGRADATION ALERTS\n")
                f.write("-" * 80 + "\n")

                alerts = self.current_data.get('degradation_alerts', [])
                if alerts:
                    for alert in alerts:
                        f.write(f"\n• {alert['sequence']}\n")
                        f.write(f"  Typ: {alert['type'].upper()}\n")
                        f.write(f"  Änderung: {alert['change_percent']:.1f}%\n")
                        f.write(f"  {alert['message']}\n")
                else:
                    f.write("\nKeine Alerts\n")

                f.write("\n" + "=" * 80 + "\n")

            QMessageBox.information(self, "Export erfolgreich", f"Report wurde nach {file_path} exportiert")

        except Exception as e:
            QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Exportieren:\n{str(e)}")

    def update_stats_visualization(self):
        """Aktualisiert die Statistik-Visualisierung"""
        if not self.current_data:
            return

        viz_type = self.viz_type_combo.currentText()
        sequence = self.viz_sequence_combo.currentData()

        # Extrahiere Daten
        timeline = self.current_data.get('timeline', [])
        cycle_times = []

        for item in timeline:
            if sequence and item.get('sequence') != sequence:
                continue
            if item.get('avg_cycle_time', 0) > 0:
                cycle_times.append(item['avg_cycle_time'])

        if not cycle_times:
            return

        # Chart 1: Hauptvisualisierung
        fig = self.stats_viz_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if viz_type == "Histogramm":
            ax.hist(cycle_times, bins=min(30, len(cycle_times)//2), alpha=0.7, edgecolor='black')
            ax.set_xlabel('Zykluszeit (ms)')
            ax.set_ylabel('Häufigkeit')
            ax.set_title('Verteilung der Zykluszeiten')
            ax.axvline(np.mean(cycle_times), color='r', linestyle='--', label=f'Durchschnitt: {np.mean(cycle_times):.2f} ms')
            ax.legend()

        elif viz_type == "Box-Plot":
            ax.boxplot(cycle_times, vert=True)
            ax.set_ylabel('Zykluszeit (ms)')
            ax.set_title('Box-Plot der Zykluszeiten')
            ax.grid(True, alpha=0.3)

        elif viz_type == "Violin-Plot":
            parts = ax.violinplot([cycle_times], vert=True, showmeans=True, showmedians=True)
            ax.set_ylabel('Zykluszeit (ms)')
            ax.set_title('Violin-Plot der Zykluszeiten')
            ax.grid(True, alpha=0.3)

        elif viz_type == "Scatter-Matrix":
            # Für Scatter-Matrix brauchen wir mehrere Variablen
            durations = [item.get('duration', 0) for item in timeline if sequence is None or item.get('sequence') == sequence]
            cycles = [item.get('cycles', 0) for item in timeline if sequence is None or item.get('sequence') == sequence]

            if len(cycle_times) == len(durations) and len(cycle_times) == len(cycles):
                ax.scatter(durations, cycle_times, alpha=0.6)
                ax.set_xlabel('Duration (s)')
                ax.set_ylabel('Zykluszeit (ms)')
                ax.set_title('Scatter: Duration vs Zykluszeit')
                ax.grid(True, alpha=0.3)

        fig.tight_layout()
        self.stats_viz_canvas.draw()

        # Chart 2: Statistik-Informationen
        fig2 = self.stats_viz_canvas2.figure
        fig2.clear()
        ax2 = fig2.add_subplot(111)

        # Textuelle Statistiken
        stats_text = f"""
Statistik-Zusammenfassung:
  • Anzahl: {len(cycle_times)}
  • Mittelwert: {np.mean(cycle_times):.2f} ms
  • Median: {np.median(cycle_times):.2f} ms
  • Std.Abw.: {np.std(cycle_times):.2f} ms
  • Min: {np.min(cycle_times):.2f} ms
  • Max: {np.max(cycle_times):.2f} ms
  • 25% Perzentil: {np.percentile(cycle_times, 25):.2f} ms
  • 75% Perzentil: {np.percentile(cycle_times, 75):.2f} ms
        """

        ax2.text(0.1, 0.5, stats_text, transform=ax2.transAxes, fontsize=11, verticalalignment='center', family='monospace')
        ax2.axis('off')

        fig2.tight_layout()
        self.stats_viz_canvas2.draw()

    def update_data_quality(self):
        """Aktualisiert Datenqualitäts-Metriken"""
        if not self.current_data:
            return

        timeline = self.current_data.get('timeline', [])
        if not timeline:
            return

        # Vollständigkeit
        complete_records = sum(1 for item in timeline if item.get('avg_cycle_time', 0) > 0)
        completeness = (complete_records / len(timeline) * 100) if timeline else 0
        self.quality_completeness.update_value(f"{completeness:.1f}%",
            "#27ae60" if completeness >= 90 else "#f39c12" if completeness >= 70 else "#e74c3c")

        # Genauigkeit (basierend auf Anomalien)
        alerts = self.current_data.get('degradation_alerts', [])
        accuracy = max(0, 100 - len(alerts) * 5)
        self.quality_accuracy.update_value(f"{accuracy:.1f}%",
            "#27ae60" if accuracy >= 90 else "#f39c12" if accuracy >= 70 else "#e74c3c")

        # Konsistenz (basierend auf Stabilität)
        trends = self.current_data.get('trends', {})
        if trends.get('status') == 'calculated':
            consistency = 100 - abs(trends.get('relative_slope_percent', 0))
            consistency = max(0, min(100, consistency))
            self.quality_consistency.update_value(f"{consistency:.1f}%",
                "#27ae60" if consistency >= 90 else "#f39c12" if consistency >= 70 else "#e74c3c")

        # Aktualität (basierend auf letztem Eintrag)
        if timeline:
            try:
                last_timestamp = parse_timestamp(timeline[-1]['timestamp'])
                age_hours = (datetime.now() - last_timestamp).total_seconds() / 3600
                timeliness = max(0, 100 - age_hours)
                timeliness = min(100, timeliness)
                self.quality_timeliness.update_value(f"{timeliness:.1f}%",
                    "#27ae60" if timeliness >= 80 else "#f39c12" if timeliness >= 50 else "#e74c3c")
            except:
                self.quality_timeliness.update_value("N/A")

        # Outlier Detection
        cycle_times = [item.get('avg_cycle_time', 0) for item in timeline if item.get('avg_cycle_time', 0) > 0]
        if len(cycle_times) > 2:
            mean = np.mean(cycle_times)
            std = np.std(cycle_times)
            threshold = self.settings['anomaly_threshold']

            outliers = []
            for i, item in enumerate(timeline):
                ct = item.get('avg_cycle_time', 0)
                if ct > 0:
                    z_score = abs((ct - mean) / std) if std > 0 else 0
                    if z_score > threshold:
                        deviation = ((ct - mean) / mean * 100) if mean > 0 else 0
                        outliers.append({
                            'run_id': item.get('run_id', 'N/A'),
                            'sequence': item.get('sequence', 'N/A'),
                            'value': ct,
                            'deviation': deviation,
                            'z_score': z_score
                        })

            # Outlier-Tabelle aktualisieren
            self.outlier_table.setRowCount(len(outliers))
            for i, outlier in enumerate(outliers):
                self.outlier_table.setItem(i, 0, QTableWidgetItem(str(outlier['run_id'])))
                self.outlier_table.setItem(i, 1, QTableWidgetItem(outlier['sequence']))
                self.outlier_table.setItem(i, 2, QTableWidgetItem(f"{outlier['value']:.2f} ms"))
                self.outlier_table.setItem(i, 3, QTableWidgetItem(f"{outlier['deviation']:.1f}%"))

                z_item = QTableWidgetItem(f"{outlier['z_score']:.2f}")
                if outlier['z_score'] > 3:
                    z_item.setBackground(QColor("#e74c3c"))
                else:
                    z_item.setBackground(QColor("#f39c12"))
                self.outlier_table.setItem(i, 4, z_item)

        # Report
        report_text = f"""
Datenqualitäts-Report:
• Vollständigkeit: {completeness:.1f}% - {'Gut' if completeness >= 90 else 'Verbesserungswürdig'}
• {len([item for item in timeline if item.get('avg_cycle_time', 0) > 0])} von {len(timeline)} Records haben gültige Daten
• {len(outliers) if 'outliers' in locals() else 0} Ausreißer gefunden (>{threshold}σ)
• Letzte Aktualisierung: {timeline[-1].get('timestamp', 'N/A') if timeline else 'N/A'}
        """
        self.quality_report.setText(report_text)

    def update_benchmarks(self):
        """Aktualisiert Benchmark-Metriken"""
        if not self.current_data:
            return

        trends = self.current_data.get('trends', {})
        if trends.get('status') != 'calculated':
            return

        # SLA-Tabelle aktualisieren
        avg_cycle_time = trends.get('avg_cycle_time', 0)

        # Ø Zykluszeit
        status = "✅" if avg_cycle_time < 100 else "⚠️" if avg_cycle_time < 150 else "❌"
        self.sla_table.setItem(0, 2, QTableWidgetItem(f"{avg_cycle_time:.2f} ms"))
        self.sla_table.setItem(0, 3, QTableWidgetItem(status))

        # Erfolgsrate
        daily = self.current_data.get('daily_summary', [])
        if daily:
            avg_success = np.mean([d['success_rate'] for d in daily])
            status = "✅" if avg_success >= 95 else "⚠️" if avg_success >= 85 else "❌"
            self.sla_table.setItem(1, 2, QTableWidgetItem(f"{avg_success:.1f}%"))
            self.sla_table.setItem(1, 3, QTableWidgetItem(status))

        # Stabilität
        std_ct = trends.get('std_cycle_time', 0)
        stability = max(0, 100 - (std_ct / avg_cycle_time * 100 if avg_cycle_time > 0 else 100))
        status = "✅" if stability >= 90 else "⚠️" if stability >= 80 else "❌"
        self.sla_table.setItem(2, 2, QTableWidgetItem(f"{stability:.1f}%"))
        self.sla_table.setItem(2, 3, QTableWidgetItem(status))

        # Anomalie-Rate
        alerts = self.current_data.get('degradation_alerts', [])
        sequences = self.current_data.get('sequence_performance', {})
        anomaly_rate = (len(alerts) / len(sequences) * 100) if sequences else 0
        status = "✅" if anomaly_rate < 5 else "⚠️" if anomaly_rate < 10 else "❌"
        self.sla_table.setItem(3, 2, QTableWidgetItem(f"{anomaly_rate:.1f}%"))
        self.sla_table.setItem(3, 3, QTableWidgetItem(status))

        # Degradation
        rel_slope = abs(trends.get('relative_slope_percent', 0))
        status = "✅" if rel_slope < 3 else "⚠️" if rel_slope < 5 else "❌"
        sign = "+" if trends.get('relative_slope_percent', 0) > 0 else ""
        self.sla_table.setItem(4, 2, QTableWidgetItem(f"{sign}{trends.get('relative_slope_percent', 0):.1f}%"))
        self.sla_table.setItem(4, 3, QTableWidgetItem(status))

        # Benchmark-Chart
        fig = self.benchmark_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        metrics = ['Zykluszeit', 'Erfolgsrate', 'Stabilität', 'Anomalie-Rate', 'Degradation']
        targets = [100, 95, 90, 5, 3]
        actuals = [
            min(100, (100 / avg_cycle_time * 100) if avg_cycle_time > 0 else 0),
            avg_success if daily else 0,
            stability,
            min(100, 100 - anomaly_rate),
            min(100, 100 - rel_slope)
        ]

        x = np.arange(len(metrics))
        width = 0.35

        ax.bar(x - width/2, targets, width, label='Ziel', alpha=0.7, color='#27ae60')
        ax.bar(x + width/2, actuals, width, label='Aktuell', alpha=0.7, color='#3498db')

        ax.set_ylabel('Score (%)')
        ax.set_title('Benchmark-Vergleich: Ziel vs Aktuell')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, rotation=15, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        fig.tight_layout()
        self.benchmark_canvas.draw()

        # Zusammenfassung
        passed = sum(1 for i in range(5) if self.sla_table.item(i, 3).text() == "✅")
        summary = f"""
Performance-Zusammenfassung:
  • SLA-Erfüllung: {passed}/5 Metriken erfüllt ({passed/5*100:.0f}%)
  • Gesamtbewertung: {'BESTANDEN ✅' if passed >= 4 else 'VERBESSERUNG NÖTIG ⚠️' if passed >= 3 else 'NICHT BESTANDEN ❌'}
  • Kritische Metriken: {5-passed} unter Zielwert
  • Empfehlung: {'Exzellente Performance - weiter so!' if passed >= 4 else 'Optimierung empfohlen' if passed >= 3 else 'Dringende Optimierung erforderlich'}
        """
        self.benchmark_summary.setText(summary)
