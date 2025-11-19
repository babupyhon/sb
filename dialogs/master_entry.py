from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QDialogButtonBox, QMessageBox
)
from widgets import DecimalLineEdit, AutoCompleteComboBox, show_message

class MasterEntryDialog(QDialog):
    def __init__(self, db_manager, master_type, parent=None, master_id=None):
        # ✅ Always call base class init
        super().__init__(parent)

        self.db_manager = db_manager
        self.master_type = master_type
        self.master_id = master_id

        self.setWindowTitle(f"{'Edit' if master_id else 'Add'} {master_type.capitalize()} Master")
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

        # Item-specific fields
        self.unit_combo = AutoCompleteComboBox(["Nos", "Kg", "Litre"])
        self.tax_rate_line = DecimalLineEdit()
        self.purchase_price_line = DecimalLineEdit()
        self.sale_price_line = DecimalLineEdit()
        self.op_stock_line = DecimalLineEdit()
        self.op_rate_line = DecimalLineEdit()

        # Extra field: group type (account) or HSN code (item)
        if master_type == 'account':
            self.extra_combo = AutoCompleteComboBox(["Sales", "Purchase", "Cash", "Bank"])
        else:
            self.extra_combo = QLineEdit()

        # --- Layout ---
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

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)

        # --- Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_entry)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        if master_id:
            self._load_master_data()

    def _load_master_data(self):
        """Load existing master record into the form."""
        data = self.db_manager.get_master_entry_by_id(self.master_id, self.master_type)
        if data:
            self.name_line.setText(data['name'])
            if isinstance(self.extra_combo, QComboBox):
                self.extra_combo.setCurrentText(data['group_or_hsn'])
            else:
                self.extra_combo.setText(data['group_or_hsn'])

    def _save_entry(self):
        """Save the form data back to the database."""
        name = self.name_line.text().strip()
        extra = self.extra_combo.currentText().strip() if isinstance(self.extra_combo, QComboBox) else self.extra_combo.text().strip()

        if not name:
            show_message(self, "Error", "Name cannot be empty", QMessageBox.Warning)
            return

        try:
            if self.master_id:
                self.db_manager.update_master_entry(
                    self.master_id, self.master_type,
                    {'name': name, 'group_or_hsn': extra}
                )
            else:
                self.db_manager.add_master_entry(
                    self.master_type,
                    {'name': name, 'group_or_hsn': extra}
                )
            self.accept()
        except Exception as e:
            show_message(self, "Error", str(e), QMessageBox.Critical)
