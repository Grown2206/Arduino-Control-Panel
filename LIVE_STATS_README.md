# 📊 Live-Statistik-Widget für Arduino Control Panel

**Version:** 2.5.0  
**Datum:** 23. Oktober 2025  
**Status:** Production Ready ✅

---

## 🎯 Beschreibung

Echtzeit-Monitoring-Widget für Testläufe im Arduino Control Panel. Zeigt Live-Statistiken, Trends und Anomalien während der Sequenz-Ausführung.

---

## ✨ Features

### Echtzeit-Monitoring
- 📊 **Live-Zyklen-Counter** mit Fortschrittsanzeige
- ⏱️ **Durchschnittliche Zykluszeit** (Echtzeit-Berechnung)
- 📈 **Live-Chart** der letzten 100 Zyklen
- 📉 **Trend-Analyse** (↑ schneller / ↓ langsamer / → stabil)

### Status-Anzeigen
- 🟢 **Aktueller Status** (Bereit / Läuft / Abgeschlossen)
- ⚠️ **Anomalie-Erkennung** (>150% Durchschnitt)
- 📊 **Fortschrittsbalken** mit Prozent

### Integration
- 🔌 **Dock-Widget** (rechte Seite der GUI)
- 🔔 **Signal-basiert** (cycle_completed)
- 🎯 **Automatisches Start/Stop** bei Tests

---

## 📦 Installation

### Voraussetzungen
```bash
Python 3.8+
PyQt6
NumPy
pyqtgraph
```

### Dateien hinzufügen
```bash
# Widget-Datei ins Hauptverzeichnis
live_stats_widget.py

# Bereits integriert in:
main.py                  # Widget-Initialisierung & Dock
core/sequence_runner.py  # cycle_completed Signal
ui/sequence_tab.py       # start_monitoring() Aufruf
```

### Integration prüfen
```python
# In main.py sollte vorhanden sein:
from live_stats_widget import LiveStatsWidget

self.live_stats_widget = LiveStatsWidget()
self.live_stats_dock = QDockWidget("📊 Live-Statistiken", self)
self.live_stats_dock.setWidget(self.live_stats_widget)
```

---

## 🚀 Verwendung

### Automatische Verwendung
Das Widget startet automatisch bei jedem Testlauf:

1. **Testlauf starten** → Widget zeigt "Zyklen: 0 / X"
2. **Während Test** → Live-Updates der Statistiken
3. **Nach Test** → Status "ABGESCHLOSSEN"

### Manuelle Steuerung
```python
# Monitoring starten
widget.start_monitoring(total_cycles=100)

# Zyklus hinzufügen
widget.add_cycle(cycle_time_ms=247.3, is_anomaly=False)

# Monitoring stoppen
widget.stop_monitoring()

# Reset
widget.reset()
```

---

## 🎨 UI-Komponenten

### Hauptanzeige
```
┌──────────────────────────┐
│ 📊 Live-Statistiken      │
├──────────────────────────┤
│ Zyklen: 37 / 100         │
│ [▓▓▓▓░░░░░░] 37%        │
│                          │
│ Ø Zykluszeit: 247.3 ms   │
│                          │
│ Aktuell: ✓ OK            │
│ Trend: → Stabil          │
│                          │
│ [Live-Chart]             │
└──────────────────────────┘
```

### Status-Icons
- ⏸️ **Bereit** - Wartet auf Start
- 🟢 **Läuft** - Test aktiv, OK
- 🔴 **Anomalie** - Zykluszeit zu hoch
- ✅ **Abgeschlossen** - Test beendet

### Trend-Icons
- ↑ **Schneller** - Zykluszeit nimmt ab
- ↓ **Langsamer** - Zykluszeit nimmt zu
- → **Stabil** - Keine signifikante Änderung

---

## 🔧 Konfiguration

### Anomalie-Schwellwert
```python
# In live_stats_widget.py (Zeile ~80)
ANOMALY_THRESHOLD = 1.5  # 150% des Durchschnitts
```

### Chart-Einstellungen
```python
# Anzahl der angezeigten Datenpunkte
MAX_CHART_POINTS = 100

# Chart-Farben
CHART_COLOR = (52, 152, 219)  # Blau
ANOMALY_COLOR = (231, 76, 60)  # Rot
```

