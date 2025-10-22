# ui/sensor_dashboard_tab.py
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QFrame, QGridLayout, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class SensorCard(QFrame):
    """Ein einzelnes Sensor-Widget mit Live-Anzeige"""
    
    def __init__(self, sensor_id, sensor_name, sensor_type, icon, unit, parent=None):
        super().__init__(parent)
        self.sensor_id = sensor_id
        self.sensor_name = sensor_name
        self.sensor_type = sensor_type
        self.icon = icon
        self.unit = unit
        self.last_value = None
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            SensorCard {
                background-color: #2b2b2b;
                border: 2px solid #444;
                border-radius: 10px;
                padding: 10px;
            }
            SensorCard:hover {
                border-color: #666;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header: Icon + Name
        header = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("font-size: 48px;")
        header.addWidget(icon_label)
        
        header.addStretch()
        
        name_label = QLabel(self.sensor_name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(name_label)
        
        layout.addLayout(header)
        
        # Wert-Anzeige (groß und prominent)
        self.value_label = QLabel("---")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("""
            font-size: 42px;
            font-weight: bold;
            color: #4CAF50;
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 15px;
        """)
        layout.addWidget(self.value_label)
        
        # Einheit
        self.unit_label = QLabel(self.unit)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unit_label.setStyleSheet("font-size: 16px; color: #999;")
        layout.addWidget(self.unit_label)
        
        # Status-Indikator
        self.status_label = QLabel("● Warte auf Daten...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; color: #FFA500;")
        layout.addWidget(self.status_label)
        
        self.setFixedSize(280, 280)
    
    def update_value(self, value):
        """Aktualisiert den angezeigten Wert"""
        self.last_value = value
        
        # Formatierung je nach Sensor-Typ
        if self.sensor_type == "temperature":
            display_value = f"{value:.1f}"
            color = self.get_temperature_color(value)
        elif self.sensor_type == "humidity":
            display_value = f"{value:.0f}"
            color = self.get_humidity_color(value)
        elif self.sensor_type == "light":
            display_value = f"{value:.0f}"
            # Farbe je nach Helligkeit
            if value < 200:
                color = "#444"  # Dunkel
            elif value < 500:
                color = "#FF9800"  # Orange
            else:
                color = "#FFD700"  # Gold - hell
        elif self.sensor_type == "distance":
            display_value = f"{value:.1f}"
            # Farbe je nach Distanz (näher = roter)
            if value < 10:
                color = "#F44336"  # Rot - sehr nah
            elif value < 50:
                color = "#FF9800"  # Orange
            else:
                color = "#00BCD4"  # Cyan - weit weg
        elif self.sensor_type == "motion":
            display_value = "BEWEGUNG!" if value > 0 else "Keine"
            color = "#F44336" if value > 0 else "#4CAF50"
        elif self.sensor_type == "flame":
            display_value = "FEUER!" if value > 0 else "Sicher"
            color = "#FF5722" if value > 0 else "#4CAF50"
        elif self.sensor_type == "gas":
            # Gas-Werte: höher = gefährlicher
            display_value = f"{value:.0f}"
            if value < 300:
                color = "#4CAF50"  # Grün - OK
            elif value < 600:
                color = "#FFC107"  # Gelb - Warnung
            else:
                color = "#F44336"  # Rot - Gefahr!
        elif self.sensor_type == "water":
            # Wasser/Feuchtigkeit
            display_value = f"{value:.0f}"
            color = "#2196F3"  # Blau
        elif self.sensor_type == "magnetic":
            # Magnetfeld erkannt?
            display_value = "MAGNET!" if value > 0 else "Kein Feld"
            color = "#9C27B0" if value > 0 else "#666"
        else:
            # Standard für unbekannte Typen
            display_value = f"{value}"
            color = "#4CAF50"
        
        self.value_label.setText(display_value)
        self.value_label.setStyleSheet(f"""
            font-size: 42px;
            font-weight: bold;
            color: {color};
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 15px;
        """)
        
        # Status auf "Live" setzen
        self.status_label.setText("● Live")
        self.status_label.setStyleSheet("font-size: 12px; color: #4CAF50;")
    
    def get_temperature_color(self, temp):
        """Gibt Farbe basierend auf Temperatur zurück"""
        if temp < 10:
            return "#2196F3"  # Blau - kalt
        elif temp < 20:
            return "#00BCD4"  # Cyan - kühl
        elif temp < 25:
            return "#4CAF50"  # Grün - angenehm
        elif temp < 30:
            return "#FFC107"  # Gelb - warm
        else:
            return "#F44336"  # Rot - heiß
    
    def get_humidity_color(self, humidity):
        """Gibt Farbe basierend auf Luftfeuchtigkeit zurück"""
        if humidity < 30:
            return "#F44336"  # Rot - zu trocken
        elif humidity < 40:
            return "#FF9800"  # Orange
        elif humidity < 60:
            return "#4CAF50"  # Grün - optimal
        elif humidity < 70:
            return "#2196F3"  # Blau
        else:
            return "#9C27B0"  # Lila - zu feucht
    
    def set_offline(self):
        """Setzt Status auf offline"""
        self.status_label.setText("● Offline")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")


class SensorDashboardTab(QWidget):
    """Dashboard für Live-Sensor-Visualisierung"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor_cards = {}  # sensor_id -> SensorCard
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📊 Sensor Dashboard - Live Monitoring")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #E0E0E0;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Refresh Button
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self.refresh_sensors)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Info-Label (wird angezeigt wenn keine Sensoren)
        self.info_label = QLabel(
            "ℹ️ Keine aktiven Sensoren konfiguriert.\n\n"
            "Gehe zu 'Board Konfiguration' und weise Sensoren zu,\n"
            "dann verbinde mit dem Arduino."
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("""
            font-size: 14px;
            color: #999;
            padding: 40px;
            background-color: #1a1a1a;
            border-radius: 8px;
        """)
        main_layout.addWidget(self.info_label)
        
        # Scroll-Area für Sensor-Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.sensor_container = QWidget()
        self.sensor_grid = QGridLayout(self.sensor_container)
        self.sensor_grid.setSpacing(15)
        self.sensor_grid.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.sensor_container)
        main_layout.addWidget(scroll)
        
        # Verstecke Grid initial
        scroll.hide()
    
    def refresh_sensors(self):
        """Lädt aktive Sensoren neu"""
        # Wird von main.py aufgerufen wenn Konfiguration geladen wird
        pass
    
    def load_active_sensors(self, active_sensors_config):
        """
        Lädt aktive Sensoren aus der Board-Konfiguration
        
        Args:
            active_sensors_config: Dict mit sensor_id -> {'sensor_type': ..., 'pin_config': ...}
        """
        # Importiere SensorLibrary
        try:
            from sensor_library import SensorLibrary
        except:
            return
        
        # Lösche alte Cards
        for card in self.sensor_cards.values():
            card.deleteLater()
        self.sensor_cards.clear()
        
        if not active_sensors_config:
            # Keine Sensoren - zeige Info
            self.info_label.show()
            self.sensor_container.parent().hide()
            return
        
        # Verstecke Info, zeige Grid
        self.info_label.hide()
        self.sensor_container.parent().show()
        
        # Erstelle Cards für jeden Sensor
        row, col = 0, 0
        max_cols = 3  # 3 Cards pro Reihe
        
        for sensor_id, config in active_sensors_config.items():
            sensor_type_id = config.get('sensor_type')
            sensor_def = SensorLibrary.get_sensor(sensor_type_id)
            
            if not sensor_def:
                continue
            
            # Erstelle Card
            card = SensorCard(
                sensor_id=sensor_id,
                sensor_name=sensor_def.name,
                sensor_type=sensor_def.sensor_type.value,
                icon=sensor_def.icon,
                unit=sensor_def.unit
            )
            
            self.sensor_cards[sensor_type_id] = card
            self.sensor_grid.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        print(f"✅ Sensor Dashboard geladen: {len(self.sensor_cards)} Sensoren")
    
    def update_sensor_value(self, sensor_id, value):
        """
        Aktualisiert einen Sensor-Wert
        
        Args:
            sensor_id: ID des Sensors (z.B. "DHT11", "LM35")
            value: Neuer Wert
        """
        if sensor_id in self.sensor_cards:
            self.sensor_cards[sensor_id].update_value(value)
        
        # Auch Varianten mit Suffix prüfen (z.B. DHT11_HUMIDITY)
        base_id = sensor_id.split('_')[0]
        if base_id in self.sensor_cards and 'HUMIDITY' in sensor_id:
            # Spezial-Fall für Luftfeuchtigkeit
            # Würde separate Card brauchen oder in DHT-Card integriert werden
            pass
    
    def clear_all(self):
        """Löscht alle Sensor-Cards"""
        for card in self.sensor_cards.values():
            card.set_offline()