# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                             QPushButton, QGroupBox, QSplitter, QProgressBar, QListWidgetItem, QStackedWidget, QGridLayout)
from PyQt6.QtCore import pyqtSignal, Qt

from .visual_editor.editor_widget import VisualEditorWidget

class SequenceTab(QWidget):
    """Der komplette UI-Tab für die Verwaltung und Steuerung von Sequenzen."""
    
    start_sequence_signal = pyqtSignal(str)
    start_test_run_signal = pyqtSignal(str)
    stop_sequence_signal = pyqtSignal()
    pause_sequence_signal = pyqtSignal()
    new_sequence_signal = pyqtSignal()
    edit_sequence_signal = pyqtSignal(str)
    delete_sequence_signal = pyqtSignal(str)
    sequence_updated_signal = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        toolbar_layout = QHBoxLayout()
        self.view_toggle_btn = QPushButton("🎨 Zum visuellen Editor wechseln")
        self.view_toggle_btn.clicked.connect(self.toggle_view)
        toolbar_layout.addWidget(self.view_toggle_btn)
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.list_view_widget = self._create_list_view()
        self.list_view_widget.setObjectName("ListView") # Wichtig für den Wechsel
        self.stacked_widget.addWidget(self.list_view_widget)

        self.visual_editor_widget = VisualEditorWidget()
        self.stacked_widget.addWidget(self.visual_editor_widget)
        
        self.visual_editor_widget.sequence_saved.connect(self.on_sequence_saved)

    def on_sequence_saved(self, seq_id, sequence_data):
        """Wird aufgerufen, wenn im visuellen Editor gespeichert wird."""
        self.sequence_updated_signal.emit(seq_id, sequence_data)
        self.stacked_widget.setCurrentWidget(self.list_view_widget)
        self.view_toggle_btn.setText("🎨 Zum visuellen Editor wechseln")

    def _create_list_view(self):
        # ... (Implementation unchanged)
        list_view_container = QWidget()
        main_layout = QHBoxLayout(list_view_container)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        seq_list_group = QGroupBox("Verfügbare Sequenzen")
        seq_list_layout = QVBoxLayout(seq_list_group)
        self.seq_list = QListWidget()
        self.seq_list.itemDoubleClicked.connect(self._on_edit_sequence)
        seq_list_layout.addWidget(self.seq_list)
        
        seq_btn_layout = QHBoxLayout()
        new_btn = QPushButton("➕ Neu"); new_btn.clicked.connect(self.new_sequence_signal.emit)
        edit_btn = QPushButton("✏️ Bearbeiten"); edit_btn.clicked.connect(self._on_edit_sequence)
        del_btn = QPushButton("🗑️ Löschen"); del_btn.clicked.connect(self._on_delete_sequence)
        seq_btn_layout.addWidget(new_btn); seq_btn_layout.addWidget(edit_btn); seq_btn_layout.addWidget(del_btn)
        seq_list_layout.addLayout(seq_btn_layout)
        left_layout.addWidget(seq_list_group)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        info_group = self._create_info_group()
        trend_group = self._create_trend_group()
        control_group = self._create_control_group()
        
        right_layout.addWidget(control_group)
        right_layout.addWidget(info_group)
        right_layout.addWidget(trend_group)
        right_layout.addStretch()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)
        return list_view_container


    def toggle_view(self):
        if self.stacked_widget.currentWidget() == self.list_view_widget:
            seq_id = self._get_selected_seq_id()
            if seq_id:
                self.edit_sequence_signal.emit(seq_id)
            else:
                QMessageBox.warning(self, "Auswahl erforderlich", "Bitte wählen Sie zuerst eine Sequenz aus, um sie im visuellen Editor zu bearbeiten.")
        else:
            self.stacked_widget.setCurrentWidget(self.list_view_widget)
            self.view_toggle_btn.setText("🎨 Zum visuellen Editor wechseln")

    def open_visual_editor_for_sequence(self, seq_id, sequence_data):
        self.visual_editor_widget.load_sequence(seq_id, sequence_data)
        self.stacked_widget.setCurrentWidget(self.visual_editor_widget)
        self.view_toggle_btn.setText("📜 Zur Listenansicht wechseln")

    def highlight_step(self, step_index):
        """NEU: Slot, der das Highlighting an den Editor weitergibt."""
        self.visual_editor_widget.highlight_step(step_index)

    def _create_control_group(self):
        # ... (Implementation unchanged)
        group = QGroupBox("Ablaufsteuerung")
        layout = QVBoxLayout(group)
        self.start_btn = QPushButton("▶️ Sequenz starten"); self.start_btn.clicked.connect(self._on_start_sequence)
        self.pause_btn = QPushButton("⏸️ Pausieren / Fortsetzen"); self.pause_btn.clicked.connect(self.pause_sequence_signal.emit)
        self.stop_btn = QPushButton("⏹️ Stoppen"); self.stop_btn.clicked.connect(self.stop_sequence_signal.emit)
        self.test_btn = QPushButton("🔬 Testlauf starten"); self.test_btn.setStyleSheet("background-color: #27ae60;")
        self.test_btn.clicked.connect(self._on_start_test_run)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.test_btn)
        
        self.set_running_state(False)
        return group


    def _create_info_group(self):
        # ... (Implementation unchanged)
        group = QGroupBox("Laufzeit-Informationen")
        layout = QGridLayout(group)
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
        
        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar, 7, 0, 1, 2)
        return group


    def _create_trend_group(self):
        # ... (Implementation unchanged)
        group = QGroupBox("Live-Analyse (Zykluszeiten)")
        layout = QVBoxLayout(group)
        self.trend_labels = {"trend": QLabel("Trend: -"), "stability": QLabel("Stabilität: -"), "anomalies": QLabel("Anomalien: -")}
        for label in self.trend_labels.values():
            layout.addWidget(label)
        return group

        
    def update_trend_info(self, analysis):
        # ... (Implementation unchanged)
        cycle_analysis = analysis.get('cycle_analysis', {})
        trend = cycle_analysis.get('trend', 'insufficient_data')
        stability = cycle_analysis.get('stability', 0)
        anomalies = cycle_analysis.get('anomalies', [])

        trend_icons = {"stable": "➡️", "increasing": "⬆️", "decreasing": "⬇️"}
        self.trend_labels["trend"].setText(f"Trend: {trend_icons.get(trend, '⏳')} {trend}")
        self.trend_labels["stability"].setText(f"Stabilität: {stability:.1f}%")
        self.trend_labels["anomalies"].setText(f"Anomalien: {len(anomalies)}")


    def update_sequence_info(self, info):
        # ... (Implementation unchanged)
        self.info_labels["status"].setText("Läuft...")
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


    def update_sequence_list(self, sequences):
        # ... (Implementation unchanged)
        current_selection = self._get_selected_seq_id()
        self.seq_list.clear()
        for seq_id, seq_data in sequences.items():
            item = QListWidgetItem(seq_data["name"])
            item.setData(Qt.ItemDataRole.UserRole, seq_id)
            self.seq_list.addItem(item)
            if seq_id == current_selection:
                self.seq_list.setCurrentItem(item)

    
    def set_running_state(self, is_running):
        # ... (Implementation unchanged)
        self.start_btn.setEnabled(not is_running)
        self.test_btn.setEnabled(not is_running)
        self.pause_btn.setEnabled(is_running)
        self.stop_btn.setEnabled(is_running)
        if not is_running:
            self.info_labels["status"].setText("Gestoppt")
            self.progress_bar.setValue(0)


    def _get_selected_seq_id(self):
        item = self.seq_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_start_sequence(self):
        seq_id = self._get_selected_seq_id()
        if seq_id: self.start_sequence_signal.emit(seq_id)
        
    def _on_start_test_run(self):
        seq_id = self._get_selected_seq_id()
        if seq_id: self.start_test_run_signal.emit(seq_id)

    def _on_edit_sequence(self):
        seq_id = self._get_selected_seq_id()
        if seq_id: self.edit_sequence_signal.emit(seq_id)
        
    def _on_delete_sequence(self):
        seq_id = self._get_selected_seq_id()
        if seq_id: self.delete_sequence_signal.emit(seq_id)
