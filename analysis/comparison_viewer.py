from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QScrollArea, QWidget, 
                             QFileDialog, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import base64

class ComparisonViewerDialog(QDialog):
    """
    Ein Dialogfenster zur Anzeige eines HTML-Vergleichsberichts mit mehreren Diagrammen.
    """
    def __init__(self, report_html, charts_base64, run_details_list=None, analysis_results=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vergleichsbericht")
        self.setMinimumSize(900, 750)
        
        # Speichere Daten für Export
        self.run_details_list = run_details_list or []
        self.analysis_results = analysis_results or []
        self.charts_base64 = charts_base64 # Diagramme für DOCX speichern

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

        # Export-Buttons
        if self.run_details_list:
            export_layout = QHBoxLayout()
            
            # DOCX als Haupt-Export
            docx_btn = QPushButton("📄 WORD (DOCX) Vergleich")
            docx_btn.clicked.connect(self.export_comparison_docx)
            docx_btn.setStyleSheet("font-weight: bold; background-color: #2980b9; color: white; padding: 8px;")
            docx_btn.setToolTip("Exportiert den Vergleichsbericht als .docx-Datei")
            export_layout.addWidget(docx_btn)
            
            csv_btn = QPushButton("📋 Batch CSV")
            csv_btn.clicked.connect(self.export_batch_csv)
            export_layout.addWidget(csv_btn)
            
            json_btn = QPushButton("🔧 Batch JSON")
            json_btn.clicked.connect(self.export_batch_json)
            export_layout.addWidget(json_btn)
            
            export_layout.addStretch()
            main_layout.addLayout(export_layout)
            
            # Hinweis
            hint = QLabel("💡 DOCX-Export enthält die Übersichtstabelle und alle Diagramme.")
            hint.setStyleSheet("color: #95a5a6; font-size: 10pt; font-style: italic; padding: 5px;")
            hint.setWordWrap(True)
            main_layout.addWidget(hint)

        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)
    
    def export_batch_csv(self):
        from analysis.export_manager import ExportManager
        
        default_name = ExportManager.get_default_filename(
            f"{len(self.run_details_list)}_vergleich", 'csv', batch=True
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Batch CSV exportieren", default_name, "CSV (*.csv)"
        )
        
        if file_path:
            try:
                # Analysis-Liste übergeben
                success = ExportManager.export_batch_csv(
                    self.run_details_list, self.analysis_results, file_path
                )
                if success:
                    QMessageBox.information(self, "Erfolg",
                        f"{len(self.run_details_list)} Tests exportiert:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")
    
    def export_batch_json(self):
        from analysis.export_manager import ExportManager
        
        default_name = ExportManager.get_default_filename(
            f"{len(self.run_details_list)}_vergleich", 'json', batch=True
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Batch JSON exportieren", default_name, "JSON (*.json)"
        )
        
        if file_path:
            try:
                # Analysis-Liste übergeben
                success = ExportManager.export_batch_json(
                    self.run_details_list, self.analysis_results, file_path
                )
                if success:
                    QMessageBox.information(self, "Erfolg",
                        f"{len(self.run_details_list)} Tests exportiert:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")
    
    def export_comparison_docx(self):
        from analysis.docx_export_manager import DocxExportManager
        from analysis.export_manager import ExportManager # Für Dateinamen

        default_name = ExportManager.get_default_filename(
            f"{len(self.run_details_list)}_vergleich", 'docx', batch=True
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Vergleichs-DOCX exportieren",
            default_name,
            "Word Dokument (*.docx)"
        )
        
        if file_path:
            try:
                success = DocxExportManager.export_comparison_report(
                    self.run_details_list, 
                    self.analysis_results, 
                    self.charts_base64, 
                    file_path
                )
                if success:
                    QMessageBox.information(self, "Erfolg",
                        f"Vergleichs-DOCX exportiert:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Fehler",
                        "DOCX-Export fehlgeschlagen. Ist 'python-docx' installiert?")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"DOCX-Export fehlgeschlagen:\n{e}")