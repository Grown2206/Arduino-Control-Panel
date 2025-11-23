from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLabel, QScrollArea, QWidget,
                             QFileDialog, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import base64

class UnifiedReportViewer(QDialog):
    """
    Einheitlicher Dialog für Report-Anzeige - unterstützt sowohl einzelne Reports
    als auch Vergleichsberichte.
    """
    def __init__(self, report_html, charts_base64,
                 run_details=None, analysis=None,
                 run_details_list=None, analysis_results=None,
                 mode='single', parent=None):
        """
        Args:
            report_html: HTML-Inhalt des Berichts
            charts_base64: Liste von Base64-codierten Diagrammen
            run_details: Einzelner Run (für mode='single')
            analysis: Einzelne Analyse (für mode='single')
            run_details_list: Liste von Runs (für mode='comparison')
            analysis_results: Liste von Analysen (für mode='comparison')
            mode: 'single' oder 'comparison'
            parent: Parent-Widget
        """
        super().__init__(parent)
        self.mode = mode

        # Speichere Daten basierend auf Modus
        if mode == 'single':
            self.setWindowTitle("Bericht-Vorschau")
            self.setMinimumSize(850, 700)
            self.run_details = run_details or {}
            self.analysis = analysis or {}
            self.chart_title = "Diagramme"
        else:  # comparison
            self.setWindowTitle("Vergleichsbericht")
            self.setMinimumSize(900, 750)
            self.run_details_list = run_details_list or []
            self.analysis_results = analysis_results or []
            self.chart_title = "Grafischer Vergleich"

        self.charts_base64 = charts_base64

        self._setup_ui(report_html)

    def _setup_ui(self, report_html):
        """Erstellt das UI-Layout"""
        main_layout = QVBoxLayout(self)

        # Scrollbereich für den gesamten Inhalt
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        container = QWidget()
        layout = QVBoxLayout(container)
        scroll_area.setWidget(container)

        # HTML-Inhalt
        text_edit = QTextEdit()
        text_edit.setHtml(report_html)
        text_edit.setReadOnly(True)
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Dynamische Höhenanpassung
        def adjust_text_edit_height():
            doc_height = text_edit.document().size().height()
            text_edit.setFixedHeight(int(doc_height) + 10)

        text_edit.document().documentLayout().documentSizeChanged.connect(adjust_text_edit_height)
        adjust_text_edit_height()

        layout.addWidget(text_edit)

        # Diagramme anzeigen
        if self.charts_base64:
            charts_label = QLabel(f"<h2>{self.chart_title}</h2>")
            charts_label.setStyleSheet("color: #ecf0f1; padding-left: 10px;")
            layout.addWidget(charts_label)

            width = 800 if self.mode == 'comparison' else 750
            for chart_b64 in self.charts_base64:
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(chart_b64))
                    chart_label = QLabel()
                    chart_label.setPixmap(pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation))
                    chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(chart_label)
                except Exception as e:
                    print(f"Fehler beim Laden des Diagramms: {e}")

        layout.addStretch()

        # Export-Buttons
        self._add_export_buttons(main_layout)

        # Schließen-Button
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

    def _add_export_buttons(self, main_layout):
        """Fügt Export-Buttons basierend auf dem Modus hinzu"""
        # Prüfe ob Daten vorhanden
        has_data = (self.mode == 'single' and self.run_details) or \
                   (self.mode == 'comparison' and self.run_details_list)

        if not has_data:
            return

        export_layout = QHBoxLayout()

        if self.mode == 'single':
            # Single Report Export Buttons
            docx_btn = QPushButton("📄 WORD (DOCX) Export")
            docx_btn.clicked.connect(self.export_docx)
            docx_btn.setStyleSheet("font-weight: bold; background-color: #2980b9; color: white; padding: 8px;")
            docx_btn.setToolTip("Exportiert einen vollständigen Bericht als .docx-Datei")
            export_layout.addWidget(docx_btn)

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

            hint_text = "💡 Tipp: DOCX-Export enthält alle Diagramme und Analyse-Daten."
        else:
            # Comparison Report Export Buttons
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

            hint_text = "💡 DOCX-Export enthält die Übersichtstabelle und alle Diagramme."

        export_layout.addStretch()
        main_layout.addLayout(export_layout)

        # Hinweis
        hint = QLabel(hint_text)
        hint.setStyleSheet("color: #95a5a6; font-size: 10pt; font-style: italic; padding: 5px;")
        hint.setWordWrap(True)
        main_layout.addWidget(hint)

    # ========== Single Report Export Methods ==========

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
        from analysis.export_manager import ExportManager

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

    # ========== Comparison Report Export Methods ==========

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
        from analysis.export_manager import ExportManager

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


# Backward compatibility aliases
class ReportViewerDialog(UnifiedReportViewer):
    """Alias für Rückwärtskompatibilität - einzelne Reports"""
    def __init__(self, report_html, charts_base64, run_details=None, analysis=None, parent=None):
        super().__init__(report_html, charts_base64,
                         run_details=run_details, analysis=analysis,
                         mode='single', parent=parent)


class ComparisonViewerDialog(UnifiedReportViewer):
    """Alias für Rückwärtskompatibilität - Vergleichsberichte"""
    def __init__(self, report_html, charts_base64, run_details_list=None, analysis_results=None, parent=None):
        super().__init__(report_html, charts_base64,
                         run_details_list=run_details_list, analysis_results=analysis_results,
                         mode='comparison', parent=parent)
