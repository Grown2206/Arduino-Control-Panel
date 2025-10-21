# -*- coding: utf-8 -*-
"""
ui/sensor_library_manager_tab.py
Tab zur Verwaltung der Sensorbibliothek (Hinzufügen/Bearbeiten/Löschen).
Speichert benutzerdefinierte Sensoren in user_sensor_library.json.
"""
import json
import os
import copy  # Für deepcopy
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                             QPushButton, QGridLayout, QLineEdit, QComboBox, QSpinBox,
                             QDoubleSpinBox, QTextEdit, QMessageBox, QSplitter,
                             QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QListWidgetItem, QApplication
                             )
from PyQt6.QtCore import Qt, pyqtSignal

# Importiere SensorDefinition und SensorType für Struktur und Typ-Auswahl
try:
    from sensor_library import SensorLibrary, SensorDefinition, SensorType
    SENSOR_LIB_AVAILABLE = True
except ImportError:
    print("WARNUNG (Sensor Manager): sensor_library.py nicht gefunden. Basis-Sensoren können nicht geladen werden.")
    SENSOR_LIB_AVAILABLE = False
    # Fallback-Klassen, damit der Manager zumindest startet

    class SensorDefinition:
        pass

    class SensorType:
        OTHER = "other"
        TEMPERATURE = "temperature"
        HUMIDITY = "humidity"

        @classmethod
        def __members__(cls):
            return {'OTHER': cls.OTHER, 'TEMPERATURE': cls.TEMPERATURE, 'HUMIDITY': cls.HUMIDITY}

        def __init__(self, value):
            self.value = value

    class SensorLibrary:
        SENSORS = {}

# Pfad zur JSON-Datei für benutzerdefinierte Sensoren
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
USER_SENSOR_FILE = os.path.join(parent_dir, "user_sensor_library.json")


