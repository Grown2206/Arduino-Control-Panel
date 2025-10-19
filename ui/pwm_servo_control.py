# -*- coding: utf-8 -*-
"""
PWM-Generator und Servo-Steuerung
Perfekt für Motoren, LEDs und Servos
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QSlider, QSpinBox, QComboBox,
                             QDial, QCheckBox, QTabWidget, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
import math

class PWMVisualization(QWidget):
    """Visualisiert ein PWM-Signal"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.duty_cycle = 0  # 0-255
        self.frequency = 490  # Hz
        self.animation_offset = 0
        
        # Animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)  # ~33 FPS
    
    def set_duty_cycle(self, value):
        """Setzt den Duty-Cycle (0-255)"""
        self.duty_cycle = value
        self.update()
    
    def set_frequency(self, freq):
        """Setzt die Frequenz"""
        self.frequency = freq
        self.update()
    
    def animate(self):
        """Animiert das Signal"""
        self.animation_offset = (self.animation_offset + 5) % self.width()
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Hintergrund
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Grid
        painter.setPen(QPen(QColor(60, 60, 60), 1, Qt.PenStyle.DotLine))
        for i in range(0, self.width(), 20):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 20):
            painter.drawLine(0, i, self.width(), i)
        
        # PWM-Signal zeichnen
        if self.duty_cycle > 0:
            painter.setPen(QPen(QColor(46, 204, 113), 2))
            
            # Berechne Periodenlänge in Pixeln
            period_width = max(20, self.width() // 4)
            high_width = int(period_width * (self.duty_cycle / 255.0))
            
            x = -self.animation_offset
            while x < self.width():
                # HIGH-Phase
                painter.drawLine(x, 10, x, 10)
                painter.drawLine(x, 10, x, self.height() - 10)
                painter.drawLine(x, self.height() - 10, x + high_width, self.height() - 10)
                
                # LOW-Phase
                painter.drawLine(x + high_width, self.height() - 10, x + high_width, 10)
                painter.drawLine(x + high_width, 10, x + period_width, 10)
                
                x += period_width
        
        # Beschriftung
        painter.setPen(QPen(QColor(236, 240, 241), 1))
        painter.drawText(10, 20, f"Duty: {self.duty_cycle}/255 ({self.duty_cycle/255*100:.1f}%)")
        painter.drawText(10, 40, f"Freq: {self.frequency} Hz")


class ServoWidget(QFrame):
    """Widget zur Steuerung eines einzelnen Servos"""
    angle_changed = pyqtSignal(int, int)  # pin, angle
    
    def __init__(self, servo_id, parent=None):
        super().__init__(parent)
        self.servo_id = servo_id
        self.current_angle = 90
        self.target_angle = 90
        self.pin = 9
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ServoWidget {
                background-color: #2D3B4A;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(f"🎯 Servo {self.servo_id}")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ecf0f1;")
        header_layout.addWidget(title)
        
        # Pin-Auswahl
        header_layout.addWidget(QLabel("Pin:"))
        self.pin_combo = QComboBox()
        self.pin_combo.addItems([f"D{i}" for i in [3, 5, 6, 9, 10, 11]])  # PWM-Pins
        self.pin_combo.setCurrentText(f"D{self.pin}")
        header_layout.addWidget(self.pin_combo)
        
        layout.addLayout(header_layout)
        
        # Servo-Visualisierung (Drehknopf)
        vis_layout = QHBoxLayout()
        
        self.servo_dial = QDial()
        self.servo_dial.setRange(0, 180)
        self.servo_dial.setValue(90)
        self.servo_dial.setNotchesVisible(True)
        self.servo_dial.setFixedSize(120, 120)
        self.servo_dial.valueChanged.connect(self.on_dial_changed)
        vis_layout.addWidget(self.servo_dial)
        
        # Winkel-Anzeige
        angle_display = QVBoxLayout()
        self.angle_label = QLabel("90°")
        self.angle_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #f39c12;
            background-color: #1e1e1e;
            border-radius: 8px;
            padding: 10px;
        """)
        self.angle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        angle_display.addWidget(self.angle_label)
        
        # Mikrosekunden-Anzeige
        self.us_label = QLabel("1500 μs")
        self.us_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        self.us_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        angle_display.addWidget(self.us_label)
        
        vis_layout.addLayout(angle_display)
        layout.addLayout(vis_layout)
        
        # Slider für Feineinstellung
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("0°"))
        
        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(0, 180)
        self.angle_slider.setValue(90)
        self.angle_slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.angle_slider)
        
        slider_layout.addWidget(QLabel("180°"))
        layout.addLayout(slider_layout)
        
        # Preset-Buttons
        preset_layout = QHBoxLayout()
        
        presets = [
            ("◀◀ 0°", 0),
            ("◀ 45°", 45),
            ("⬤ 90°", 90),
            ("▶ 135°", 135),
            ("▶▶ 180°", 180),
        ]
        
        for text, angle in presets:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, a=angle: self.set_angle(a))
            preset_layout.addWidget(btn)
        
        layout.addLayout(preset_layout)
        
        # Sweep-Funktion
        sweep_layout = QHBoxLayout()
        
        self.sweep_check = QCheckBox("Sweep")
        sweep_layout.addWidget(self.sweep_check)
        
        sweep_layout.addWidget(QLabel("Speed:"))
        self.sweep_speed = QSpinBox()
        self.sweep_speed.setRange(10, 1000)
        self.sweep_speed.setValue(100)
        self.sweep_speed.setSuffix(" ms")
        sweep_layout.addWidget(self.sweep_speed)
        
        sweep_layout.addStretch()
        layout.addLayout(sweep_layout)
        
        # Sweep-Timer
        self.sweep_timer = QTimer(self)
        self.sweep_timer.timeout.connect(self.do_sweep)
        self.sweep_check.stateChanged.connect(self.toggle_sweep)
        self.sweep_direction = 1
    
    def on_dial_changed(self, value):
        """Wird aufgerufen, wenn der Drehknopf bewegt wird"""
        self.angle_slider.blockSignals(True)
        self.angle_slider.setValue(value)
        self.angle_slider.blockSignals(False)
        self.set_angle(value)
    
    def on_slider_changed(self, value):
        """Wird aufgerufen, wenn der Slider bewegt wird"""
        self.servo_dial.blockSignals(True)
        self.servo_dial.setValue(value)
        self.servo_dial.blockSignals(False)
        self.set_angle(value)
    
    def set_angle(self, angle):
        """Setzt den Winkel des Servos"""
        self.current_angle = angle
        self.angle_label.setText(f"{angle}°")
        
        # Mikrosekunden berechnen (Standard-Servo: 1000-2000μs für 0-180°)
        microseconds = 1000 + (angle * 1000 // 180)
        self.us_label.setText(f"{microseconds} μs")
        
        # Signal aussenden
        pin_str = self.pin_combo.currentText()
        self.angle_changed.emit(int(pin_str[1:]), angle)
    
    def toggle_sweep(self, state):
        """Aktiviert/Deaktiviert Sweep"""
        if state == Qt.CheckState.Checked.value:
            self.sweep_timer.start(self.sweep_speed.value())
        else:
            self.sweep_timer.stop()
    
    def do_sweep(self):
        """Führt einen Sweep-Schritt aus"""
        new_angle = self.current_angle + (5 * self.sweep_direction)
        
        if new_angle >= 180:
            new_angle = 180
            self.sweep_direction = -1
        elif new_angle <= 0:
            new_angle = 0
            self.sweep_direction = 1
        
        self.servo_dial.setValue(new_angle)


class PWMServoControl(QWidget):
    """Haupt-Widget für PWM und Servo-Steuerung"""
    command_signal = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # === TAB 1: PWM-Generator ===
        pwm_tab = QWidget()
        pwm_layout = QVBoxLayout(pwm_tab)
        
        # PWM-Kanäle
        pwm_channels_group = QGroupBox("📡 PWM-Kanäle")
        channels_grid = QGridLayout(pwm_channels_group)
        
        self.pwm_channels = {}
        pwm_pins = [3, 5, 6, 9, 10, 11]  # Arduino PWM-Pins
        
        for idx, pin in enumerate(pwm_pins):
            row = idx // 2
            col = (idx % 2) * 3
            
            # Pin-Label
            pin_label = QLabel(f"D{pin}")
            pin_label.setStyleSheet("font-weight: bold; color: #3498db;")
            channels_grid.addWidget(pin_label, row, col)
            
            # Slider
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(0)
            slider.valueChanged.connect(lambda v, p=pin: self.pwm_value_changed(p, v))
            channels_grid.addWidget(slider, row, col + 1)
            
            # Wert-Anzeige
            value_label = QLabel("0")
            value_label.setFixedWidth(40)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            channels_grid.addWidget(value_label, row, col + 2)
            
            self.pwm_channels[pin] = {'slider': slider, 'label': value_label}
        
        pwm_layout.addWidget(pwm_channels_group)
        
        # PWM-Visualisierung
        vis_group = QGroupBox("📊 Signal-Visualisierung")
        vis_layout = QVBoxLayout(vis_group)
        
        self.pwm_vis = PWMVisualization()
        vis_layout.addWidget(self.pwm_vis)
        
        # Ausgewählter Pin für Visualisierung
        vis_control = QHBoxLayout()
        vis_control.addWidget(QLabel("Anzeigen:"))
        self.vis_pin_combo = QComboBox()
        self.vis_pin_combo.addItems([f"D{p}" for p in pwm_pins])
        self.vis_pin_combo.currentTextChanged.connect(self.update_visualization)
        vis_control.addWidget(self.vis_pin_combo)
        vis_control.addStretch()
        vis_layout.addLayout(vis_control)
        
        pwm_layout.addWidget(vis_group)
        
        # Preset-Funktionen
        presets_group = QGroupBox("⚡ Presets")
        presets_layout = QHBoxLayout(presets_group)
        
        all_off_btn = QPushButton("🌑 Alle aus")
        all_off_btn.clicked.connect(lambda: self.set_all_pwm(0))
        presets_layout.addWidget(all_off_btn)
        
        all_25_btn = QPushButton("◔ 25%")
        all_25_btn.clicked.connect(lambda: self.set_all_pwm(64))
        presets_layout.addWidget(all_25_btn)
        
        all_50_btn = QPushButton("◑ 50%")
        all_50_btn.clicked.connect(lambda: self.set_all_pwm(128))
        presets_layout.addWidget(all_50_btn)
        
        all_75_btn = QPushButton("◕ 75%")
        all_75_btn.clicked.connect(lambda: self.set_all_pwm(192))
        presets_layout.addWidget(all_75_btn)
        
        all_max_btn = QPushButton("🌕 Alle max")
        all_max_btn.clicked.connect(lambda: self.set_all_pwm(255))
        presets_layout.addWidget(all_max_btn)
        
        pwm_layout.addWidget(presets_group)
        pwm_layout.addStretch()
        
        tabs.addTab(pwm_tab, "PWM Generator")
        
        # === TAB 2: Servo-Steuerung ===
        servo_tab = QWidget()
        servo_layout = QVBoxLayout(servo_tab)
        
        # Servo-Grid
        servo_grid = QGridLayout()
        
        self.servos = []
        for i in range(4):
            servo = ServoWidget(i + 1)
            servo.angle_changed.connect(self.servo_angle_changed)
            row, col = divmod(i, 2)
            servo_grid.addWidget(servo, row, col)
            self.servos.append(servo)
        
        servo_layout.addLayout(servo_grid)
        
        # Choreographie
        choreo_group = QGroupBox("🎭 Choreographie")
        choreo_layout = QVBoxLayout(choreo_group)
        
        choreo_btn_layout = QHBoxLayout()
        
        wave_btn = QPushButton("🌊 Welle")
        wave_btn.clicked.connect(self.choreography_wave)
        choreo_btn_layout.addWidget(wave_btn)
        
        sync_btn = QPushButton("⚡ Synchron")
        sync_btn.clicked.connect(self.choreography_sync)
        choreo_btn_layout.addWidget(sync_btn)
        
        random_btn = QPushButton("🎲 Zufällig")
        random_btn.clicked.connect(self.choreography_random)
        choreo_btn_layout.addWidget(random_btn)
        
        reset_btn = QPushButton("🔄 Reset (90°)")
        reset_btn.clicked.connect(self.choreography_reset)
        choreo_btn_layout.addWidget(reset_btn)
        
        choreo_layout.addLayout(choreo_btn_layout)
        servo_layout.addWidget(choreo_group)
        
        servo_layout.addStretch()
        
        tabs.addTab(servo_tab, "Servo-Steuerung")
        
        main_layout.addWidget(tabs)
    
    def pwm_value_changed(self, pin, value):
        """Wird aufgerufen, wenn ein PWM-Wert geändert wird"""
        self.pwm_channels[pin]['label'].setText(str(value))
        
        # Visualisierung aktualisieren
        current_pin = int(self.vis_pin_combo.currentText()[1:])
        if pin == current_pin:
            self.pwm_vis.set_duty_cycle(value)
        
        # Kommando senden
        self.command_signal.emit({
            'command': 'analog_write',
            'pin': f'D{pin}',
            'value': value
        })
    
    def update_visualization(self):
        """Aktualisiert die PWM-Visualisierung"""
        pin = int(self.vis_pin_combo.currentText()[1:])
        value = self.pwm_channels[pin]['slider'].value()
        self.pwm_vis.set_duty_cycle(value)
    
    def set_all_pwm(self, value):
        """Setzt alle PWM-Kanäle auf einen Wert"""
        for pin, widgets in self.pwm_channels.items():
            widgets['slider'].setValue(value)
    
    def servo_angle_changed(self, pin, angle):
        """Wird aufgerufen, wenn ein Servo-Winkel geändert wird"""
        # Hier würde der Arduino-Befehl gesendet werden
        self.command_signal.emit({
            'command': 'servo_write',
            'pin': f'D{pin}',
            'angle': angle
        })
    
    def choreography_wave(self):
        """Wellen-Choreographie"""
        import random
        for i, servo in enumerate(self.servos):
            QTimer.singleShot(i * 200, lambda s=servo: s.set_angle(random.randint(0, 180)))
    
    def choreography_sync(self):
        """Synchrone Bewegung"""
        import random
        angle = random.randint(0, 180)
        for servo in self.servos:
            servo.set_angle(angle)
    
    def choreography_random(self):
        """Zufällige Bewegung"""
        import random
        for servo in self.servos:
            servo.set_angle(random.randint(0, 180))
    
    def choreography_reset(self):
        """Alle Servos auf 90° zurücksetzen"""
        for servo in self.servos:
            servo.set_angle(90)
