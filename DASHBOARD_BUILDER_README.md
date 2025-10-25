# Dashboard Builder 🎨

Drag & Drop Editor zum Erstellen individueller Dashboards für das Arduino Control Panel.

## Features

### 🎯 Haupt-Features
- **Drag & Drop Interface** - Ziehen Sie Widgets auf das Canvas
- **6 Widget-Typen** - Verschiedene Visualisierungen verfügbar
- **Edit-Modus** - Widgets können verschoben und resized werden
- **Layout-Speicherung** - Speichern und Laden von Dashboard-Layouts
- **HTML-Export** - Export als standalone HTML-Datei
- **Responsive** - Widgets passen sich an

### 📊 Verfügbare Widgets

#### 1. Value Display Widget
- Zeigt einen einzelnen Wert mit Einheit an
- Ideal für Temperatur, Feuchtigkeit, etc.
- Anpassbare Farben

#### 2. Gauge Widget
- Tachometer/Gauge-Anzeige
- Min/Max-Werte konfigurierbar
- Farbcodierung: Grün → Gelb → Orange → Rot
- Warning- und Critical-Schwellwerte

#### 3. LED Widget
- LED-Indikator für ON/OFF States
- Glow-Effekt wenn aktiv
- Anpassbare Farben

#### 4. Button Widget
- Anklickbarer Button
- Sendet Events beim Klicken
- Kann Commands auslösen

#### 5. Progress Bar Widget
- Fortschrittsbalken
- Prozentanzeige
- Anpassbarer Maximalwert

#### 6. Label Widget
- Einfaches Text-Label
- Word-Wrap Support
- Anpassbare Schriftgröße und Farbe

## Verwendung

### Dashboard erstellen

1. **Widget hinzufügen**
   - Widget aus der Palette auswählen
   - Auf das Canvas ziehen
   - Widget wird automatisch platziert

2. **Widget positionieren**
   - Im Edit-Modus: Widget anklicken und ziehen
   - Position wird automatisch gespeichert

3. **Widget resizen**
   - Im Edit-Modus: Grünes Handle unten rechts ziehen
   - Minimale/Maximale Größe wird eingehalten

4. **Widget konfigurieren**
   - Rechtsklick auf Widget → "Konfigurieren"
   - Titel, Farben, etc. ändern

5. **Widget löschen**
   - Rechtsklick auf Widget → "Löschen"

### Dashboard speichern

```python
# Über UI: Toolbar → "💾 Speichern"
# Datei wird als JSON gespeichert

# Programmgesteuert:
dashboard_builder.save_dashboard()
```

### Dashboard laden

```python
# Über UI: Toolbar → "📂 Öffnen"
# JSON-Datei auswählen

# Programmgesteuert:
dashboard_builder.open_dashboard()
```

### HTML Export

```python
# Über UI: Toolbar → "🌐 HTML Export"
# Erstellt standalone HTML-Datei

# Features des Exports:
# - Alle Widgets mit Positionierung
# - CSS-Styling eingebettet
# - Bereit für WebSocket-Integration
```

## Programmierung

### Neues Widget erstellen

```python
from ui.dashboard_builder.base_widget import DashboardWidgetBase, DashboardWidgetFactory

class MyCustomWidget(DashboardWidgetBase):
    def __init__(self, parent=None):
        super().__init__(title="Custom Widget", parent=parent)
        self.widget_type = "custom"

        # UI Setup
        self.value_label = QLabel("Value")
        self.content_layout.addWidget(self.value_label)

    def update_data(self, data):
        """Aktualisiert Widget-Daten"""
        self.value_label.setText(str(data))

    def to_html(self):
        """HTML-Export"""
        return f"<div>Custom Widget: {self.value_label.text()}</div>"

# Widget registrieren
DashboardWidgetFactory.register_widget_type("custom", MyCustomWidget)
```

### Widget-Daten aktualisieren

```python
# Einzelnes Widget
dashboard_builder.update_widget_data(widget_id, data)

# Mehrere Widgets
canvas = dashboard_builder.get_canvas()
for widget_id, widget in canvas.widgets.items():
    widget.update_data(new_data)
```

### Events abfangen

```python
# Widget-Events
widget.widget_moved.connect(on_widget_moved)
widget.widget_resized.connect(on_widget_resized)
widget.widget_deleted.connect(on_widget_deleted)
widget.widget_config_changed.connect(on_config_changed)

# Canvas-Events
canvas.widget_added.connect(on_widget_added)
canvas.widget_removed.connect(on_widget_removed)
canvas.layout_changed.connect(on_layout_changed)

# Button-Widget Click
button_widget.clicked.connect(lambda widget_id: print(f"Clicked: {widget_id}"))
```

## Dateiformate

### Dashboard JSON

```json
{
  "version": "1.0",
  "created": "2025-10-24T12:34:56",
  "canvas_size": [800, 600],
  "widgets": [
    {
      "widget_id": "abc-123-def",
      "widget_type": "value_display",
      "title": "Temperatur",
      "position": [100, 50],
      "size": [150, 100],
      "config": {
        "background_color": "#2b2b2b",
        "border_color": "#555",
        "title_color": "#e0e0e0",
        "update_interval": 1000
      }
    }
  ]
}
```

## Keyboard Shortcuts

