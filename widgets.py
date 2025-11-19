import sys
from decimal import Decimal, getcontext
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit, QComboBox, QCompleter, QMessageBox

getcontext().prec = 28

def show_message(parent, title, message, icon):
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(icon)
    msg.exec()

class AutoCompleteComboBox(QComboBox):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.completer = QCompleter(items, self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.setCompleter(self.completer)
        self.addItems(items)

    def currentText(self):
        return self.lineEdit().text() if self.isEditable() else super().currentText()

class DecimalLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("0.00")
        self.setAlignment(Qt.AlignRight)
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        validator.setLocale(self.locale)
        self.setValidator(validator)

    def value(self):
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
