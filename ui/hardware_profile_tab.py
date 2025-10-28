# -*- coding: utf-8 -*-
"""
ui/hardware_profile_tab.py
UI für Hardware-Profil-Management
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QGroupBox, QLineEdit, QTextEdit, QComboBox, QMessageBox,
    QFileDialog, QDialog, QFormLayout, QDialogButtonBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime

try:
    from core.hardware_profile_manager import HardwareProfileManager, HardwareProfile
    PROFILE_MANAGER_AVAILABLE = True
except ImportError:
    PROFILE_MANAGER_AVAILABLE = False
    print("⚠️ Hardware Profile Manager nicht verfügbar")

try:
    from analysis.advanced_stats import parse_timestamp
except ImportError:
    # Fallback-Funktion falls advanced_stats nicht verfügbar
    def parse_timestamp(timestamp_str: str) -> datetime:
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            return datetime.strptime(timestamp_str, '%d.%m.%Y %H:%M:%S')


class ProfileDialog(QDialog):
    """Dialog zum Erstellen/Bearbeiten von Profilen"""

    def __init__(
        self,
        profile: HardwareProfile = None,
        board_types: list = None,
        parent=None
    ):
        super().__init__(parent)
        self.profile = profile
        self.board_types = board_types or HardwareProfileManager.BOARD_TYPES

        self.setWindowTitle("Profil bearbeiten" if profile else "Neues Profil")
        self.setMinimumSize(500, 400)

        self.setup_ui()

        if profile:
            self.load_profile_data()

    def setup_ui(self):
        """Erstellt die UI"""
        layout = QVBoxLayout(self)

        # Formular
        form_layout = QFormLayout()

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Profilname eingeben")
        form_layout.addRow("Name:", self.name_edit)

        # Board-Typ
        self.board_type_combo = QComboBox()
        self.board_type_combo.addItems(self.board_types)
        form_layout.addRow("Board-Typ:", self.board_type_combo)

        # Beschreibung
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Beschreibung (optional)")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Beschreibung:", self.description_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_profile_data(self):
        """Lädt Profil-Daten in Formular"""
        if not self.profile:
            return

        self.name_edit.setText(self.profile.name)
        self.board_type_combo.setCurrentText(self.profile.board_type)
        self.description_edit.setPlainText(self.profile.description)

    def get_profile_data(self) -> dict:
        """Gibt Profil-Daten zurück"""
        return {
            'name': self.name_edit.text().strip(),
            'board_type': self.board_type_combo.currentText(),
            'description': self.description_edit.toPlainText().strip()
        }


class HardwareProfileTab(QWidget):
    """
    Tab für Hardware-Profil-Management
    """

    # Signal wenn Profil geladen werden soll
    load_profile_signal = pyqtSignal(str)  # profile_id

    def __init__(self, parent=None):
        super().__init__(parent)

        if not PROFILE_MANAGER_AVAILABLE:
            self.show_error_layout()
            return

        self.profile_manager = HardwareProfileManager()
        self.current_profile_id = None

        self.setup_ui()
        self.load_profile_list()

    def show_error_layout(self):
        """Zeigt Fehler-Layout"""
        layout = QVBoxLayout(self)
        error_label = QLabel("⚠️ Hardware Profile Manager nicht verfügbar")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)

    def setup_ui(self):
        """Erstellt die UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)

        # Splitter für Profil-Liste und Details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Linke Seite: Profil-Liste
        left_widget = self.create_profile_list_widget()
        splitter.addWidget(left_widget)

        # Rechte Seite: Profil-Details
        right_widget = self.create_profile_details_widget()
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

    def create_toolbar(self) -> QWidget:
        """Erstellt die Toolbar"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar.setStyleSheet("background-color: rgba(40, 40, 50, 0.9);")

        layout = QHBoxLayout(toolbar)

        # Titel
        title = QLabel("🛠️ Hardware Profile")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        layout.addWidget(title)

        layout.addStretch()

        # Neues Profil
        new_btn = QPushButton("➕ Neu")
        new_btn.clicked.connect(self.create_new_profile)
        layout.addWidget(new_btn)

        # Import
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self.import_profile)
        layout.addWidget(import_btn)

        # Export
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_profile)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        # Board erkennen
        detect_btn = QPushButton("🔍 Board erkennen")
        detect_btn.clicked.connect(self.detect_boards)
        layout.addWidget(detect_btn)

        return toolbar

    def create_profile_list_widget(self) -> QWidget:
        """Erstellt Profil-Listen-Widget"""
        widget = QGroupBox("Profile")
        layout = QVBoxLayout(widget)

        # Liste
        self.profile_list = QListWidget()
        self.profile_list.itemSelectionChanged.connect(self.on_profile_selected)
        layout.addWidget(self.profile_list)

        # Aktionen
        actions_layout = QHBoxLayout()

        clone_btn = QPushButton("📋 Klonen")
        clone_btn.clicked.connect(self.clone_profile)
        actions_layout.addWidget(clone_btn)

        delete_btn = QPushButton("🗑️ Löschen")
        delete_btn.clicked.connect(self.delete_profile)
        actions_layout.addWidget(delete_btn)

        layout.addLayout(actions_layout)

        return widget

    def create_profile_details_widget(self) -> QWidget:
        """Erstellt Profil-Details-Widget"""
        widget = QGroupBox("Profil-Details")
        layout = QVBoxLayout(widget)

        # Name und Board-Typ
        info_layout = QFormLayout()

        self.detail_name_label = QLabel("N/A")
        self.detail_name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_layout.addRow("Name:", self.detail_name_label)

        self.detail_board_type_label = QLabel("N/A")
        info_layout.addRow("Board-Typ:", self.detail_board_type_label)

        self.detail_description_label = QLabel("N/A")
        self.detail_description_label.setWordWrap(True)
        info_layout.addRow("Beschreibung:", self.detail_description_label)

        self.detail_created_label = QLabel("N/A")
        info_layout.addRow("Erstellt:", self.detail_created_label)

        self.detail_modified_label = QLabel("N/A")
        info_layout.addRow("Geändert:", self.detail_modified_label)

        layout.addLayout(info_layout)

        # Pin-Konfiguration
        pin_group = QGroupBox("Pin-Konfiguration")
        pin_layout = QVBoxLayout(pin_group)

        self.pin_table = QTableWidget()
        self.pin_table.setColumnCount(2)
        self.pin_table.setHorizontalHeaderLabels(["Pin", "Funktion"])
        self.pin_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pin_layout.addWidget(self.pin_table)

        layout.addWidget(pin_group)

        # Aktionen
        actions_layout = QHBoxLayout()

        edit_btn = QPushButton("✏️ Bearbeiten")
        edit_btn.clicked.connect(self.edit_profile)
        actions_layout.addWidget(edit_btn)

        load_btn = QPushButton("📥 Profil laden")
        load_btn.clicked.connect(self.load_selected_profile)
        actions_layout.addWidget(load_btn)

        layout.addLayout(actions_layout)

        return widget

    def load_profile_list(self):
        """Lädt Profil-Liste"""
        self.profile_list.clear()

        profiles = self.profile_manager.get_all_profiles()

        for profile in profiles:
            item = QListWidgetItem(f"{profile.name} ({profile.board_type})")
            item.setData(Qt.ItemDataRole.UserRole, profile.profile_id)

            # Farbcodierung nach Board-Typ
            if "Uno" in profile.board_type:
                item.setForeground(QColor("#3498db"))
            elif "Mega" in profile.board_type:
                item.setForeground(QColor("#e74c3c"))
            elif "Nano" in profile.board_type:
                item.setForeground(QColor("#f39c12"))

            self.profile_list.addItem(item)

        # Wähle erstes Profil
        if self.profile_list.count() > 0:
            self.profile_list.setCurrentRow(0)

    def on_profile_selected(self):
        """Wird aufgerufen wenn Profil ausgewählt wird"""
        items = self.profile_list.selectedItems()
        if not items:
            self.current_profile_id = None
            self.export_btn.setEnabled(False)
            self.clear_profile_details()
            return

        profile_id = items[0].data(Qt.ItemDataRole.UserRole)
        self.current_profile_id = profile_id
        self.export_btn.setEnabled(True)

        # Lade Details
        self.load_profile_details(profile_id)

    def load_profile_details(self, profile_id: str):
        """Lädt Profil-Details"""
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            return

        self.detail_name_label.setText(profile.name)
        self.detail_board_type_label.setText(profile.board_type)
        self.detail_description_label.setText(profile.description or "Keine Beschreibung")

        # Formatiere Zeitstempel
        try:
            created = parse_timestamp(profile.created_at).strftime("%d.%m.%Y %H:%M")
            modified = parse_timestamp(profile.modified_at).strftime("%d.%m.%Y %H:%M")
        except (ValueError, AttributeError) as e:
            created = profile.created_at
            modified = profile.modified_at

        self.detail_created_label.setText(created)
        self.detail_modified_label.setText(modified)

        # Pin-Konfiguration
        self.pin_table.setRowCount(len(profile.pin_config))

        for i, (pin, function) in enumerate(sorted(profile.pin_config.items())):
            self.pin_table.setItem(i, 0, QTableWidgetItem(pin))

            function_item = QTableWidgetItem(function)

            # Farbcodierung
            if function == "OUTPUT":
                function_item.setBackground(QColor("#e74c3c"))
            elif function == "INPUT":
                function_item.setBackground(QColor("#27ae60"))
            elif "ANALOG" in function:
                function_item.setBackground(QColor("#3498db"))

            self.pin_table.setItem(i, 1, function_item)

    def clear_profile_details(self):
        """Leert Profil-Details"""
        self.detail_name_label.setText("N/A")
        self.detail_board_type_label.setText("N/A")
        self.detail_description_label.setText("N/A")
        self.detail_created_label.setText("N/A")
        self.detail_modified_label.setText("N/A")
        self.pin_table.setRowCount(0)

    def create_new_profile(self):
        """Erstellt neues Profil"""
        dialog = ProfileDialog(parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_profile_data()

            if not data['name']:
                QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein")
                return

            # Generiere ID
            profile_id = f"profile_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            new_profile = HardwareProfile(
                profile_id=profile_id,
                name=data['name'],
                board_type=data['board_type'],
                description=data['description']
            )

            if self.profile_manager.add_profile(new_profile):
                QMessageBox.information(self, "Erfolg", f"Profil '{data['name']}' erstellt")
                self.load_profile_list()
            else:
                QMessageBox.critical(self, "Fehler", "Profil konnte nicht erstellt werden")

    def edit_profile(self):
        """Bearbeitet aktuelles Profil"""
        if not self.current_profile_id:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Profil aus")
            return

        profile = self.profile_manager.get_profile(self.current_profile_id)
        if not profile:
            return

        dialog = ProfileDialog(profile=profile, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_profile_data()

            if self.profile_manager.update_profile(
                self.current_profile_id,
                name=data['name'],
                description=data['description']
            ):
                QMessageBox.information(self, "Erfolg", "Profil aktualisiert")
                self.load_profile_list()
                self.load_profile_details(self.current_profile_id)
            else:
                QMessageBox.critical(self, "Fehler", "Profil konnte nicht aktualisiert werden")

    def clone_profile(self):
        """Klont aktuelles Profil"""
        if not self.current_profile_id:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Profil aus")
            return

        profile = self.profile_manager.get_profile(self.current_profile_id)
        if not profile:
            return

        new_name, ok = QMessageBox.getText(
            self,
            "Profil klonen",
            "Name für geklontes Profil:",
            text=f"{profile.name} (Kopie)"
        )

        if ok and new_name:
            new_id = self.profile_manager.clone_profile(self.current_profile_id, new_name)
            if new_id:
                QMessageBox.information(self, "Erfolg", f"Profil geklont: {new_name}")
                self.load_profile_list()
            else:
                QMessageBox.critical(self, "Fehler", "Profil konnte nicht geklont werden")

    def delete_profile(self):
        """Löscht aktuelles Profil"""
        if not self.current_profile_id:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Profil aus")
            return

        profile = self.profile_manager.get_profile(self.current_profile_id)
        if not profile:
            return

        reply = QMessageBox.question(
            self,
            "Profil löschen",
            f"Soll das Profil '{profile.name}' wirklich gelöscht werden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_profile(self.current_profile_id):
                QMessageBox.information(self, "Erfolg", "Profil gelöscht")
                self.current_profile_id = None
                self.load_profile_list()
            else:
                QMessageBox.critical(self, "Fehler", "Profil konnte nicht gelöscht werden")

    def export_profile(self):
        """Exportiert aktuelles Profil"""
        if not self.current_profile_id:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Profil aus")
            return

        profile = self.profile_manager.get_profile(self.current_profile_id)
        if not profile:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Profil exportieren",
            f"{profile.name}.json",
            "JSON Files (*.json)"
        )

        if file_path:
            if self.profile_manager.export_profile(self.current_profile_id, file_path):
                QMessageBox.information(self, "Erfolg", f"Profil exportiert nach:\n{file_path}")
            else:
                QMessageBox.critical(self, "Fehler", "Export fehlgeschlagen")

    def import_profile(self):
        """Importiert Profil"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Profil importieren",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            profile_id = self.profile_manager.import_profile(file_path)
            if profile_id:
                QMessageBox.information(self, "Erfolg", "Profil erfolgreich importiert")
                self.load_profile_list()
            else:
                QMessageBox.critical(self, "Fehler", "Import fehlgeschlagen")

    def detect_boards(self):
        """Erkennt verbundene Boards automatisch"""
        detected = HardwareProfileManager.detect_connected_boards()

        if not detected:
            QMessageBox.information(
                self,
                "Keine Boards gefunden",
                "Es wurden keine Arduino-Boards erkannt.\nStellen Sie sicher, dass ein Board angeschlossen ist."
            )
            return

        # Zeige erkannte Boards
        message = "Erkannte Boards:\n\n"
        for i, board in enumerate(detected):
            message += f"{i + 1}. {board.get('board_type', 'Unbekannt')}\n"
            message += f"   Port: {board['port']}\n"
            message += f"   {board['description']}\n\n"

        message += "\nMöchten Sie Profile für diese Boards erstellen?"

        reply = QMessageBox.question(
            self,
            "Boards erkannt",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for board in detected:
                profile_id = self.profile_manager.create_profile_from_board(board)
                if profile_id:
                    print(f"✅ Profil erstellt für {board.get('board_type')}")

            QMessageBox.information(self, "Erfolg", f"{len(detected)} Profile erstellt")
            self.load_profile_list()

    def load_selected_profile(self):
        """Lädt ausgewähltes Profil in Board-Config"""
        if not self.current_profile_id:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie ein Profil aus")
            return

        # Emittiere Signal
        self.load_profile_signal.emit(self.current_profile_id)
        QMessageBox.information(self, "Profil geladen", "Profil wurde in die Board-Konfiguration geladen")
