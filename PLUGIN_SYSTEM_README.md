# 🔌 Plugin-System für Arduino Control Panel

## Übersicht

Das Arduino Control Panel verfügt über ein leistungsstarkes, erweiterbares Plugin-System, das es Entwicklern ermöglicht, die Funktionalität der Anwendung zu erweitern, ohne den Kern-Code zu modifizieren.

## Features

✅ **Einfache Plugin-Entwicklung** - Klare API und Basis-Klassen
✅ **Typ-basierte Plugins** - Sensoren, Export, Analyse, Visualisierung, etc.
✅ **Automatisches Laden** - Plugins werden beim Start automatisch entdeckt und geladen
✅ **Abhängigkeits-Management** - Plugins können andere Plugins als Abhängigkeiten definieren
✅ **Prioritäts-System** - Kontrolliere die Lade-Reihenfolge
✅ **Event-System** - Reagiere auf Anwendungs-Events (Hooks)
✅ **Sicherer Kontext** - Plugins haben nur kontrollierten Zugriff auf App-Funktionen
✅ **UI-Integration** - Verwalte Plugins über eine grafische Oberfläche
✅ **Hot-Enable/Disable** - Aktiviere/Deaktiviere Plugins zur Laufzeit

---

## Plugin-Typen

Das System unterstützt verschiedene Plugin-Typen:

| Typ | Beschreibung | Beispiele |
|-----|--------------|-----------|
| **SENSOR** | Neue Sensor-Typen | DHT22, BME280, Ultraschall |
| **EXPORT** | Export-Formate | CSV, Excel, JSON, XML |
| **ANALYSIS** | Datenanalyse | FFT, Korrelation, ML-Modelle |
| **VISUALIZATION** | Visualisierung | Custom Charts, 3D-Plots |
| **HARDWARE** | Hardware-Integration | I2C, SPI, OneWire |
| **AUTOMATION** | Automatisierung | Scheduler, Trigger |
| **UI** | UI-Erweiterungen | Custom Tabs, Widgets |
| **GENERAL** | Allgemein | Diverse Funktionen |

---

## Schnellstart: Dein erstes Plugin

### 1. Plugin-Datei erstellen

Erstelle eine Python-Datei in `plugins/user/` oder `plugins/installed/`:

```python
# plugins/user/my_first_plugin.py
from plugins import (
    PluginInterface, PluginMetadata, PluginType,
    PluginPriority, PluginCapability, ApplicationContext
)
from typing import List

class MyFirstPlugin(PluginInterface):
    """Mein erstes Plugin!"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="com.example.my_first_plugin",
            name="My First Plugin",
            version="1.0.0",
            author="Dein Name",
            description="Mein erstes Arduino Control Panel Plugin",
            plugin_type=PluginType.GENERAL,
            priority=PluginPriority.NORMAL
        )

    def get_capabilities(self) -> List[PluginCapability]:
        return [PluginCapability.ADD_MENU]

    def initialize(self, app_context: ApplicationContext) -> bool:
        self._app_context = app_context
        print("✅ My First Plugin initialisiert!")

        # Registriere Event-Handler
        app_context.register_callback(
            "sequence_start",
            self.on_sequence_start
        )

        return True

    def shutdown(self) -> bool:
        print("Plugin heruntergefahren")
        return True

    def on_sequence_start(self, seq_id):
        """Wird aufgerufen wenn eine Sequenz startet"""
        print(f"Sequenz {seq_id} gestartet!")
```

### 2. Plugin laden

Starte die Anwendung neu. Das Plugin wird automatisch entdeckt und geladen.

Oder verwende die Plugin-Verwaltungs-UI im Tab "🔌 Plugins".

---

## Plugin-API Referenz

### PluginInterface

Die Basis-Klasse für alle Plugins.

#### Abstrakte Methoden (müssen implementiert werden)

```python
def get_metadata(self) -> PluginMetadata:
    """Gibt Plugin-Metadaten zurück"""
    pass

def get_capabilities(self) -> List[PluginCapability]:
    """Gibt Plugin-Fähigkeiten zurück"""
    pass

def initialize(self, app_context: ApplicationContext) -> bool:
    """Initialisiert das Plugin"""
    pass

def shutdown(self) -> bool:
    """Fährt das Plugin herunter"""
    pass
```