---

## 📡 Signal-Integration

### Signal definieren
```python
# In SequenceRunner (core/sequence_runner.py)
from PyQt6.QtCore import pyqtSignal

class SequenceRunner:
    cycle_completed = pyqtSignal(float, bool)  # (time_ms, is_anomaly)
```

### Signal emittieren
```python
# Nach jedem Zyklus
cycle_time_ms = (time.time() - start) * 1000
is_anomaly = False  # Oder eigene Logik
self.cycle_completed.emit(cycle_time_ms, is_anomaly)
```

### Signal verbinden
```python
# In MainWindow.__init__ oder setup_connections()
self.seq_runner.cycle_completed.connect(
    self.live_stats_widget.add_cycle
)
```

---

## 🐛 Troubleshooting

### Widget nicht sichtbar?
```python
# Prüfe in main.py:
print(hasattr(self, 'live_stats_widget'))  # Sollte True sein
print(hasattr(self, 'live_stats_dock'))     # Sollte True sein
```

### Keine Live-Updates?
```python
# Prüfe Signal-Verbindung:
print(hasattr(self.seq_runner, 'cycle_completed'))  # Signal vorhanden?

# Prüfe emit() Aufruf im SequenceRunner
```

### Widget zeigt nicht "ABGESCHLOSSEN"?
```python
# stop_monitoring() muss aufgerufen werden:
# In ui/sequence_tab.py, Methode set_running_state()
if not is_running:
    if hasattr(self.main_window, 'live_stats_widget'):
        self.main_window.live_stats_widget.stop_monitoring()
```

---

## 📊 API-Referenz

### `LiveStatsWidget`

#### Methoden

**`start_monitoring(total_cycles: int)`**
- Startet Monitoring für `total_cycles` Zyklen
- Reset aller Statistiken
- Setzt Status auf "Läuft"

**`add_cycle(cycle_time: float, is_anomaly: bool = False)`**
- Fügt Zyklus-Daten hinzu
- `cycle_time`: Zeit in Millisekunden
- `is_anomaly`: Ob Zyklus eine Anomalie ist
- Aktualisiert alle Anzeigen

**`stop_monitoring()`**
- Stoppt Monitoring
- Setzt Status auf "ABGESCHLOSSEN"
- Behält Statistiken

**`reset()`**
- Löscht alle Daten
- Setzt auf Anfangszustand zurück

#### Properties

**`current_cycle: int`**
- Aktueller Zyklus-Counter

**`total_cycles: int`**
- Gesamtzahl der Zyklen

**`average_time: float`**
- Durchschnittliche Zykluszeit (ms)

**`is_monitoring: bool`**
- Ob aktuell aktiv

---

## 🧪 Testing

### Standalone-Test
```bash
python live_stats_widget.py
```

Öffnet Test-Fenster mit simulierten Daten.

### Integration-Test
```bash
python -B main.py
# Starte einen Testlauf
# Beobachte Widget rechts
```

---

## 📝 Changelog

### v2.5.0 (23.10.2025)
- ✅ Initial Release
- ✅ Live-Monitoring
- ✅ Anomalie-Erkennung
- ✅ Trend-Analyse
- ✅ Live-Chart
- ✅ Dock-Widget Integration

### Geplant für v2.6.0
- [ ] Konfigurierbare Anomalie-Schwellwerte
- [ ] Export von Statistiken
- [ ] Historische Vergleiche
- [ ] Alarm-Benachrichtigungen

---

## 🤝 Beitragen

Verbesserungsvorschläge und Pull Requests sind willkommen!

### Guidelines
1. Code-Style: PEP 8
2. Docstrings für alle Methoden
3. Type Hints verwenden
4. Tests hinzufügen

---

## 📄 Lizenz

[Deine Lizenz hier]

---

## 👥 Autoren

**Drexler Dynamics Team**

---

## 🙏 Danksagungen

- PyQt6 für das UI-Framework
- pyqtgraph für Charts
- NumPy für Berechnungen

---

## 📞 Support

- **Issues:** [GitHub Issues]
- **Email:** [deine-email]
- **Dokumentation:** Siehe `VERBESSERUNGSVORSCHLAEGE.md`

---

**Happy Monitoring!** 📊✨
