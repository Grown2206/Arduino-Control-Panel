from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QSpinBox, QLabel, QTableWidget, QHBoxLayout, 
                             QPushButton, QDialogButtonBox, QComboBox, QTableWidgetItem)

class SequenceDialog(QDialog):
    """Dialog zum Erstellen und Bearbeiten von Testsequenzen."""
    def __init__(self, parent=None, sequence=None):
        super().__init__(parent)
        self.setWindowTitle("Sequenz bearbeiten")
        self.setMinimumSize(700, 500)
        self.sequence = sequence or {"name": "", "cycles": 1, "steps": []}
        self.setup_ui()
        self.load_sequence()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.name_edit = QLineEdit()
        form.addRow("Name:", self.name_edit)
        
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(0, 99999)
        self.cycles_spin.setSpecialValueText("∞ Unendlich")
        form.addRow("Zyklen:", self.cycles_spin)
        layout.addLayout(form)
        
        layout.addWidget(QLabel("Schritte:"))
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels(["Aktion", "Pin", "Wert", "Wartezeit/Timeout (ms)"])
        layout.addWidget(self.steps_table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+ Schritt hinzufügen"); add_btn.clicked.connect(self.add_step)
        del_btn = QPushButton("- Schritt löschen"); del_btn.clicked.connect(self.delete_step)
        btn_layout.addWidget(add_btn); btn_layout.addWidget(del_btn); btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept); btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
    
    def load_sequence(self):
        self.name_edit.setText(self.sequence["name"])
        self.cycles_spin.setValue(self.sequence["cycles"])
        for step in self.sequence["steps"]:
            self.add_step_to_table(step)
    
    def add_step(self):
        self.add_step_to_table({"action": "SET_HIGH", "pin": "D8", "value": 0, "wait": 100})
    
    def add_step_to_table(self, step):
        row = self.steps_table.rowCount()
        self.steps_table.insertRow(row)
        
        action_combo = QComboBox()
        action_combo.addItems(["SET_HIGH", "SET_LOW", "WAIT", "WAIT_FOR_PIN"])
        action_combo.setCurrentText(step["action"])
        self.steps_table.setCellWidget(row, 0, action_combo)
        
        pin_combo = QComboBox(); pins = [f"D{i}" for i in range(14)] + [f"A{i}" for i in range(6)]
        pin_combo.addItems(pins); pin_combo.setCurrentText(step.get("pin", "D8"))
        self.steps_table.setCellWidget(row, 1, pin_combo)
        
        self.update_row_widgets(row, step.get("action"))
        
        # Set initial values
        action = step.get("action")
        if action == "WAIT_FOR_PIN":
            value_combo = self.steps_table.cellWidget(row, 2)
            value_combo.setCurrentText(str(step.get("value", "HIGH")))
            self.steps_table.setItem(row, 3, QTableWidgetItem(str(step.get("timeout", 5000))))
        else:
            self.steps_table.setItem(row, 2, QTableWidgetItem(str(step.get("value", 0))))
            self.steps_table.setItem(row, 3, QTableWidgetItem(str(step.get("wait", 100))))

        action_combo.currentTextChanged.connect(lambda text, r=row: self.update_row_widgets(r, text))

    def update_row_widgets(self, row, action):
        if action == "WAIT_FOR_PIN":
            value_combo = QComboBox()
            value_combo.addItems(["HIGH", "LOW"])
            self.steps_table.setCellWidget(row, 2, value_combo)
        else: # For SET_HIGH, SET_LOW, WAIT
            self.steps_table.setCellWidget(row, 2, None) # Remove widget if it exists
            self.steps_table.setItem(row, 2, QTableWidgetItem("0"))

    def delete_step(self):
        row = self.steps_table.currentRow()
        if row >= 0: self.steps_table.removeRow(row)
    
    def get_sequence(self):
        steps = []
        for row in range(self.steps_table.rowCount()):
            action = self.steps_table.cellWidget(row, 0).currentText()
            step = {
                "action": action,
                "pin": self.steps_table.cellWidget(row, 1).currentText(),
            }
            if action == "WAIT_FOR_PIN":
                step["value"] = self.steps_table.cellWidget(row, 2).currentText()
                step["timeout"] = int(self.steps_table.item(row, 3).text() or 5000)
            else:
                step["value"] = int(self.steps_table.item(row, 2).text() or 0)
                step["wait"] = int(self.steps_table.item(row, 3).text() or 100)
            steps.append(step)
        
        return {"name": self.name_edit.text(), "cycles": self.cycles_spin.value(), "steps": steps}

