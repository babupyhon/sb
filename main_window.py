from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
from db_manager import DBManager
from dialogs.master_entry import MasterEntryDialog
from dialogs.voucher import VoucherDialog
from dialogs.ledger import LedgerReportDialog
from dialogs.daybook import DayBookDialog
from dialogs.stock_register import StockRegisterDialog
from dialogs.subsidiary import SubsidiaryBookDialog
from dialogs.trial_balance import TrialBalanceDialog

#-----------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, db_path="appdata.db"):
        super().__init__()
        self.db_manager = DBManager(db_path)
        self.setWindowTitle("Accounting Framework")
        self.resize(800, 600)

        central = QWidget()
        layout = QVBoxLayout(central)

        btn_add_account = QPushButton("Add Account Master")
        btn_add_account.clicked.connect(lambda: MasterEntryDialog(self.db_manager, "account", self).exec())

        btn_add_item = QPushButton("Add Item Master")
        btn_add_item.clicked.connect(lambda: MasterEntryDialog(self.db_manager, "item", self).exec())

        btn_voucher = QPushButton("New Voucher")
        btn_voucher.clicked.connect(lambda: VoucherDialog(self.db_manager, "PAY", self).exec())

        btn_ledger = QPushButton("Ledger Report")
        btn_ledger.clicked.connect(lambda: LedgerReportDialog(self.db_manager, self).exec())

        btn_daybook = QPushButton("Day Book")
        btn_daybook.clicked.connect(lambda: DayBookDialog(self.db_manager, self).exec())

        btn_stock = QPushButton("Stock Register")
        btn_stock.clicked.connect(lambda: StockRegisterDialog(self.db_manager, self).exec())

        btn_subsidiary = QPushButton("Subsidiary Book")
        btn_subsidiary.clicked.connect(lambda: SubsidiaryBookDialog(self.db_manager, self).exec())

        btn_trial = QPushButton("Trial Balance")
        btn_trial.clicked.connect(lambda: TrialBalanceDialog(self.db_manager, self).exec())

        for b in [btn_add_account, btn_add_item, btn_voucher, btn_ledger, btn_daybook, btn_stock, btn_subsidiary, btn_trial]:
            layout.addWidget(b)

        central.setLayout(layout)
        self.setCentralWidget(central)
