from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHBoxLayout, 
                             QPushButton, QAbstractItemView, QTableWidgetItem, QMessageBox)
from PyQt6.QtCore import pyqtSignal

class ArchiveTab(QWidget):
    """Der 'Archiv'-Tab, der vergangene Testläufe anzeigt und Exporte ermöglicht."""
    export_pdf_signal = pyqtSignal(int)
    export_excel_signal = pyqtSignal(int)
    show_analysis_signal = pyqtSignal(int)
    show_report_signal = pyqtSignal(int)
    compare_runs_signal = pyqtSignal(list) # NEU
    refresh_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.archive_table = QTableWidget(0, 7)
        self.archive_table.setHorizontalHeaderLabels(["ID", "Name", "Sequenz", "Start", "Dauer (s)", "Zyklen", "Status"])
        self.archive_table.horizontalHeader().setStretchLastSection(True)
        # NEU: Mehrfachauswahl erlauben
        self.archive_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.archive_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.archive_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.archive_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.archive_table)
        
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Neu laden"); refresh_btn.clicked.connect(self.refresh_signal.emit)
        report_btn = QPushButton("📄 Einzelbericht"); report_btn.clicked.connect(self.on_show_report)
        
        # NEU: Button für den Vergleichsbericht
        self.compare_btn = QPushButton("📊 Vergleichen"); self.compare_btn.clicked.connect(self.on_compare_runs)
        self.compare_btn.setEnabled(False) # Standardmäßig deaktiviert

        pdf_btn = QPushButton("📄 PDF-Export"); pdf_btn.clicked.connect(self.on_export_pdf)
        excel_btn = QPushButton("📊 Excel-Export"); excel_btn.clicked.connect(self.on_export_excel)
        analyze_btn = QPushButton("🔍 Trend-Analyse"); analyze_btn.clicked.connect(self.on_show_analysis)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(report_btn)
        btn_layout.addWidget(self.compare_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(pdf_btn)
        btn_layout.addWidget(excel_btn)
        btn_layout.addWidget(analyze_btn)
        layout.addLayout(btn_layout)

    def on_selection_changed(self):
        """Aktiviert/Deaktiviert den Vergleichs-Button basierend auf der Auswahl."""
        selected_rows = len(self.archive_table.selectionModel().selectedRows())
        self.compare_btn.setEnabled(selected_rows > 1)

    def on_compare_runs(self):
        """Sendet die IDs der ausgewählten Testläufe für einen Vergleich."""
        selected_ids = self.get_selected_run_ids()
        if len(selected_ids) > 1:
            self.compare_runs_signal.emit(selected_ids)
        else:
            QMessageBox.information(self, "Hinweis", "Bitte wählen Sie mindestens zwei Testläufe für einen Vergleich aus.")

    def on_export_pdf(self):
        run_id = self.get_selected_run_id()
        if run_id is not None: self.export_pdf_signal.emit(run_id)

    def on_export_excel(self):
        run_id = self.get_selected_run_id()
        if run_id is not None: self.export_excel_signal.emit(run_id)

    def on_show_analysis(self):
        run_id = self.get_selected_run_id()
        if run_id is not None: self.show_analysis_signal.emit(run_id)
        
    def on_show_report(self):
        run_id = self.get_selected_run_id()
        if run_id is not None: self.show_report_signal.emit(run_id)

    def get_selected_run_id(self):
        """Gibt die ID der ersten ausgewählten Zeile zurück."""
        selected_items = self.archive_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Keine Auswahl", "Bitte wählen Sie einen Testlauf aus der Liste aus.")
            return None
        return int(self.archive_table.item(selected_items[0].row(), 0).text())

    def get_selected_run_ids(self):
        """Gibt eine Liste der IDs aller ausgewählten Zeilen zurück."""
        selected_rows = self.archive_table.selectionModel().selectedRows()
        return [int(self.archive_table.item(index.row(), 0).text()) for index in selected_rows]

    def update_archive_list(self, runs):
        self.archive_table.setRowCount(0)
        for run in runs:
            row = self.archive_table.rowCount()
            self.archive_table.insertRow(row)
            for col, value in enumerate(run):
                if col == 4 and value: value = f"{value:.1f}"
                self.archive_table.setItem(row, col, QTableWidgetItem(str(value or "-")))

