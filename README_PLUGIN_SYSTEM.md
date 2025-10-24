# 🔌 Plugin-System Update für Arduino Control Panel

## Neue Features

Das Arduino Control Panel wurde um ein vollständiges **Plugin-System** erweitert!

### ✨ Was ist neu?

- **🔌 Vollständiges Plugin-System** - Erweitere die App ohne Core-Änderungen
- **8 Plugin-Typen** - Sensoren, Export, Analyse, Visualisierung, Hardware, etc.
- **📦 Plugin-Manager UI** - Verwalte Plugins grafisch
- **🎯 Event-System** - Reagiere auf App-Events
- **🔒 Sicherer Kontext** - Kontrollierter Zugriff auf App-Funktionen
- **📚 Umfassende Dokumentation** - Entwickler-Guide mit Beispielen

### 🚀 Quick Start

1. **Plugin entwickeln** - Siehe `PLUGIN_SYSTEM_README.md`
2. **Plugin aktivieren** - Im Tab "🔌 Plugins"
3. **Fertig!** - Dein Plugin erweitert die App

### 📖 Dokumentation

- **[Plugin-System Dokumentation](PLUGIN_SYSTEM_README.md)** - Vollständige API-Referenz
- **[Beispiel-Plugin](plugins/installed/example_data_export.py)** - CSV-Export Plugin

### 🛠️ Integration in main.py

Das Plugin-System ist vollständig in die Hauptanwendung integriert:

```python
# Automatisches Laden beim Start
if PLUGIN_SYSTEM_AVAILABLE:
    self.app_context = ApplicationContext(self, self.db, self.config_manager)
    self.plugin_manager = PluginManager(self.app_context)
    self.plugin_manager.load_all_plugins()

# Plugin-Manager Tab in der UI
self.tabs.addTab(self.plugin_manager_tab, "🔌 Plugins")
```

### 📁 Verzeichnisstruktur

```
Arduino-Control-Panel/
├── plugins/
│   ├── plugin_api.py           # API-Definition
│   ├── plugin_manager.py       # Plugin-Manager
│   ├── installed/              # Offizielle Plugins
│   │   └── example_data_export.py
│   └── user/                   # Benutzer-Plugins
├── ui/
│   └── plugin_manager_tab.py   # Plugin-UI
└── PLUGIN_SYSTEM_README.md     # Dokumentation
```

### 🎨 Beispiel: Eigenes Plugin erstellen

```python
from plugins import PluginInterface, PluginMetadata, PluginType

class MyPlugin(PluginInterface):
    def get_metadata(self):
        return PluginMetadata(
            id="com.example.my_plugin",
            name="My Plugin",
            version="1.0.0",
            author="Your Name",
            description="Was dein Plugin macht",
            plugin_type=PluginType.EXPORT
        )

    def initialize(self, app_context):
        # Plugin initialisieren
        return True

    def shutdown(self):
        # Aufräumen
        return True
```

Speichere als `plugins/user/my_plugin.py` und starte die App neu!

### 🔧 Weitere Updates

Zusätzlich zum Plugin-System:

- ✅ **Unicode-Logging Fix** - Emoji-Support für Windows
- ✅ **Deutsches Datumsformat** - Robustes Parsing
- ✅ **Live-Stats Auto-Start** - Mit echter Zyklus-Anzahl
- ✅ **Board-Typ Selector** - 10 Board-Typen wählbar
- ✅ **Makro-Bearbeiten** - Vollständiger Edit-Dialog

### 📦 Commits

- **feat: Add comprehensive Plugin System** - Vollständiges Plugin-System
- **feat: Implement all pending TODOs** - 4 Code-Verbesserungen
- **fix: Support German date format** - Datumsformat-Fix
- **fix: Resolve logging Unicode error** - Emoji-Support

### 🎯 Nächste Schritte

1. **Plugins entwickeln** - Nutze die API
2. **ML-Features** - Als Plugin implementieren
3. **Community** - Teile deine Plugins

---

Für Details siehe [PLUGIN_SYSTEM_README.md](PLUGIN_SYSTEM_README.md)