- **Ctrl+N** - Neues Dashboard
- **Ctrl+O** - Dashboard öffnen
- **Ctrl+S** - Dashboard speichern
- **Entf** - Ausgewähltes Widget löschen
- **Esc** - Edit-Modus beenden

## Beispiele

### Beispiel 1: Sensor-Dashboard

```python
# Dashboard Builder öffnen
dashboard_builder = DashboardBuilderWidget()

# LED für Verbindungsstatus
led_widget = DashboardWidgetFactory.create_widget("led")
led_widget.config['title'] = "Verbindung"
dashboard_builder.canvas.add_widget(led_widget, (20, 20))

# Gauge für Temperatur
gauge_widget = DashboardWidgetFactory.create_widget("gauge")
gauge_widget.config['title'] = "Temperatur"
gauge_widget.min_value = 0
gauge_widget.max_value = 100
dashboard_builder.canvas.add_widget(gauge_widget, (200, 20))

# Value Display für Luftfeuchtigkeit
value_widget = DashboardWidgetFactory.create_widget("value_display")
value_widget.config['title'] = "Luftfeuchtigkeit"
dashboard_builder.canvas.add_widget(value_widget, (420, 20))

# Speichern
dashboard_builder.save_dashboard_as()
```

### Beispiel 2: Live-Daten-Update

```python
import time
from PyQt6.QtCore import QTimer

# Timer für Updates
update_timer = QTimer()

def update_dashboard():
    # Simuliere Sensor-Daten
    temperature = 23.5 + (time.time() % 10)
    humidity = 45.2
    is_connected = True

    # Update Widgets
    dashboard_builder.update_widget_data("gauge_temp", {
        'value': temperature,
        'max': 100
    })

    dashboard_builder.update_widget_data("value_humidity", {
        'value': humidity,
        'unit': '%'
    })

    dashboard_builder.update_widget_data("led_conn", is_connected)

# Starte Updates
update_timer.timeout.connect(update_dashboard)
update_timer.start(1000)  # Jede Sekunde
```

### Beispiel 3: Button-Actions

```python
# Button-Widget erstellen
button = DashboardWidgetFactory.create_widget("button")
button.config['button_text'] = "LED AN"
button.config['button_command'] = {'command': 'digital_write', 'pin': 13, 'value': 1}

# Click-Handler
def on_button_clicked(widget_id):
    widget = canvas.widgets[widget_id]
    command = widget.config.get('button_command')
    if command:
        send_command(command)  # Sende an Arduino

button.clicked.connect(on_button_clicked)
```

## API-Referenz

### DashboardBuilderWidget

| Methode | Beschreibung |
|---------|-------------|
| `new_dashboard()` | Erstellt neues Dashboard |
| `open_dashboard()` | Öffnet Dashboard aus Datei |
| `save_dashboard()` | Speichert Dashboard |
| `save_dashboard_as()` | Speichert unter neuem Namen |
| `export_html()` | Exportiert als HTML |
| `clear_dashboard()` | Löscht alle Widgets |
| `get_canvas()` | Gibt Canvas-Objekt zurück |
| `update_widget_data(id, data)` | Aktualisiert Widget-Daten |

### DashboardCanvas

| Methode | Beschreibung |
|---------|-------------|
| `add_widget(widget, pos)` | Fügt Widget hinzu |
| `remove_widget(widget_id)` | Entfernt Widget |
| `set_edit_mode(enabled)` | Setzt Edit-Modus |
| `clear()` | Löscht alle Widgets |
| `get_layout_config()` | Gibt Layout als JSON |
| `load_layout_config(config)` | Lädt Layout |

### DashboardWidgetFactory

| Methode | Beschreibung |
|---------|-------------|
| `register_widget_type(type, class)` | Registriert Widget-Typ |
| `create_widget(type, config)` | Erstellt Widget |
| `get_available_widgets()` | Liste aller Typen |

## Tipps & Tricks

### Performance-Optimierung
- Limitieren Sie Update-Rate für Widgets (max. 10 Hz)
- Verwenden Sie QTimer für Updates statt Dauerschleife
- Deaktivieren Sie Edit-Modus im Produktivbetrieb

### Best Practices
- Gruppieren Sie zusammengehörige Widgets
- Verwenden Sie aussagekräftige Titel
- Speichern Sie Layouts regelmäßig
- Testen Sie HTML-Export vor Deployment

### Troubleshooting

**Problem**: Widget lässt sich nicht verschieben
- **Lösung**: Edit-Modus aktivieren (Button oben rechts)

**Problem**: Widget wird zu klein dargestellt
- **Lösung**: Minimum-Größe wird eingehalten, Resize-Handle nutzen

**Problem**: HTML-Export zeigt keine Daten
- **Lösung**: HTML ist statisch, WebSocket-Integration erforderlich für Live-Daten

## Roadmap

### Geplante Features
- [ ] Grid-Snapping für Widgets
- [ ] Widget-Gruppen
- [ ] Mehr Widget-Typen (Chart, Table, Video)
- [ ] Themes/Templates
- [ ] Undo/Redo
- [ ] Copy/Paste für Widgets
- [ ] Export als PNG/PDF
- [ ] WebSocket-Integration im HTML-Export
- [ ] Mobile-optimierte Layouts

## Lizenz

Dieses Feature ist Teil des Arduino Control Panel Projekts.

---

**Erstellt**: Oktober 2025
**Version**: 1.0
