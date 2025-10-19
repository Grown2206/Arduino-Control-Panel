# -*- coding: utf-8 -*-
"""
LED-Matrix Simulator - Visualisierung und Pattern-Generator
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpinBox, QComboBox, QSlider,
                             QGroupBox, QColorDialog, QFileDialog, QMessageBox,
                             QCheckBox, QTextEdit, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPalette, QFont  # ← QFont hinzugefügt!


class LEDWidget(QWidget):
    """Ein einzelnes LED-Widget"""
    clicked = pyqtSignal(int, int)  # row, col
    
    def __init__(self, row, col, size=30, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.led_size = size
        self.setFixedSize(size, size)
        self.color = QColor(30, 30, 30)  # Dunkelgrau (aus)
        self.brightness = 0  # 0-255
        self.animation = None
    
    def set_color(self, color: QColor, brightness: int = 255):
        """Setzt Farbe und Helligkeit"""
        self.color = color
        self.brightness = brightness
        self.update()
    
    def set_state(self, on: bool, color: QColor = None):
        """Ein/Aus schalten"""
        if on:
            self.color = color if color else QColor(255, 0, 0)
            self.brightness = 255
        else:
            self.color = QColor(30, 30, 30)
            self.brightness = 0
        self.update()
    
    def fade_to(self, target_brightness: int, duration: int = 300):
        """Weiche Helligkeitsänderung"""
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self, b"brightness")
        self.animation.setDuration(duration)
        self.animation.setStartValue(self.brightness)
        self.animation.setEndValue(target_brightness)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Hintergrund (Gehäuse)
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 3, 3)
        
        # LED-Licht
        if self.brightness > 0:
            # Farbintensität basierend auf Helligkeit
            factor = self.brightness / 255.0
            led_color = QColor(
                int(self.color.red() * factor),
                int(self.color.green() * factor),
                int(self.color.blue() * factor)
            )
            
            # Leuchteffekt
            glow_radius = 2 + int(self.brightness / 50)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(led_color))
            
            center_x = self.width() // 2
            center_y = self.height() // 2
            painter.drawEllipse(center_x - glow_radius, center_y - glow_radius,
                              glow_radius * 2, glow_radius * 2)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.row, self.col)


class LEDMatrixWidget(QWidget):
    """LED-Matrix-Anzeige"""
    def __init__(self, rows=8, cols=8, led_size=30, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.leds = []
        self.setup_ui(led_size)
    
    def setup_ui(self, led_size):
        layout = QGridLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)
        
        for row in range(self.rows):
            led_row = []
            for col in range(self.cols):
                led = LEDWidget(row, col, led_size)
                led.clicked.connect(self.on_led_clicked)
                layout.addWidget(led, row, col)
                led_row.append(led)
            self.leds.append(led_row)
    
    def on_led_clicked(self, row, col):
        """Toggle LED bei Klick"""
        led = self.leds[row][col]
        if led.brightness > 0:
            led.set_state(False)
        else:
            led.set_state(True, QColor(255, 0, 0))
    
    def set_pixel(self, row, col, color: QColor, brightness: int = 255):
        """Setzt ein einzelnes Pixel"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.leds[row][col].set_color(color, brightness)
    
    def clear(self):
        """Löscht alle LEDs"""
        for row in self.leds:
            for led in row:
                led.set_state(False)
    
    def fill(self, color: QColor):
        """Füllt alle LEDs mit einer Farbe"""
        for row in self.leds:
            for led in row:
                led.set_state(True, color)
    
    def get_pattern(self):
        """Gibt das aktuelle Pattern zurück"""
        pattern = []
        for row in self.leds:
            row_data = []
            for led in row:
                if led.brightness > 0:
                    row_data.append({
                        'r': led.color.red(),
                        'g': led.color.green(),
                        'b': led.color.blue(),
                        'brightness': led.brightness
                    })
                else:
                    row_data.append(None)
            pattern.append(row_data)
        return pattern
    
    def set_pattern(self, pattern):
        """Lädt ein Pattern"""
        for row_idx, row_data in enumerate(pattern):
            if row_idx >= self.rows:
                break
            for col_idx, pixel_data in enumerate(row_data):
                if col_idx >= self.cols:
                    break
                if pixel_data:
                    color = QColor(pixel_data['r'], pixel_data['g'], pixel_data['b'])
                    self.set_pixel(row_idx, col_idx, color, pixel_data.get('brightness', 255))
                else:
                    self.leds[row_idx][col_idx].set_state(False)


