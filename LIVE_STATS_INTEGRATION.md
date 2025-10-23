# 📊 LIVE-STATISTIK-WIDGET - INTEGRATIONS-ANLEITUNG

## Schnell-Integration (3 Schritte)

### Schritt 1: Widget zum Dashboard hinzufügen

In `main.py`, in der `setup_ui()` Methode, nach der Dashboard-Initialisierung:

```python
# Im Dashboard-Tab - Falls Enhanced Dashboard vorhanden
if hasattr(self, 'dashboard_tab') and hasattr(self.dashboard_tab, 'add_widget'):
    self.dashboard_tab.add_widget(
        widget_id='live_stats',
        title='📊 Live-Statistiken',
        icon='📊',
        widget_instance=self.live_stats_widget,
        geometry=(10, 400, 400, 500),  # x, y, width, height
        category='Monitoring'
    )
    print('✅ Live-Statistik zum Dashboard hinzugefügt')
```

### Schritt 2: Mit SequenceRunner verbinden

In `main.py`, in der `setup_connections()` Methode:

```python
# Live-Stats mit SequenceRunner verbinden
if hasattr(self.seq_runner, 'cycle_completed'):
    self.seq_runner.cycle_completed.connect(
        self.live_stats_widget.add_cycle
    )
    print('✅ Live-Stats mit SequenceRunner verbunden')
else:
    print('⚠️ SequenceRunner hat kein cycle_completed Signal')
```

### Schritt 3: Start/Stop im SequenceRunner

In der Methode, die den Testlauf **startet**:

```python
def start_sequence_run(self, sequence, cycles):
    # ... existing code ...
    
    # Live-Stats starten
    if hasattr(self, 'live_stats_widget'):
        self.live_stats_widget.start_monitoring(cycles)
    
    # ... run sequence ...
```

In der Methode, die den Testlauf **beendet**:

```python
def on_sequence_complete(self):
    # ... existing code ...
    
    # Live-Stats stoppen
    if hasattr(self, 'live_stats_widget'):
        self.live_stats_widget.stop_monitoring()
    
    # ... rest ...
```

---

## Detaillierte Integration

### A. Signal in SequenceRunner emittieren

In `core/sequence_runner.py`, am **Ende** der `run_cycle()` Methode:

```python
def run_cycle(self, cycle_number):
    start_time = time.time()
    
    # ... führe Schritte aus ...
    
    end_time = time.time()
    cycle_time = (end_time - start_time) * 1000  # in ms
    
    # NEU: Emittiere für Live-Stats
    # Optional: Anomalie-Check
    is_anomaly = False
    if hasattr(self, 'check_if_anomaly'):
        is_anomaly = self.check_if_anomaly(cycle_time)
    
    # Signal emittieren
    if hasattr(self, 'cycle_completed'):
        self.cycle_completed.emit(cycle_time, is_anomaly)
    
    return cycle_time
```

### B. Anomalie-Check implementieren (Optional)

Falls du Echtzeit-Anomalieerkennung willst:

```python
class SequenceRunner:
    def __init__(self):
        # ... existing code ...
        
        # Für Anomalie-Erkennung
        self.cycle_times_buffer = []
        self.z_threshold = 2.5
    
    def check_if_anomaly(self, cycle_time):
        """Prüft ob Zykluszeit eine Anomalie ist."""
        if len(self.cycle_times_buffer) < 10:
            # Zu wenig Daten für Statistik
            self.cycle_times_buffer.append(cycle_time)
            return False
        
        # Berechne Z-Score
        import numpy as np
        times = np.array(self.cycle_times_buffer)
        mean = np.mean(times)
        std = np.std(times)
        
        if std == 0:
            return False
        
        z_score = abs((cycle_time - mean) / std)
        
        # Buffer aktualisieren (rolling window)
        self.cycle_times_buffer.append(cycle_time)
        if len(self.cycle_times_buffer) > 50:
            self.cycle_times_buffer.pop(0)
        
        return z_score > self.z_threshold
```

---

## Alternative: Ohne Enhanced Dashboard

Falls du **kein** Enhanced Dashboard hast, füge das Widget als separates Dock-Widget hinzu:

```python
from PyQt6.QtWidgets import QDockWidget

class MainWindow(QMainWindow):
    def setup_ui(self):
        # ... existing code ...
        
        # Live-Stats als Dock-Widget
        self.live_stats_dock = QDockWidget("📊 Live-Statistiken", self)
        self.live_stats_dock.setWidget(self.live_stats_widget)
        self.live_stats_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        
        # Rechts andocken
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.live_stats_dock)
        
        print('✅ Live-Stats als Dock-Widget hinzugefügt')
```

---

## Testing

### 1. Standalone-Test (ohne Integration)

```bash
python live_stats_widget.py
```

Sollte ein Test-Fenster öffnen mit Simulate-Button.

### 2. Integration-Test

```bash
python main.py
```

Prüfe:
- ✅ Widget ist sichtbar (im Dashboard oder als Dock)
- ✅ Starte einen Testlauf
- ✅ Widget zeigt Live-Updates
- ✅ Statistiken aktualisieren sich
- ✅ Chart zeigt Verlauf

### 3. Debug-Output

Falls es nicht funktioniert, füge Debug-Prints hinzu:

```python
# In main.py
print(f"Live-Stats Widget vorhanden: {hasattr(self, 'live_stats_widget')}")
print(f"Signal verbunden: {hasattr(self.seq_runner, 'cycle_completed')}")

# Im SequenceRunner
print(f"Emittiere cycle_completed: {cycle_time:.2f}ms, Anomalie: {is_anomaly}")

# Im Widget
def add_cycle(self, cycle_time, is_anomaly):
    print(f"📊 Neuer Zyklus empfangen: {cycle_time:.2f}ms")
    # ... rest ...
```

---

## Troubleshooting

### Problem: Widget zeigt keine Updates

**Lösung:**
1. Prüfe ob Signal verbunden ist
2. Prüfe ob `start_monitoring()` aufgerufen wurde
3. Prüfe ob `cycle_completed` emittiert wird

### Problem: "QTimer can only be used with threads started with QThread"

**Lösung:**
Widget muss im Main-Thread erstellt werden.

### Problem: Chart zeigt nichts

**Lösung:**
Stelle sicher, dass `add_cycle()` aufgerufen wird und Widget sichtbar ist.

---

## Erweiterte Konfiguration

### Anpassung der Update-Frequenz

```python
# Im Widget
self.update_timer.setInterval(1000)  # 1 Sekunde statt 500ms
```

### Chart-Historie ändern

```python
# Beim Erstellen
self.mini_chart = MiniChartWidget(max_points=100)  # Statt 50
```

### Farben anpassen

```python
# Im MiniChartWidget.__init__
self.line_color = QColor('#YOUR_COLOR')
self.anomaly_color = QColor('#YOUR_COLOR')
```

---

## API-Referenz

### LiveStatsWidget

**Methoden:**
- `start_monitoring(total_cycles: int)` - Startet Monitoring
- `stop_monitoring()` - Stoppt Monitoring  
- `add_cycle(cycle_time: float, is_anomaly: bool)` - Fügt Zyklus hinzu
- `get_stats() -> dict` - Gibt aktuelle Stats zurück

**Signals:**
- `pause_requested` - Emittiert wenn Nutzer pausieren will (noch nicht verwendet)

---

Viel Erfolg! 🚀
