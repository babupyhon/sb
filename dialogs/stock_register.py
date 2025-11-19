from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import QDate

class StockRegisterDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Stock Register")
        self.resize(700, 400)

        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_to.setCalendarPopup(True)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Item", "HSN", "Qty", "Rate", "Amount"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_fetch = QPushButton("Fetch")
        btn_fetch.clicked.connect(self._fetch_data)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("From:"))
        layout.addWidget(self.date_from)
        layout.addWidget(QLabel("To:"))
        layout.addWidget(self.date_to)
        layout.addWidget(btn_fetch)
        layout.addWidget(self.table)

    def _fetch_data(self):
        data = self.db_manager.get_stock_register_data(
            self.date_from.date().toString("yyyy-MM-dd"),
            self.date_to.date().toString("yyyy-MM-dd")
        )
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))
