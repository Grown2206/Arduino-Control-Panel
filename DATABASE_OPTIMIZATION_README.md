# 🗄️ Datenbank-Optimierung

## Übersicht

Das Arduino Control Panel bietet umfassende Datenbank-Optimierungsfunktionen für bessere Performance und effiziente Speichernutzung.

## 🎯 Features

### 1. Automatische Indizierung ✅
- Index auf `start_time` (zeitbasierte Queries)
- Index auf `status` (Filterung)
- Index auf `sequence_name` (Gruppierung)
- Composite Index `(start_time, status)` (kombinierte Queries)

### 2. Archivierung alter Daten 📦
- Automatisches Archivieren von Testläufen älter als X Tage
- Separate Archiv-Datenbank (`arduino_tests_archive.db`)
- Wiederherstellung aus Archiv möglich

### 3. VACUUM & ANALYZE 🔧
- **VACUUM**: Komprimiert Datenbank, gibt Speicher frei
- **ANALYZE**: Aktualisiert Statistiken für Query Optimizer

### 4. Cleanup verwaister Daten 🧹
- Entfernt ungültige Einträge
- Bereinigt NULL-Werte

### 5. Statistiken & Monitoring 📊
- Datenbank-Größe
- Anzahl Testläufe
- Gruppierung nach Status/Monat
- Durchschnittliche Log-Größe

---

## 🚀 Verwendung

### Python API

```python
from core.database_optimizer import DatabaseOptimizer

# Initialisiere Optimizer
optimizer = DatabaseOptimizer(db_file="arduino_tests.db")

# --- Einzelne Operationen ---

# 1. Erstelle Indizes
optimizer.create_indexes()

# 2. Analysiere Datenbank
stats = optimizer.analyze_database()
print(f"Gesamt-Läufe: {stats['total_runs']}")
print(f"Größe: {stats['total_size_mb']} MB")

# 3. Archiviere alte Daten (älter als 90 Tage)
result = optimizer.archive_old_runs(days_old=90)
print(f"Archiviert: {result['archived_count']} Läufe")

# 4. VACUUM (komprimieren)
optimizer.vacuum_database()

# 5. ANALYZE (Statistiken aktualisieren)
optimizer.analyze_and_optimize()

# 6. Cleanup
cleaned = optimizer.cleanup_orphaned_data()
print(f"Bereinigte Einträge: {cleaned}")

# --- Vollständige Optimierung ---
results = optimizer.optimize_all(archive_days=90)

print(f"""
Optimierung abgeschlossen:
  • Größe vorher: {results['summary']['size_before_mb']} MB
  • Größe nachher: {results['summary']['size_after_mb']} MB
  • Ersparnis: {results['summary']['space_saved_mb']} MB
  • Archivierte Läufe: {results['summary']['runs_archived']}
""")
```

---

## 📦 Archiv-Management

### Archivieren

```python
# Archiviere Läufe älter als 90 Tage
result = optimizer.archive_old_runs(days_old=90)

print(f"Archivierte Läufe: {result['archived_count']}")
print(f"Archiv-Datei: {result['archive_file']}")
```

### Archiv-Informationen

```python
info = optimizer.get_archive_info()

print(f"Archiv vorhanden: {info['exists']}")
print(f"Archiv-Größe: {info['size_mb']} MB")
print(f"Gesamt-Läufe: {info['total_runs']}")
print(f"Ältester Lauf: {info['oldest_run']}")
print(f"Neuester Lauf: {info['newest_run']}")
```

### Wiederherstellung aus Archiv

```python
# Stelle bestimmte Läufe wieder her
run_ids = [1, 2, 3, 4, 5]
restored = optimizer.restore_from_archive(run_ids)

print(f"Wiederhergestellt: {restored} Läufe")
```

---

## 📊 Statistiken

### Datenbank-Analyse

```python
stats = optimizer.analyze_database()

# Gesamt-Statistiken
print(f"Gesamt-Läufe: {stats['total_runs']}")
print(f"Datenbank-Größe: {stats['total_size_mb']} MB")
print(f"Ältester Lauf: {stats['oldest_run']}")
print(f"Neuester Lauf: {stats['newest_run']}")

# Nach Status gruppiert
for status, count in stats['runs_by_status'].items():
    print(f"  {status}: {count}")

# Nach Monat gruppiert
for month, count in stats['runs_by_month'].items():
    print(f"  {month}: {count}")

# Durchschnittliche Log-Größe
print(f"Ø Log-Größe: {stats['avg_log_size_kb']} KB")

# Tabellen-Größen
for table, count in stats['table_sizes'].items():
    print(f"  {table}: {count} Einträge")
```

---

## 🔧 Automatische Optimierung

### Empfohlene Zeitintervalle

