# ======================================================================
# PART 1: Imports, Helpers, Custom Widgets
# ======================================================================

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

def show_message(parent, title, message, icon):
    """Reusable message box."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(icon)
    msg.exec()

class AutoCompleteComboBox(QComboBox):
    """ComboBox with integrated completer."""
    def __init__(self, items: List[str], parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.completer = QCompleter(items, self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.setCompleter(self.completer)
        self.addItems(items)

    def currentText(self) -> str:
        return self.lineEdit().text() if self.isEditable() else super().currentText()

class DecimalLineEdit(QLineEdit):
    """LineEdit restricted to decimals."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("0.00")
        self.setAlignment(Qt.AlignRight)

        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        validator.setLocale(self.locale)
        self.setValidator(validator)

    def value(self) -> Decimal:
        try:
            text = self.text().replace(self.locale.thousandsSeparator(), '').replace(self.locale.decimalPoint(), '.')
            cleaned = text.strip()
            if not cleaned or cleaned in ['.', '-']:
                return Decimal('0.00')
            return Decimal(cleaned)
        except Exception:
            return Decimal('0.00')

    def set_value(self, val: Decimal):
        self.setText(f"{val:,.2f}")

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.set_value(self.value())
# ======================================================================
# PART 2: Database Manager
# ======================================================================

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        # Account Master
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_master (
                id INTEGER PRIMARY KEY,
                master_name TEXT NOT NULL UNIQUE,
                alias TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                group_type TEXT NOT NULL,
                is_taxable INTEGER DEFAULT 0,
                default_tax_rate REAL DEFAULT 0.0,
                opening_balance REAL DEFAULT 0.0,
                ob_type TEXT DEFAULT 'Dr',
                contact TEXT,
                gst_no TEXT,
                pan_no TEXT
            )
        """)
        # Item Master
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_master (
                id INTEGER PRIMARY KEY,
                item_name TEXT NOT NULL UNIQUE,
                alias TEXT,
                hsn_code TEXT,
                unit TEXT,
                tax_rate REAL DEFAULT 0.0,
                purchase_price REAL DEFAULT 0.0,
                sale_price REAL DEFAULT 0.0,
                opening_stock REAL DEFAULT 0.0,
                opening_rate REAL DEFAULT 0.0,
                address TEXT,
                phone TEXT,
                email TEXT
            )
        """)
        # Voucher Master
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS voucher_master (
                id INTEGER PRIMARY KEY,
                voucher_type TEXT NOT NULL,
                date TEXT NOT NULL,
                narration TEXT,
                reference_no TEXT
            )
        """)
        # Transactions
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                voucher_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                is_debit INTEGER NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (voucher_id) REFERENCES voucher_master(id),
                FOREIGN KEY (account_id) REFERENCES account_master(id)
            )
        """)
        self.conn.commit()

    # --- Master CRUD ---
    def add_master_entry(self, master_type: str, data: dict) -> int | None:
        if master_type == 'account':
            sql = "INSERT INTO account_master (master_name, group_type) VALUES (?, ?)"
        elif master_type == 'item':
            sql = "INSERT INTO item_master (item_name, hsn_code) VALUES (?, ?)"
        else:
            raise ValueError("Invalid master type")
        try:
            self.cursor.execute(sql, (data['name'], data['group_or_hsn']))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ValueError(f"{master_type.capitalize()} '{data['name']}' already exists.")

    # ======================================================================
    # PART 12: Extended Voucher Handling in DBManager
    # ======================================================================

    # --- Voucher Handling ---
    def add_account_voucher(self, vouch_type_code: str, header_data: dict, line_data: list):
        try:
            self.cursor.execute("""
                INSERT INTO voucher_master (voucher_type, date, narration, reference_no)
                VALUES (?, ?, ?, ?)
            """, (vouch_type_code, header_data['vouch_date'], header_data['narrative'], header_data['ref_no']))
            voucher_id = self.cursor.lastrowid

            for line in line_data:
                self.cursor.execute("""
                    INSERT INTO transactions (voucher_id, account_id, is_debit, amount)
                    VALUES (?, ?, ?, ?)
                """, (voucher_id, line['account_id'], line['is_debit'], float(line['amount'])))

            self.conn.commit()
            return voucher_id
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error adding account voucher: {e}")

    def delete_account_voucher(self, voucher_id: int) -> bool:
        try:
            self.cursor.execute("DELETE FROM transactions WHERE voucher_id=?", (voucher_id,))
            self.cursor.execute("DELETE FROM voucher_master WHERE id=?", (voucher_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Error deleting voucher: {e}")

    # ======================================================================
    # PART 13: Utility Functions for DBManager
    # ======================================================================

    def get_id_by_name(self, name: str, master_type: str) -> Optional[int]:
        table = "account_master" if master_type == "account" else "item_master"
        column = "master_name" if master_type == "account" else "item_name"
        self.cursor.execute(f"SELECT id FROM {table} WHERE {column}=?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_account_group_names(self) -> List[str]:
        self.cursor.execute("SELECT DISTINCT group_type FROM account_master ORDER BY group_type")
        return [row[0] for row in self.cursor.fetchall()]



# ======================================================================
# PART 3: DBManager continued
# ======================================================================

    def update_master_entry(self, master_id: int, master_type: str, data: dict) -> bool:
        if master_type == 'account':
            sql = "UPDATE account_master SET master_name=?, group_type=? WHERE id=?"
        elif master_type == 'item':
            sql = "UPDATE item_master SET item_name=?, hsn_code=? WHERE id=?"
        else:
            raise ValueError("Invalid master type")
        self.cursor.execute(sql, (data['name'], data['group_or_hsn'], master_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_master_entry(self, master_id: int, master_type: str) -> bool:
        table = "account_master" if master_type == 'account' else "item_master"
        self.cursor.execute(f"DELETE FROM {table} WHERE id=?", (master_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_all_master_entries(self, master_type: str) -> List[Dict]:
        table = "account_master" if master_type == 'account' else "item_master"
        name_col = "master_name" if master_type == 'account' else "item_name"
        extra_col = "group_type" if master_type == 'account' else "hsn_code"
        self.cursor.execute(f"SELECT id, {name_col}, {extra_col} FROM {table} ORDER BY {name_col}")
        return [{'id': r[0], 'name': r[1], 'group_or_hsn': r[2]} for r in self.cursor.fetchall()]

    def get_account_names(self) -> List[str]:
        return [r[0] for r in self.cursor.execute("SELECT master_name FROM account_master ORDER BY master_name")]

    def get_item_names(self) -> List[str]:
        return [r[0] for r in self.cursor.execute("SELECT item_name FROM item_master ORDER BY item_name")]

    def get_ledger_data(self, date_from: str, date_to: str, account_name: str) -> List[Tuple]:
        account_id = self.get_id_by_name(account_name, 'account')
        if not account_id:
            return []
        try:
            self.cursor.execute("""
                SELECT v.date, v.voucher_type, t.amount, t.is_debit
                FROM voucher_master v
                JOIN transactions t ON v.id = t.voucher_id
                WHERE v.date BETWEEN ? AND ? AND t.account_id = ?
                ORDER BY v.date
            """, (date_from, date_to, account_id))
            return self.cursor.fetchall()
        except Exception as e:
            print("Ledger fetch error:", e)
            return []
# ======================================================================
# PART 4: Master Entry Dialog
# ======================================================================

class MasterEntryDialog(QDialog):
    def __init__(self, db_manager: DBManager, master_type: str, parent=None, master_id=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.master_type = master_type
        self.master_id = master_id

        self.setWindowTitle(f"{'Edit' if master_id else 'Add'} {master_type.capitalize()} Master")
        self.setModal(True)
        self.resize(500, 300)

        # --- Widgets ---
        self.name_line = QLineEdit()
        self.alias_line = QLineEdit()
        self.address_text = QTextEdit()
        self.phone_line = QLineEdit()
        self.email_line = QLineEdit()
        self.op_bal_line = DecimalLineEdit()
        self.op_type_combo = QComboBox()
        self.op_type_combo.addItems(['Dr', 'Cr'])

        self.gst_line = QLineEdit()
        self.pan_line = QLineEdit()

        # Item-specific
        self.unit_combo = AutoCompleteComboBox(["Nos", "Kg", "Litre"])
        self.tax_rate_line = DecimalLineEdit()
        self.purchase_price_line = DecimalLineEdit()
        self.sale_price_line = DecimalLineEdit()
        self.op_stock_line = DecimalLineEdit()
        self.op_rate_line = DecimalLineEdit()

        # Extra field
        if master_type == 'account':
            self.extra_combo = AutoCompleteComboBox(["Sales", "Purchase", "Cash", "Bank"])
        else:
            self.extra_combo = QLineEdit()

        # Layout
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Name:"), self.name_line)
        form_layout.addRow(QLabel("Alias:"), self.alias_line)

        if master_type == 'account':
            form_layout.addRow(QLabel("Group Type:"), self.extra_combo)
            form_layout.addRow(QLabel("Opening Balance:"), self.op_bal_line)
            form_layout.addRow(QLabel("OB Type:"), self.op_type_combo)
            form_layout.addRow(QLabel("GST No.:"), self.gst_line)
            form_layout.addRow(QLabel("PAN No.:"), self.pan_line)
        else:
            form_layout.addRow(QLabel("HSN Code:"), self.extra_combo)
            form_layout.addRow(QLabel("Unit:"), self.unit_combo)
            form_layout.addRow(QLabel("Tax Rate (%):"), self.tax_rate_line)
            form_layout.addRow(QLabel("Purchase Price:"), self.purchase_price_line)
            form_layout.addRow(QLabel("Sale Price:"), self.sale_price_line)
            form_layout.addRow(QLabel("Opening Stock:"), self.op_stock_line)
            form_layout.addRow(QLabel("Opening Rate:"), self.op_rate_line)

        form_layout.addRow(QLabel("Address:"), self.address_text)
        form_layout.addRow(QLabel("Phone:"), self.phone_line)
        form_layout.addRow(QLabel("Email:"), self.email_line)

        main_layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_entry)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        if master_id:
            self._load_master_data()

    def _load_master_data(self):
        data = self.db_manager.get_master_entry_by_id(self.master_id, self.master_type)
        if data:
            self.name_line.setText(data['name'])
            self.extra_combo.setCurrentText(data['group_or_hsn'])

    def _save_entry(self):
        name = self.name_line.text().strip()
        extra = self.extra_combo.currentText().strip() if isinstance(self.extra_combo, QComboBox) else self.extra_combo.text().strip()
        if not name:
            show_message(self, "Error", "Name cannot be empty", QMessageBox.Warning)
            return
        try:
            if self.master_id:
                self.db_manager.update_master_entry(self.master_id, self.master_type, {'name': name, 'group_or_hsn': extra})
            else:
                self.db_manager.add_master_entry(self.master_type, {'name': name, 'group_or_hsn': extra})
            self.accept()
        except Exception as e:
            show_message(self, "Error", str(e), QMessageBox.Critical)
# ======================================================================
# PART 5: Voucher Dialogs
# ======================================================================

class VoucherDialog(QDialog):
    """Generic voucher entry dialog (Payment/Receipt/Sale/Purchase)."""
    def __init__(self, db_manager: DBManager, vouch_type: str, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.vouch_type = vouch_type

        self.setWindowTitle(f"{vouch_type.capitalize()} Voucher")
        self.resize(600, 400)

        # Widgets
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.vouch_no_line = QLineEdit()
        self.narration_text = QTextEdit()
        self.amount_line = DecimalLineEdit()

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Date:"), self.date_edit)
        form_layout.addRow(QLabel("Voucher No:"), self.vouch_no_line)
        form_layout.addRow(QLabel("Narration:"), self.narration_text)
        form_layout.addRow(QLabel("Amount:"), self.amount_line)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_voucher)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _save_voucher(self):
        try:
            header_data = {
                'vouch_date': self.date_edit.date().toString("yyyy-MM-dd"),
                'vouch_no': self.vouch_no_line.text().strip(),
                'total_amount': self.amount_line.value(),
                'narrative': self.narration_text.toPlainText().strip(),
                'ref_no': ""
            }
            line_data = []  # extend later
            self.db_manager.add_account_voucher(self.vouch_type, header_data, line_data)
            self.accept()
        except Exception as e:
            show_message(self, "Error", str(e), QMessageBox.Critical)
# ======================================================================
# PART 6: Report Views
# ======================================================================

class LedgerReportDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Ledger Report")
        self.resize(700, 400)

        self.account_combo = AutoCompleteComboBox(self.db_manager.get_account_names())
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_to.setCalendarPopup(True)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Voucher No", "Type", "Debit/Credit", "Amount"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_fetch = QPushButton("Fetch")
        btn_fetch.clicked.connect(self._fetch_data)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Account:"))
        layout.addWidget(self.account_combo)
        layout.addWidget(QLabel("From:"))
        layout.addWidget(self.date_from)
        layout.addWidget(QLabel("To:"))
        layout.addWidget(self.date_to)
        layout.addWidget(btn_fetch)
        layout.addWidget(self.table)

    def _fetch_data(self):
        acc_name = self.account_combo.currentText()
        data = self.db_manager.get_ledger_data(
            self.date_from.date().toString("yyyy-MM-dd"),
            self.date_to.date().toString("yyyy-MM-dd"),
            acc_name
        )
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))
# ======================================================================
# PART 7: Main Window
# ======================================================================

class MainWindow(QMainWindow):
    def __init__(self, db_path="appdata.db"):
        super().__init__()
        self.db_manager = DBManager(db_path)
        self.setWindowTitle("Accounting Framework")
        self.resize(800, 600)

        # Central widget
        central = QWidget()
        layout = QVBoxLayout(central)

        # Buttons instead of QAction
        btn_add_account = QPushButton("Add Account Master")
        btn_add_account.clicked.connect(lambda: MasterEntryDialog(self.db_manager, "account", self).exec())

        btn_add_item = QPushButton("Add Item Master")
        btn_add_item.clicked.connect

# ======================================================================
# PART 15: Hooking Reports into MainWindow
# ======================================================================

        btn_daybook = QPushButton("Day Book")
        btn_daybook.clicked.connect(lambda: DayBookDialog(self.db_manager, self).exec())

        btn_stock = QPushButton("Stock Register")
        btn_stock.clicked.connect(lambda: StockRegisterDialog(self.db_manager, self).exec())

        btn_subsidiary = QPushButton("Subsidiary Book")
        btn_subsidiary.clicked.connect(lambda: SubsidiaryBookDialog(self.db_manager, self).exec())

        btn_trial = QPushButton("Trial Balance")
        btn_trial.clicked.connect(lambda: TrialBalanceDialog(self.db_manager, self).exec())

        layout.addWidget(btn_daybook)
        layout.addWidget(btn_stock)
        layout.addWidget(btn_subsidiary)
        layout.addWidget(btn_trial)

# ======================================================================
# PART 8: Main Window continued (buttons and navigation)
# ======================================================================

class MainWindow(QMainWindow):
    def __init__(self, db_path="appdata.db"):
        super().__init__()
        self.db_manager = DBManager(db_path)
        self.setWindowTitle("Accounting Framework")
        self.resize(800, 600)

        # Central widget
        central = QWidget()
        layout = QVBoxLayout(central)

        # Buttons instead of QAction
        btn_add_account = QPushButton("Add Account Master")
        btn_add_account.clicked.connect(lambda: MasterEntryDialog(self.db_manager, "account", self).exec())

        btn_add_item = QPushButton("Add Item Master")
        btn_add_item.clicked.connect(lambda: MasterEntryDialog(self.db_manager, "item", self).exec())

        btn_voucher = QPushButton("New Voucher")
        btn_voucher.clicked.connect(lambda: VoucherDialog(self.db_manager, "PAY", self).exec())

        btn_ledger = QPushButton("Ledger Report")
        btn_ledger.clicked.connect(lambda: LedgerReportDialog(self.db_manager, self).exec())

        # Add buttons to layout
        layout.addWidget(btn_add_account)
        layout.addWidget(btn_add_item)
        layout.addWidget(btn_voucher)
        layout.addWidget(btn_ledger)

        central.setLayout(layout)
        self.setCentralWidget(central)
# ======================================================================
# PART 9: Utility Dialogs (Day Book, Stock Register)
# ======================================================================

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


class StockRegisterDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Stock Register")
        self.resize(700, 400)

        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_to.setCalendarPopup(True)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Item", "Qty", "Rate"])
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
# ======================================================================
# PART 10: Subsidiary Book Dialog
# ======================================================================

class SubsidiaryBookDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Subsidiary Book")
        self.resize(700, 400)

        self.group_combo = AutoCompleteComboBox(self.db_manager.get_account_group_names())
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_to.setCalendarPopup(True)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Voucher No", "Group", "Amount"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_fetch = QPushButton("Fetch")
        btn_fetch.clicked.connect(self._fetch_data)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Group:"))
        layout.addWidget(self.group_combo)
        layout.addWidget(QLabel("From:"))
        layout.addWidget(self.date_from)
        layout.addWidget(QLabel("To:"))
        layout.addWidget(self.date_to)
        layout.addWidget(btn_fetch)
        layout.addWidget(self.table)

    def _fetch_data(self):
        group = self.group_combo.currentText()
        data = self.db_manager.get_subsidiary_book_data(
            self.date_from.date().toString("yyyy-MM-dd"),
            self.date_to.date().toString("yyyy-MM-dd"),
            group
        )
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

# ======================================================================
# PART 14: Trial Balance Dialog
# ======================================================================

class TrialBalanceDialog(QDialog):
    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Trial Balance")
        self.resize(700, 400)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Account", "Debit", "Credit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_fetch = QPushButton("Generate")
        btn_fetch.clicked.connect(self._fetch_data)

        layout = QVBoxLayout(self)
        layout.addWidget(btn_fetch)
        layout.addWidget(self.table)

    def _fetch_data(self):
        accounts = self.db_manager.get_all_master_entries("account")
        self.table.setRowCount(len(accounts))
        for r, acc in enumerate(accounts):
            debit = 0.0
            credit = 0.0
            # simplistic: opening balance only
            if acc['group_or_hsn'] == 'Dr':
                debit = acc.get('opening_balance', 0.0)
            else:
                credit = acc.get('opening_balance', 0.0)
            self.table.setItem(r, 0, QTableWidgetItem(acc['name']))
            self.table.setItem(r, 1, QTableWidgetItem(str(debit)))
            self.table.setItem(r, 2, QTableWidgetItem(str(credit)))


# ======================================================================
# PART 11: Application Entry Point
# ======================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