class SensorLibraryManagerTab(QWidget):
    sensors_updated_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_sensors = {}
        self.user_sensors = {}
        self.selected_sensor_id = None
        self.is_new_sensor = False

        self.setup_ui()
        self.load_all_sensors()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- Linke Seite (Bibliothek) ---
        left_widget = QGroupBox("Sensorbibliothek")
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)

        self.sensor_list_widget = QListWidget()
        self.sensor_list_widget.currentItemChanged.connect(self.on_sensor_selected)
        left_layout.addWidget(self.sensor_list_widget)

        list_button_layout = QHBoxLayout()
        new_btn = QPushButton("➕ Neu")
        new_btn.clicked.connect(self.create_new_sensor)
        list_button_layout.addWidget(new_btn)

        copy_btn = QPushButton("📋 Kopieren")
        copy_btn.clicked.connect(self.copy_sensor)
        list_button_layout.addWidget(copy_btn)

        delete_btn = QPushButton("🗑️ Löschen")
        delete_btn.clicked.connect(self.delete_sensor)
        list_button_layout.addWidget(delete_btn)
        left_layout.addLayout(list_button_layout)

        # --- Rechte Seite (Editor) ---
        right_widget = QGroupBox("Sensor bearbeiten")
        right_layout = QVBoxLayout(right_widget)
        splitter.addWidget(right_widget)

        self.editor_form_layout = QGridLayout()
        right_layout.addLayout(self.editor_form_layout)

        self.editor_fields = {
            "id": QLineEdit(),
            "name": QLineEdit(),
            "sensor_type": QComboBox(),
            "protocol": QComboBox(),
            "value_range_min": QDoubleSpinBox(),
            "value_range_max": QDoubleSpinBox(),
            "unit": QLineEdit(),
            "icon": QLineEdit(),
            "description": QTextEdit(),
            "pins_table": QTableWidget()
        }

        # --- Formularfelder ---
        self.editor_form_layout.addWidget(QLabel("ID (Eindeutig):"), 0, 0)
        self.editor_form_layout.addWidget(self.editor_fields["id"], 0, 1)

        self.editor_form_layout.addWidget(QLabel("Name:"), 1, 0)
        self.editor_form_layout.addWidget(self.editor_fields["name"], 1, 1)

        self.editor_form_layout.addWidget(QLabel("Typ:"), 2, 0)
        if SENSOR_LIB_AVAILABLE and hasattr(SensorType, '__members__'):
            for member in SensorType:
                self.editor_fields["sensor_type"].addItem(member.value, member)
        else:
            self.editor_fields["sensor_type"].addItems(["temperature", "distance", "light", "motion", "other"])
        self.editor_form_layout.addWidget(self.editor_fields["sensor_type"], 2, 1)

        self.editor_form_layout.addWidget(QLabel("Protokoll:"), 3, 0)
        self.editor_fields["protocol"].addItems(["digital", "analog", "i2c", "spi", "onewire", "serial", "other"])
        self.editor_form_layout.addWidget(self.editor_fields["protocol"], 3, 1)

        range_layout = QHBoxLayout()
        self.editor_fields["value_range_min"].setRange(-1e9, 1e9)
        range_layout.addWidget(self.editor_fields["value_range_min"])
        range_layout.addWidget(QLabel("bis"))
        self.editor_fields["value_range_max"].setRange(-1e9, 1e9)
        range_layout.addWidget(self.editor_fields["value_range_max"])
        self.editor_form_layout.addWidget(QLabel("Wertebereich:"), 4, 0)
        self.editor_form_layout.addLayout(range_layout, 4, 1)

        self.editor_form_layout.addWidget(QLabel("Einheit:"), 5, 0)
        self.editor_form_layout.addWidget(self.editor_fields["unit"], 5, 1)

        self.editor_form_layout.addWidget(QLabel("Icon:"), 6, 0)
        self.editor_form_layout.addWidget(self.editor_fields["icon"], 6, 1)

        self.editor_form_layout.addWidget(QLabel("Beschreibung:"), 7, 0)
        self.editor_fields["description"].setFixedHeight(60)
        self.editor_form_layout.addWidget(self.editor_fields["description"], 7, 1)

        # --- Pin-Tabelle ---
        self.editor_form_layout.addWidget(QLabel("Benötigte Pins:"), 8, 0, Qt.AlignmentFlag.AlignTop)
        pins_table = self.editor_fields["pins_table"]
        pins_table.setColumnCount(2)
        pins_table.setHorizontalHeaderLabels(["Pin-Rolle", "Default Pin"])
        pins_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pins_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        pins_table.setFixedHeight(100)
        self.editor_form_layout.addWidget(pins_table, 8, 1)

        pin_button_layout = QHBoxLayout()
        add_pin_btn = QPushButton("➕ Pin hinzufügen")
        add_pin_btn.clicked.connect(self.add_pin_row)
        pin_button_layout.addWidget(add_pin_btn)
        remove_pin_btn = QPushButton("➖ Pin entfernen")
        remove_pin_btn.clicked.connect(self.remove_pin_row)
        pin_button_layout.addWidget(remove_pin_btn)
        pin_button_layout.addStretch()
        self.editor_form_layout.addLayout(pin_button_layout, 9, 1)

        right_layout.addStretch()
        save_btn = QPushButton("💾 Änderungen speichern")
        save_btn.clicked.connect(self.save_sensor)
        save_btn.setStyleSheet("background-color: #27ae60;")
        right_layout.addWidget(save_btn)

        splitter.setSizes([300, 500])
        self.set_editor_enabled(False)

    def load_all_sensors(self):
        self.current_sensors = {}
        self.user_sensors = {}
        self.selected_sensor_id = None
        self.sensor_list_widget.clear()
        self.clear_editor()
        self.set_editor_enabled(False)

        # Lade Basis-Sensoren
        if SENSOR_LIB_AVAILABLE:
            SensorLibrary.load_all_sensors(force_reload=False)
            all_loaded = SensorLibrary.get_all_sensors()
            for sensor_id, sensor_def in all_loaded.items():
                if isinstance(sensor_def, SensorDefinition) and not sensor_def.is_user:
                    self.current_sensors[sensor_id] = {'def': copy.deepcopy(sensor_def), 'is_user': False}

        # Lade Benutzer-Sensoren
        if os.path.exists(USER_SENSOR_FILE):
            try:
                with open(USER_SENSOR_FILE, 'r', encoding='utf-8') as f:
                    loaded_user_sensors_data = json.load(f)
                    if not isinstance(loaded_user_sensors_data, dict):
                        loaded_user_sensors_data = {}
                    for sensor_id, data in loaded_user_sensors_data.items():
                        user_def = SensorDefinition.from_dict(data) if SENSOR_LIB_AVAILABLE else self._dict_to_sensor_def(data)
                        if user_def:
                            self.user_sensors[sensor_id] = user_def
                            self.current_sensors[sensor_id] = {'def': user_def, 'is_user': True}
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler Laden {USER_SENSOR_FILE}:\n{e}")
        else:
            print(f"INFO: {USER_SENSOR_FILE} nicht gefunden.")

        # Fülle die Liste
        for sensor_id in sorted(self.current_sensors.keys()):
            sensor_data = self.current_sensors[sensor_id]
            sensor_def = sensor_data['def']
            icon = getattr(sensor_def, 'icon', '❓')
            name = getattr(sensor_def, 'name', 'Unbekannt')

            item_text = f"{icon} {name}"
            if sensor_data['is_user']:
                item_text += " [User]"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, sensor_id)
            self.sensor_list_widget.addItem(item)

    def _dict_to_sensor_def(self, data):
        """ Hilfsfunktion, um ein Dict in ein (Mock-)SensorDef-Objekt umzuwandeln. """
        if not isinstance(data, dict):
            return None
        # Mock-Objekt erstellen, falls SensorDefinition nicht verfügbar ist
        sensor_def = type('SensorDefMock', (object,), {})()
        sensor_def.id = data.get('id', '')
        sensor_def.name = data.get('name', 'Unbenannt')
        sensor_def.sensor_type = data.get('sensor_type', 'other')
        sensor_def.pins = data.get('pins', {})
        sensor_def.protocol = data.get('protocol', 'other')
        sensor_def.value_range = tuple(data.get('value_range', (0, 0)))
        sensor_def.unit = data.get('unit', '')
        sensor_def.icon = data.get('icon', '❓')
        sensor_def.description = data.get('description', '')
        sensor_def.is_user = True
        return sensor_def

    def _sensor_def_to_dict(self, sensor_def):
        """ Hilfsfunktion, um ein SensorDef-Objekt in ein serialisierbares Dict umzuwandeln. """
        if not sensor_def:
            return {}
        sensor_type_val = getattr(sensor_def, 'sensor_type', 'other')
        if SENSOR_LIB_AVAILABLE and isinstance(sensor_type_val, SensorType):
            sensor_type_val = sensor_type_val.value
        return {
            'id': getattr(sensor_def, 'id', ''),
            'name': getattr(sensor_def, 'name', ''),
            'sensor_type': sensor_type_val,
            'pins': getattr(sensor_def, 'pins', {}),
            'protocol': getattr(sensor_def, 'protocol', ''),
            'value_range': list(getattr(sensor_def, 'value_range', (0, 0))),
            'unit': getattr(sensor_def, 'unit', ''),
            'icon': getattr(sensor_def, 'icon', ''),
            'description': getattr(sensor_def, 'description', '')
        }

    def on_sensor_selected(self, current_item, previous_item):
        """ Wird aufgerufen, wenn ein Sensor in der Liste ausgewählt wird. """
        if not current_item:
            self.clear_editor()
            self.set_editor_enabled(False)
            self.selected_sensor_id = None
            return

        sensor_id = current_item.data(Qt.ItemDataRole.UserRole)
        if sensor_id in self.current_sensors:
            self.selected_sensor_id = sensor_id
            sensor_data = self.current_sensors[sensor_id]
            sensor_def = sensor_data['def']
            is_user = sensor_data['is_user']
            self.is_new_sensor = False

            # Fülle die Editor-Felder
            self.editor_fields["id"].setText(getattr(sensor_def, 'id', ''))
            self.editor_fields["id"].setReadOnly(True)
            self.editor_fields["name"].setText(getattr(sensor_def, 'name', ''))

            # Sensor-Typ ComboBox
            sensor_type_val = getattr(sensor_def, 'sensor_type', 'other')
            type_str_to_find = sensor_type_val.value if SENSOR_LIB_AVAILABLE and isinstance(sensor_type_val, SensorType) else sensor_type_val
            combo_type = self.editor_fields["sensor_type"]
            index_type = combo_type.findText(type_str_to_find)
            combo_type.setCurrentIndex(index_type if index_type != -1 else combo_type.findText("other"))

            self.editor_fields["protocol"].setCurrentText(getattr(sensor_def, 'protocol', 'other'))

            # Wertebereich
            value_range = getattr(sensor_def, 'value_range', (0, 0))
            self.editor_fields["value_range_min"].setValue(value_range[0] if len(value_range) > 0 else 0)
            self.editor_fields["value_range_max"].setValue(value_range[1] if len(value_range) > 1 else 0)

            self.editor_fields["unit"].setText(getattr(sensor_def, 'unit', ''))
            self.editor_fields["icon"].setText(getattr(sensor_def, 'icon', ''))
            self.editor_fields["description"].setPlainText(getattr(sensor_def, 'description', ''))

            # Pin-Tabelle füllen
            pins_table = self.editor_fields["pins_table"]
            pins_table.setRowCount(0)
            pins = getattr(sensor_def, 'pins', {})
            for role, default_pin in pins.items():
                self.add_pin_row(role, default_pin)

            # Editor (de)aktivieren
            self.set_editor_enabled(is_user)

    def create_new_sensor(self):
        """ Bereitet den Editor für einen neuen Sensor vor. """
        self.sensor_list_widget.clearSelection()
        self.clear_editor()
        self.set_editor_enabled(True)
        self.editor_fields["id"].setReadOnly(False)
        self.editor_fields["id"].setFocus()
        self.selected_sensor_id = None
        self.is_new_sensor = True

    def copy_sensor(self):
        """ Kopiert den ausgewählten Sensor und bereitet ihn als neuen Sensor vor. """
        if not self.selected_sensor_id or self.selected_sensor_id not in self.current_sensors:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie einen Sensor zum Kopieren aus.")
            return

        original_def = self.current_sensors[self.selected_sensor_id]['def']

        # Editor leeren und für neuen Sensor vorbereiten
        self.clear_editor()
        self.set_editor_enabled(True)
        self.editor_fields["id"].setReadOnly(False)

        # Felder mit kopierten Werten füllen
        new_id = f"{getattr(original_def, 'id', 'kopie')}_Kopie"
        self.editor_fields["id"].setText(new_id)
        self.editor_fields["name"].setText(f"{getattr(original_def, 'name', '')} (Kopie)")

        sensor_type_val = getattr(original_def, 'sensor_type', 'other')
        type_str = sensor_type_val.value if SENSOR_LIB_AVAILABLE and isinstance(sensor_type_val, SensorType) else sensor_type_val
        idx = self.editor_fields["sensor_type"].findText(type_str)
        self.editor_fields["sensor_type"].setCurrentIndex(idx if idx != -1 else 0)

        self.editor_fields["protocol"].setCurrentText(getattr(original_def, 'protocol', 'other'))

        value_range = getattr(original_def, 'value_range', (0, 0))
        self.editor_fields["value_range_min"].setValue(value_range[0] if len(value_range) > 0 else 0)
        self.editor_fields["value_range_max"].setValue(value_range[1] if len(value_range) > 1 else 0)

        self.editor_fields["unit"].setText(getattr(original_def, 'unit', ''))
        self.editor_fields["icon"].setText(getattr(original_def, 'icon', ''))
        self.editor_fields["description"].setPlainText(getattr(original_def, 'description', ''))

        # Pin-Tabelle füllen
        pins_table = self.editor_fields["pins_table"]
        pins_table.setRowCount(0)
        pins = getattr(original_def, 'pins', {})
        for role, default_pin in pins.items():
            self.add_pin_row(role, default_pin)

        self.selected_sensor_id = None
        self.is_new_sensor = True

    def delete_sensor(self):
        """ Löscht den ausgewählten [User]-Sensor. """
        if not self.selected_sensor_id or not self.current_sensors[self.selected_sensor_id]['is_user']:
            QMessageBox.warning(self, "Fehler", "Nur [User] Sensoren können gelöscht werden.")
            return

        reply = QMessageBox.question(self, "Bestätigung",
                                     f"Den Sensor '{self.selected_sensor_id}' wirklich löschen?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.selected_sensor_id in self.user_sensors:
                del self.user_sensors[self.selected_sensor_id]
            
            if self.save_user_sensors_to_file():
                self.load_all_sensors()
                self.sensors_updated_signal.emit()

    def save_sensor(self):
        """ Speichert den aktuell im Editor befindlichen Sensor. """
        sensor_id_text = self.editor_fields["id"].text().strip()
        if not sensor_id_text:
            QMessageBox.warning(self, "Fehler", "ID darf nicht leer sein.")
            return

        # Prüfen, ob ID existiert (nur wenn neu oder ID geändert)
        is_id_changed = self.is_new_sensor or (sensor_id_text != self.selected_sensor_id)
        reply = QMessageBox.StandardButton.Yes # Standardannahme
        
        if is_id_changed and sensor_id_text in self.current_sensors:
            reply = QMessageBox.question(self, "ID existiert",
                                         f"Die Sensor ID '{sensor_id_text}' existiert bereits. Überschreiben?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return

        # Erstelle ein neues SensorDefinition-Objekt (oder Mock)
        new_sensor_def = type('SensorDefMock', (object,), {})()
        new_sensor_def.id = sensor_id_text
        new_sensor_def.name = self.editor_fields["name"].text().strip()

        # Sensor-Typ
        idx_type = self.editor_fields["sensor_type"].currentIndex()
        type_data = self.editor_fields["sensor_type"].itemData(idx_type)
        new_sensor_def.sensor_type = type_data if SENSOR_LIB_AVAILABLE and isinstance(type_data, SensorType) else self.editor_fields["sensor_type"].currentText()

        new_sensor_def.protocol = self.editor_fields["protocol"].currentText()
        new_sensor_def.value_range = (self.editor_fields["value_range_min"].value(), self.editor_fields["value_range_max"].value())
        new_sensor_def.unit = self.editor_fields["unit"].text().strip()
        new_sensor_def.icon = self.editor_fields["icon"].text().strip()
        new_sensor_def.description = self.editor_fields["description"].toPlainText().strip()

        # Pins aus Tabelle lesen
        new_sensor_def.pins = {}
        pins_table = self.editor_fields["pins_table"]
        for row in range(pins_table.rowCount()):
            role_item = pins_table.item(row, 0)
            pin_item = pins_table.item(row, 1)
            if role_item and pin_item:
                role = role_item.text().strip()
                pin = pin_item.text().strip()
                if role and pin:
                    # Einfache Pin-Validierung
                    if not (pin.startswith('D') or pin.startswith('A') or pin in ['VCC', 'GND', 'SDA', 'SCL', 'SCK', 'MISO', 'MOSI']):
                        QMessageBox.warning(self, "Ungültiger Pin", f"Der Pin '{pin}' in Zeile {row + 1} ist ungültig.")
                        return
                    new_sensor_def.pins[role] = pin

        new_sensor_def.is_user = True
        self.user_sensors[sensor_id_text] = new_sensor_def

        # Speichern und UI aktualisieren
        if self.save_user_sensors_to_file():
            current_id_to_select = sensor_id_text
            self.load_all_sensors()

            # Versuche, den gerade gespeicherten Sensor in der Liste auszuwählen
            for i in range(self.sensor_list_widget.count()):
                item = self.sensor_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == current_id_to_select:
                    self.sensor_list_widget.setCurrentItem(item)
                    break

            self.sensors_updated_signal.emit()
            QMessageBox.information(self, "Gespeichert", f"Sensor '{sensor_id_text}' wurde gespeichert.")

    def save_user_sensors_to_file(self):
        """ Speichert das self.user_sensors Dictionary in die JSON-Datei """
        try:
            sensors_to_save = {sid: self._sensor_def_to_dict(sdef) for sid, sdef in self.user_sensors.items()}

            with open(USER_SENSOR_FILE, 'w', encoding='utf-8') as f:
                json.dump(sensors_to_save, f, indent=4, ensure_ascii=False)

            # Diese Aktionen *nach* dem erfolgreichen Schließen der Datei
            print(f"User-Sensoren gespeichert in {USER_SENSOR_FILE}")
            if SENSOR_LIB_AVAILABLE:
                SensorLibrary._loaded = False  # Erzwinge Neuladen in der SensorLibrary
            return True
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Speichern", f"Konnte {USER_SENSOR_FILE} nicht schreiben:\n{e}")
            return False

    def clear_editor(self):
        """ Leert alle Felder im Sensor-Editor. """
        for field in self.editor_fields.values():
            if isinstance(field, QLineEdit):
                field.clear()
            elif isinstance(field, QComboBox):
                field.setCurrentIndex(0)
            elif isinstance(field, (QSpinBox, QDoubleSpinBox)):
                field.setValue(0)
            elif isinstance(field, QTextEdit):
                field.clear()
            elif isinstance(field, QTableWidget):
                field.setRowCount(0)
        self.editor_fields["id"].setReadOnly(True)

    def set_editor_enabled(self, enabled):
        """ Aktiviert oder deaktiviert alle Felder im Editor. """
        for key, field in self.editor_fields.items():
            if key == "id":
                # ID ist nur bearbeitbar, wenn 'enabled' UND 'is_new_sensor'
                field.setEnabled(enabled and self.is_new_sensor)
            else:
                field.setEnabled(enabled)

    def add_pin_row(self, role="", default_pin=""):
        """ Fügt eine neue Zeile zur Pin-Tabelle hinzu. """
        table = self.editor_fields["pins_table"]
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, 0, QTableWidgetItem(role))
        table.setItem(row, 1, QTableWidgetItem(default_pin))

    def remove_pin_row(self):
        """ Entfernt die aktuell ausgewählte Zeile aus der Pin-Tabelle. """
        table = self.editor_fields["pins_table"]
        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)

