# -*- coding: utf-8 -*-
"""
BaseTab - Basisklasse für alle UI-Tabs
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                             QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from ui.theme_constants import (Colors, Spacing, Fonts,
                               get_status_stylesheet, get_button_stylesheet)


class BaseTab(QWidget):
    """
    Basisklasse für alle UI-Tabs mit gemeinsamer Funktionalität.

    Bietet:
    - Standardisiertes Layout
    - Button-Factory-Methoden
    - Status-Label-Helpers
    - Dialog-Helpers
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_base_layout()
        self.setup_ui()

    def _setup_base_layout(self):
        """Initialisiert Standard-Layout mit Margins und Spacing."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(
            Spacing.MARGIN_STANDARD,
            Spacing.MARGIN_STANDARD,
            Spacing.MARGIN_STANDARD,
            Spacing.MARGIN_STANDARD
        )
        self.layout.setSpacing(Spacing.SPACING_STANDARD)

    def setup_ui(self):
        """
        Überschreiben in Unterklassen, um das UI zu erstellen.
        Wird automatisch in __init__ aufgerufen.
        """
        pass

    # ========== Button Factory Methods ==========

    def create_button(self, text, tooltip=None, callback=None,
                     max_width=None, style_variant=None):
        """
        Factory-Methode für standardisierte Button-Erstellung.

        Args:
            text: Button-Text
            tooltip: Tooltip-Text (optional)
            callback: Click-Handler (optional)
            max_width: Maximale Breite in Pixeln (optional)
            style_variant: 'primary', 'success', 'warning', 'error' (optional)

        Returns:
            QPushButton
        """
        btn = QPushButton(text)
        if tooltip:
            btn.setToolTip(tooltip)
        if callback:
            btn.clicked.connect(callback)
        if max_width:
            btn.setMaximumWidth(max_width)
        if style_variant:
            btn.setStyleSheet(get_button_stylesheet(style_variant))
        return btn

    # ========== Group Box Factory ==========

    def create_group_box(self, title, layout=None):
        """
        Erstellt eine standardisierte QGroupBox.

        Args:
            title: Titel der GroupBox
            layout: Layout (optional, default: QVBoxLayout)

        Returns:
            QGroupBox
        """
        group = QGroupBox(title)
        if layout is None:
            layout = QVBoxLayout()
        group.setLayout(layout)
        return group

    # ========== Status Label Helpers ==========

    def create_status_label(self, text, status_type='info'):
        """
        Erstellt ein Status-Label mit Standard-Styling.

        Args:
            text: Label-Text
            status_type: 'success', 'warning', 'error', oder 'info'

        Returns:
            QLabel
        """
        label = QLabel(text)
        label.setStyleSheet(get_status_stylesheet(status_type))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def update_status_label(self, label, text=None, status_type=None):
        """
        Aktualisiert ein Status-Label.

        Args:
            label: Das zu aktualisierende QLabel
            text: Neuer Text (optional)
            status_type: Neuer Status-Typ (optional)
        """
        if text is not None:
            label.setText(text)
        if status_type is not None:
            label.setStyleSheet(get_status_stylesheet(status_type))

    # ========== Dialog Helpers ==========

    def show_info_dialog(self, title, message):
        """Zeigt einen standardisierten Info-Dialog."""
        QMessageBox.information(self, title, message)

    def show_warning_dialog(self, title, message):
        """Zeigt einen standardisierten Warning-Dialog."""
        QMessageBox.warning(self, title, message)

    def show_error_dialog(self, title, message):
        """Zeigt einen standardisierten Error-Dialog."""
        QMessageBox.critical(self, title, message)

    def show_question_dialog(self, title, message):
        """
        Zeigt einen standardisierten Question-Dialog.

        Returns:
            bool: True wenn "Yes", False wenn "No"
        """
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
