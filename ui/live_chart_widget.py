from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QTimer
import pyqtgraph as pg
from collections import deque

class LiveChartWidget(QWidget):
    """Live-Diagramm für Pin- oder Sensor-Visualisierung mit optimiertem Update-Mechanismus."""
    clear_button_pressed = pyqtSignal()

    def __init__(self, title="Live Visualisierung"):
        super().__init__()
        self.pin_data = {}
        self.max_points = 500
        self._title = title
        self.setup_ui()

        # Puffer für neue Datenpunkte
        self.data_buffer = []

        # Timer für gebündelte Updates
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(150)  # Update-Intervall in ms
        self.update_timer.timeout.connect(self.batch_update_plot)
        self.update_timer.start()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        control_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Diagramm zurücksetzen")
        clear_btn.clicked.connect(self.clear_button_pressed.emit)
        control_layout.addStretch()
        control_layout.addWidget(clear_btn)
        layout.addLayout(control_layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e1e')
        self.plot_widget.setLabel('left', 'Wert', color='#ecf0f1')
        self.plot_widget.setLabel('bottom', 'Zeit (s)', color='#ecf0f1')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setTitle(self._title, color='#ecf0f1', size='12pt')
        self.plot_widget.addLegend()
        layout.addWidget(self.plot_widget)
    
    def add_data_point(self, data_key, value, timestamp):
        """Sammelt neue Datenpunkte im Puffer"""
        self.data_buffer.append((data_key, value, timestamp))
        # Timer kümmert sich um Updates!
    def batch_update_plot(self):
        """Verarbeitet alle gepufferten Datenpunkte"""
        if not self.data_buffer:
            return
        
        print(f"🔄 Chart-Update: {len(self.data_buffer)} neue Punkte")  # ← DEBUG
        
        for data_key, value, timestamp in self.data_buffer:
            if data_key not in self.pin_data:
                pen_color = self._get_pen_color(data_key)
                self.pin_data[data_key] = {
                    'x': deque(maxlen=self.max_points),
                    'y': deque(maxlen=self.max_points),
                    'plot': self.plot_widget.plot(pen=pg.mkPen(pen_color, width=2), name=data_key)
                }
                print(f"✅ Neue Datenreihe erstellt: {data_key}")  # ← DEBUG
            
            self.pin_data[data_key]['x'].append(timestamp)
            self.pin_data[data_key]['y'].append(value)
        
        self.data_buffer.clear()

        # Update
        for data_key, data in self.pin_data.items():
            try:
                x_list = list(data['x'])
                y_list = list(data['y'])
                print(f"📊 Update {data_key}: {len(x_list)} Punkte")  # ← DEBUG
                data['plot'].setData(x_list, y_list)
            except Exception as e:
                print(f"❌ Fehler bei {data_key}: {e}")
    
    def _get_pen_color(self, data_key):
        """Weist Farben basierend auf dem Schlüssel zu."""
        color_map = {
            "Temperatur": '#e74c3c',
            "Luftfeuchtigkeit": '#3498db',
        }
        # Fallback-Farben für dynamisch hinzugefügte Pins
        fallback_colors = ['#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        
        if data_key in color_map:
            return color_map[data_key]
        else:
            # Einfacher Hash, um eine konsistente Farbe pro Pin-Name zu erhalten
            hash_val = sum(ord(c) for c in data_key)
            return fallback_colors[hash_val % len(fallback_colors)]
    
    def clear(self):
        self.data_buffer.clear()
        self.pin_data.clear()
        self.plot_widget.clear()
        self.plot_widget.addLegend()

    def downsample_data(self, data, target_points=500):
        """Reduziert Datenpunkte für bessere Performance"""
        if len(data) <= target_points:
            return data
        
            step = len(data) // target_points
            return data[::step]


    def closeEvent(self, event):
        self.update_timer.stop()
        super().closeEvent(event)