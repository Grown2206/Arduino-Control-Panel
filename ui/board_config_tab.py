# -*- coding: utf-8 -*-
"""
ui/board_config_tab.py
Ein Tab zur visuellen Konfiguration der Arduino Pin-Belegung.
"""
import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QPushButton, QGridLayout, QSpacerItem, QSizePolicy,
                             QScrollArea, QFrame, QApplication, QMessageBox)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QRect

# --- Angepasster Import für sensor_library ---
try:
    from sensor_library import SensorLibrary, SensorDefinition, SensorType
    SENSOR_LIB_AVAILABLE = True
    print("INFO (Board Config): sensor_library direkt importiert.")
except ImportError:
    try:
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            print(f"INFO (Board Config): Füge '{parent_dir}' zu sys.path hinzu.")
        from sensor_library import SensorLibrary, SensorDefinition, SensorType
        SENSOR_LIB_AVAILABLE = True
        print("INFO (Board Config): sensor_library über sys.path importiert.")
    except ImportError as e:
        print(f"WARNUNG (Board Config): sensor_library.py konnte nicht importiert werden: {e}. Sensor-spezifische Pin-Auswahl nicht verfügbar.")
        SENSOR_LIB_AVAILABLE = False
        class SensorDefinition: pass
        class SensorType:
             OTHER = "other" # Minimaler Fallback
             @classmethod
             def __members__(cls): return {'OTHER': cls.OTHER}
             def __init__(self, value): self.value = value
        class SensorLibrary:
             @classmethod
             def get_all_sensors(cls): return {} # Leeres Dict als Fallback
             @classmethod
             def load_all_sensors(cls, force_reload=False): pass # Dummy Methode
             
             
class ArduinoPinWidget(QWidget):
    """Kleines Widget für einen einzelnen Pin auf dem Board-Diagramm"""
    pin_config_changed = pyqtSignal(str, str)  # pin_name, function

    def __init__(self, pin_name, available_functions, default_function="INPUT", parent=None):
        super().__init__(parent)
        self.pin_name = pin_name
        self.available_functions = available_functions
        self.default_function = default_function
        self.setToolTip(f"Konfiguriere Pin {pin_name}")
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(4)

        self.label = QLabel(self.pin_name)
        self.label.setFixedWidth(25)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.label.setStyleSheet("font-size: 9px; font-weight: bold; color: #333;")

        self.combo = QComboBox()
        self.combo.addItems(self.available_functions)
        self.combo.setCurrentText(self.default_function)
        self.combo.setMinimumWidth(0)
        self.combo.setMaximumWidth(80)
        self.combo.setStyleSheet("font-size: 9px; background-color: rgba(125, 125, 125, 0.8);")
        self.combo.currentTextChanged.connect(self.on_combo_change)

        layout.addWidget(self.label)
        layout.addWidget(self.combo)

    def on_combo_change(self, text):
        self.pin_config_changed.emit(self.pin_name, text)

    def get_config(self):
        return self.pin_name, self.combo.currentText()

    def set_config(self, function_name):
        self.combo.blockSignals(True)
        self.combo.setCurrentText(function_name)
        self.combo.blockSignals(False)

    def update_functions(self, new_functions):
        """
        Aktualisiert die verfügbaren Funktionen in der ComboBox.
        Behält die aktuelle Auswahl bei, falls sie noch in der neuen Liste vorhanden ist.
        
        Args:
            new_functions: Liste der neuen verfügbaren Funktionen
        """
        current_selection = self.combo.currentText()
        
        # ComboBox Signale blockieren während des Updates
        self.combo.blockSignals(True)
        
        # Alte Einträge löschen und neue hinzufügen
        self.combo.clear()
        self.combo.addItems(new_functions)
        
        # Versuche, die vorherige Auswahl wiederherzustellen
        if current_selection in new_functions:
            self.combo.setCurrentText(current_selection)
        else:
            # Falls die vorherige Auswahl nicht mehr verfügbar ist,
            # setze auf den ersten Eintrag (normalerweise "UNUSED")
            if len(new_functions) > 0:
                self.combo.setCurrentIndex(0)
        
        # Signale wieder aktivieren
        self.combo.blockSignals(False)
        
        # Speichere die neue Funktionsliste
        self.available_functions = new_functions

