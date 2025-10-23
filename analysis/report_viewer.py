from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QScrollArea, QWidget,
                             QFileDialog, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QByteArray, QBuffer
from datetime import datetime
import base64

class ReportViewerDialog(QDialog):
    """
    Ein Dialogfenster zur Anzeige eines HTML-Berichts mit eingebetteten Diagrammen.
    """
    def __init__(self, report_html, charts_base64, run_details=None, analysis=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bericht-Vorschau")
        self.setMinimumSize(850, 700)
        
        # Speichere Daten für Export
        self.run_details = run_details or {}
        self.analysis = analysis or {}
        self.charts_base64 = charts_base64 # Diagramme für DOCX speichern

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

        # Export-Buttons
        if self.run_details:
            export_layout = QHBoxLayout()
            
            # NEU: DOCX als Haupt-Export
            docx_btn = QPushButton("📄 WORD (DOCX) Export")
            docx_btn.clicked.connect(self.export_docx)
            docx_btn.setStyleSheet("font-weight: bold; background-color: #2980b9; color: white; padding: 8px;")
            docx_btn.setToolTip("Exportiert einen vollständigen Bericht als .docx-Datei")
            export_layout.addWidget(docx_btn)

            # PDF als Fallback (oder für andere Zwecke)
            pdf_btn = QPushButton("PDF")
            pdf_btn.clicked.connect(self.export_pdf)
            export_layout.addWidget(pdf_btn)
            
            csv_btn = QPushButton("CSV")
            csv_btn.clicked.connect(self.export_csv)
            export_layout.addWidget(csv_btn)
            
            json_btn = QPushButton("JSON")
            json_btn.clicked.connect(self.export_json)
            export_layout.addWidget(json_btn)
            
            excel_btn = QPushButton("Excel")
            excel_btn.clicked.connect(self.export_excel)
            export_layout.addWidget(excel_btn)
            
            export_layout.addStretch()
            main_layout.addLayout(export_layout)
            
            # Hinweis für DOCX
            hint = QLabel("💡 Tipp: DOCX-Export enthält alle Diagramme und Analyse-Daten.")
            hint.setStyleSheet("color: #95a5a6; font-size: 10pt; font-style: italic; padding: 5px;")
            hint.setWordWrap(True)
            main_layout.addWidget(hint)

        # Schließen-Button
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)
    
    def export_csv(self):
        from analysis.export_manager import ExportManager
        
        default_name = ExportManager.get_default_filename(
            self.run_details.get('name', 'bericht'), 'csv'
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "CSV exportieren", default_name, "CSV (*.csv)"
        )
        
        if file_path:
            try:
                # Analysis-Objekt übergeben
                success = ExportManager.export_csv(self.run_details, self.analysis, file_path)
                if success:
                    QMessageBox.information(self, "Erfolg", 
                        f"CSV exportiert nach:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", 
                    f"Export fehlgeschlagen:\n{e}")
    
    def export_json(self):
        from analysis.export_manager import ExportManager
        
        default_name = ExportManager.get_default_filename(
            self.run_details.get('name', 'bericht'), 'json'
        )
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSON exportieren", default_name, "JSON (*.json)"
        )
        
        if file_path:
            try:
                # Analysis-Objekt übergeben
                success = ExportManager.export_json(self.run_details, self.analysis, file_path)
                if success:
                    QMessageBox.information(self, "Erfolg", 
                        f"JSON exportiert nach:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", 
                    f"Export fehlgeschlagen:\n{e}")
    
    def export_pdf(self):
        from analysis.report_generator import ReportGenerator
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF exportieren",
            f"bericht_{self.run_details.get('id')}.pdf",
            "PDF (*.pdf)"
        )
        
        if file_path:
            try:
                ReportGenerator.generate_pdf(self.run_details, file_path)
                QMessageBox.information(self, "Erfolg", 
                    f"PDF exportiert nach:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", 
                    f"PDF-Export fehlgeschlagen:\n{e}")
    
    def export_excel(self):
        from analysis.report_generator import ReportGenerator
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Excel exportieren",
            f"bericht_{self.run_details.get('id')}.xlsx",
            "Excel (*.xlsx)"
        )
        
        if file_path:
            try:
                ReportGenerator.generate_excel(self.run_details, file_path)
                QMessageBox.information(self, "Erfolg", 
                    f"Excel exportiert nach:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", 
                    f"Excel-Export fehlgeschlagen:\n{e}")

    def export_docx(self):
        from analysis.docx_export_manager import DocxExportManager
        from analysis.export_manager import ExportManager # Für Dateinamen
        
        default_name = ExportManager.get_default_filename(
            self.run_details.get('name', 'bericht'), 'docx'
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self, "WORD (DOCX) exportieren",
            default_name,
            "Word Dokument (*.docx)"
        )
        
        if file_path:
            try:
                success = DocxExportManager.export_single_report(
                    self.run_details, 
                    self.analysis, 
                    self.charts_base64, 
                    file_path
                )
                if success:
                    QMessageBox.information(self, "Erfolg", 
                        f"DOCX exportiert nach:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Fehler",
                        "DOCX-Export fehlgeschlagen. Ist 'python-docx' installiert?")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", 
                    f"DOCX-Export fehlgeschlagen:\n{e}")