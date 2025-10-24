# -*- coding: utf-8 -*-
"""
Makro-System: Zeichne Aktionen auf und spiele sie ab
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QInputDialog, QMessageBox, QTextEdit, QComboBox,
                             QSpinBox, QCheckBox, QSplitter, QDialog, QFormLayout,
                             QDialogButtonBox, QLineEdit, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QColor
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

class EditActionDialog(QDialog):
    """Dialog zum Bearbeiten einer Makro-Aktion"""

    def __init__(self, action: 'MacroAction', parent=None):
        super().__init__(parent)
        self.action = action
        self.setWindowTitle("Aktion bearbeiten")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Form Layout
        form = QFormLayout()

        # Timestamp
        self.timestamp_spin = QDoubleSpinBox()
        self.timestamp_spin.setRange(0, 999999)
        self.timestamp_spin.setDecimals(3)
        self.timestamp_spin.setSuffix(" s")
        self.timestamp_spin.setValue(self.action.timestamp)
        form.addRow("Zeitstempel:", self.timestamp_spin)

        # Action Type
        self.type_combo = QComboBox()
        action_types = ["pin_write", "delay", "sensor_read", "sequence_start", "custom"]
        self.type_combo.addItems(action_types)
        if self.action.action_type in action_types:
            self.type_combo.setCurrentText(self.action.action_type)
        else:
            self.type_combo.addItem(self.action.action_type)
            self.type_combo.setCurrentText(self.action.action_type)
        form.addRow("Aktions-Typ:", self.type_combo)

        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setText(self.action.description)
        form.addRow("Beschreibung:", self.description_edit)

        # Parameters (JSON)
        self.parameters_edit = QTextEdit()
        self.parameters_edit.setMaximumHeight(150)
        params_json = json.dumps(self.action.parameters, indent=2)
        self.parameters_edit.setPlainText(params_json)
        form.addRow("Parameter (JSON):", self.parameters_edit)

        layout.addLayout(form)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_action(self) -> 'MacroAction':
        """Gibt die bearbeitete Aktion zurück"""
        try:
            parameters = json.loads(self.parameters_edit.toPlainText())
        except json.JSONDecodeError:
            parameters = self.action.parameters

        return MacroAction(
            timestamp=self.timestamp_spin.value(),
            action_type=self.type_combo.currentText(),
            parameters=parameters,
            description=self.description_edit.text()
        )


@dataclass
class MacroAction:
    """Eine einzelne Makro-Aktion"""
    timestamp: float
    action_type: str  # "pin_write", "delay", "sensor_read", etc.
    parameters: Dict[str, Any]
    description: str = ""

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'action_type': self.action_type,
            'parameters': self.parameters,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            timestamp=data['timestamp'],
            action_type=data['action_type'],
            parameters=data['parameters'],
            description=data.get('description', '')
        )


class Macro:
    """Ein vollständiges Makro mit mehreren Aktionen"""
    def __init__(self, name: str):
        self.name = name
        self.actions: List[MacroAction] = []
        self.created_at = time.time()
        self.description = ""
    
    def add_action(self, action: MacroAction):
        self.actions.append(action)
    
    def clear(self):
        self.actions.clear()
    
    def duration(self):
        """Gibt die Gesamtdauer des Makros zurück"""
        if not self.actions:
            return 0
        return self.actions[-1].timestamp - self.actions[0].timestamp
    
    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'actions': [a.to_dict() for a in self.actions]
        }
    
    @classmethod
    def from_dict(cls, data):
        macro = cls(data['name'])
        macro.description = data.get('description', '')
        macro.created_at = data.get('created_at', time.time())
        macro.actions = [MacroAction.from_dict(a) for a in data.get('actions', [])]
        return macro


class MacroRecorder(QWidget):
    """Makro-Recorder mit Aufzeichnung und Wiedergabe"""
    command_signal = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.macros: Dict[str, Macro] = {}
        self.current_macro = None
        self.recording = False
        self.playing = False
        self.record_start_time = 0
        
        # Playback
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.playback_step)
        self.playback_index = 0
        self.playback_start_time = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === LINKE SEITE: Makro-Liste ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Makro-Verwaltung
        manage_group = QGroupBox("📂 Makro-Bibliothek")
        manage_layout = QVBoxLayout(manage_group)
        
        # Liste der Makros
        self.macro_list = QListWidget()
        self.macro_list.itemClicked.connect(self.on_macro_selected)
        manage_layout.addWidget(self.macro_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        new_btn = QPushButton("➕ Neu")
        new_btn.clicked.connect(self.new_macro)
        btn_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("🗑️ Löschen")
        delete_btn.clicked.connect(self.delete_macro)
        btn_layout.addWidget(delete_btn)
        
        duplicate_btn = QPushButton("📋 Duplizieren")
        duplicate_btn.clicked.connect(self.duplicate_macro)
        btn_layout.addWidget(duplicate_btn)
        
        manage_layout.addLayout(btn_layout)
        
        # Import/Export
        io_layout = QHBoxLayout()
        
        export_btn = QPushButton("💾 Exportieren")
        export_btn.clicked.connect(self.export_macro)
        io_layout.addWidget(export_btn)
        
        import_btn = QPushButton("📂 Importieren")
        import_btn.clicked.connect(self.import_macro)
        io_layout.addWidget(import_btn)
        
        manage_layout.addLayout(io_layout)
        
        left_layout.addWidget(manage_group)
        
        # Makro-Info
        info_group = QGroupBox("ℹ️ Makro-Info")
        info_layout = QVBoxLayout(info_group)
        
        self.info_name = QLabel("--")
        self.info_name.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_layout.addWidget(self.info_name)
        
        self.info_actions = QLabel("Aktionen: 0")
        info_layout.addWidget(self.info_actions)
        
        self.info_duration = QLabel("Dauer: 0.0s")
        info_layout.addWidget(self.info_duration)
        
        self.info_created = QLabel("Erstellt: --")
        info_layout.addWidget(self.info_created)
        
        left_layout.addWidget(info_group)
        left_layout.addStretch()
        
        splitter.addWidget(left_widget)
        
        # === RECHTE SEITE: Recorder/Player ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Recorder-Steuerung
        recorder_group = QGroupBox("🎙️ Aufnahme")
        recorder_layout = QVBoxLayout(recorder_group)
        
        # Status
        status_layout = QHBoxLayout()
        
        self.status_indicator = QLabel("⚪")
        self.status_indicator.setStyleSheet("font-size: 32px;")
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(self.status_label, 1)
        
        recorder_layout.addLayout(status_layout)
        
        # Record-Buttons
        record_btn_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("🔴 Aufzeichnung starten")
        self.record_btn.clicked.connect(self.toggle_recording)
        record_btn_layout.addWidget(self.record_btn)
        
        self.stop_btn = QPushButton("⏹️ Stoppen")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        record_btn_layout.addWidget(self.stop_btn)
        
        recorder_layout.addLayout(record_btn_layout)
        
        # Aufnahme-Optionen
        options_layout = QHBoxLayout()
        
        self.record_delays_check = QCheckBox("Verzögerungen aufzeichnen")
        self.record_delays_check.setChecked(True)
        options_layout.addWidget(self.record_delays_check)
        
        options_layout.addStretch()
        recorder_layout.addLayout(options_layout)
        
        right_layout.addWidget(recorder_group)
        
        # Player-Steuerung
        player_group = QGroupBox("▶️ Wiedergabe")
        player_layout = QVBoxLayout(player_group)
        
        # Playback-Status
        playback_status = QHBoxLayout()
        
        self.playback_progress = QLabel("Fortschritt: 0%")
        playback_status.addWidget(self.playback_progress)
        
        self.playback_time = QLabel("Zeit: 0.0s / 0.0s")
        playback_status.addWidget(self.playback_time, 1)
        
        player_layout.addLayout(playback_status)
        
        # Play-Buttons
        play_btn_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️ Abspielen")
        self.play_btn.clicked.connect(self.play_macro)
        play_btn_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.clicked.connect(self.pause_playback)
        self.pause_btn.setEnabled(False)
        play_btn_layout.addWidget(self.pause_btn)
        
        self.stop_play_btn = QPushButton("⏹️ Stoppen")
        self.stop_play_btn.clicked.connect(self.stop_playback)
        self.stop_play_btn.setEnabled(False)
        play_btn_layout.addWidget(self.stop_play_btn)
        
        player_layout.addLayout(play_btn_layout)
        
        # Wiedergabe-Optionen
        play_options = QHBoxLayout()
        
        play_options.addWidget(QLabel("Geschwindigkeit:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1x", "2x", "4x"])
        self.speed_combo.setCurrentText("1x")
        play_options.addWidget(self.speed_combo)
        
        self.loop_check = QCheckBox("Endlos-Schleife")
        play_options.addWidget(self.loop_check)
        
        play_options.addStretch()
        player_layout.addLayout(play_options)
        
        right_layout.addWidget(player_group)
        
        # Aktions-Liste
        actions_group = QGroupBox("📜 Aktionen")
        actions_layout = QVBoxLayout(actions_group)
        
        self.action_list = QListWidget()
        actions_layout.addWidget(self.action_list)
        
        # Aktion bearbeiten
        edit_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️ Bearbeiten")
        edit_btn.clicked.connect(self.edit_action)
        edit_layout.addWidget(edit_btn)
        
        delete_action_btn = QPushButton("🗑️ Löschen")
        delete_action_btn.clicked.connect(self.delete_action)
        edit_layout.addWidget(delete_action_btn)
        
        insert_delay_btn = QPushButton("⏱️ Delay einfügen")
        insert_delay_btn.clicked.connect(self.insert_delay)
        edit_layout.addWidget(insert_delay_btn)
        
        actions_layout.addLayout(edit_layout)
        
        right_layout.addWidget(actions_group)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter)
        
        # Update-Timer für Playback-Anzeige
        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self.update_playback_ui)
        self.ui_update_timer.start(100)
    
    def new_macro(self):
        """Erstellt ein neues Makro"""
        name, ok = QInputDialog.getText(self, "Neues Makro", "Name:")
        if ok and name:
            if name in self.macros:
                QMessageBox.warning(self, "Fehler", "Ein Makro mit diesem Namen existiert bereits!")
                return
            
            macro = Macro(name)
            self.macros[name] = macro
            self.update_macro_list()
            self.select_macro(name)
    
    def delete_macro(self):
        """Löscht das ausgewählte Makro"""
        item = self.macro_list.currentItem()
        if not item:
            return
        
        name = item.text().split(" - ")[0]
        
        reply = QMessageBox.question(
            self, "Bestätigung",
            f"Möchten Sie das Makro '{name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.macros[name]
            self.update_macro_list()
            self.clear_info()
    
    def duplicate_macro(self):
        """Dupliziert das ausgewählte Makro"""
        item = self.macro_list.currentItem()
        if not item:
            return
        
        name = item.text().split(" - ")[0]
        original = self.macros[name]
        
        new_name, ok = QInputDialog.getText(self, "Makro duplizieren", "Neuer Name:", text=f"{name} (Kopie)")
        if ok and new_name:
            new_macro = Macro.from_dict(original.to_dict())
            new_macro.name = new_name
            self.macros[new_name] = new_macro
            self.update_macro_list()
    
    def toggle_recording(self):
        """Startet/Stoppt die Aufzeichnung"""
        if not self.recording:
            # Makro auswählen
            item = self.macro_list.currentItem()
            if not item:
                QMessageBox.warning(self, "Fehler", "Bitte wählen Sie zuerst ein Makro aus!")
                return
            
            name = item.text().split(" - ")[0]
            self.current_macro = self.macros[name]
            self.current_macro.clear()
            
            self.recording = True
            self.record_start_time = time.time()
            
            self.status_indicator.setText("🔴")
            self.status_label.setText("Aufnahme läuft...")
            self.record_btn.setText("⏸️ Pause")
            self.stop_btn.setEnabled(True)
        else:
            self.recording = False
            self.status_indicator.setText("⏸️")
            self.status_label.setText("Pausiert")
            self.record_btn.setText("🔴 Weiter aufnehmen")
    
    def stop_recording(self):
        """Stoppt die Aufzeichnung komplett"""
        self.recording = False
        self.record_start_time = 0
        
        self.status_indicator.setText("⚪")
        self.status_label.setText("Bereit")
        self.record_btn.setText("🔴 Aufzeichnung starten")
        self.stop_btn.setEnabled(False)
        
        self.update_action_list()
        self.update_info()
    
    def record_action(self, action_type: str, parameters: Dict[str, Any], description: str = ""):
        """Zeichnet eine Aktion auf"""
        if not self.recording or not self.current_macro:
            return
        
        timestamp = time.time() - self.record_start_time
        
        action = MacroAction(
            timestamp=timestamp,
            action_type=action_type,
            parameters=parameters,
            description=description
        )
        
        self.current_macro.add_action(action)
        self.update_action_list()
    
    def play_macro(self):
        """Spielt das ausgewählte Makro ab"""
        item = self.macro_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Makro aus!")
            return
        
        name = item.text().split(" - ")[0]
        macro = self.macros[name]
        
        if not macro.actions:
            QMessageBox.warning(self, "Fehler", "Dieses Makro enthält keine Aktionen!")
            return
        
        self.playing = True
        self.playback_index = 0
        self.playback_start_time = time.time()
        self.current_macro = macro
        
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_play_btn.setEnabled(True)
        
        self.playback_timer.start(10)  # 100 Hz
    
    def playback_step(self):
        """Führt einen Playback-Schritt aus"""
        if not self.playing or not self.current_macro:
            return
        
        # Geschwindigkeitsfaktor
        speed_text = self.speed_combo.currentText()
        speed = float(speed_text[:-1])
        
        elapsed = (time.time() - self.playback_start_time) * speed
        
        # Alle Aktionen ausführen, die fällig sind
        while self.playback_index < len(self.current_macro.actions):
            action = self.current_macro.actions[self.playback_index]
            
            if action.timestamp > elapsed:
                break
            
            # Aktion ausführen
            self.execute_action(action)
            
            # Highlight in Liste
            self.action_list.setCurrentRow(self.playback_index)
            
            self.playback_index += 1
        
        # Makro zu Ende?
        if self.playback_index >= len(self.current_macro.actions):
            if self.loop_check.isChecked():
                # Loop
                self.playback_index = 0
                self.playback_start_time = time.time()
            else:
                self.stop_playback()
    
    def execute_action(self, action: MacroAction):
        """Führt eine Makro-Aktion aus"""
        if action.action_type == "pin_write":
            self.command_signal.emit({
                'command': 'digital_write',
                'pin': action.parameters['pin'],
                'value': action.parameters['value']
            })
        elif action.action_type == "analog_write":
            self.command_signal.emit({
                'command': 'analog_write',
                'pin': action.parameters['pin'],
                'value': action.parameters['value']
            })
        elif action.action_type == "delay":
            # Delay wird durch Timing gehandhabt
            pass
    
    def pause_playback(self):
        """Pausiert die Wiedergabe"""
        self.playing = not self.playing
        
        if self.playing:
            self.pause_btn.setText("⏸️ Pause")
            self.playback_start_time = time.time() - (self.current_macro.actions[self.playback_index].timestamp if self.playback_index < len(self.current_macro.actions) else 0)
        else:
            self.pause_btn.setText("▶️ Weiter")
    
    def stop_playback(self):
        """Stoppt die Wiedergabe"""
        self.playing = False
        self.playback_timer.stop()
        self.playback_index = 0
        
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_play_btn.setEnabled(False)
        self.pause_btn.setText("⏸️ Pause")
        
        self.action_list.clearSelection()
    
    def update_playback_ui(self):
        """Aktualisiert die Playback-UI"""
        if not self.playing or not self.current_macro:
            return
        
        speed_text = self.speed_combo.currentText()
        speed = float(speed_text[:-1])
        elapsed = (time.time() - self.playback_start_time) * speed
        
        total_duration = self.current_macro.duration()
        progress = (elapsed / total_duration * 100) if total_duration > 0 else 0
        
        self.playback_progress.setText(f"Fortschritt: {progress:.1f}%")
        self.playback_time.setText(f"Zeit: {elapsed:.1f}s / {total_duration:.1f}s")
    
    def on_macro_selected(self, item):
        """Wird aufgerufen, wenn ein Makro ausgewählt wird"""
        name = item.text().split(" - ")[0]
        self.select_macro(name)
    
    def select_macro(self, name):
        """Wählt ein Makro aus und aktualisiert die Anzeigen"""
        if name not in self.macros:
            return
        
        macro = self.macros[name]
        self.current_macro = macro
        
        self.update_info()
        self.update_action_list()
    
    def update_macro_list(self):
        """Aktualisiert die Makro-Liste"""
        self.macro_list.clear()
        
        for name, macro in self.macros.items():
            item_text = f"{name} - {len(macro.actions)} Aktionen"
            self.macro_list.addItem(item_text)
    
    def update_info(self):
        """Aktualisiert die Makro-Info"""
        if not self.current_macro:
            self.clear_info()
            return
        
        self.info_name.setText(self.current_macro.name)
        self.info_actions.setText(f"Aktionen: {len(self.current_macro.actions)}")
        self.info_duration.setText(f"Dauer: {self.current_macro.duration():.1f}s")
        
        created_dt = QDateTime.fromSecsSinceEpoch(int(self.current_macro.created_at))
        self.info_created.setText(f"Erstellt: {created_dt.toString('dd.MM.yyyy hh:mm')}")
    
    def clear_info(self):
        """Löscht die Makro-Info"""
        self.info_name.setText("--")
        self.info_actions.setText("Aktionen: 0")
        self.info_duration.setText("Dauer: 0.0s")
        self.info_created.setText("Erstellt: --")
        self.action_list.clear()
    
    def update_action_list(self):
        """Aktualisiert die Aktions-Liste"""
        self.action_list.clear()
        
        if not self.current_macro:
            return
        
        for action in self.current_macro.actions:
            desc = action.description or f"{action.action_type}: {action.parameters}"
            item_text = f"[{action.timestamp:.2f}s] {desc}"
            self.action_list.addItem(item_text)
    
    def edit_action(self):
        """Bearbeitet die ausgewählte Aktion"""
        row = self.action_list.currentRow()
        if row < 0 or not self.current_macro:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie eine Aktion zum Bearbeiten aus")
            return

        if row >= len(self.current_macro.actions):
            return

        # Hole die aktuelle Aktion
        action = self.current_macro.actions[row]

        # Zeige Bearbeiten-Dialog
        dialog = EditActionDialog(action, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Übernehme die bearbeitete Aktion
            edited_action = dialog.get_action()
            self.current_macro.actions[row] = edited_action
            self.update_action_list()
            self.update_info()
            QMessageBox.information(self, "Erfolg", "Aktion wurde erfolgreich bearbeitet!")
    
    def delete_action(self):
        """Löscht die ausgewählte Aktion"""
        row = self.action_list.currentRow()
        if row >= 0 and self.current_macro:
            del self.current_macro.actions[row]
            self.update_action_list()
            self.update_info()
    
    def insert_delay(self):
        """Fügt ein Delay ein"""
        delay_ms, ok = QInputDialog.getInt(self, "Delay einfügen", "Verzögerung (ms):", 1000, 0, 60000, 100)
        if ok and self.current_macro:
            row = self.action_list.currentRow()
            if row < 0:
                row = len(self.current_macro.actions)
            
            timestamp = self.current_macro.actions[row].timestamp if row < len(self.current_macro.actions) else 0
            
            action = MacroAction(
                timestamp=timestamp,
                action_type='delay',
                parameters={'duration_ms': delay_ms},
                description=f"Delay {delay_ms}ms"
            )
            
            self.current_macro.actions.insert(row, action)
            self.update_action_list()
    
    def export_macro(self):
        """Exportiert ein Makro"""
        item = self.macro_list.currentItem()
        if not item:
            return
        
        name = item.text().split(" - ")[0]
        macro = self.macros[name]
        
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Makro exportieren",
            f"{name}.macro.json",
            "Makro (*.macro.json)"
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(macro.to_dict(), f, indent=2)
            
            QMessageBox.information(self, "Erfolg", f"Makro '{name}' wurde exportiert!")
    
    def import_macro(self):
        """Importiert ein Makro"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Makro importieren",
            "",
            "Makro (*.macro.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                macro = Macro.from_dict(data)
                
                # Name anpassen falls schon vorhanden
                original_name = macro.name
                counter = 1
                while macro.name in self.macros:
                    macro.name = f"{original_name} ({counter})"
                    counter += 1
                
                self.macros[macro.name] = macro
                self.update_macro_list()
                
                QMessageBox.information(self, "Erfolg", f"Makro '{macro.name}' wurde importiert!")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Import fehlgeschlagen:\n{e}")
