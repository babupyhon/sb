from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QDateEdit, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import QDate
from widgets import DecimalLineEdit, show_message

class VoucherDialog(QDialog):
    def __init__(self, db_manager, vouch_type, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.vouch_type = vouch_type

        self.setWindowTitle(f"{vouch_type.capitalize()} Voucher")
        self.resize(600, 400)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.vouch_no_line = QLineEdit()
        self.narration_text = QTextEdit()
        self.amount_line = DecimalLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Date:"), self.date_edit)
        form_layout.addRow(QLabel("Voucher No:"), self.vouch_no_line)
        form_layout.addRow(QLabel("Narration:"), self.narration_text)
        form_layout.addRow(QLabel("Amount:"), self.amount_line)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)

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
            line_data = []
            self.db_manager.add_account_voucher(self.vouch_type, header_data, line_data)
            self.accept()
        except Exception as e:
            show_message(self, "Error", str(e), QMessageBox.Critical)
