# -*- coding: utf-8 -*-
"""
Zentrales Logging-Modul für Arduino Control Panel
Bietet konsistentes, strukturiertes Logging für die gesamte Anwendung
"""
import logging
import sys
import io
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class ArduinoLogger:
    """Zentrale Logging-Konfiguration für Arduino Control Panel"""

    _configured = False
    _loggers = {}

    @classmethod
    def setup(cls,
              log_file: str = "arduino_panel.log",
              level: int = logging.INFO,
              console_output: bool = True,
              file_output: bool = True,
              max_bytes: int = 10 * 1024 * 1024,  # 10 MB
              backup_count: int = 5) -> None:
        """
        Konfiguriert das zentrale Logging-System

        Args:
            log_file: Pfad zur Log-Datei
            level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Ausgabe in die Konsole
            file_output: Ausgabe in Datei
            max_bytes: Maximale Größe der Log-Datei vor Rotation
            backup_count: Anzahl der Backup-Dateien
        """
        if cls._configured:
            return

        # Root Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Entferne existierende Handler
        root_logger.handlers.clear()

        # Format für Log-Nachrichten
        log_format = logging.Formatter(
            fmt='%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console Handler mit UTF-8 Encoding (für Windows-Kompatibilität)
        if console_output:
            utf8_stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                line_buffering=True
            )
            console_handler = logging.StreamHandler(utf8_stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(log_format)
            root_logger.addHandler(console_handler)

        # File Handler mit Rotation und UTF-8 Encoding
        if file_output:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(log_format)
            root_logger.addHandler(file_handler)

        cls._configured = True
        root_logger.info("=" * 80)
        root_logger.info("Arduino Control Panel - Logging System initialisiert")
        root_logger.info("=" * 80)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Gibt einen konfigurierten Logger für ein Modul zurück

        Args:
            name: Name des Moduls (z.B. __name__)

        Returns:
            Konfigurierter Logger
        """
        if not cls._configured:
            cls.setup()

        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)

        return cls._loggers[name]

    @classmethod
    def set_level(cls, level: int, logger_name: Optional[str] = None) -> None:
        """
        Ändert das Logging-Level zur Laufzeit

        Args:
            level: Neues Logging-Level
            logger_name: Name des Loggers (None = Root Logger)
        """
        if logger_name:
            logging.getLogger(logger_name).setLevel(level)
        else:
            logging.getLogger().setLevel(level)

    @classmethod
    def enable_debug(cls) -> None:
        """Aktiviert DEBUG-Level für detailliertes Logging"""
        cls.set_level(logging.DEBUG)
        logging.info("Debug-Logging aktiviert")

    @classmethod
    def disable_debug(cls) -> None:
        """Deaktiviert DEBUG-Level"""
        cls.set_level(logging.INFO)
        logging.info("Debug-Logging deaktiviert")


# Convenience-Funktion für schnellen Zugriff
def get_logger(name: str) -> logging.Logger:
    """
    Shortcut-Funktion zum Abrufen eines Loggers

    Usage:
        from core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Nachricht")

    Args:
        name: Name des Moduls (typischerweise __name__)

    Returns:
        Konfigurierter Logger
    """
    return ArduinoLogger.get_logger(name)


# Bei Import automatisch Setup durchführen
if __name__ != "__main__":
    ArduinoLogger.setup()
