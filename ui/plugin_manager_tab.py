# -*- coding: utf-8 -*-
"""
ui/plugin_manager_tab.py
UI für Plugin-Verwaltung
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QTextEdit, QGroupBox, QSplitter, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from typing import Optional

try:
    from plugins import PluginManager, PluginInterface
    PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    PLUGIN_SYSTEM_AVAILABLE = False
    print("⚠️ Plugin-System nicht verfügbar")


class PluginManagerTab(QWidget):
    """
    Tab für Plugin-Verwaltung.

    Features:
    - Liste aller Plugins
    - Plugin-Informationen
    - Aktivieren/Deaktivieren
    - Plugin-Einstellungen
    """

    plugin_enabled_signal = pyqtSignal(str)
    plugin_disabled_signal = pyqtSignal(str)

    def __init__(self, plugin_manager: 'PluginManager' = None, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.current_plugin_id = None

        if not PLUGIN_SYSTEM_AVAILABLE or not plugin_manager:
            self.show_error_layout()
        else:
            self.setup_ui()
            self.refresh_plugin_list()

    def show_error_layout(self):
        """Zeigt Fehler-Layout wenn Plugin-System nicht verfügbar"""
        layout = QVBoxLayout(self)
        error_label = QLabel(
            "⚠️ Plugin-System nicht verfügbar\n\n"
            "Das Plugin-System konnte nicht geladen werden."
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("font-size: 14px; color: #e74c3c;")
        layout.addWidget(error_label)

    def setup_ui(self):
        """Erstellt die UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("<h2>🔌 Plugin-Verwaltung</h2>")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Refresh Button
        refresh_btn = QPushButton("🔄 Neu laden")
        refresh_btn.clicked.connect(self.refresh_plugin_list)
        header_layout.addWidget(refresh_btn)

        main_layout.addLayout(header_layout)

        # Splitter für Liste und Details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Linke Seite: Plugin-Liste
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("<b>Verfügbare Plugins:</b>"))

        self.plugin_list = QListWidget()
        self.plugin_list.itemClicked.connect(self.on_plugin_selected)
        left_layout.addWidget(self.plugin_list)

        # Buttons unter der Liste
        list_buttons = QHBoxLayout()

        self.enable_btn = QPushButton("✅ Aktivieren")
        self.enable_btn.clicked.connect(self.enable_plugin)
        self.enable_btn.setEnabled(False)
        list_buttons.addWidget(self.enable_btn)

        self.disable_btn = QPushButton("❌ Deaktivieren")
        self.disable_btn.clicked.connect(self.disable_plugin)
        self.disable_btn.setEnabled(False)
        list_buttons.addWidget(self.disable_btn)

        left_layout.addLayout(list_buttons)

        # Rechte Seite: Plugin-Details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Info-Group
        info_group = QGroupBox("Plugin-Informationen")
        info_layout = QVBoxLayout()

        self.plugin_name_label = QLabel("<b>Kein Plugin ausgewählt</b>")
        self.plugin_name_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(self.plugin_name_label)

        self.plugin_info_table = QTableWidget()
        self.plugin_info_table.setColumnCount(2)
        self.plugin_info_table.setHorizontalHeaderLabels(["Eigenschaft", "Wert"])
        self.plugin_info_table.horizontalHeader().setStretchLastSection(True)
        self.plugin_info_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plugin_info_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        info_layout.addWidget(self.plugin_info_table)

        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)

        # Beschreibung
        desc_group = QGroupBox("Beschreibung")
        desc_layout = QVBoxLayout()

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(150)
        desc_layout.addWidget(self.description_text)

        desc_group.setLayout(desc_layout)
        right_layout.addWidget(desc_group)

        # Capabilities
        cap_group = QGroupBox("Fähigkeiten")
        cap_layout = QVBoxLayout()

        self.capabilities_list = QListWidget()
        self.capabilities_list.setMaximumHeight(120)
        cap_layout.addWidget(self.capabilities_list)

        cap_group.setLayout(cap_layout)
        right_layout.addWidget(cap_group)

        # Settings Button
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()

        self.settings_btn = QPushButton("⚙️ Einstellungen")
        self.settings_btn.clicked.connect(self.show_plugin_settings)
        self.settings_btn.setEnabled(False)
        settings_layout.addWidget(self.settings_btn)

        right_layout.addLayout(settings_layout)
        right_layout.addStretch()

        # Add to Splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])

        main_layout.addWidget(splitter)

    def refresh_plugin_list(self):
        """Aktualisiert die Plugin-Liste"""
        if not self.plugin_manager:
            return

        self.plugin_list.clear()

        # Hole alle Plugin-Infos
        plugins_info = self.plugin_manager.get_plugin_info()

        for info in plugins_info:
            # Erstelle List-Item
            item_text = f"{info['name']} v{info['version']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, info['id'])

            # Färbe basierend auf Status
            if info['enabled']:
                item.setForeground(QColor("#27ae60"))  # Grün
                item.setText(f"✅ {item_text}")
            else:
                item.setForeground(QColor("#95a5a6"))  # Grau
                item.setText(f"⚪ {item_text}")

            self.plugin_list.addItem(item)

    def on_plugin_selected(self, item: QListWidgetItem):
        """Wird aufgerufen wenn ein Plugin ausgewählt wird"""
        plugin_id = item.data(Qt.ItemDataRole.UserRole)
        if not plugin_id:
            return

        self.current_plugin_id = plugin_id
        plugin = self.plugin_manager.get_plugin(plugin_id)

        if not plugin:
            return

        metadata = plugin.get_metadata()

        # Update Name
        self.plugin_name_label.setText(f"<b>{metadata.name}</b> v{metadata.version}")

        # Update Info-Table
        self.plugin_info_table.setRowCount(0)

        info_items = [
            ("ID", metadata.id),
            ("Version", metadata.version),
            ("Autor", metadata.author),
            ("Typ", metadata.plugin_type.value),
            ("Priorität", metadata.priority.name),
            ("Min. App-Version", metadata.min_app_version),
            ("Lizenz", metadata.license),
            ("Website", metadata.website or "Keine"),
            ("Abhängigkeiten", ", ".join(metadata.dependencies) or "Keine"),
            ("Status", "Aktiviert" if plugin.is_enabled() else "Deaktiviert")
        ]

        for prop, value in info_items:
            row = self.plugin_info_table.rowCount()
            self.plugin_info_table.insertRow(row)
            self.plugin_info_table.setItem(row, 0, QTableWidgetItem(prop))
            self.plugin_info_table.setItem(row, 1, QTableWidgetItem(str(value)))

        # Update Description
        self.description_text.setText(metadata.description)

        # Update Capabilities
        self.capabilities_list.clear()
        capabilities = plugin.get_capabilities()
        for cap in capabilities:
            self.capabilities_list.addItem(f"• {cap.value}")

        # Update Buttons
        is_enabled = plugin.is_enabled()
        self.enable_btn.setEnabled(not is_enabled)
        self.disable_btn.setEnabled(is_enabled)
        self.settings_btn.setEnabled(is_enabled)

    def enable_plugin(self):
        """Aktiviert das ausgewählte Plugin"""
        if not self.current_plugin_id:
            return

        try:
            if self.plugin_manager.initialize_plugin(self.current_plugin_id):
                QMessageBox.information(
                    self,
                    "Erfolg",
                    "Plugin wurde erfolgreich aktiviert!"
                )
                self.plugin_enabled_signal.emit(self.current_plugin_id)
                self.refresh_plugin_list()

                # Re-select current plugin
                for i in range(self.plugin_list.count()):
                    item = self.plugin_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == self.current_plugin_id:
                        self.plugin_list.setCurrentItem(item)
                        self.on_plugin_selected(item)
                        break
            else:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Plugin konnte nicht aktiviert werden.\nBitte Log prüfen."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Aktivieren des Plugins:\n{str(e)}"
            )

    def disable_plugin(self):
        """Deaktiviert das ausgewählte Plugin"""
        if not self.current_plugin_id:
            return

        try:
            if self.plugin_manager.shutdown_plugin(self.current_plugin_id):
                QMessageBox.information(
                    self,
                    "Erfolg",
                    "Plugin wurde erfolgreich deaktiviert!"
                )
                self.plugin_disabled_signal.emit(self.current_plugin_id)
                self.refresh_plugin_list()

                # Re-select current plugin
                for i in range(self.plugin_list.count()):
                    item = self.plugin_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == self.current_plugin_id:
                        self.plugin_list.setCurrentItem(item)
                        self.on_plugin_selected(item)
                        break
            else:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Plugin konnte nicht deaktiviert werden.\nBitte Log prüfen."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Deaktivieren des Plugins:\n{str(e)}"
            )

    def show_plugin_settings(self):
        """Zeigt Plugin-Einstellungen"""
        if not self.current_plugin_id:
            return

        plugin = self.plugin_manager.get_plugin(self.current_plugin_id)
        if not plugin:
            return

        # Versuche, Settings-Widget zu holen
        settings_widget = plugin.get_settings_widget()

        if settings_widget:
            # TODO: Zeige Settings-Widget in Dialog
            QMessageBox.information(
                self,
                "Einstellungen",
                "Plugin-Einstellungen werden in einem späteren Update verfügbar sein."
            )
        else:
            QMessageBox.information(
                self,
                "Keine Einstellungen",
                "Dieses Plugin hat keine konfigurierbaren Einstellungen."
            )
