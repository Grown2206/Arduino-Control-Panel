from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QScrollArea, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import base64

class ReportViewerDialog(QDialog):
    """
    Ein Dialogfenster zur Anzeige eines HTML-Berichts mit eingebetteten Diagrammen.
    """
    def __init__(self, report_html, charts_base64, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bericht-Vorschau")
        self.setMinimumSize(850, 700)

        main_layout = QVBoxLayout(self)

        # Scrollbereich für den gesamten Inhalt
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        # Container-Widget für den Inhalt im Scrollbereich
        container = QWidget()
        layout = QVBoxLayout(container)
        scroll_area.setWidget(container)

        # HTML-Inhalt für Text und Tabellen
        text_edit = QTextEdit()
        text_edit.setHtml(report_html)
        text_edit.setReadOnly(True)
        # Deaktivieren der vertikalen Scrollbar des Textfeldes, da der Haupt-Scrollbereich verwendet wird
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Funktion zur dynamischen Höhenanpassung des Textfeldes
        def adjust_text_edit_height():
            doc_height = text_edit.document().size().height()
            text_edit.setFixedHeight(int(doc_height) + 10)

        # Verbinde das Signal, das bei Größenänderung des Dokuments ausgelöst wird
        text_edit.document().documentLayout().documentSizeChanged.connect(adjust_text_edit_height)
        # Initiale Anpassung, um die Starthöhe korrekt zu setzen
        adjust_text_edit_height()

        layout.addWidget(text_edit)

        # Diagramme
        if charts_base64:
            charts_label = QLabel("<h2>Diagramme</h2>")
            charts_label.setStyleSheet("color: #ecf0f1;")
            layout.addWidget(charts_label)
            for chart_b64 in charts_base64:
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(chart_b64))
                    chart_label = QLabel()
                    # Skalieren der Diagramme auf eine feste Breite mit Beibehaltung des Seitenverhältnisses
                    chart_label.setPixmap(pixmap.scaledToWidth(750, Qt.TransformationMode.SmoothTransformation))
                    chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(chart_label)
                except Exception as e:
                    print(f"Fehler beim Laden des Diagramms: {e}")
        
        layout.addStretch()

        # Schließen-Button
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