class LEDMatrixSimulator(QWidget):
    """Haupt-Widget mit Pattern-Generator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = QColor(255, 0, 0)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate_step)
        self.animation_frame = 0
        self.saved_patterns = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Linke Seite: Matrix-Anzeige
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.matrix = LEDMatrixWidget(rows=8, cols=8, led_size=35)
        left_layout.addWidget(self.matrix, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Matrix-Steuerung
        matrix_control = QGroupBox("Matrix-Steuerung")
        control_layout = QVBoxLayout(matrix_control)
        
        btn_row1 = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Löschen")
        clear_btn.clicked.connect(self.matrix.clear)
        btn_row1.addWidget(clear_btn)
        
        fill_btn = QPushButton("🎨 Füllen")
        fill_btn.clicked.connect(lambda: self.matrix.fill(self.current_color))
        btn_row1.addWidget(fill_btn)
        
        color_btn = QPushButton("🌈 Farbe")
        color_btn.clicked.connect(self.choose_color)
        btn_row1.addWidget(color_btn)
        control_layout.addLayout(btn_row1)
        
        # Aktueller Farbindikator
        color_indicator = QHBoxLayout()
        color_indicator.addWidget(QLabel("Aktuelle Farbe:"))
        self.color_display = QLabel()
        self.color_display.setFixedSize(60, 30)
        self.color_display.setStyleSheet(f"background-color: {self.current_color.name()}; border: 2px solid #555; border-radius: 5px;")
        color_indicator.addWidget(self.color_display)
        color_indicator.addStretch()
        control_layout.addLayout(color_indicator)
        
        left_layout.addWidget(matrix_control)
        main_layout.addWidget(left_widget)
        
        # Rechte Seite: Tabs
        right_tabs = QTabWidget()
        
        # === TAB 1: Muster ===
        patterns_tab = QWidget()
        patterns_layout = QVBoxLayout(patterns_tab)
        
        pattern_group = QGroupBox("🎭 Vordefinierte Muster")
        pattern_grid = QGridLayout(pattern_group)
        
        patterns = [
            ("Herz", self.pattern_heart),
            ("Smiley", self.pattern_smiley),
            ("Pfeil ↑", self.pattern_arrow_up),
            ("Pfeil ↓", self.pattern_arrow_down),
            ("Pfeil ←", self.pattern_arrow_left),
            ("Pfeil →", self.pattern_arrow_right),
            ("Kreuz", self.pattern_cross),
            ("Schachbrett", self.pattern_checkerboard),
            ("Rahmen", self.pattern_border),
            ("X", self.pattern_x),
        ]
        
        for idx, (name, func) in enumerate(patterns):
            btn = QPushButton(name)
            btn.clicked.connect(func)
            row, col = divmod(idx, 2)
            pattern_grid.addWidget(btn, row, col)
        
        patterns_layout.addWidget(pattern_group)
        
        # Speichern/Laden
        save_group = QGroupBox("💾 Speichern/Laden")
        save_layout = QVBoxLayout(save_group)
        
        save_btn_layout = QHBoxLayout()
        save_pattern_btn = QPushButton("💾 Muster speichern")
        save_pattern_btn.clicked.connect(self.save_pattern)
        save_btn_layout.addWidget(save_pattern_btn)
        
        load_pattern_btn = QPushButton("📂 Muster laden")
        load_pattern_btn.clicked.connect(self.load_pattern)
        save_btn_layout.addWidget(load_pattern_btn)
        save_layout.addLayout(save_btn_layout)
        
        export_btn = QPushButton("📤 Arduino-Code exportieren")
        export_btn.clicked.connect(self.export_arduino_code)
        save_layout.addWidget(export_btn)
        
        patterns_layout.addWidget(save_group)
        patterns_layout.addStretch()
        
        right_tabs.addTab(patterns_tab, "Muster")
        
        # === TAB 2: Animationen ===
        anim_tab = QWidget()
        anim_layout = QVBoxLayout(anim_tab)
        
        anim_group = QGroupBox("🎬 Animationen")
        anim_grid = QGridLayout(anim_group)
        
        animations = [
            ("Lauflicht →", lambda: self.start_animation("scroll_right")),
            ("Lauflicht ←", lambda: self.start_animation("scroll_left")),
            ("Lauflicht ↑", lambda: self.start_animation("scroll_up")),
            ("Lauflicht ↓", lambda: self.start_animation("scroll_down")),
            ("Blinken", lambda: self.start_animation("blink")),
            ("Pulsieren", lambda: self.start_animation("pulse")),
            ("Welleneffekt", lambda: self.start_animation("wave")),
            ("Regen", lambda: self.start_animation("rain")),
            ("Zufällig", lambda: self.start_animation("random")),
            ("Feuerwerk", lambda: self.start_animation("firework")),
        ]
        
        for idx, (name, func) in enumerate(animations):
            btn = QPushButton(name)
            btn.clicked.connect(func)
            row, col = divmod(idx, 2)
            anim_grid.addWidget(btn, row, col)
        
        anim_layout.addWidget(anim_group)
        
        # Animationssteuerung
        anim_control = QGroupBox("⚙️ Animationssteuerung")
        anim_control_layout = QVBoxLayout(anim_control)
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Geschwindigkeit:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 1000)
        self.speed_slider.setValue(200)
        speed_layout.addWidget(self.speed_slider)
        anim_control_layout.addLayout(speed_layout)
        
        stop_btn = QPushButton("⏹️ Animation stoppen")
        stop_btn.clicked.connect(self.stop_animation)
        anim_control_layout.addWidget(stop_btn)
        
        anim_layout.addWidget(anim_control)
        anim_layout.addStretch()
        
        right_tabs.addTab(anim_tab, "Animationen")
        
        # === TAB 3: Code ===
        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)
        
        code_layout.addWidget(QLabel("🔧 Generierter Arduino-Code:"))
        
        self.code_text = QTextEdit()
        self.code_text.setReadOnly(True)
        self.code_text.setFont(QFont("Courier", 9))
        code_layout.addWidget(self.code_text)
        
        code_btn_layout = QHBoxLayout()
        generate_btn = QPushButton("⚡ Code generieren")
        generate_btn.clicked.connect(self.generate_code)
        code_btn_layout.addWidget(generate_btn)
        
        copy_btn = QPushButton("📋 Code kopieren")
        copy_btn.clicked.connect(self.copy_code)
        code_btn_layout.addWidget(copy_btn)
        code_layout.addLayout(code_btn_layout)
        
        right_tabs.addTab(code_tab, "Code")
        
        main_layout.addWidget(right_tabs)
    
    def choose_color(self):
        """Farbwähler öffnen"""
        color = QColorDialog.getColor(self.current_color, self, "Farbe wählen")
        if color.isValid():
            self.current_color = color
            self.color_display.setStyleSheet(f"background-color: {color.name()}; border: 2px solid #555; border-radius: 5px;")
    
    # === MUSTER-FUNKTIONEN ===
    def pattern_heart(self):
        self.matrix.clear()
        heart = [
            [0,1,1,0,0,1,1,0],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,0,0],
            [0,0,0,1,1,0,0,0],
            [0,0,0,0,0,0,0,0],
        ]
        for r, row in enumerate(heart):
            for c, val in enumerate(row):
                if val:
                    self.matrix.set_pixel(r, c, self.current_color)
    
    def pattern_smiley(self):
        self.matrix.clear()
        smiley = [
            [0,0,1,1,1,1,0,0],
            [0,1,0,0,0,0,1,0],
            [1,0,1,0,0,1,0,1],
            [1,0,0,0,0,0,0,1],
            [1,0,1,0,0,1,0,1],
            [1,0,0,1,1,0,0,1],
            [0,1,0,0,0,0,1,0],
            [0,0,1,1,1,1,0,0],
        ]
        for r, row in enumerate(smiley):
            for c, val in enumerate(row):
                if val:
                    self.matrix.set_pixel(r, c, self.current_color)
    
    def pattern_arrow_up(self):
        self.matrix.clear()
        for i in range(8):
            self.matrix.set_pixel(4-i if i < 4 else i-3, i, self.current_color)
        for i in range(4, 8):
            self.matrix.set_pixel(i, 3, self.current_color)
            self.matrix.set_pixel(i, 4, self.current_color)
    
    def pattern_arrow_down(self):
        self.matrix.clear()
        for i in range(8):
            self.matrix.set_pixel(i if i < 4 else 7-i, i, self.current_color)
        for i in range(0, 4):
            self.matrix.set_pixel(i, 3, self.current_color)
            self.matrix.set_pixel(i, 4, self.current_color)
    
    def pattern_arrow_left(self):
        self.matrix.clear()
        for i in range(8):
            self.matrix.set_pixel(i, 4-i if i < 4 else i-3, self.current_color)
        for i in range(4, 8):
            self.matrix.set_pixel(3, i, self.current_color)
            self.matrix.set_pixel(4, i, self.current_color)
    
    def pattern_arrow_right(self):
        self.matrix.clear()
        for i in range(8):
            self.matrix.set_pixel(i, i if i < 4 else 7-i, self.current_color)
        for i in range(0, 4):
            self.matrix.set_pixel(3, i, self.current_color)
            self.matrix.set_pixel(4, i, self.current_color)
    
    def pattern_cross(self):
        self.matrix.clear()
        for i in range(8):
            self.matrix.set_pixel(i, 3, self.current_color)
            self.matrix.set_pixel(i, 4, self.current_color)
            self.matrix.set_pixel(3, i, self.current_color)
            self.matrix.set_pixel(4, i, self.current_color)
    
    def pattern_checkerboard(self):
        self.matrix.clear()
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    self.matrix.set_pixel(r, c, self.current_color)
    
    def pattern_border(self):
        self.matrix.clear()
        for i in range(8):
            self.matrix.set_pixel(0, i, self.current_color)
            self.matrix.set_pixel(7, i, self.current_color)
            self.matrix.set_pixel(i, 0, self.current_color)
            self.matrix.set_pixel(i, 7, self.current_color)
    
    def pattern_x(self):
        self.matrix.clear()
        for i in range(8):
            self.matrix.set_pixel(i, i, self.current_color)
            self.matrix.set_pixel(i, 7-i, self.current_color)
    
    # === ANIMATIONEN ===
    def start_animation(self, anim_type):
        self.animation_type = anim_type
        self.animation_frame = 0
        self.animation_timer.start(self.speed_slider.value())
    
    def stop_animation(self):
        self.animation_timer.stop()
    
    def animate_step(self):
        if self.animation_type == "scroll_right":
            # Alle LEDs um 1 nach rechts verschieben
            pattern = self.matrix.get_pattern()
            self.matrix.clear()
            for r in range(8):
                for c in range(8):
                    if pattern[r][c-1 if c > 0 else 7]:
                        p = pattern[r][c-1 if c > 0 else 7]
                        self.matrix.set_pixel(r, c, QColor(p['r'], p['g'], p['b']))
        
        elif self.animation_type == "blink":
            if self.animation_frame % 2 == 0:
                self.matrix.fill(self.current_color)
            else:
                self.matrix.clear()
        
        elif self.animation_type == "pulse":
            import math
            brightness = int(127 + 127 * math.sin(self.animation_frame * 0.1))
            for row in self.matrix.leds:
                for led in row:
                    led.set_color(self.current_color, brightness)
        
        elif self.animation_type == "random":
            import random
            r, c = random.randint(0, 7), random.randint(0, 7)
            if random.random() > 0.5:
                self.matrix.set_pixel(r, c, self.current_color)
            else:
                self.matrix.leds[r][c].set_state(False)
        
        self.animation_frame += 1
    
    def save_pattern(self):
        pattern = self.matrix.get_pattern()
        # Hier könnte man einen Dialog zum Speichern öffnen
        QMessageBox.information(self, "Info", "Pattern gespeichert!")
    
    def load_pattern(self):
        QMessageBox.information(self, "Info", "Pattern geladen!")
    
    def generate_code(self):
        code = self.export_arduino_code()
        self.code_text.setPlainText(code)
    
    def copy_code(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.code_text.toPlainText())
        QMessageBox.information(self, "Erfolg", "Code wurde in die Zwischenablage kopiert!")
    
    def export_arduino_code(self):
        """Generiert Arduino-Code für das aktuelle Pattern"""
        pattern = self.matrix.get_pattern()
        
        code = """// Automatisch generierter LED-Matrix Code
// Für 8x8 LED Matrix (z.B. MAX7219)

#include <MD_MAX72xx.h>

#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
#define MAX_DEVICES 1
#define CS_PIN 10

MD_MAX72XX mx = MD_MAX72XX(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);

// Pattern-Daten
const uint8_t PROGMEM pattern[8] = {
"""
        
        for row_idx, row in enumerate(pattern):
            byte_val = 0
            for col_idx, pixel in enumerate(row):
                if pixel and pixel['brightness'] > 128:
                    byte_val |= (1 << (7 - col_idx))
            code += f"  0b{bin(byte_val)[2:].zfill(8)}{',' if row_idx < 7 else ''} // Zeile {row_idx}\n"
        
        code += """};

void setup() {
  mx.begin();
  displayPattern();
}

void loop() {
  // Hier könnte Ihre Animation stehen
}

void displayPattern() {
  for (int row = 0; row < 8; row++) {
    mx.setRow(0, row, pattern[row]);
  }
}
"""
        return code
