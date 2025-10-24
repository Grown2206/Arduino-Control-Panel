# -*- coding: utf-8 -*-
"""
core/database_optimizer.py
Datenbank-Optimierung: Archivierung, Indizierung, Performance-Boost
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger("DatabaseOptimizer")


class DatabaseOptimizer:
    """
    Optimiert die SQLite-Datenbank für bessere Performance
    - Archivierung alter Daten
    - Index-Management
    - Vacuum und Analyze
    - Statistiken
    """

    def __init__(self, db_file: str = "arduino_tests.db"):
        self.db_file = db_file
        self.archive_db_file = db_file.replace(".db", "_archive.db")

    def create_indexes(self) -> bool:
        """
        Erstellt Performance-Indizes auf wichtigen Spalten

        Returns:
            True wenn erfolgreich
        """
        logger.info("Erstelle Datenbank-Indizes...")

        indexes = [
            # Index auf start_time für zeitbasierte Queries
            ("idx_test_runs_start_time", "test_runs", "start_time"),
            # Index auf status für Filterung
            ("idx_test_runs_status", "test_runs", "status"),
            # Index auf sequence_name für Gruppierung
            ("idx_test_runs_sequence", "test_runs", "sequence_name"),
            # Composite Index für häufige Queries
            ("idx_test_runs_time_status", "test_runs", "start_time, status"),
        ]

        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()

                for idx_name, table, columns in indexes:
                    # Prüfe ob Index bereits existiert
                    c.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name=?", (idx_name,))
                    if c.fetchone():
                        logger.info(f"  ✓ Index {idx_name} existiert bereits")
                        continue

                    # Erstelle Index
                    sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})"
                    c.execute(sql)
                    logger.info(f"  ✅ Index erstellt: {idx_name}")

                conn.commit()

            logger.info("✅ Alle Indizes erstellt")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Indizes: {e}")
            return False

    def analyze_database(self) -> Dict[str, Any]:
        """
        Analysiert Datenbank-Statistiken

        Returns:
            Dictionary mit Statistiken
        """
        logger.info("Analysiere Datenbank...")

        stats = {
            'total_runs': 0,
            'total_size_mb': 0,
            'oldest_run': None,
            'newest_run': None,
            'runs_by_status': {},
            'runs_by_month': {},
            'avg_log_size_kb': 0,
            'table_sizes': {}
        }

        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()

                # Gesamt-Anzahl
                c.execute("SELECT COUNT(*) as count FROM test_runs")
                stats['total_runs'] = c.fetchone()['count']

                # Ältester und neuester Lauf
                c.execute("SELECT MIN(start_time) as oldest, MAX(start_time) as newest FROM test_runs")
                row = c.fetchone()
                stats['oldest_run'] = row['oldest']
                stats['newest_run'] = row['newest']

                # Nach Status gruppiert
                c.execute("SELECT status, COUNT(*) as count FROM test_runs GROUP BY status")
                for row in c.fetchall():
                    stats['runs_by_status'][row['status']] = row['count']

                # Nach Monat gruppiert
                c.execute("""
                    SELECT strftime('%Y-%m', start_time) as month, COUNT(*) as count
                    FROM test_runs
                    WHERE start_time IS NOT NULL
                    GROUP BY month
                    ORDER BY month
                """)
                for row in c.fetchall():
                    stats['runs_by_month'][row['month']] = row['count']

                # Durchschnittliche Log-Größe
                c.execute("SELECT AVG(LENGTH(log)) as avg_size FROM test_runs WHERE log IS NOT NULL")
                avg_bytes = c.fetchone()['avg_size'] or 0
                stats['avg_log_size_kb'] = round(avg_bytes / 1024, 2)

                # Datei-Größe
                if os.path.exists(self.db_file):
                    size_bytes = os.path.getsize(self.db_file)
                    stats['total_size_mb'] = round(size_bytes / (1024 * 1024), 2)

                # Tabellen-Größen
                c.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row['name'] for row in c.fetchall()]

                for table in tables:
                    c.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = c.fetchone()['count']
                    stats['table_sizes'][table] = count

            logger.info(f"✅ Datenbank-Analyse abgeschlossen: {stats['total_runs']} Läufe, {stats['total_size_mb']} MB")
            return stats

        except Exception as e:
            logger.error(f"❌ Fehler bei Datenbank-Analyse: {e}")
            return stats

    def archive_old_runs(self, days_old: int = 90) -> Dict[str, Any]:
        """
        Archiviert Testläufe älter als X Tage

        Args:
            days_old: Tage ab wann archiviert wird

        Returns:
            Dictionary mit Archivierungs-Statistiken
        """
        logger.info(f"Archiviere Läufe älter als {days_old} Tage...")

        cutoff_date = datetime.now() - timedelta(days=days_old)

        result = {
            'archived_count': 0,
            'failed_count': 0,
            'cutoff_date': cutoff_date.isoformat(),
            'archive_file': self.archive_db_file
        }

        try:
            # Erstelle Archiv-Datenbank falls nicht vorhanden
            self._init_archive_db()

            with sqlite3.connect(self.db_file) as conn_main:
                conn_main.row_factory = sqlite3.Row

                with sqlite3.connect(self.archive_db_file) as conn_archive:
                    c_main = conn_main.cursor()
                    c_archive = conn_archive.cursor()

                    # Finde alte Läufe
                    c_main.execute("""
                        SELECT * FROM test_runs
                        WHERE start_time < ?
                        ORDER BY start_time ASC
                    """, (cutoff_date.isoformat(),))

                    old_runs = c_main.fetchall()

                    if not old_runs:
                        logger.info("  ℹ️ Keine Läufe zum Archivieren gefunden")
                        return result

                    # Kopiere in Archiv
                    for run in old_runs:
                        try:
                            run_dict = dict(run)

                            # Füge in Archiv ein
                            c_archive.execute("""
                                INSERT INTO test_runs
                                (id, name, sequence_name, start_time, end_time, duration, cycles, status, log)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                run_dict['id'],
                                run_dict['name'],
                                run_dict['sequence_name'],
                                run_dict['start_time'],
                                run_dict.get('end_time'),
                                run_dict.get('duration'),
                                run_dict.get('cycles'),
                                run_dict.get('status'),
                                run_dict.get('log')
                            ))

                            result['archived_count'] += 1

                        except Exception as e:
                            logger.error(f"  ❌ Fehler beim Archivieren von Run {run_dict['id']}: {e}")
                            result['failed_count'] += 1

                    conn_archive.commit()

                    # Lösche aus Haupt-DB
                    if result['archived_count'] > 0:
                        c_main.execute("""
                            DELETE FROM test_runs
                            WHERE start_time < ?
                        """, (cutoff_date.isoformat(),))

                        conn_main.commit()

                        logger.info(f"✅ {result['archived_count']} Läufe archiviert, {result['failed_count']} Fehler")
                    else:
                        logger.warning("⚠️ Keine Läufe archiviert (möglicherweise Fehler)")

            return result

        except Exception as e:
            logger.error(f"❌ Fehler bei Archivierung: {e}")
            result['error'] = str(e)
            return result

    def _init_archive_db(self):
        """Initialisiert Archiv-Datenbank mit gleicher Struktur"""
        with sqlite3.connect(self.archive_db_file) as conn:
            c = conn.cursor()

            # Erstelle gleiche Tabellen-Struktur wie in Haupt-DB
            c.execute('''
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    sequence_name TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration REAL,
                    cycles INTEGER,
                    status TEXT,
                    log TEXT
                )
            ''')

            # Erstelle Metadaten-Tabelle
            c.execute('''
                CREATE TABLE IF NOT EXISTS archive_metadata (
                    created_at TEXT,
                    last_archived TEXT,
                    total_runs INTEGER
                )
            ''')

            # Prüfe ob Metadaten existieren
            c.execute("SELECT COUNT(*) as count FROM archive_metadata")
            if c.fetchone()[0] == 0:
                c.execute("""
                    INSERT INTO archive_metadata (created_at, last_archived, total_runs)
                    VALUES (?, ?, 0)
                """, (datetime.now().isoformat(), None))

            conn.commit()

        logger.info(f"✅ Archiv-Datenbank initialisiert: {self.archive_db_file}")

    def vacuum_database(self) -> bool:
        """
        Führt VACUUM aus (komprimiert Datenbank, gibt Speicher frei)

        Returns:
            True wenn erfolgreich
        """
        logger.info("Führe VACUUM aus...")

        try:
            size_before = os.path.getsize(self.db_file) if os.path.exists(self.db_file) else 0

            with sqlite3.connect(self.db_file) as conn:
                conn.execute("VACUUM")

            size_after = os.path.getsize(self.db_file) if os.path.exists(self.db_file) else 0

            saved_mb = (size_before - size_after) / (1024 * 1024)

            logger.info(f"✅ VACUUM abgeschlossen. Platzeinsparung: {saved_mb:.2f} MB")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler bei VACUUM: {e}")
            return False

    def analyze_and_optimize(self) -> bool:
        """
        Führt ANALYZE aus (aktualisiert Statistiken für Query Optimizer)

        Returns:
            True wenn erfolgreich
        """
        logger.info("Führe ANALYZE aus...")

        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute("ANALYZE")

            logger.info("✅ ANALYZE abgeschlossen")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler bei ANALYZE: {e}")
            return False

    def cleanup_orphaned_data(self) -> int:
        """
        Bereinigt verwaiste Daten (z.B. Läufe ohne Log)

        Returns:
            Anzahl bereinigter Einträge
        """
        logger.info("Bereinige verwaiste Daten...")

        cleaned = 0

        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()

                # Lösche Läufe mit NULL-Namen (sollte nicht vorkommen)
                c.execute("DELETE FROM test_runs WHERE name IS NULL")
                cleaned += c.rowcount

                # Lösche Läufe ohne start_time
                c.execute("DELETE FROM test_runs WHERE start_time IS NULL")
                cleaned += c.rowcount

                conn.commit()

            logger.info(f"✅ {cleaned} verwaiste Einträge bereinigt")
            return cleaned

        except Exception as e:
            logger.error(f"❌ Fehler bei Bereinigung: {e}")
            return 0

    def optimize_all(self, archive_days: int = 90) -> Dict[str, Any]:
        """
        Führt alle Optimierungen aus

        Args:
            archive_days: Tage für Archivierung

        Returns:
            Sammlung aller Ergebnisse
        """
        logger.info("🚀 Starte vollständige Datenbank-Optimierung...")

        results = {
            'started_at': datetime.now().isoformat(),
            'steps': {}
        }

        # 1. Erstelle Indizes
        results['steps']['create_indexes'] = self.create_indexes()

        # 2. Analysiere Datenbank (vor Optimierung)
        results['stats_before'] = self.analyze_database()

        # 3. Bereinige verwaiste Daten
        results['steps']['cleanup'] = {
            'cleaned_count': self.cleanup_orphaned_data()
        }

        # 4. Archiviere alte Daten
        results['steps']['archive'] = self.archive_old_runs(days_old=archive_days)

        # 5. Vacuum
        results['steps']['vacuum'] = self.vacuum_database()

        # 6. Analyze
        results['steps']['analyze'] = self.analyze_and_optimize()

        # 7. Analysiere Datenbank (nach Optimierung)
        results['stats_after'] = self.analyze_database()

        results['completed_at'] = datetime.now().isoformat()

        # Zusammenfassung
        size_before = results['stats_before'].get('total_size_mb', 0)
        size_after = results['stats_after'].get('total_size_mb', 0)
        saved_mb = size_before - size_after

        results['summary'] = {
            'size_before_mb': size_before,
            'size_after_mb': size_after,
            'space_saved_mb': round(saved_mb, 2),
            'runs_archived': results['steps']['archive'].get('archived_count', 0),
            'success': all([
                results['steps']['create_indexes'],
                results['steps']['vacuum'],
                results['steps']['analyze']
            ])
        }

        logger.info(f"""
✅ Datenbank-Optimierung abgeschlossen!

Zusammenfassung:
  • Größe vorher: {size_before:.2f} MB
  • Größe nachher: {size_after:.2f} MB
  • Platzersparnis: {saved_mb:.2f} MB
  • Archivierte Läufe: {results['steps']['archive'].get('archived_count', 0)}
  • Bereinigte Einträge: {results['steps']['cleanup'].get('cleaned_count', 0)}
        """)

        return results

    def restore_from_archive(self, run_ids: List[int]) -> int:
        """
        Stellt archivierte Läufe wieder her

        Args:
            run_ids: Liste von Run-IDs

        Returns:
            Anzahl wiederhergestellter Läufe
        """
        logger.info(f"Stelle {len(run_ids)} Läufe aus Archiv wieder her...")

        restored = 0

        try:
            if not os.path.exists(self.archive_db_file):
                logger.error("Archiv-Datenbank nicht gefunden")
                return 0

            with sqlite3.connect(self.archive_db_file) as conn_archive:
                conn_archive.row_factory = sqlite3.Row

                with sqlite3.connect(self.db_file) as conn_main:
                    c_archive = conn_archive.cursor()
                    c_main = conn_main.cursor()

                    for run_id in run_ids:
                        # Hole aus Archiv
                        c_archive.execute("SELECT * FROM test_runs WHERE id=?", (run_id,))
                        run = c_archive.fetchone()

                        if not run:
                            logger.warning(f"  ⚠️ Run {run_id} nicht im Archiv gefunden")
                            continue

                        run_dict = dict(run)

                        # Füge in Haupt-DB ein
                        c_main.execute("""
                            INSERT OR REPLACE INTO test_runs
                            (id, name, sequence_name, start_time, end_time, duration, cycles, status, log)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            run_dict['id'],
                            run_dict['name'],
                            run_dict['sequence_name'],
                            run_dict['start_time'],
                            run_dict.get('end_time'),
                            run_dict.get('duration'),
                            run_dict.get('cycles'),
                            run_dict.get('status'),
                            run_dict.get('log')
                        ))

                        restored += 1

                    conn_main.commit()

            logger.info(f"✅ {restored} Läufe wiederhergestellt")
            return restored

        except Exception as e:
            logger.error(f"❌ Fehler bei Wiederherstellung: {e}")
            return 0

    def get_archive_info(self) -> Dict[str, Any]:
        """
        Gibt Informationen über das Archiv zurück

        Returns:
            Dictionary mit Archiv-Informationen
        """
        if not os.path.exists(self.archive_db_file):
            return {
                'exists': False,
                'size_mb': 0,
                'total_runs': 0
            }

        try:
            size_mb = os.path.getsize(self.archive_db_file) / (1024 * 1024)

            with sqlite3.connect(self.archive_db_file) as conn:
                c = conn.cursor()

                c.execute("SELECT COUNT(*) as count FROM test_runs")
                total_runs = c.fetchone()[0]

                c.execute("SELECT MIN(start_time) as oldest, MAX(start_time) as newest FROM test_runs")
                row = c.fetchone()

                return {
                    'exists': True,
                    'file_path': self.archive_db_file,
                    'size_mb': round(size_mb, 2),
                    'total_runs': total_runs,
                    'oldest_run': row[0],
                    'newest_run': row[1]
                }

        except Exception as e:
            logger.error(f"Fehler beim Lesen des Archivs: {e}")
            return {
                'exists': True,
                'error': str(e)
            }