class BoardContainerWidget(QWidget):
     # (Unverändert von der vorherigen Antwort)
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.board_pixmap = QPixmap(image_path)
        if self.board_pixmap.isNull():
            print(f"WARNUNG: Arduino Bild nicht gefunden oder konnte nicht geladen werden: {image_path}")
            self.setMinimumSize(600, 450)
            self.board_pixmap = None
        else:
            print(f"INFO: Arduino Bild geladen: {image_path} ({self.board_pixmap.width()}x{self.board_pixmap.height()})")
            self.setMinimumSize(self.board_pixmap.width(), self.board_pixmap.height())
            self.setMaximumSize(self.board_pixmap.width(), self.board_pixmap.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.board_pixmap:
            painter.drawPixmap(0, 0, self.board_pixmap)
        else:
            painter.fillRect(self.rect(), QColor(Qt.GlobalColor.lightGray))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Arduino Bild nicht gefunden")


class BoardConfigTab(QWidget):
    """ Visuelle Konfiguration der Arduino Pin-Belegung """
    apply_config_signal = pyqtSignal(dict)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.pin_widgets = {}
        self.arduino_image_path = os.path.join("assets", "arduino_uno_pinout.png")
        self.digital_functions = []
        self.analog_functions = []
        # Fülle die Listen initial, bevor UI erstellt wird
        self.update_available_functions()
        self.setup_ui()
        self.load_config()

    def update_available_functions(self):
        """ Lädt die verfügbaren Funktionen (Basis + Sensoren) neu """
        print("Aktualisiere verfügbare Pin-Funktionen...")
        self.digital_functions = ["UNUSED", "INPUT", "OUTPUT", "INPUT_PULLUP"]
        self.analog_functions = ["UNUSED", "ANALOG_INPUT"]

        if SENSOR_LIB_AVAILABLE and SensorDefinition:
            # Stelle sicher, dass die Bibliothek geladen ist
            SensorLibrary.load_all_sensors(force_reload=True)
            # --- KORREKTUR: Verwende get_all_sensors() statt SENSORS ---
            all_sensors = SensorLibrary.get_all_sensors()
            # -----------------------------------------------------------
            print(f"  Gefundene Sensoren für Funktionsliste: {len(all_sensors)}")

            for sensor_id, sensor_def in all_sensors.items():
                if not isinstance(sensor_def, SensorDefinition): continue
                if not hasattr(sensor_def, 'protocol') or not hasattr(sensor_def, 'pins'): continue
                if not isinstance(sensor_def.pins, dict): continue

                if sensor_def.protocol in ["digital", "analog", "onewire"]:
                    for pin_role, default_pin in sensor_def.pins.items():
                         if not isinstance(default_pin, str): continue
                         func_name = f"{getattr(sensor_def, 'name', 'Unbekannt')} ({pin_role})"
                         if default_pin.startswith("A"):
                             if func_name not in self.analog_functions: self.analog_functions.append(func_name)
                         elif default_pin.startswith("D"):
                              if func_name not in self.digital_functions: self.digital_functions.append(func_name)
        else:
             print("  SensorBibliothek nicht verfügbar, nur Basis-Funktionen.")

        # Aktualisiere ComboBoxen der vorhandenen Pin-Widgets
        for pin_name, pin_widget in self.pin_widgets.items():
             if pin_name.startswith("D"):
                 pin_widget.update_functions(self.digital_functions)
             elif pin_name.startswith("A"):
                 pin_widget.update_functions(self.analog_functions)

    def setup_ui(self):
        # (Unverändert von der vorherigen Antwort)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(QLabel("<b>Arduino Pin Konfiguration</b>")); toolbar_layout.addStretch()
        self.apply_button = QPushButton("✅ Konfiguration an Arduino senden & Verbinden"); self.apply_button.clicked.connect(self.send_config_and_connect); self.apply_button.setStyleSheet("background-color: #27ae60;"); toolbar_layout.addWidget(self.apply_button)
        save_btn = QPushButton("💾 Speichern"); save_btn.clicked.connect(self.save_config); toolbar_layout.addWidget(save_btn)
        load_btn = QPushButton("📂 Laden"); load_btn.clicked.connect(self.load_config); toolbar_layout.addWidget(load_btn)
        main_layout.addLayout(toolbar_layout)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setStyleSheet("QScrollArea { border: 1px solid #555; }"); main_layout.addWidget(scroll_area)
        self.board_container = BoardContainerWidget(self.arduino_image_path); scroll_area.setWidget(self.board_container)
        self.place_pin_widgets()

    def place_pin_widgets(self):
        """ Positioniert die Pin-Konfigurations-Widgets über dem Bild """
        # Pin Positionen (Koordinaten relativ zum board_container)
        # Diese Werte müssen ggf. an dein spezifisches Bild angepasst werden!
        pin_positions = {
            "D13": (1125, 376),
            "D12": (1125, 402),
            "D11": (1125, 428),
            "D10": (1125, 454),
            "D9": (1125, 480),
            "D8": (1125, 506),
            "D7": (1125, 550),
            "D6": (1125, 576),
            "D5": (1125, 602),
            "D4": (1125, 628),
            "D3": (1125, 654),
            "D2": (1125, 680), 
            "A0": (420, 602),
            "A1": (420, 628),
            "A2": (420, 654),
            "A3": (420, 680),
            "A4": (420, 706),
            "A5": (420, 732),
        }

        for pin_name, pos in pin_positions.items():
            if pin_name.startswith("D"):
                functions = self.digital_functions; default = "INPUT"
            elif pin_name.startswith("A"):
                functions = self.analog_functions; default = "ANALOG_INPUT"
            else: continue

            # WICHTIG: Parent ist jetzt self.board_container
            pin_widget = ArduinoPinWidget(pin_name, functions, default, parent=self.board_container)
            pin_widget.move(pos[0], pos[1])
            pin_widget.pin_config_changed.connect(self.handle_pin_change)
            self.pin_widgets[pin_name] = pin_widget
            pin_widget.show() # Sicherstellen, dass es sichtbar ist


    def handle_pin_change(self, pin_name, function):
        # (Unverändert von der vorherigen Antwort)
        print(f"Pin {pin_name} geändert zu: {function}")

    def get_current_board_config(self):
        """Sammelt die aktuelle Konfiguration aller Pin-Widgets"""
        config = {}
        active_sensors = {}
        sensor_pin_map = {}
        pin_usage_check = {}

        for pin_name, widget in self.pin_widgets.items():
            _, function = widget.get_config()
            config[pin_name] = function

            if function != "UNUSED":
                if pin_name in pin_usage_check:
                    raise ValueError(f"Pin {pin_name} wird mehrfach verwendet: '{pin_usage_check[pin_name]}' und '{function}'")
                pin_usage_check[pin_name] = function

            # Sensor-Pins separat sammeln (nur wenn SensorLibrary geladen wurde)
            if SensorLibrary and SensorDefinition and "(" in function and ")" in function:
                try:
                    sensor_name_part = function.split(" (")[0]
                    pin_role = function.split(" (")[1][:-1]
                    sensor_id = None
                    sensor_def = None
                    
                    # WICHTIG: Verwende get_all_sensors() statt SENSORS
                    for sid, sdef_search in SensorLibrary.get_all_sensors().items():
                        # Sicherstellen, dass sdef_search ein SensorDefinition Objekt ist
                        if isinstance(sdef_search, SensorDefinition) and hasattr(sdef_search, 'name') and sdef_search.name == sensor_name_part:
                            sensor_id = sid
                            sensor_def = sdef_search
                            break

                    if sensor_id and sensor_def:
                        if sensor_id not in active_sensors:
                            active_sensors[sensor_id] = {'sensor_type': sensor_def.id, 'pin_config': {}}
                        pin_number = pinToNumber(pin_name)
                        if pin_number == -1:
                            raise ValueError(f"Ungültiger Pin-Name '{pin_name}' für Sensor '{function}'")
                        active_sensors[sensor_id]['pin_config'][pin_role] = pin_number
                        sensor_pin_map[function] = pin_name
                    elif sensor_id is None:
                        print(f"Warnung: Konnte Sensor-ID für Funktion '{function}' nicht finden.")

                except Exception as e:
                    print(f"Fehler beim Parsen der Sensorfunktion: {function} - {e}")
                    raise ValueError(f"Fehler bei Sensorfunktion '{function}': {e}")

        return config, active_sensors

    def send_config_and_connect(self):
         # (Unverändert von der vorherigen Antwort)
        try:
            pin_function_map, active_sensors_config = self.get_current_board_config()
            config_to_send = {'pin_functions': pin_function_map, 'active_sensors': active_sensors_config}
            print("Konfiguration wird gesendet:", config_to_send)
            self.apply_config_signal.emit(config_to_send); self.save_config()
        except ValueError as e: QMessageBox.warning(self, "Konfigurationsfehler", str(e))
        except Exception as e: QMessageBox.critical(self, "Fehler", f"Fehler beim Senden der Konfiguration:\n{e}")

    def save_config(self):
         # (Unverändert von der vorherigen Antwort)
        try:
            pin_function_map, _ = self.get_current_board_config()
            self.config_manager.set("board_pin_config", pin_function_map)
            self.config_manager.save_config_to_file()
            print("Board-Konfiguration gespeichert.")
        except ValueError as e: print(f"Hinweis beim Speichern (Konflikt ignoriert): {e}")
        except Exception as e: print(f"Fehler beim Speichern der Board-Konfiguration: {e}")

    def load_config(self):
         # (Unverändert von der vorherigen Antwort)
        pin_function_map = self.config_manager.get("board_pin_config", {})
        if not pin_function_map:
            print("Keine gespeicherte Board-Konfiguration gefunden, verwende Standard.")
            for pin_widget in self.pin_widgets.values(): pin_widget.set_config(pin_widget.default_function)
            return
        print("Lade Board-Konfiguration...")
        for pin_name, function in pin_function_map.items():
            if pin_name in self.pin_widgets:
                widget = self.pin_widgets[pin_name]; found = False
                for i in range(widget.combo.count()):
                    if widget.combo.itemText(i) == function: widget.set_config(function); found = True; break
                if not found: print(f"Warnung: Ungültige Funktion '{function}' für Pin {pin_name}. Setze Default."); widget.set_config(widget.default_function)
            else: print(f"Warnung: Pin {pin_name} aus Konfig nicht im UI gefunden.")
        print("Board-Konfiguration geladen.")

# Hilfsfunktion (unverändert)
def pinToNumber(pinStr):
  if pinStr.startswith("D"):
    try: num = int(pinStr[1:]);
    except ValueError: return -1
    if 0 <= num <= 19: return num
  elif pinStr.startswith("A"):
    try: num = int(pinStr[1:]);
    except ValueError: return -1
    if 0 <= num <= 15: return 14 + num # A0=14, A1=15,...
  return -1


# --- Zum Testen des Widgets (sys.path Anpassung hinzugefügt) ---
if __name__ == '__main__':
    # Füge das Parent-Verzeichnis hinzu, damit sensor_library gefunden wird
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    print("sys.path für Test angepasst:", sys.path) # Debug

    # Jetzt sollte der Import funktionieren
    try:
        from sensor_library import SensorLibrary
        print("SensorLibrary erfolgreich für Test importiert.")
    except ImportError:
        print("SensorLibrary konnte für Test NICHT importiert werden.")
        SensorLibrary = None # Stelle sicher, dass die Variable existiert


    class DummyConfigManager: # (Unverändert)
        _config = {}
        def get(self, key, default=None): return self._config.get(key, default)
        def set(self, key, value): self._config[key] = value
        def save_config_to_file(self): print("Dummy Save:", self._config)
        def load_config(self): return self._config

    app = QApplication(sys.argv)
    try: from branding import get_full_stylesheet; app.setStyleSheet(get_full_stylesheet())
    except ImportError: pass

    window = QWidget()
    window.setWindowTitle("Board Config Tab Test")
    layout = QVBoxLayout(window)
    # config_tab = BoardConfigTab(DummyConfigManager())

    # Lade echte Konfig zum Testen, falls vorhanden
    # Stelle sicher, dass der Pfad zur Config-Datei relativ zum Ausführungsort passt!
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(parent_dir, "arduino_config.json") # Annahme: im Hauptverzeichnis
    print(f"Versuche Konfig zu laden von: {config_file_path}")
    real_cm = ConfigManager(config_file_path)
    config_tab = BoardConfigTab(real_cm)


    layout.addWidget(config_tab)
    window.setGeometry(100, 100, 750, 600)
    window.show()
    sys.exit(app.exec())