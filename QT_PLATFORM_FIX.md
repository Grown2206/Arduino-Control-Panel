# Qt Platform Plugin Error - Lösungsanleitung

## Problem
```
qt.qpa.plugin: Could not load the Qt platform plugin "windows" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized.
```

## Ursache
Dieses Problem tritt auf Windows auf, wenn PyQt6 die Windows-Plattform-Plugins nicht richtig laden kann. Dies kann durch mehrere Faktoren verursacht werden:
- Fehlende oder beschädigte Qt-DLLs
- Konfliktierend Qt-Installationen
- Falsche Umgebungsvariablen
- Probleme mit der virtuellen Umgebung

## Lösungen (in dieser Reihenfolge ausprobieren)

### Lösung 1: PyQt6 neu installieren
Das häufigste Problem ist eine beschädigte PyQt6-Installation.

```bash
# Aktiviere die virtuelle Umgebung
.venv\Scripts\activate

# Deinstalliere PyQt6 komplett
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip -y

# Installiere PyQt6 neu
pip install PyQt6

# Teste die Installation
python -c "from PyQt6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); print('PyQt6 funktioniert!')"
```

### Lösung 2: Umgebungsvariable setzen
Manchmal muss Qt explizit mitgeteilt werden, wo die Plugins sind.

```bash
# Finde den Plugin-Pfad
python -c "import PyQt6; import os; print(os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins'))"

# Setze die Umgebungsvariable (ersetze PFAD mit dem Ausgabe-Pfad von oben)
set QT_QPA_PLATFORM_PLUGIN_PATH=PFAD\platforms
```

### Lösung 3: Prüfe auf Konflikte
Stelle sicher, dass keine anderen Qt-Installationen im PATH sind.

```bash
# Prüfe auf Qt-Dateien im PATH
where qt6core.dll
where Qt6Core.dll

# Wenn Dateien außerhalb deiner venv gefunden werden, könnten sie konfliktieren
# Entferne andere Qt-Installationen oder passe den PATH an
```

### Lösung 4: Virtuelle Umgebung neu erstellen
Als letzter Ausweg erstelle eine neue virtuelle Umgebung.

```bash
# Deaktiviere aktuelle venv
deactivate

# Erstelle neue venv
python -m venv .venv_new

# Aktiviere neue venv
.venv_new\Scripts\activate

# Installiere requirements
pip install -r requirements.txt

# Teste
python main.py
```

### Lösung 5: Verwende PySide6 als Alternative
Falls PyQt6 weiterhin Probleme macht, kannst du PySide6 als Alternative verwenden.

```bash
pip uninstall PyQt6 -y
pip install PySide6
```

**Hinweis**: Dies erfordert Änderungen im Code (PyQt6 → PySide6 imports).

## Schnelltest
Nach jeder Lösung teste mit:

```bash
python -c "from PyQt6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); print('Qt funktioniert!')"
```

Wenn dieser Befehl ohne Fehler läuft, sollte `python main.py` auch funktionieren.

## Weitere Hilfe
Wenn keine dieser Lösungen funktioniert:
1. Prüfe die Python-Version: `python --version` (sollte 3.8+ sein)
2. Prüfe PyQt6-Version: `pip show PyQt6`
3. Erstelle ein minimal reproduzierbares Beispiel
4. Öffne ein Issue auf GitHub mit allen Versions-Informationen
