#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Profiling Tool für Arduino Control Panel

Identifiziert Performance-Bottlenecks in kritischen Komponenten.
"""
import cProfile
import pstats
import io
import time
import sys
from pathlib import Path
from datetime import datetime

# Füge Projekt-Root zum Path hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def profile_config_manager():
    """Profiling für ConfigManager"""
    from core.config_manager import ConfigManager
    import tempfile

    print("\n" + "=" * 80)
    print("PROFILING: ConfigManager")
    print("=" * 80)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        config_file = f.name

    profiler = cProfile.Profile()
    profiler.enable()

    # Test-Szenario: Viele Lese/Schreib-Operationen
    config_manager = ConfigManager(config_file)

    for i in range(1000):
        config_manager.set(f"key_{i}", f"value_{i}")

    config_manager.save_config_to_file()

    # Lade erneut
    config_manager2 = ConfigManager(config_file)

    for i in range(1000):
        value = config_manager2.get(f"key_{i}")

    profiler.disable()

    # Ergebnisse
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 Funktionen

    print(s.getvalue())

    # Cleanup
    Path(config_file).unlink(missing_ok=True)


def profile_database():
    """Profiling für Database"""
    from core.database import Database
    import tempfile

    print("\n" + "=" * 80)
    print("PROFILING: Database")
    print("=" * 80)

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_file = f.name

    profiler = cProfile.Profile()
    profiler.enable()

    # Test-Szenario: Viele Datensätze hinzufügen und lesen
    db = Database(db_file=db_file)

    # 100 Testläufe hinzufügen
    run_ids = []
    for i in range(100):
        run_id = db.add_run(f"Test Run {i}", f"Sequence {i % 10}")
        run_ids.append(run_id)

    # Aktualisiere alle
    for run_id in run_ids:
        db.update_run(run_id, cycles=10, status="completed", log={
            'events': [{'cycle': j, 'duration_ms': 100 + j} for j in range(10)],
            'sensors': {'temp': {'avg': 22.5}}
        })

    # Lese alle
    all_runs = db.get_all_runs()

    # Lese Details
    for run_id in run_ids[:20]:  # Nur erste 20
        details = db.get_run_details(run_id)

    profiler.disable()

    # Ergebnisse
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)

    print(s.getvalue())

    # Cleanup
    Path(db_file).unlink(missing_ok=True)


def profile_serial_worker():
    """Profiling für SerialWorker (Simulation-Modus)"""
    from core.serial_worker import SerialWorker
    from PyQt6.QtCore import QCoreApplication

    print("\n" + "=" * 80)
    print("PROFILING: SerialWorker (Simulation)")
    print("=" * 80)

    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])

    profiler = cProfile.Profile()
    profiler.enable()

    # Test-Szenario: Simulation mit vielen Commands
    worker = SerialWorker()
    worker.connect_simulation()

    # Warte kurz bis Thread läuft
    time.sleep(0.2)

    # Sende viele Commands
    for i in range(500):
        worker.send_command({
            "command": "digital_write",
            "pin": f"D{i % 10}",
            "value": i % 2
        })

        if i % 50 == 0:
            QCoreApplication.processEvents()

    # Warte auf Verarbeitung
    time.sleep(0.5)
    QCoreApplication.processEvents()

    # Trenne
    worker.disconnect_serial()

    profiler.disable()

    # Ergebnisse
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)

    print(s.getvalue())


def benchmark_component(name, func, iterations=100):
    """Benchmark-Funktion für einfache Performance-Messung"""
    print(f"\n{'=' * 80}")
    print(f"BENCHMARK: {name} ({iterations} Iterationen)")
    print('=' * 80)

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"Durchschnitt: {avg_time * 1000:.2f} ms")
    print(f"Minimum:      {min_time * 1000:.2f} ms")
    print(f"Maximum:      {max_time * 1000:.2f} ms")
    print(f"Total:        {sum(times) * 1000:.2f} ms")

    return {
        'avg': avg_time,
        'min': min_time,
        'max': max_time,
        'total': sum(times)
    }


def generate_report(results):
    """Generiert einen Performance-Report"""
    report_file = project_root / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ARDUINO CONTROL PANEL - PERFORMANCE REPORT\n")
        f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("ZUSAMMENFASSUNG\n")
        f.write("-" * 80 + "\n")

        for component, data in results.items():
            f.write(f"\n{component}:\n")
            f.write(f"  Durchschnitt: {data['avg'] * 1000:.2f} ms\n")
            f.write(f"  Minimum:      {data['min'] * 1000:.2f} ms\n")
            f.write(f"  Maximum:      {data['max'] * 1000:.2f} ms\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("EMPFEHLUNGEN\n")
        f.write("-" * 80 + "\n\n")

        # Automatische Empfehlungen basierend auf Ergebnissen
        for component, data in results.items():
            if data['avg'] > 0.1:  # > 100ms
                f.write(f"⚠️ {component}: Langsame Performance ({data['avg'] * 1000:.0f}ms)\n")
                f.write(f"   → Empfehlung: Optimierung prüfen\n\n")
            elif data['avg'] > 0.01:  # > 10ms
                f.write(f"✓ {component}: Akzeptable Performance ({data['avg'] * 1000:.1f}ms)\n\n")
            else:
                f.write(f"✓ {component}: Gute Performance ({data['avg'] * 1000:.2f}ms)\n\n")

    print(f"\n✓ Performance-Report erstellt: {report_file}")


def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("ARDUINO CONTROL PANEL - PERFORMANCE PROFILING")
    print("=" * 80)

    results = {}

    # Profiling
    try:
        profile_config_manager()
        profile_database()
        profile_serial_worker()
    except Exception as e:
        print(f"Fehler beim Profiling: {e}")
        import traceback
        traceback.print_exc()

    # Benchmarks
    try:
        from core.config_manager import ConfigManager
        import tempfile

        def bench_config_save():
            with tempfile.NamedTemporaryFile(suffix='.json') as f:
                cm = ConfigManager(f.name)
                cm.set("test", "value")
                cm.save_config_to_file()

        results['ConfigManager.save'] = benchmark_component(
            "ConfigManager Save Operation",
            bench_config_save,
            iterations=50
        )

    except Exception as e:
        print(f"Fehler beim Benchmark: {e}")

    # Generiere Report
    if results:
        generate_report(results)

    print("\n" + "=" * 80)
    print("PROFILING ABGESCHLOSSEN")
    print("=" * 80)


if __name__ == "__main__":
    main()
