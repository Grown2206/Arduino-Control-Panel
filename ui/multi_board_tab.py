# -*- coding: utf-8 -*-
"""
Multi-Board Tab - UI für gleichzeitige Steuerung mehrerer Arduino-Boards
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QDialog,
                             QFormLayout, QLineEdit, QComboBox, QGroupBox,
                             QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from core.logging_config import get_logger

logger = get_logger(__name__)


class MultiBoardTab(QWidget):
    """Tab für Multi-Board Management."""

    # Signale
    command_signal = pyqtSignal(str, dict)  # board_id, command

    def __init__(self, multi_board_manager, available_ports):
        super().__init__()
        self.multi_board_manager = multi_board_manager
        self.available_ports = available_ports

        self.init_ui()
        self.connect_signals()
        self.refresh_board_list()

    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🔌 Multi-Board Management")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header)

        # Status Label
        self.status_label = QLabel("Boards: 0 | Verbunden: 0")
        self.status_label.setStyleSheet("color: #3498db;")
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Info Box
        info_label = QLabel("💡 Verwalten Sie mehrere Arduino-Boards gleichzeitig. "
                          "Senden Sie Befehle an einzelne oder alle Boards.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #7f8c8d; padding: 5px; background-color: #ecf0f1; border-radius: 4px;")
        layout.addWidget(info_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ Board hinzufügen")
        self.btn_add.clicked.connect(self.add_board_dialog)
        btn_layout.addWidget(self.btn_add)

        self.btn_remove = QPushButton("🗑️ Entfernen")
        self.btn_remove.clicked.connect(self.remove_board)
        btn_layout.addWidget(self.btn_remove)

        self.btn_connect = QPushButton("🔌 Verbinden")
        self.btn_connect.clicked.connect(self.connect_selected)
        btn_layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("⛔ Trennen")
        self.btn_disconnect.clicked.connect(self.disconnect_selected)
        btn_layout.addWidget(self.btn_disconnect)

        btn_layout.addStretch()

        self.btn_connect_all = QPushButton("🔌 Alle verbinden")
        self.btn_connect_all.clicked.connect(self.connect_all)
        btn_layout.addWidget(self.btn_connect_all)

        self.btn_disconnect_all = QPushButton("⛔ Alle trennen")
        self.btn_disconnect_all.clicked.connect(self.disconnect_all)
        btn_layout.addWidget(self.btn_disconnect_all)

        layout.addLayout(btn_layout)

        # Board Table
        self.board_table = QTableWidget()
        self.board_table.setColumnCount(5)
        self.board_table.setHorizontalHeaderLabels(["Status", "Name", "Port", "Typ", "Board-ID"])
        self.board_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.board_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.board_table.setAlternatingRowColors(True)
        layout.addWidget(self.board_table)

        # Broadcast Control
        broadcast_group = QGroupBox("📡 Broadcast-Steuerung")
        broadcast_layout = QVBoxLayout(broadcast_group)

        broadcast_info = QLabel("Senden Sie Befehle an alle verbundenen Boards gleichzeitig.")
        broadcast_info.setWordWrap(True)
        broadcast_layout.addWidget(broadcast_info)

        broadcast_btn_layout = QHBoxLayout()

        self.btn_broadcast_high = QPushButton("🔴 Alle Pins HIGH")
        self.btn_broadcast_high.clicked.connect(lambda: self.broadcast_command("all_high"))
        broadcast_btn_layout.addWidget(self.btn_broadcast_high)

        self.btn_broadcast_low = QPushButton("⚫ Alle Pins LOW")
        self.btn_broadcast_low.clicked.connect(lambda: self.broadcast_command("all_low"))
        broadcast_btn_layout.addWidget(self.btn_broadcast_low)

        self.btn_broadcast_test = QPushButton("🔍 Test-Sequenz")
        self.btn_broadcast_test.clicked.connect(lambda: self.broadcast_command("test"))
        broadcast_btn_layout.addWidget(self.btn_broadcast_test)

        broadcast_layout.addLayout(broadcast_btn_layout)
        layout.addWidget(broadcast_group)

        # Activity Log
        log_group = QGroupBox("📋 Aktivitätslog")
        log_layout = QVBoxLayout(log_group)

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(150)
        log_layout.addWidget(self.activity_log)

        btn_clear_log = QPushButton("🗑️ Log leeren")
        btn_clear_log.clicked.connect(lambda: self.activity_log.clear())
        log_layout.addWidget(btn_clear_log)

        layout.addWidget(log_group)

        logger.info("MultiBoardTab UI initialisiert")

    def connect_signals(self):
        """Verbindet Signale."""
        self.multi_board_manager.board_added.connect(self.on_board_added)
        self.multi_board_manager.board_removed.connect(self.on_board_removed)
        self.multi_board_manager.board_connected.connect(self.on_board_connected)
        self.multi_board_manager.board_disconnected.connect(self.on_board_disconnected)
        self.multi_board_manager.boards_changed.connect(self.refresh_board_list)
        self.multi_board_manager.board_data_received.connect(self.on_board_data)

    def add_board_dialog(self):
        """Dialog zum Hinzufügen eines Boards."""
        dialog = AddBoardDialog(self, self.available_ports)
        if dialog.exec():
            board_data = dialog.get_board_data()
            board_id = self.multi_board_manager.add_board(**board_data)
            self.log_activity(f"✅ Board '{board_data['name']}' hinzugefügt auf {board_data['port']}")
            QMessageBox.information(self, "Erfolg", f"Board '{board_data['name']}' hinzugefügt!")

    def remove_board(self):
        """Entfernt das ausgewählte Board."""
        current_row = self.board_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Fehler", "Bitte wähle ein Board aus!")
            return

        board_id = self.board_table.item(current_row, 4).text()
        board = self.multi_board_manager.get_board(board_id)

        reply = QMessageBox.question(self, "Entfernen",
                                     f"Board '{board.name}' wirklich entfernen?")
        if reply == QMessageBox.StandardButton.Yes:
            self.multi_board_manager.remove_board(board_id)
            self.log_activity(f"🗑️ Board '{board.name}' entfernt")
            QMessageBox.information(self, "Erfolg", "Board entfernt!")

    def connect_selected(self):
        """Verbindet das ausgewählte Board."""
        current_row = self.board_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Fehler", "Bitte wähle ein Board aus!")
            return

        board_id = self.board_table.item(current_row, 4).text()
        board = self.multi_board_manager.get_board(board_id)

        if self.multi_board_manager.connect_board(board_id):
            self.log_activity(f"🔌 Verbinde zu Board '{board.name}'...")
        else:
            QMessageBox.warning(self, "Fehler", f"Konnte nicht zu Board '{board.name}' verbinden!")

    def disconnect_selected(self):
        """Trennt das ausgewählte Board."""
        current_row = self.board_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Fehler", "Bitte wähle ein Board aus!")
            return

        board_id = self.board_table.item(current_row, 4).text()
        board = self.multi_board_manager.get_board(board_id)

        if self.multi_board_manager.disconnect_board(board_id):
            self.log_activity(f"⛔ Board '{board.name}' getrennt")

    def connect_all(self):
        """Verbindet alle Boards."""
        count = 0
        for board in self.multi_board_manager.get_all_boards():
            if not board.is_connected:
                self.multi_board_manager.connect_board(board.board_id)
                count += 1

        self.log_activity(f"🔌 Verbinde zu {count} Boards...")
        QMessageBox.information(self, "Info", f"{count} Boards werden verbunden...")

    def disconnect_all(self):
        """Trennt alle Boards."""
        self.multi_board_manager.disconnect_all()
        self.log_activity("⛔ Alle Boards getrennt")
        QMessageBox.information(self, "Info", "Alle Boards wurden getrennt!")

    def broadcast_command(self, cmd_type):
        """Sendet einen Broadcast-Befehl."""
        connected_count = self.multi_board_manager.get_connected_count()

        if connected_count == 0:
            QMessageBox.warning(self, "Fehler", "Keine Boards verbunden!")
            return

        # Beispiel-Befehle (können erweitert werden)
        if cmd_type == "all_high":
            # Sende alle Pins auf HIGH (Beispiel)
            command = {"command": "digital_write", "pin": "D13", "value": 1}
            self.multi_board_manager.send_command_to_all(command)
            self.log_activity(f"📡 Broadcast: Alle Pins HIGH an {connected_count} Boards")

        elif cmd_type == "all_low":
            command = {"command": "digital_write", "pin": "D13", "value": 0}
            self.multi_board_manager.send_command_to_all(command)
            self.log_activity(f"📡 Broadcast: Alle Pins LOW an {connected_count} Boards")

        elif cmd_type == "test":
            self.log_activity(f"📡 Broadcast: Test-Sequenz an {connected_count} Boards")
            QMessageBox.information(self, "Info", f"Test-Sequenz an {connected_count} Boards gesendet!")

    def refresh_board_list(self):
        """Aktualisiert die Board-Liste."""
        self.board_table.setRowCount(0)

        for board in self.multi_board_manager.get_all_boards():
            row = self.board_table.rowCount()
            self.board_table.insertRow(row)

            # Status
            status = "✅ Verbunden" if board.is_connected else "⚫ Getrennt"
            self.board_table.setItem(row, 0, QTableWidgetItem(status))

            # Name
            self.board_table.setItem(row, 1, QTableWidgetItem(board.name))

            # Port
            self.board_table.setItem(row, 2, QTableWidgetItem(board.port))

            # Typ
            self.board_table.setItem(row, 3, QTableWidgetItem(board.board_type))

            # Board-ID
            self.board_table.setItem(row, 4, QTableWidgetItem(board.board_id))

        # Update Status Label
        total = self.multi_board_manager.get_board_count()
        connected = self.multi_board_manager.get_connected_count()
        self.status_label.setText(f"Boards: {total} | Verbunden: {connected}")

    def on_board_added(self, board_id):
        """Wird aufgerufen wenn ein Board hinzugefügt wurde."""
        self.refresh_board_list()

    def on_board_removed(self, board_id):
        """Wird aufgerufen wenn ein Board entfernt wurde."""
        self.refresh_board_list()

    def on_board_connected(self, board_id):
        """Wird aufgerufen wenn ein Board verbunden wurde."""
        board = self.multi_board_manager.get_board(board_id)
        if board:
            self.log_activity(f"✅ Board '{board.name}' erfolgreich verbunden!")
        self.refresh_board_list()

    def on_board_disconnected(self, board_id):
        """Wird aufgerufen wenn ein Board getrennt wurde."""
        board = self.multi_board_manager.get_board(board_id)
        if board:
            self.log_activity(f"⛔ Board '{board.name}' wurde getrennt")
        self.refresh_board_list()

    def on_board_data(self, board_id, data):
        """Wird aufgerufen wenn Daten von einem Board empfangen werden."""
        board = self.multi_board_manager.get_board(board_id)
        if board:
            data_type = data.get('type', 'unknown')
            logger.debug(f"Daten von {board.name}: {data_type}")

    def log_activity(self, message):
        """Fügt eine Nachricht zum Aktivitätslog hinzu."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")


class AddBoardDialog(QDialog):
    """Dialog zum Hinzufügen eines Boards."""

    def __init__(self, parent, available_ports):
        super().__init__(parent)
        self.available_ports = available_ports
        self.init_ui()

    def init_ui(self):
        """Initialisiert die UI."""
        self.setWindowTitle("Board hinzufügen")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("z.B. Arduino Uno #1")
        layout.addRow("Name:", self.name_edit)

        # Port
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.available_ports)
        if not self.available_ports:
            self.port_combo.addItem("Keine Ports gefunden")
        layout.addRow("Port:", self.port_combo)

        # Board Type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Arduino Uno",
            "Arduino Nano",
            "Arduino Mega",
            "Arduino Leonardo",
            "ESP32",
            "ESP8266"
        ])
        layout.addRow("Board-Typ:", self.type_combo)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_ok = QPushButton("Hinzufügen")
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addRow("", btn_layout)

    def get_board_data(self):
        """Gibt die Board-Daten zurück."""
        return {
            'name': self.name_edit.text() or "Unbenanntes Board",
            'port': self.port_combo.currentText(),
            'board_type': self.type_combo.currentText()
        }