# --- Hilfsfunktion pinToNumber (wird hier nicht direkt verwendet, aber nützlich) ---
def pinToNumber(pinStr):
    """ Wandelt einen Pin-String (z.B. 'D5', 'A0') in eine interne Nummer um. """
    if isinstance(pinStr, str):
        if pinStr.startswith("D"):
            try:
                num = int(pinStr[1:])
                if 0 <= num <= 19:
                    return num
            except ValueError:
                pass
        elif pinStr.startswith("A"):
            try:
                num = int(pinStr[1:])
                if 0 <= num <= 15:
                    return 14 + num  # A0 = 14, A1 = 15, ...
            except ValueError:
                pass
    return -1

# --- Testblock zum direkten Ausführen der Datei ---
if __name__ == '__main__':
    import sys
    
    # Füge das übergeordnete Verzeichnis zum Sys-Pfad hinzu, um 'sensor_library' zu finden
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        
    try:
        # Erneuter Importversuch (jetzt mit korrektem Pfad)
        from sensor_library import SensorLibrary
        print("SensorLibrary OK für Test.")
    except ImportError:
        print("SensorLibrary NICHT OK für Test.")
        SensorLibrary = None # Stelle sicher, dass die Fallback-Klasse verwendet wird

    # Dummy-Klasse für den Test, falls benötigt
    class DummyConfigManager:
        _config = {}
        def get(self, key, default=None): return self._config.get(key, default)
        def set(self, key, value): self._config[key] = value
        def save_config_to_file(self): print("Dummy Save:", self.config)
        def load_config(self): return self.config

    app = QApplication(sys.argv)
    
    window = SensorLibraryManagerTab()
    window.setWindowTitle("Sensor Library Manager Test")
    window.setGeometry(100, 100, 900, 700)
    window.show()
    sys.exit(app.exec())
