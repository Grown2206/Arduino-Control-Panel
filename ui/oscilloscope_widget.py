# -*- coding: utf-8 -*-
"""
Digitales Oszilloskop-Widget für Arduino-Pins
Misst Spannungen, Frequenzen und zeigt Wellenformen an
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QCheckBox,
                             QSpinBox, QSlider, QSplitter)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import pyqtgraph as pg
from collections import deque
import numpy as np
import time

class OscilloscopeWidget(QWidget):
    """Oszilloskop-Widget mit Trigger und Messungen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Daten-Puffer
        self.buffer_size = 1000
        self.channels = {
            'CH1': {'enabled': False, 'pin': 'A0', 'color': '#e74c3c', 'data': deque(maxlen=self.buffer_size), 'time': deque(maxlen=self.buffer_size)},
            'CH2': {'enabled': False, 'pin': 'A1', 'color': '#3498db', 'data': deque(maxlen=self.buffer_size), 'time': deque(maxlen=self.buffer_size)},
            'CH3': {'enabled': False, 'pin': 'A2', 'color': '#2ecc71', 'data': deque(maxlen=self.buffer_size), 'time': deque(maxlen=self.buffer_size)},
            'CH4': {'enabled': False, 'pin': 'A3', 'color': '#f39c12', 'data': deque(maxlen=self.buffer_size), 'time': deque(maxlen=self.buffer_size)},
        }
        
        self.trigger_enabled = False
        self.trigger_level = 512
        self.trigger_edge = 'rising'
        self.trigger_channel = 'CH1'
        self.triggered = False
        
        self.time_base = 1.0  # Sekunden pro Division
        self.voltage_scale = 1.0  # Volt pro Division
        
        self.setup_ui()
        
        # Messungen
        self.measurements = {ch: {'vpp': 0, 'vmax': 0, 'vmin': 0, 'vavg': 0, 'freq': 0} for ch in self.channels}
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # === OBERER BEREICH: Wellenform-Anzeige ===
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        # Plot-Widget
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#1a1a1a')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setLabel('left', 'Spannung', units='V', color='#ecf0f1')
        self.plot.setLabel('bottom', 'Zeit', units='s', color='#ecf0f1')
        self.plot.setTitle("Oszilloskop - 4 Kanäle", color='#ecf0f1', size='14pt')
        self.plot.setYRange(0, 5)  # 0-5V für Arduino
        
        # Plot-Kurven für jeden Kanal
        self.plot_curves = {}
        for ch_name, ch_data in self.channels.items():
            curve = self.plot.plot(pen=pg.mkPen(ch_data['color'], width=2), name=ch_name)
            self.plot_curves[ch_name] = curve
        
        # Trigger-Linie
        self.trigger_line = pg.InfiniteLine(
            pos=self.trigger_level * 5.0 / 1024,
            angle=0,
            pen=pg.mkPen('#f39c12', width=2, style=Qt.PenStyle.DashLine),
            movable=True
        )
        self.trigger_line.sigPositionChanged.connect(self.on_trigger_moved)
        self.plot.addItem(self.trigger_line)
        
        plot_layout.addWidget(self.plot)
        splitter.addWidget(plot_widget)
        
        # === UNTERER BEREICH: Steuerung ===
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        
        # Kanal-Konfiguration
        channels_group = QGroupBox("📡 Kanäle")
        channels_layout = QVBoxLayout(channels_group)
        
        self.channel_widgets = {}
        for ch_name in ['CH1', 'CH2', 'CH3', 'CH4']:
            ch_layout = QHBoxLayout()
            
            # Enable-Checkbox
            enable_cb = QCheckBox(ch_name)
            enable_cb.setStyleSheet(f"QCheckBox {{ color: {self.channels[ch_name]['color']}; font-weight: bold; }}")
            enable_cb.stateChanged.connect(lambda state, ch=ch_name: self.toggle_channel(ch, state))
            ch_layout.addWidget(enable_cb)
            
            # Pin-Auswahl
            pin_combo = QComboBox()
            pin_combo.addItems([f"A{i}" for i in range(6)] + [f"D{i}" for i in range(14)])
            pin_combo.setCurrentText(self.channels[ch_name]['pin'])
            pin_combo.currentTextChanged.connect(lambda pin, ch=ch_name: self.set_channel_pin(ch, pin))
            ch_layout.addWidget(pin_combo)
            
            # Messungen
            meas_label = QLabel("V: --  f: --")
            meas_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
            ch_layout.addWidget(meas_label, 1)
            
            self.channel_widgets[ch_name] = {
                'enable': enable_cb,
                'pin': pin_combo,
                'meas': meas_label
            }
            
            channels_layout.addLayout(ch_layout)
        
        control_layout.addWidget(channels_group)
        
        # Zeitbasis und Trigger
        settings_group = QGroupBox("⚙️ Einstellungen")
        settings_layout = QVBoxLayout(settings_group)
        
        # Zeitbasis
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Zeit/Div:"))
        self.timebase_combo = QComboBox()
        self.timebase_combo.addItems(["10 ms", "50 ms", "100 ms", "500 ms", "1 s", "2 s", "5 s"])
        self.timebase_combo.setCurrentText("1 s")
        self.timebase_combo.currentTextChanged.connect(self.update_timebase)
        time_layout.addWidget(self.timebase_combo)
        settings_layout.addLayout(time_layout)
        
        # Spannungsskala
        volt_layout = QHBoxLayout()
        volt_layout.addWidget(QLabel("Volt/Div:"))
        self.volt_combo = QComboBox()
        self.volt_combo.addItems(["0.5 V", "1 V", "2 V", "5 V"])
        self.volt_combo.setCurrentText("1 V")
        self.volt_combo.currentTextChanged.connect(self.update_voltage_scale)
        volt_layout.addWidget(self.volt_combo)
        settings_layout.addLayout(volt_layout)
        
        # Trigger
        trigger_layout = QHBoxLayout()
        self.trigger_enable_cb = QCheckBox("Trigger")
        self.trigger_enable_cb.stateChanged.connect(self.toggle_trigger)
        trigger_layout.addWidget(self.trigger_enable_cb)
        
        self.trigger_ch_combo = QComboBox()
        self.trigger_ch_combo.addItems(['CH1', 'CH2', 'CH3', 'CH4'])
        trigger_layout.addWidget(self.trigger_ch_combo)
        
        self.trigger_edge_combo = QComboBox()
        self.trigger_edge_combo.addItems(['Steigende Flanke', 'Fallende Flanke'])
        trigger_layout.addWidget(self.trigger_edge_combo)
        
        settings_layout.addLayout(trigger_layout)
        
        # Trigger-Level
        trigger_level_layout = QHBoxLayout()
        trigger_level_layout.addWidget(QLabel("Level:"))
        self.trigger_slider = QSlider(Qt.Orientation.Horizontal)
        self.trigger_slider.setRange(0, 1023)
        self.trigger_slider.setValue(512)
        self.trigger_slider.valueChanged.connect(self.update_trigger_level)
        trigger_level_layout.addWidget(self.trigger_slider)
        self.trigger_level_label = QLabel("2.5V")
        trigger_level_layout.addWidget(self.trigger_level_label)
        settings_layout.addLayout(trigger_level_layout)
        
        control_layout.addWidget(settings_group)
        
        # Steuerungstasten
        buttons_group = QGroupBox("🎮 Steuerung")
        buttons_layout = QVBoxLayout(buttons_group)
        
        run_btn = QPushButton("▶️ Run")
        run_btn.clicked.connect(self.start_acquisition)
        buttons_layout.addWidget(run_btn)
        
        stop_btn = QPushButton("⏸️ Stop")
        stop_btn.clicked.connect(self.stop_acquisition)
        buttons_layout.addWidget(stop_btn)
        
        single_btn = QPushButton("📸 Single")
        single_btn.clicked.connect(self.single_acquisition)
        buttons_layout.addWidget(single_btn)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_data)
        buttons_layout.addWidget(clear_btn)
        
        auto_scale_btn = QPushButton("🎯 Auto Scale")
        auto_scale_btn.clicked.connect(self.auto_scale)
        buttons_layout.addWidget(auto_scale_btn)
        
        buttons_layout.addStretch()
        control_layout.addWidget(buttons_group)
        
        # Messungen-Anzeige
        meas_group = QGroupBox("📊 Messungen")
        meas_layout = QVBoxLayout(meas_group)
        
        self.cursor_label = QLabel("Cursor: --")
        meas_layout.addWidget(self.cursor_label)
        
        self.freq_label = QLabel("Frequenz: --")
        meas_layout.addWidget(self.freq_label)
        
        self.period_label = QLabel("Periode: --")
        meas_layout.addWidget(self.period_label)
        
        meas_layout.addStretch()
        control_layout.addWidget(meas_group)
        
        splitter.addWidget(control_widget)
        splitter.setSizes([600, 250])
        
        main_layout.addWidget(splitter)
    
    def toggle_channel(self, channel, state):
        """Aktiviert/Deaktiviert einen Kanal"""
        self.channels[channel]['enabled'] = (state == Qt.CheckState.Checked.value)
        self.plot_curves[channel].setVisible(self.channels[channel]['enabled'])
    
    def set_channel_pin(self, channel, pin):
        """Setzt den Pin für einen Kanal"""
        self.channels[channel]['pin'] = pin
    
    def update_timebase(self, text):
        """Aktualisiert die Zeitbasis"""
        value = float(text.split()[0])
        unit = text.split()[1]
        
        if unit == 'ms':
            self.time_base = value / 1000.0
        else:  # 's'
            self.time_base = value
        
        # X-Achse anpassen
        self.plot.setXRange(0, self.time_base * 10)
    
    def update_voltage_scale(self, text):
        """Aktualisiert die Spannungsskala"""
        self.voltage_scale = float(text.split()[0])
        self.plot.setYRange(0, self.voltage_scale * 8)
    
    def toggle_trigger(self, state):
        """Aktiviert/Deaktiviert den Trigger"""
        self.trigger_enabled = (state == Qt.CheckState.Checked.value)
        self.trigger_line.setVisible(self.trigger_enabled)
    
    def update_trigger_level(self, value):
        """Aktualisiert den Trigger-Level"""
        self.trigger_level = value
        voltage = value * 5.0 / 1024
        self.trigger_line.setPos(voltage)
        self.trigger_level_label.setText(f"{voltage:.2f}V")
    
    def on_trigger_moved(self):
        """Wird aufgerufen, wenn die Trigger-Linie bewegt wird"""
        voltage = self.trigger_line.value()
        self.trigger_level = int(voltage * 1024 / 5.0)
        self.trigger_slider.setValue(self.trigger_level)
    
    def add_sample(self, pin, value, timestamp=None):
        """Fügt einen Sample-Wert hinzu"""
        if timestamp is None:
            timestamp = time.time()
        
        # Zu welchem Kanal gehört dieser Pin?
        for ch_name, ch_data in self.channels.items():
            if ch_data['pin'] == pin and ch_data['enabled']:
                ch_data['data'].append(value)
                ch_data['time'].append(timestamp)
                
                # Trigger-Check
                if self.trigger_enabled and ch_name == self.trigger_channel:
                    self.check_trigger(value)
                
                # Messungen aktualisieren
                self.update_measurements(ch_name)
                break
    
    def check_trigger(self, value):
        """Prüft Trigger-Bedingung"""
        if not self.triggered:
            if self.trigger_edge == 'rising' and value > self.trigger_level:
                self.triggered = True
            elif self.trigger_edge == 'falling' and value < self.trigger_level:
                self.triggered = True
    
    def update_measurements(self, channel):
        """Aktualisiert Messungen für einen Kanal"""
        data = list(self.channels[channel]['data'])
        
        if len(data) < 2:
            return
        
        # Spannung in Volt umrechnen (Arduino ADC: 0-1023 = 0-5V)
        voltages = [v * 5.0 / 1024 for v in data]
        
        # Messungen berechnen
        vmax = max(voltages)
        vmin = min(voltages)
        vpp = vmax - vmin
        vavg = np.mean(voltages)
        
        # Frequenz schätzen (Zero-Crossings)
        freq = self.estimate_frequency(voltages, self.channels[channel]['time'])
        
        self.measurements[channel] = {
            'vpp': vpp,
            'vmax': vmax,
            'vmin': vmin,
            'vavg': vavg,
            'freq': freq
        }
        
        # Anzeige aktualisieren
        meas_text = f"Vpp: {vpp:.2f}V  Freq: {freq:.1f}Hz" if freq > 0 else f"Vpp: {vpp:.2f}V"
        self.channel_widgets[channel]['meas'].setText(meas_text)
    
    def estimate_frequency(self, voltages, timestamps):
        """Schätzt die Frequenz aus Zero-Crossings"""
        if len(voltages) < 10 or len(timestamps) < 10:
            return 0
        
        try:
            # Mittelwert als Schwellwert
            threshold = np.mean(voltages)
            
            # Zero-Crossings finden
            crossings = []
            for i in range(1, len(voltages)):
                if voltages[i-1] < threshold <= voltages[i]:
                    crossings.append(list(timestamps)[i])
            
            if len(crossings) < 2:
                return 0
            
            # Durchschnittliche Periode berechnen
            periods = [crossings[i+1] - crossings[i] for i in range(len(crossings)-1)]
            avg_period = np.mean(periods)
            
            return 1.0 / avg_period if avg_period > 0 else 0
        except (ValueError, IndexError, ZeroDivisionError) as e:
            return 0
    
    def update_plot(self):
        """Aktualisiert den Plot"""
        for ch_name, ch_data in self.channels.items():
            if not ch_data['enabled']:
                continue
            
            if len(ch_data['data']) < 2:
                continue
            
            # Zeit relativ zum ersten Sample
            times = list(ch_data['time'])
            if len(times) == 0:
                continue
            
            start_time = times[0]
            rel_times = [t - start_time for t in times]
            
            # Spannung in Volt
            voltages = [v * 5.0 / 1024 for v in ch_data['data']]
            
            # Plot aktualisieren
            self.plot_curves[ch_name].setData(rel_times, voltages)
    
    def start_acquisition(self):
        """Startet die Datenerfassung"""
        self.triggered = False
    
    def stop_acquisition(self):
        """Stoppt die Datenerfassung"""
        pass
    
    def single_acquisition(self):
        """Einzelne Aufnahme"""
        self.triggered = False
    
    def clear_data(self):
        """Löscht alle Daten"""
        for ch_data in self.channels.values():
            ch_data['data'].clear()
            ch_data['time'].clear()
        
        for curve in self.plot_curves.values():
            curve.clear()
    
    def auto_scale(self):
        """Automatische Skalierung"""
        # Finde Min/Max über alle aktiven Kanäle
        all_voltages = []
        
        for ch_data in self.channels.values():
            if ch_data['enabled'] and len(ch_data['data']) > 0:
                voltages = [v * 5.0 / 1024 for v in ch_data['data']]
                all_voltages.extend(voltages)
        
        if all_voltages:
            vmin = min(all_voltages)
            vmax = max(all_voltages)
            margin = (vmax - vmin) * 0.1
            
            self.plot.setYRange(vmin - margin, vmax + margin)
