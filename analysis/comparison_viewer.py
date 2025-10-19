from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QScrollArea, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import base64

class ComparisonViewerDialog(QDialog):
    """
    Ein Dialogfenster zur Anzeige eines HTML-Vergleichsberichts mit mehreren Diagrammen.
    """
    def __init__(self, report_html, charts_base64, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vergleichsbericht")
        self.setMinimumSize(900, 750)

        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        scroll_area.setWidget(container)

        text_edit = QTextEdit()
        text_edit.setHtml(report_html)
        text_edit.setReadOnly(True)
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Funktion zur dynamischen Höhenanpassung des Textfeldes
        def adjust_text_edit_height():
            doc_height = text_edit.document().size().height()
            text_edit.setFixedHeight(int(doc_height) + 10)

        # Verbinde das Signal, das bei Größenänderung des Dokuments ausgelöst wird
        text_edit.document().documentLayout().documentSizeChanged.connect(adjust_text_edit_height)
        # Initiale Anpassung
        adjust_text_edit_height()

        layout.addWidget(text_edit)

        # Diagramme anzeigen
        if charts_base64:
            charts_label = QLabel("<h2>Grafischer Vergleich</h2>")
            charts_label.setStyleSheet("color: #ecf0f1; padding-left: 10px;")
            layout.addWidget(charts_label)
            for chart_b64 in charts_base64:
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(chart_b64))
                    chart_label = QLabel()
                    chart_label.setPixmap(pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation))
                    chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(chart_label)
                except Exception as e:
                    print(f"Fehler beim Laden des Vergleichs-Diagramms: {e}")

        layout.addStretch()

        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)
