import sys
import sqlite3
from decimal import Decimal, getcontext
from typing import List, Dict, Tuple, Optional

from PySide6.QtCore import Qt, QDate, QLocale
from PySide6.QtGui import QFont, QDoubleValidator
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QLineEdit,
    QComboBox, QDateEdit, QGridLayout, QMessageBox,
    QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QTableWidget,
    QHeaderView, QDialogButtonBox, QPushButton,
    QFormLayout, QTextEdit, QStyledItemDelegate, QTableWidgetItem,
    QListWidget, QCompleter, QSizePolicy, QStackedWidget,
    QAbstractItemView
)

# Decimal precision for financial accuracy
getcontext().prec = 28

from db_manager import DBManager

#-------------------------

class DayBookDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Day Book")
        self.resize(700, 400)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Voucher No", "Type", "Amount", "Narration"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_fetch = QPushButton("Fetch")
        btn_fetch.clicked.connect(self._fetch_data)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(self.date_edit)
        layout.addWidget(btn_fetch)
        layout.addWidget(self.table)

    def _fetch_data(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        data = self.db_manager.get_day_book_data(date)
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))