```python
import schedule
import time

def optimize_database():
    optimizer = DatabaseOptimizer()
    results = optimizer.optimize_all(archive_days=90)
    print(f"Optimierung: {results['summary']['space_saved_mb']} MB gespart")

# Täglich um 2 Uhr nachts
schedule.every().day.at("02:00").do(optimize_database)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

### Integration in Main Application

```python
# In main.py
from core.database_optimizer import DatabaseOptimizer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ...

        # Setup automatische Optimierung
        self.setup_database_optimization()

    def setup_database_optimization(self):
        # Optimiere beim Start (wenn nötig)
        optimizer = DatabaseOptimizer()
        stats = optimizer.analyze_database()

        # Wenn DB > 100 MB, optimiere
        if stats['total_size_mb'] > 100:
            print("Führe Datenbank-Optimierung durch...")
            optimizer.optimize_all(archive_days=90)

        # Timer für monatliche Optimierung
        self.optimization_timer = QTimer()
        self.optimization_timer.timeout.connect(self.optimize_database)
        self.optimization_timer.start(30 * 24 * 60 * 60 * 1000)  # 30 Tage

    def optimize_database(self):
        optimizer = DatabaseOptimizer()
        results = optimizer.optimize_all(archive_days=90)

        QMessageBox.information(
            self,
            "Datenbank optimiert",
            f"Platzersparnis: {results['summary']['space_saved_mb']} MB\n"
            f"Archivierte Läufe: {results['summary']['runs_archived']}"
        )
```

---

## 🎨 UI Integration

### Menü-Aktion

```python
# In main.py - _create_menu_bar()

# Tools Menü
tools_menu = self.menuBar().addMenu("Tools")

# Datenbank-Optimierung
optimize_action = QAction("🗄️ Datenbank optimieren", self)
optimize_action.triggered.connect(self.show_database_optimizer)
tools_menu.addAction(optimize_action)

def show_database_optimizer(self):
    from core.database_optimizer import DatabaseOptimizer

    optimizer = DatabaseOptimizer()

    # Zeige aktuelle Statistiken
    stats = optimizer.analyze_database()

    msg = f"""
Datenbank-Statistiken:
━━━━━━━━━━━━━━━━━━━━━━━
📊 Gesamt-Läufe: {stats['total_runs']}
💾 Größe: {stats['total_size_mb']} MB
📅 Ältester Lauf: {stats['oldest_run']}
🕐 Neuester Lauf: {stats['newest_run']}

Möchten Sie die Datenbank jetzt optimieren?
(Archiviert Läufe > 90 Tage, komprimiert DB)
    """

    reply = QMessageBox.question(
        self,
        "Datenbank-Optimierung",
        msg,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        # Führe Optimierung durch
        results = optimizer.optimize_all(archive_days=90)

        summary = f"""
✅ Optimierung abgeschlossen!

📉 Größe vorher: {results['summary']['size_before_mb']} MB
📈 Größe nachher: {results['summary']['size_after_mb']} MB
💰 Ersparnis: {results['summary']['space_saved_mb']} MB
📦 Archivierte Läufe: {results['summary']['runs_archived']}
        """

        QMessageBox.information(
            self,
            "Optimierung erfolgreich",
            summary
        )
```

---

## ⚙️ Erweiterte Konfiguration

### Eigene Archivierungs-Regeln

```python
class CustomOptimizer(DatabaseOptimizer):
    def archive_by_status(self, status: str):
        """Archiviere nach Status"""
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Finde Läufe mit bestimmtem Status
            c.execute("""
                SELECT * FROM test_runs
                WHERE status = ?
            """, (status,))

            runs = c.fetchall()
            # ... Archivierungs-Logik ...

    def archive_by_sequence(self, sequence_name: str, keep_last: int = 10):
        """Archiviere alte Läufe einer Sequenz, behalte letzten X"""
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            c.execute("""
                SELECT id FROM test_runs
                WHERE sequence_name = ?
                ORDER BY start_time DESC
                LIMIT -1 OFFSET ?
            """, (sequence_name, keep_last))

            old_runs = [row[0] for row in c.fetchall()]
            # ... Archiviere old_runs ...
```

---

## 📈 Performance-Tipps

1. **Regelmäßige Optimierung**: Führe `optimize_all()` monatlich aus
2. **Archivierung**: Archiviere Läufe > 90 Tage
3. **VACUUM**: Führe VACUUM nach großen Löschvorgängen aus
4. **Indizes**: Erstelle Indizes für häufige Queries
5. **Monitoring**: Überwache DB-Größe und Performance

---

## 🐛 Troubleshooting

### Datenbank ist gesperrt

```python
# Stelle sicher, dass keine anderen Verbindungen aktiv sind
# Schließe alle QT-Threads vor Optimierung
```

### VACUUM schlägt fehl

```python
# VACUUM benötigt temporär freien Speicher (ca. DB-Größe)
# Stelle sicher genug Speicherplatz vorhanden ist
```

### Archiv nicht verfügbar

```python
# Prüfe ob Archiv-Datei existiert
info = optimizer.get_archive_info()
if not info['exists']:
    print("Archiv noch nicht erstellt")
```

---

## 📖 Weitere Informationen

- **SQLite VACUUM**: https://www.sqlite.org/lang_vacuum.html
- **SQLite ANALYZE**: https://www.sqlite.org/lang_analyze.html
- **SQLite Indexing**: https://www.sqlite.org/queryplanner.html

---

**Version:** 1.0.0
**Modul:** `core/database_optimizer.py`
**Abhängigkeiten:** sqlite3, datetime, logging