#### Optionale Methoden

```python
def enable(self) -> bool:
    """Aktiviert das Plugin"""
    pass

def disable(self) -> bool:
    """Deaktiviert das Plugin"""
    pass

def get_settings_widget(self) -> Optional[QWidget]:
    """Gibt Settings-Widget zurück"""
    pass
```

### ApplicationContext

Sichere Schnittstelle zum Zugriff auf App-Funktionen.

```python
# Datenbank-Zugriff
db = app_context.get_database()

# Config-Manager
config = app_context.get_config_manager()

# Events registrieren
app_context.register_callback("sequence_start", callback_func)

# Events triggern
app_context.trigger_event("custom_event", data)

# UI-Elemente hinzufügen
app_context.add_menu_item("Tools", "My Tool", callback)
app_context.add_tab("My Tab", widget)

# Daten abrufen
sensor_data = app_context.get_sensor_data("sensor_id")

# Befehle senden
app_context.send_command("SET_PIN", {"pin": "D8", "value": 1})
```

---

## Verfügbare Events (Hooks)

Registriere Callbacks für diese Events:

### Anwendungs-Lifecycle
- `app_startup` - App startet
- `app_shutdown` - App beendet sich

### Sequenz-Events
- `sequence_start` - Sequenz startet
- `sequence_end` - Sequenz endet
- `sequence_step` - Sequenz-Schritt ausgeführt

### Daten-Events
- `data_received` - Daten vom Arduino empfangen
- `data_processed` - Daten verarbeitet
- `data_saved` - Daten in DB gespeichert

### Hardware-Events
- `arduino_connected` - Arduino verbunden
- `arduino_disconnected` - Arduino getrennt
- `pin_changed` - Pin-Zustand geändert

---

## Beispiele

### 1. Einfacher Logger

```python
class LoggerPlugin(PluginInterface):
    def initialize(self, app_context):
        self._app_context = app_context

        # Logge alle Events
        for event in ['sequence_start', 'sequence_end', 'data_received']:
            app_context.register_callback(event, self.log_event)

        return True

    def log_event(self, *args, **kwargs):
        with open('plugin_log.txt', 'a') as f:
            f.write(f"{datetime.now()}: {args}, {kwargs}\n")
```

### 2. JSON Export Plugin

```python
class JSONExportPlugin(PluginInterface):
    def get_metadata(self):
        return PluginMetadata(
            id="com.example.json_export",
            name="JSON Exporter",
            plugin_type=PluginType.EXPORT,
            # ...
        )

    def initialize(self, app_context):
        self._app_context = app_context
        # Füge Menü-Item hinzu
        app_context.add_menu_item(
            "Export",
            "Als JSON exportieren",
            self.export_json
        )
        return True

    def export_json(self):
        db = self._app_context.get_database()
        # Export-Logik...
```

### 3. Benachrichtigungs-Plugin

```python
class NotificationPlugin(PluginInterface):
    def initialize(self, app_context):
        self._app_context = app_context

        # Benachrichtige bei Sequenz-Ende
        app_context.register_callback(
            'sequence_end',
            self.send_notification
        )
        return True

    def send_notification(self, seq_id, status):
        # Email, Telegram, Desktop-Notification, etc.
        pass
```

---

## Plugin-Verzeichnisse

```
plugins/
├── __init__.py               # Plugin-System Initialisierung
├── plugin_api.py             # API-Definitionen
├── plugin_manager.py         # Plugin-Manager
├── installed/                # Vorinstallierte Plugins
│   ├── __init__.py
│   └── example_data_export.py
└── user/                     # Benutzer-Plugins
    └── __init__.py
```

- **`plugins/installed/`** - Vorinstallierte/offizielle Plugins
- **`plugins/user/`** - Eigene Plugins

---

## Plugin-Metadaten

```python
PluginMetadata(
    id="com.example.my_plugin",        # Eindeutige ID (Reverse-Domain)
    name="My Plugin",                  # Anzeigename
    version="1.0.0",                   # Semantic Versioning
    author="Your Name",                # Autor
    description="What it does",        # Beschreibung
    plugin_type=PluginType.EXPORT,     # Typ
    priority=PluginPriority.NORMAL,    # Lade-Priorität
    dependencies=["other.plugin.id"],  # Abhängigkeiten
    min_app_version="1.0.0",           # Min. App-Version
    website="https://...",             # Website/Repo
    license="MIT"                      # Lizenz
)
```

