from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from decimal import Decimal

class TrialBalanceDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Trial Balance")
        self.resize(700, 400)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Account", "Debit", "Credit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_generate = QPushButton("Generate")
        btn_generate.clicked.connect(self._generate)

        layout = QVBoxLayout(self)
        layout.addWidget(btn_generate)
        layout.addWidget(self.table)

    def _generate(self):
        # Basic computation: sum transactions by account into Dr/Cr totals
        rows = self.db_manager.get_trial_balance_rows()
        self.table.setRowCount(len(rows))
        for r, (acc_name, dr, cr) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(acc_name))
            self.table.setItem(r, 1, QTableWidgetItem(f"{Decimal(dr):,.2f}"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{Decimal(cr):,.2f}"))
