# -*- coding: utf-8 -*-
"""
Multi-Board Manager - Verwaltung mehrerer Arduino-Boards gleichzeitig
"""

import uuid
from typing import Dict, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from core.serial_worker import SerialWorker
from core.logging_config import get_logger

logger = get_logger(__name__)


class BoardConnection:
    """Repräsentiert eine Board-Verbindung."""

    def __init__(self, board_id: str, name: str, port: str, board_type: str):
        """
        Args:
            board_id: Eindeutige ID
            name: Benutzerfreundlicher Name
            port: COM-Port (z.B. "COM3" oder "/dev/ttyUSB0")
            board_type: Typ (z.B. "Arduino Uno", "Arduino Mega")
        """
        self.board_id = board_id
        self.name = name
        self.port = port
        self.board_type = board_type
        self.worker: Optional[SerialWorker] = None
        self.is_connected = False
        self.last_data = {}

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            'board_id': self.board_id,
            'name': self.name,
            'port': self.port,
            'board_type': self.board_type,
            'is_connected': self.is_connected
        }


class MultiBoardManager(QObject):
    """
    Manager für mehrere Arduino-Boards.
    Ermöglicht gleichzeitige Steuerung und Überwachung mehrerer Boards.
    """

    # Signale
    board_added = pyqtSignal(str)  # board_id
    board_removed = pyqtSignal(str)  # board_id
    board_connected = pyqtSignal(str)  # board_id
    board_disconnected = pyqtSignal(str)  # board_id
    board_data_received = pyqtSignal(str, dict)  # board_id, data
    boards_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.boards: Dict[str, BoardConnection] = {}
        logger.info("MultiBoardManager initialisiert")

    def add_board(self, name: str, port: str, board_type: str = "Arduino Uno") -> str:
        """
        Fügt ein neues Board hinzu.

        Args:
            name: Benutzerfreundlicher Name
            port: COM-Port
            board_type: Board-Typ

        Returns:
            board_id: Eindeutige ID des Boards
        """
        board_id = str(uuid.uuid4())
        board = BoardConnection(board_id, name, port, board_type)

        self.boards[board_id] = board
        self.board_added.emit(board_id)
        self.boards_changed.emit()

        logger.info(f"Board hinzugefügt: {name} auf {port} (ID: {board_id})")
        return board_id

    def remove_board(self, board_id: str) -> bool:
        """
        Entfernt ein Board.

        Args:
            board_id: ID des Boards

        Returns:
            True wenn erfolgreich
        """
        if board_id not in self.boards:
            return False

        board = self.boards[board_id]

        # Verbindung trennen falls verbunden
        if board.is_connected:
            self.disconnect_board(board_id)

        del self.boards[board_id]
        self.board_removed.emit(board_id)
        self.boards_changed.emit()

        logger.info(f"Board entfernt: {board.name} (ID: {board_id})")
        return True

    def connect_board(self, board_id: str) -> bool:
        """
        Verbindet zu einem Board.

        Args:
            board_id: ID des Boards

        Returns:
            True wenn Verbindung gestartet
        """
        if board_id not in self.boards:
            logger.error(f"Board nicht gefunden: {board_id}")
            return False

        board = self.boards[board_id]

        if board.is_connected:
            logger.warning(f"Board bereits verbunden: {board.name}")
            return False

        # Erstelle neuen SerialWorker
        board.worker = SerialWorker()

        # Verbinde Signale
        board.worker.data_received.connect(
            lambda data: self._on_board_data(board_id, data)
        )
        board.worker.status_changed.connect(
            lambda msg: self._on_board_status(board_id, msg)
        )

        # Starte Verbindung
        board.worker.connect_serial(board.port)

        logger.info(f"Verbinde zu Board: {board.name} auf {board.port}")
        return True

    def disconnect_board(self, board_id: str) -> bool:
        """
        Trennt die Verbindung zu einem Board.

        Args:
            board_id: ID des Boards

        Returns:
            True wenn erfolgreich
        """
        if board_id not in self.boards:
            return False

        board = self.boards[board_id]

        if not board.is_connected or not board.worker:
            return False

        board.worker.disconnect_serial()
        board.is_connected = False
        board.worker = None

        self.board_disconnected.emit(board_id)
        self.boards_changed.emit()

        logger.info(f"Board getrennt: {board.name}")
        return True

    def send_command_to_board(self, board_id: str, command: dict) -> bool:
        """
        Sendet einen Befehl an ein spezifisches Board.

        Args:
            board_id: ID des Boards
            command: Befehl-Dictionary

        Returns:
            True wenn erfolgreich
        """
        if board_id not in self.boards:
            logger.error(f"Board nicht gefunden: {board_id}")
            return False

        board = self.boards[board_id]

        if not board.is_connected or not board.worker:
            logger.error(f"Board nicht verbunden: {board.name}")
            return False

        board.worker.send_command(command)
        logger.debug(f"Befehl an Board {board.name}: {command}")
        return True

    def send_command_to_all(self, command: dict):
        """
        Sendet einen Befehl an alle verbundenen Boards.

        Args:
            command: Befehl-Dictionary
        """
        count = 0
        for board_id, board in self.boards.items():
            if board.is_connected and board.worker:
                board.worker.send_command(command)
                count += 1

        logger.info(f"Befehl an {count} Boards gesendet: {command}")

    def get_board(self, board_id: str) -> Optional[BoardConnection]:
        """Gibt ein Board zurück."""
        return self.boards.get(board_id)

    def get_all_boards(self) -> List[BoardConnection]:
        """Gibt alle Boards zurück."""
        return list(self.boards.values())

    def get_connected_boards(self) -> List[BoardConnection]:
        """Gibt alle verbundenen Boards zurück."""
        return [b for b in self.boards.values() if b.is_connected]

    def get_board_count(self) -> int:
        """Gibt die Anzahl der Boards zurück."""
        return len(self.boards)

    def get_connected_count(self) -> int:
        """Gibt die Anzahl der verbundenen Boards zurück."""
        return len(self.get_connected_boards())

    def _on_board_data(self, board_id: str, data: dict):
        """Wird aufgerufen wenn Daten von einem Board empfangen werden."""
        if board_id in self.boards:
            board = self.boards[board_id]
            board.last_data = data
            self.board_data_received.emit(board_id, data)
            logger.debug(f"Daten von Board {board.name}: {data.get('type')}")

    def _on_board_status(self, board_id: str, message: str):
        """Wird aufgerufen wenn sich der Status eines Boards ändert."""
        if board_id in self.boards:
            board = self.boards[board_id]

            if "Verbunden" in message or "Connected" in message:
                board.is_connected = True
                self.board_connected.emit(board_id)
                self.boards_changed.emit()
                logger.info(f"Board verbunden: {board.name}")

            elif "Fehler" in message or "Error" in message or "Getrennt" in message:
                if board.is_connected:
                    board.is_connected = False
                    self.board_disconnected.emit(board_id)
                    self.boards_changed.emit()
                    logger.warning(f"Board Verbindung verloren: {board.name}")

    def create_board_group(self, name: str, board_ids: List[str]) -> str:
        """
        Erstellt eine Gruppe von Boards für koordinierte Aktionen.

        Args:
            name: Name der Gruppe
            board_ids: Liste von Board-IDs

        Returns:
            group_id: ID der Gruppe
        """
        # Placeholder für zukünftige Gruppen-Funktionalität
        group_id = str(uuid.uuid4())
        logger.info(f"Board-Gruppe erstellt: {name} mit {len(board_ids)} Boards")
        return group_id

    def disconnect_all(self):
        """Trennt alle Board-Verbindungen."""
        for board_id in list(self.boards.keys()):
            self.disconnect_board(board_id)
        logger.info("Alle Boards getrennt")

    def get_board_status_summary(self) -> dict:
        """Gibt eine Zusammenfassung aller Board-Status zurück."""
        return {
            'total_boards': self.get_board_count(),
            'connected': self.get_connected_count(),
            'disconnected': self.get_board_count() - self.get_connected_count(),
            'boards': [b.to_dict() for b in self.get_all_boards()]
        }
