Drexler Dynamics - Arduino Control Panel

Ein umfassendes GUI-Tool, entwickelt mit Python und PyQt6, zur Steuerung, Überwachung und Automatisierung von Arduino-basierten Projekten.

Übersicht

Dieses Control Panel bietet eine fortschrittliche, benutzerfreundliche Oberfläche zur Interaktion mit einem Arduino in Echtzeit. Es ermöglicht die direkte Steuerung von Pins, die Erstellung und Ausführung komplexer Testsequenzen (sowohl tabellarisch als auch visuell), die detaillierte Analyse und die Erstellung von Vergleichsberichten für Testläufe.

Die Anwendung ist modular aufgebaut und wurde auf Performance und eine ansprechende Optik optimiert.

Features

Modernes Dashboard: Vollständig anpassbares und speicherbares Widget-Layout zur Anzeige der wichtigsten Informationen auf einen Blick.

Pin-Steuerung: Direkter Zugriff auf alle digitalen und analogen Pins zum Lesen und Schreiben von Werten mit moderner UI.

Tabellarischer Sequenz-Editor: Erstellen, Bearbeiten und Speichern von Schritt-für-Schritt-Abläufen zur Automatisierung von Tests.

Visueller Sequenz-Editor: Ein Node-basierter Editor, um komplexe Abläufe grafisch zu erstellen, inklusive Live-Feedback während der Ausführung.

Test-Archiv & Datenbank: Eine SQLite-Datenbank speichert alle Testläufe mit detaillierten Logs, Statistiken und Sensorwerten. Die Datenbankzugriffe erfolgen asynchron, um die UI nicht zu blockieren.

Umfassende Berichterstellung:

Detaillierte Einzelberichte (HTML-Vorschau, PDF, Excel).

Vergleichsberichte zur Gegenüberstellung mehrerer Testläufe.

Automatisch generierte Diagramme (Zeitverläufe, Box-Plots, Sensor-Graphen).

Live-Visualisierung: Performante Echtzeit-Diagramme zur grafischen Darstellung von Pin- und Sensor-Zuständen.

Sensor-Integration: Dedizierte Widgets zur Anzeige von Temperatur-, Luftfeuchtigkeits- und Vibrationsdaten.

Anpassbares Design: Das Erscheinungsbild der Anwendung kann zentral über die ui/branding.py angepasst werden.

Installation

Um die Anwendung zu starten, folgen Sie diesen Schritten:

Repository klonen:

git clone [https://github.com/orgs/github/repositories](https://github.com/orgs/github/repositories)
cd [Projektordner]


Virtuelle Umgebung erstellen:
Es wird dringend empfohlen, eine virtuelle Umgebung zu verwenden.

python -m venv .venv


Virtuelle Umgebung aktivieren:

Windows: .\.venv\Scripts\activate

macOS / Linux: source .venv/bin/activate

Abhängigkeiten installieren:
Alle benötigten Bibliotheken sind in der requirements.txt aufgelistet.

pip install -r requirements.txt


Verwendung

Arduino vorbereiten:

Laden Sie den Sketch aus dem Verzeichnis /sketch_.../ auf Ihr Arduino Board.

Stellen Sie sicher, dass die Baudrate im Sketch (115200) mit der in der Anwendung übereinstimmt.

Anwendung starten:

python main.py


Verbinden:

Wählen Sie den korrekten COM-Port Ihres Arduinos aus der Dropdown-Liste aus.

Klicken Sie auf "Verbinden".

Alternativ können Sie den Simulations-Modus verwenden, um die Anwendung ohne angeschlossenen Arduino zu testen.

Projektstruktur

/analysis/: Logik für Trendanalyse und Berichterstellung.

/assets/: Bilder und Logos für die Benutzeroberfläche.

/core/: Kernkomponenten (Serial-Worker, Datenbank, Sequenz-Ablauf, Konfiguration).

/sketch_.../: Der Arduino-Code (.ino) für den Mikrocontroller.

/ui/: Alle PyQt6-Widgets, die die Benutzeroberfläche bilden.

/ui/visual_editor/: Komponenten für den visuellen Sequenz-Editor.

main.py: Hauptanwendung, die alle Module initialisiert und verbindet.

requirements.txt: Liste der Python-Abhängigkeiten.

.gitignore: Definiert Dateien und Ordner, die von Git ignoriert werden sollen.