---

## Capabilities

Definiere, was dein Plugin kann:

```python
def get_capabilities(self):
    return [
        PluginCapability.READ_SENSOR_DATA,
        PluginCapability.EXPORT_DATA,
        PluginCapability.ADD_MENU,
        PluginCapability.DATABASE_ACCESS,
        # ...
    ]
```

Verfügbare Capabilities:
- `READ_SENSOR_DATA`, `WRITE_SENSOR_DATA`, `PROCESS_DATA`, `EXPORT_DATA`
- `HARDWARE_CONTROL`, `SERIAL_COMMUNICATION`
- `ADD_MENU`, `ADD_TAB`, `ADD_WIDGET`, `ADD_TOOLBAR`
- `BACKGROUND_TASK`, `DATABASE_ACCESS`, `FILE_ACCESS`, `NETWORK_ACCESS`

---

## Prioritäten

Kontrolliere die Lade-Reihenfolge:

```python
PluginPriority.CRITICAL  # 0 - Muss zuerst geladen werden
PluginPriority.HIGH      # 1 - Hohe Priorität
PluginPriority.NORMAL    # 2 - Standard
PluginPriority.LOW       # 3 - Niedrige Priorität
```

---

## Abhängigkeiten

```python
PluginMetadata(
    # ...
    dependencies=[
        "com.example.base_plugin",
        "com.example.util_plugin"
    ]
)
```

Das Plugin wird nur geladen, wenn alle Abhängigkeiten erfüllt sind.

---

## Best Practices

### ✅ DO

- Verwende eindeutige Plugin-IDs (Reverse-Domain-Notation)
- Implementiere saubere `shutdown()` Methoden
- Nutze das Event-System statt direkter Zugriffe
- Dokumentiere dein Plugin
- Teste mit verschiedenen App-Versionen
- Handle Exceptions gracefully

### ❌ DON'T

- Greife nicht direkt auf private App-Attribute zu
- Blockiere nicht den Main-Thread
- Speichere keine sensitiven Daten unverschlüsselt
- Verlasse dich nicht auf bestimmte Lade-Reihenfolgen (außer via Priorität)

---

## Debugging

### Logging

```python
import logging
logger = logging.getLogger(f"Plugin.{self.get_metadata().name}")

def initialize(self, app_context):
    logger.info("Plugin initialisiert")
    logger.debug("Debug-Info")
    logger.warning("Warnung")
    logger.error("Fehler")
```

### Print-Statements

Print-Ausgaben erscheinen in der Konsole:

```python
print(f"✅ {self.get_metadata().name} gestartet")
```

---

## Plugin-Verwaltungs-UI

Zugriff über den Tab "🔌 Plugins":

- **Plugin-Liste** - Alle verfügbaren Plugins
- **Plugin-Details** - Metadaten, Capabilities, Status
- **Aktivieren/Deaktivieren** - Zur Laufzeit
- **Neu laden** - Entdecke neue Plugins
- **Einstellungen** - Falls vom Plugin bereitgestellt

---

## Veröffentlichung

### Eigene Plugins teilen

1. Erstelle ein GitHub-Repository
2. Füge README und Beispiele hinzu
3. Teile den Link in der Community

### Plugin-Format

Einzelne `.py` Datei oder Verzeichnis mit `__init__.py`:

```
my_awesome_plugin/
├── __init__.py           # Plugin-Klasse
├── README.md             # Dokumentation
├── requirements.txt      # Abhängigkeiten
└── assets/               # Ressourcen
```

---

## Support & Community

- **GitHub Issues**: https://github.com/Grown2206/Arduino-Control-Panel/issues
- **Discussions**: Plugin-Entwicklung und Ideen
- **Wiki**: Weitere Beispiele und Tutorials

---

## Lizenz

Das Plugin-System ist Teil des Arduino Control Panels und steht unter der gleichen Lizenz.

Plugins können eigene Lizenzen haben - bitte angeben in den Metadaten.

---

**Viel Erfolg beim Plugin-Entwickeln! 🚀**
