# digi modified
import sys
import sqlite3
import time
from decimal import Decimal, getcontext
from functools import partial
from typing import List, Tuple, Any, Dict, Optional

# Set Decimal precision for financial accuracy
getcontext().prec = 28

'''
# --- PYSIDE6 IMPORTS (Replaced PyQt6) ---
try:
    from PySide6.QtCore import (
        Qt, QDate, QLocale
    )
    from PySide6.QtGui import (
        QFont, QDoubleValidator
    )
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QDialog, QLineEdit, 
        QComboBox, QDateEdit, QGridLayout, QMessageBox, 
        QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QTableWidget, 
        QHeaderView, QDialogButtonBox, QPushButton, 
        QFormLayout, QTextEdit, QStyledItemDelegate, QTableWidgetItem,
        QListWidget, QCompleter, QSizePolicy, QStackedWidget,
        QAbstractItemView, QAction
    )
    
except ImportError:
    print("FATAL: Failed to import PySide6. Ensure PySide6 is installed (`pip install pyside6`).")
    sys.exit(1)
'''

from PySide6.QtCore import (
    Qt, QDate, QLocale
)
from PySide6.QtGui import (
    QFont, QDoubleValidator
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QLineEdit, 
    QComboBox, QDateEdit, QGridLayout, QMessageBox, 
    QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QTableWidget, 
    QHeaderView, QDialogButtonBox, QPushButton, 
    QFormLayout, QTextEdit, QStyledItemDelegate, QTableWidgetItem,
    QListWidget, QCompleter, QSizePolicy, QStackedWidget,
    QAbstractItemView
)
#from PySide6.QtWidgets import QAction

# ==============================================================================
# 0. HELPER CLASSES & FUNCTIONS
# ==============================================================================

def show_message(parent, title, message, icon):
    """A standard message box."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(icon)
    msg.exec()

class AutoCompleteComboBox(QComboBox):
    """A QComboBox with integrated QCompleter for search-as-you-type."""
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.completer = QCompleter(items, self)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
      
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(self.completer)
        self.addItems(items)
        
    def currentText(self) -> str:
        """Override to ensure the text from QLineEdit part is returned."""
        return self.lineEdit().text() if self.isEditable() else super().currentText()

class DecimalLineEdit(QLineEdit):
    """A QLineEdit configured to accept only decimal numbers."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("0.00")
   
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        validator = QDoubleValidator()
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates) 
        validator.setLocale(self.locale) 
        self.setValidator(validator)

    def value(self) -> Decimal:
        """Returns the current value as a Decimal object."""
        try:
          
            # 1. Clean up formatting
            text = self.text().replace(self.locale.thousandsSeparator(), '').replace(self.locale.decimalPoint(), '.')
            
            # 2. Robust check for empty/invalid input (THE FIX)
            cleaned_text = text.strip()
            
            if not cleaned_text or cleaned_text == '.' or cleaned_text == '-':
                return Decimal('0.00')
                
            return Decimal(cleaned_text)
                
        except Exception:
            return Decimal('0.00')

    def set_value(self, val: Decimal):
        """Sets the 
 text from a Decimal object."""
        self.setText(f"{val:,.2f}")
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        val = self.value()
        self.set_value(val)
        
# ==============================================================================
# 1. DATABASE MANAGER (EXTENDED for Master CRUD &  Reports)
# ==============================================================================

class DBManager:
    def __init__(self, db_path: str):
        """Initializes the database connection and ensures tables exist."""
        self.conn = None
        self.cursor = None
        self.db_path = db_path
        
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
  
           
            # --- UPDATED DATABASE SCHEMAS (including new fields) ---
            
            # 1. Account Master Schema
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
                    ob_type TEXT DEFAULT 'Dr', -- Dr/Cr
                    contact TEXT,
                    gst_no TEXT,
                  
 pan_no TEXT -- ADDED: PAN No.
                )
            """)
            
            # 2. Item Master Schema
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
            
            # 3. Voucher Master Schema
            # (Ensure the rest of your table creation logic remains here)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS voucher_master (
   
                 id INTEGER PRIMARY KEY,
                    voucher_type TEXT NOT NULL, -- e.g., 'Payment', 'Receipt', 'Sale', 'Purchase'
                    date TEXT NOT NULL,
                    narration TEXT,
       
              reference_no TEXT
                )
            """)
            
            # 4. Transaction Details Schema
            self.cursor.execute("""
                CREATE TABLE 
 IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    voucher_id INTEGER NOT NULL,
                    account_id INTEGER NOT NULL,
                    is_debit INTEGER NOT NULL, -- 1 for 
 Debit, 0 for Credit
                    amount REAL NOT NULL,
                    FOREIGN KEY (voucher_id) REFERENCES voucher_master(id),
                    FOREIGN KEY (account_id) REFERENCES account_master(id)
                )
          
   """)
            
            self.conn.commit()

        except Exception as e:
            # Handle error (close connection, re-raise)
            if self.conn:
                self.conn.close()
            raise Exception(f"Failed to initialize database:  {e}")
   
    # --- MASTER CRUD UTILITIES ---
    def _get_master_table(self, master_type: str) -> Tuple[str, str, str]:
        if master_type == 'account':
            return 'account_master', 'master_name', 'group_type'
        elif master_type == 'item':
            return 'item_master', 'item_name', 'hsn_code'
        raise ValueError("Invalid master type")

    def add_master_entry(self, master_type: str, data: dict) -> int | None:
        table, name_col, extra_col = self._get_master_table(master_type)
        try:
            self.cursor.execute(f"INSERT INTO {table} ({name_col}, {extra_col}) VALUES (?, ?)", 
                                (data['name'], data['group_or_hsn']))
            self.conn.commit()
            return self.cursor.lastrowid
  
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ValueError(f"{master_type.capitalize()} name '{data['name']}' already exists.")
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"DB Error adding {master_type} master: {e}")

    def update_master_entry(self, master_id: int, master_type: str, data: dict) -> bool:
                
        table, name_col, extra_col = self._get_master_table(master_type)
        try:
            sql = f"UPDATE {table} SET {name_col} = ?, {extra_col} = ? WHERE id = ?"
            self.cursor.execute(sql, (data['name'], data['group_or_hsn'], master_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ValueError(f"{master_type.capitalize()} name '{data['name']}' already exists.")
        except Exception as e:
            self.conn.rollback()
       
        raise Exception(f"DB Error updating {master_type} master: {e}")

    def get_master_entry_by_id(self, master_id: int, master_type: str) -> Dict | None:
        table, name_col, extra_col = self._get_master_table(master_type)
        self.cursor.execute(f"SELECT {name_col}, {extra_col} FROM {table} WHERE id = ?", (master_id,))
        result = self.cursor.fetchone()
        if result:
            return {'name': result[0], 'group_or_hsn': result[1], 'id': master_id}
        return None

    def get_all_master_entries(self, master_type: str) -> List[Dict]:
        table, name_col, extra_col = self._get_master_table(master_type)
    
        self.cursor.execute(f"SELECT id, {name_col}, {extra_col} FROM {table} ORDER BY {name_col}")
        return [{'id': row[0], 'name': row[1], 'group_or_hsn': row[2]} for row in self.cursor.fetchall()]

    def delete_master_entry(self, master_id: int, master_type: str) -> bool:
        table, _, _ = self._get_master_table(master_type)
        try:
            self.cursor.execute(f"DELETE FROM {table} WHERE id = ?", (master_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ValueError(f"Cannot delete {master_type} master. It is used in transactions.")
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"DB Error deleting {master_type} master: {e}")
            
    # --- GETTERS AND LOOKUPS (Existing) ---
    def get_setting(self, setting_type: str) -> str | None:
        try:
            self.cursor.execute("SELECT setting_value FROM utilities_settings WHERE setting_type = ?", (setting_type,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def save_setting(self, setting_type: str, setting_value: str, description: str = ""):
        try:
            self.cursor.execute("""
                    INSERT INTO utilities_settings (setting_type, setting_value, description) VALUES (?, ?, ?) ON CONFLICT(setting_type) DO UPDATE SET setting_value = ?, description = ? """, (setting_type, setting_value, description, setting_value, description))
            self.conn.commit()
            
            return True
        except Exception as e:
            print(f"Error saving setting: {e}")
            return False
            
    def get_account_names(self, exclude_groups: List[str] = None) -> List[str]:
        query = "SELECT master_name FROM account_master"
        params = []
        if exclude_groups:
     
            placeholders = ','.join('?' for _ in exclude_groups)
            query += f" WHERE group_type NOT IN ({placeholders})"
            params = exclude_groups
            
        query += " ORDER BY master_name"
        
        return [row[0] for row in self.cursor.execute(query, params)]

    def get_item_names(self) -> List[str]:
        return [row[0] for row in self.cursor.execute("SELECT item_name FROM item_master ORDER BY item_name")]

    def get_id_by_name(self, name: str, master_type: str) -> int |None:
        table = f"{master_type}_master"
        column = f"{master_type}_name"
        if master_type == 'account':
            column = 'master_name'
        
        try:
            self.cursor.execute(f"SELECT id FROM {table} WHERE {column} = ?", (name,))
            result = self.cursor.fetchone()
     
            return result[0] if result else None
        except Exception:
            return None
            
    def get_account_name_by_id(self, id: int) -> str |None:
        try:
            self.cursor.execute("SELECT master_name FROM account_master WHERE id = ?", (id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None
            
    def get_account_group_names(self) -> List[str]:
        return [row[0] for row in self.cursor.execute("SELECT DISTINCT group_type FROM account_master ORDER BY group_type")]


    # --- VOUCHER DATA FETCH (Existing) ---
    def _get_account_vouch_tables(self, vouch_type_code: str) -> Tuple[str, str] |None:
        vouch_map = {'PAY': 'payment', 'REC': 'receipt', 'JNL': 'journal', 'CON': 'journal'}
        base_name = vouch_map.get(vouch_type_code)
        if base_name:
            return f"{base_name}_header", f"{base_name}_lines"
        return None
        
    def _get_item_vouch_tables(self, vouch_type_code: str) -> Tuple[str, str] |None:
        item_map = {'SAL': 'sales', 'PUR': 'purchase', 'CN': 'creditnote', 'DN': 'debitnote'}
        base_name = item_map.get(vouch_type_code)
        if base_name:
            return f"{base_name}_header", f"{base_name}_lines"
        return None
        
    def add_account_voucher(self, vouch_type_code, header_data, line_data):
        tables = self._get_account_vouch_tables(vouch_type_code)
        if not tables: raise ValueError("Invalid account voucher type")
        header_table, line_table = tables
        
        try:
            self.cursor.execute(f"""
                INSERT INTO {header_table} (vouch_date, vouch_no, total_amount, narrative, ref_no, mode_of_payment_ref)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (header_data['vouch_date'], header_data['vouch_no'], 
            float(header_data['total_amount']), header_data['narrative'], header_data['ref_no'], header_data['mode_of_payment_ref']))
            header_id = self.cursor.lastrowid
            
            for line in line_data:
                self.cursor.execute(f"""
                    INSERT INTO {line_table} (vouch_header_id, dr_cr, master_account_id, amount, against_ref_no, remarks)
            
         VALUES (?, ?, ?, ?, ?, ?)
                """, (header_id, line['dr_cr'], line['master_account_id'], float(line['amount']), line['against_ref_no'], line['remarks']))
                
            self.conn.commit()
            return header_id
        except Exception as e:
            
            self.conn.rollback()
        raise ValueError(f"DB Error adding voucher: {e}")
            
    def update_account_voucher(self, voucher_id, vouch_type_code, header_data, line_data):
        # Placeholder update logic
        self.delete_account_voucher(voucher_id, vouch_type_code)
        return self.add_account_voucher(vouch_type_code, header_data, line_data)

    def delete_account_voucher(self, voucher_id, vouch_type_code):
        tables = self._get_account_vouch_tables(vouch_type_code)
        if not tables: return False
  
        header_table, _ = tables
        self.cursor.execute(f"DELETE FROM {header_table} WHERE id = ?", (voucher_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def add_item_voucher(self, vouch_type_code, header_data, line_data):
        tables = self._get_item_vouch_tables(vouch_type_code)
        if not tables: raise ValueError("Invalid item voucher type")
        header_table, line_table = tables
        
     
        try:
            self.cursor.execute(f"""
                INSERT INTO {header_table} (trans_date, vouch_no, ref_no, party_mas_id, tax_type, total_taxable_amt, total_tax_amt, final_bill_amt, narration, against_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (header_data['date'], header_data['vouch_no'], header_data['ref_no'], header_data['party_mas_id'], header_data['tax_type'], float(header_data['total_taxable_amt']), float(header_data['total_tax_amt']), float(header_data['final_bill_amt']), header_data['narration'], header_data['against_ref']))
         
            header_id = self.cursor.lastrowid
            
            for line in line_data:
                self.cursor.execute(f"""
                    INSERT INTO {line_table} (trans_header_id, item_mas_id, hsn_code, qty, rate, discount, taxable_amt, tax_amt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (header_id, line['item_mas_id'], line['hsn_code'], float(line['qty']), float(line['rate']), float(line['discount']), float(line['taxable_amt']), float(line['tax_amt'])))
                
            self.conn.commit()
            return header_id
        except Exception as e:
            self.conn.rollback()
      
        raise ValueError(f"DB Error adding item voucher: {e}")

    def update_item_voucher(self, voucher_id, vouch_type_code, header_data, line_data):
        # Placeholder update logic
        self.delete_item_voucher(voucher_id, vouch_type_code)
        return self.add_item_voucher(vouch_type_code, header_data, line_data)
        
    def delete_item_voucher(self, voucher_id, vouch_type_code):
        tables = self._get_item_vouch_tables(vouch_type_code)
        if not tables: return False
        header_table, _ = tables
        self.cursor.execute(f"DELETE FROM {header_table} WHERE id = ?", (voucher_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_voucher_data_by_id(self, voucher_id: int, vouch_type_code: str) -> Tuple[Dict, List[Dict]] |None:
        if vouch_type_code in ['PAY', 'REC', 'JNL', 'CON']:
            tables = self._get_account_vouch_tables(vouch_type_code)
            if not tables: return None
            header_table, line_table = tables
            
            # 1. Fetch Header Data
            self.cursor.execute(f"SELECT vouch_date, vouch_no, total_amount, narrative, ref_no, mode_of_payment_ref FROM {header_table} WHERE id = ?", (voucher_id,))
            header_row = self.cursor.fetchone()
            if not header_row: return None
            
            header_data = {
                'vouch_date': header_row[0], 'vouch_no': header_row[1], 'total_amount': header_row[2], 
          
                'narrative': header_row[3], 'ref_no': header_row[4], 'mode_of_payment_ref': header_row[5]
            }

            # 2. Fetch Line Data
            self.cursor.execute(f"""
                SELECT l.dr_cr, am.master_name, l.amount 
                FROM {line_table} l
           
            JOIN account_master am ON l.master_account_id = am.id
                WHERE l.vouch_header_id = ?""", (voucher_id,))
            
            line_data = [{'dr_cr': row[0], 'account_name': row[1], 'amount': Decimal(str(row[2]))} for row in self.cursor.fetchall()]
            return header_data, line_data

        elif vouch_type_code in ['SAL', 'PUR', 'CN', 'DN']:
            tables = self._get_item_vouch_tables(vouch_type_code)
            if not tables: return None
      
            header_table, line_table = tables

            # 1. Fetch Header Data
            self.cursor.execute(f"""
                SELECT h.trans_date, h.vouch_no, h.ref_no, am.master_name, h.tax_type, h.total_taxable_amt, h.total_tax_amt, h.final_bill_amt, h.narration, h.against_ref
                FROM {header_table} h
                JOIN account_master am ON h.party_mas_id = am.id
                WHERE h.id = ?
            """, (voucher_id,))
            header_row = self.cursor.fetchone()
            if not header_row: return None
            
            header_data = {
         
        'date': header_row[0], 'vouch_no': header_row[1], 'ref_no': header_row[2], 'party_name': header_row[3],
                'tax_type': header_row[4], 'total_taxable_amt': header_row[5], 'total_tax_amt': header_row[6],
                'final_bill_amt': header_row[7], 'narration': header_row[8], 'against_ref': header_row[9]
            }

            # 2. Fetch Line Data
            self.cursor.execute(f"""
    
             SELECT im.item_name, l.qty, l.rate, l.discount, l.taxable_amt, l.tax_amt
                FROM {line_table} l
                JOIN item_master im ON l.item_mas_id = im.id
                WHERE l.trans_header_id = ?""", (voucher_id,))
            
            line_data = [{
                'item_name': row[0], 'qty': Decimal(str(row[1])), 'rate': Decimal(str(row[2])), 
                'discount': Decimal(str(row[3])), 'taxable_amt': Decimal(str(row[4])), 
                'tax_amt': Decimal(str(row[5]))
            } for row in self.cursor.fetchall()]
            
            return header_data, line_data
        
        return None

    # --- REPORT DATA METHODS (Extended) ---
    def get_ledger_data(self, date_from: str, date_to: str, account_name: str) -> List[Tuple]:
        """Fetches all transactions for a specific account."""
        account_id = self.get_id_by_name(account_name, 'account')
       
        if not account_id: return [] 
        sub_queries = []
             # Account Vouchers
        for type_code, base in {'PAY': 'payment', 'REC': 'receipt', 'JNL': 'journal'}.items():
                sub_queries.append(f"""
                    SELECT h.vouch_date, h.vouch_no, '{type_code}', l.dr_cr, l.amount, h.narrative
                    FROM {base}_header h
                JOIN {base}_lines l ON h.id = l.vouch_header_id
                WHERE h.vouch_date BETWEEN ?AND ? AND l.master_account_id = ?
                """)
        
                combined_query = "\nUNION ALL\n".join(sub_queries)
                combined_query += " ORDER BY vouch_date, vouch_no"
                
                params = [param for sublist in [[date_from, date_to, account_id] for _ in range(len(sub_queries))] for param in sublist]
        
        try:
            self.cursor.execute(combined_query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"DB Error fetching Ledger: {e}")
            return []

    def get_day_book_data(self, date: str) -> List[Tuple]:
        """Fetches a summary of all voucher headers for a single day."""
        all_vouchers = []
        
  
        # Account Vouchers (PAY, REC, JNL)
        for type_code, base in {'PAY': 'payment', 'REC': 'receipt', 'JNL': 'journal'}.items():
            self.cursor.execute(f"""
                SELECT vouch_date, vouch_no, '{type_code}', total_amount, narrative
                FROM {base}_header
                WHERE vouch_date = ?""", (date,))
            all_vouchers.extend([(row[0], row[1], row[2], row[3], row[4]) for row in self.cursor.fetchall()])
            
            # Item Vouchers (SAL, PUR, CN, DN)
        for type_code, base in {'SAL': 'sales', 'PUR': 'purchase', 'CN': 'creditnote', 'DN': 'debitnote'}.items():
            self.cursor.execute(f"""
                SELECT trans_date, vouch_no, '{type_code}', final_bill_amt, narration
 
                FROM {base}_header
                WHERE trans_date = ?
            """, (date,))
            all_vouchers.extend([(row[0], row[1], row[2], row[3], row[4]) for row in self.cursor.fetchall()])

        return sorted(all_vouchers, key=lambda x: (x[0], x[1]))
        
            # Placeholder for Stock Register and Subsidiary  Book data (used in Report views)
    def get_stock_register_data(self, date_from: str, date_to: str) -> List[Tuple]:
        """Placeholder for Stock Register data."""
        return []
        
    def get_subsidiary_book_data(self, date_from: str, date_to: str, group_type: str) -> List[Tuple]:
        """Placeholder for Subsidiary Book data."""
        return []


# ==============================================================================
# 2. MASTER DIALOGS (NEW)
# ==============================================================================

class MasterEntryDialog(QDialog):
    def __init__(self, db_manager, master_type, parent=None, master_id=None):
     
        super().__init__(parent)
        self.db_manager = db_manager
        self.master_type = master_type
        self.current_master_id = master_id
        
        self.setWindowTitle(f"{'Edit' if master_id else 'Add'} {master_type.capitalize()} Master")
        self.setModal(True)
        self.resize(500, 300) # Adjusted size to fit more fields

            # --- WIDGETS ---
        self.name_line = QLineEdit()
        self.alias_line = QLineEdit() # NEW
        self.address_text = QTextEdit() # NEW
        self.phone_line = QLineEdit() # NEW
        self.email_line = QLineEdit() # NEW
        self.op_bal_line = DecimalLineEdit()
        self.op_type_combo = QComboBox() # Only for Account Master
        self.op_type_combo.addItems(['Dr', 'Cr'])
        
            # GST/PAN fields
        self.gst_line = QLineEdit()
        self.pan_line = QLineEdit() # NEW
        
        # Item specific fields
        self.unit_combo = AutoCompleteComboBox(self.db_manager, 'unit') # Only for Item Master
        self.tax_rate_line = DecimalLineEdit() # Only for Item Master
        self.purchase_price_line = DecimalLineEdit() # Only for Item Master
        self.sale_price_line = DecimalLineEdit() # Only for Item Master
        self.op_stock_line = DecimalLineEdit() # Only for Item Master
        self.op_rate_line = DecimalLineEdit() # Only for Item Master
        
        # Extra field: Group Type (Account) or HSN Code (Item)
        if master_type == 'account':
            self.extra_combo = AutoCompleteComboBox(self.db_manager, 'group')
            self.extra_combo.setCurrentText("Sales") # Default group

        else:
            self.extra_combo = QLineEdit() # HSN Code is just a line edit
    
        # --- LAYOUT ---
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        form_layout.addRow(QLabel("Name:"), self.name_line)
        form_layout.addRow(QLabel("Alias:"), self.alias_line) # NEW
     
    
        if self.master_type == 'account':
            form_layout.addRow(QLabel("Group Type (Extra):"), self.extra_combo)
            form_layout.addRow(QLabel("Opening Balance:"), self.op_bal_line)
            form_layout.addRow(QLabel("OB Type:"), self.op_type_combo)
            form_layout.addRow(QLabel("GST No.:"), self.gst_line)
            form_layout.addRow(QLabel("PAN No.:"), self.pan_line) # NEW
            
 
        elif self.master_type == 'item':
            form_layout.addRow(QLabel("HSN Code (Extra):"), self.extra_combo)
            form_layout.addRow(QLabel("Unit:"), self.unit_combo)
            form_layout.addRow(QLabel("Tax Rate (%):"), self.tax_rate_line)
            form_layout.addRow(QLabel("Purchase Price:"), self.purchase_price_line)
            form_layout.addRow(QLabel("Sale Price:"), self.sale_price_line)
            form_layout.addRow(QLabel("Opening Stock:"), self.op_stock_line)
     
        form_layout.addRow(QLabel("Opening Rate:"), self.op_rate_line)

        # Common contact/address fields (NEW)
        form_layout.addRow(QLabel("Address:"), self.address_text)
        form_layout.addRow(QLabel("Phone:"), self.phone_line)
        form_layout.addRow(QLabel("Email:"), self.email_line)
        
        main_layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._save_entry)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        if master_id:
            self._load_master_data()

    def _load_master_data(self):
        data = self.db_manager.get_master_entry_by_id(self.master_id, self.master_type)
        if data:
            self.name_edit.setText(data['name'])
            self.extra_combo.setCurrentText(data['group_or_hsn'])

    def _save_entry(self):
        """Handles saving the master entry to the database."""
        
        name = self.name_line.text().strip()
        alias = self.alias_line.text().strip()
        address = self.address_text.toPlainText().strip()
        phone = self.phone_line.text().strip()
        email = self.email_line.text().strip()
        
            # --- FIXED LOGIC  (Correctly get text based on widget type) ---
        if self.master_type == 'account':
            group_or_hsn = self.extra_combo.currentText().strip()
        else: # item master (QLineEdit)
            group_or_hsn = self.extra_combo.text().strip()
        # -------------------------------------------------------------
            
        opening_balance = self.op_bal_line.value()
        ob_type = self.op_type_combo.currentText()
 
        gst_no = self.gst_line.text().strip()
        pan_no = self.pan_line.text().strip() # NEW

        if not name:
            show_message(self, "Validation Error", "Name cannot be empty.", QMessageBox.Icon.Warning)
            return

        try:
            is_new = self.current_master_id is None
            if is_new and self.db_manager.master_exists(self.master_type, name):
                show_message(self, "Validation Error", f"{self.master_type.capitalize()} with this name already exists.", QMessageBox.Icon.Warning)
                return
            
                # Data dictionary updated to include all new fields
                data = {
                'name': name,
                'alias': alias,
                'address': address,
                'phone': phone,
                'email': email,
                'extra': group_or_hsn,
                'op_bal': opening_balance
                }
            
                if self.master_type == 'account':
                    data.update({'ob_type': ob_type,'gst_no': gst_no, 'pan_no': pan_no})

                elif self.master_type == 'item':
                    data.update({'unit': self.unit_combo.currentText().strip(),
                        'tax_rate': self.tax_rate_line.value(),
                        'purchase_price': self.purchase_price_line.value(),
                        'sale_price': self.sale_price_line.value(),
                        'opening_stock': self.op_stock_line.value(),
            
                    'opening_rate': self.op_rate_line.value()
                    })
                
                if is_new:
                    self.db_manager.add_master(self.master_type, data)
                    show_message(self, "Success", f"{self.master_type.capitalize()} added successfully.", QMessageBox.Icon.Information)
                else:
                    self.db_manager.update_master(self.master_type, self.current_master_id, data)
                    show_message(self, "Success", f"{self.master_type.capitalize()} updated successfully.", QMessageBox.Icon.Information)

                self.accept()

        except Exception as e:
            show_message(self, "Database Error", f"An error occurred while saving: {e}", QMessageBox.Icon.Critical)

class MasterViewWindow(QDialog):
    def __init__(self, db_manager: DBManager, master_type: str, parent=None):
  
        super().__init__(parent)
        self.db_manager = db_manager
        self.master_type = master_type
        
        type_name = self.master_type.capitalize()
        self.setWindowTitle(f"{type_name} Master List")
        self.setGeometry(100, 100, 800, 500)

        # Widgets
        self.master_table = QTableWidget()
        self.master_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.master_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.master_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.master_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        self.add_button = QPushButton(f"&Add New {type_name}")
        self.modify_button = QPushButton(f"&Modify Selected {type_name}")
        self.delete_button = QPushButton(f"&Delete Selected {type_name}")
        
        self.add_button.clicked.connect(self._add_entry)
        self.modify_button.clicked.connect(self._modify_entry)
        self.delete_button.clicked.connect(self._delete_entry)
        
        # Layout
        main_layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.modify_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.master_table)
        
        self.load_data()

    def load_data(self):
        data = self.db_manager.get_all_master_entries(self.master_type)
        if self.master_type == 'account':
            headers = ["ID", "Account Name", "Group Type"]
        else:
            headers = ["ID", "Item Name", "HSN Code"]
        
        self.master_table.setRowCount(len(data))
        self.master_table.setColumnCount(len(headers))
        self.master_table.setHorizontalHeaderLabels(headers)
        
        for row_index, row_data in enumerate(data):
            self.master_table.setItem(row_index, 0, QTableWidgetItem(str(row_data['id'])))
            self.master_table.setItem(row_index, 1, QTableWidgetItem(row_data['name']))
            self.master_table.setItem(row_index, 2, QTableWidgetItem(row_data['group_or_hsn']))
            
        self.master_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.master_table.resizeColumnsToContents()
        
    def _get_selected_id(self) -> int |None:
        selected_rows = self.master_table.selectionModel().selectedRows()
        if not selected_rows:
            show_message(self, "Selection Error", f"Please select a {self.master_type.capitalize()} to modify/delete.", QMessageBox.Icon.Warning)
            return None
        return int(self.master_table.item(selected_rows[0].row(), 0).text())

    def _add_entry(self):
        dialog = MasterEntryDialog(self.db_manager, self.master_type, parent=self)
        if dialog.exec():
            self.load_data()

    def _modify_entry(self):
        master_id = self._get_selected_id()
        if master_id:
            dialog = MasterEntryDialog(self.db_manager, self.master_type, master_id, parent=self)
            if dialog.exec():
                self.load_data()

    def _delete_entry(self):
        master_id = self._get_selected_id()
        if not master_id:
            return
            
        name = self.master_table.item(self.master_table.selectionModel().selectedRows()[0].row(), 1).text()
        reply = QMessageBox.question(self, f"Delete {self.master_type.capitalize()}", f"Are you sure you want to delete {self.master_type.capitalize()} '{name}'?", QMessageBox.StandardButton.Yes |
 QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.db_manager.delete_master_entry(master_id, self.master_type):
                    show_message(self, "Success", f"{self.master_type.capitalize()} deleted.", QMessageBox.Icon.Information)
                    self.load_data()
                
            except ValueError as e:
                show_message(self, "Constraint Error", str(e), QMessageBox.Icon.Warning)
            except Exception as e:
                show_message(self, "DB Error", f"Error during deletion: {e}", QMessageBox.Icon.Critical)

# ==============================================================================
# 3. VOUCHER DIALOGS (Fixed self.account_names initialization and False ID loading)
# ==============================================================================

class VoucherEntryDialog(QDialog):
    
    VOUCHER_TYPES = {
        'PAY': 'Payment', 'REC': 'Receipt', 'JNL': 'Journal', 'CON': 'Contra',
        'SAL': 'Sales', 'PUR': 'Purchase', 'CN': 'Credit Note', 'DN': 'Debit Note'
    }

    def __init__(self, db_manager: DBManager, vouch_type_code: str, parent=None, voucher_id: int = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.vouch_type_code = vouch_type_code
        self.voucher_id = voucher_id # Can be None for new entry

        self.is_item_voucher = vouch_type_code in ['SAL', 'PUR', 'CN', 'DN']
        
        # --- Data Sources (Fetch once) ---
        self.item_names = self.db_manager.get_item_names()
        
        # Determine the group type for Party/Account selection
        party_master_type = self.db_manager.get_setting("PartyMasterType")
        if party_master_type:
            # Exclude the party group itself from the line item selection for safety/logic
            self.account_names = self.db_manager.get_account_names(exclude_groups=[party_master_type])
            self.party_names = self.db_manager.get_account_names(exclude_groups=[])
        else:
            # Default to all accounts if setting is missing (Party Combo uses all, Line Combo excludes nothing)
            self.account_names = self.db_manager.get_account_names(exclude_groups=[]) 
            self.party_names = self.account_names

        # --- Header Widgets ---
        self.vouch_no_edit = QLineEdit()
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.ref_no_edit = QLineEdit()
        self.narration_edit = QTextEdit()
        self.narration_edit.setPlaceholderText("Enter transaction details/remarks here...")

        # --- Footer Widgets (Account Voucher only) ---
        self.total_dr_label = QLabel("Total Dr: 0.00")
        self.total_cr_label = QLabel("Total Cr: 0.00")
        self.total_dr_label.setStyleSheet("font-weight: bold;") 
        self.total_cr_label.setStyleSheet("font-weight: bold;")
        
        # Layout structure setup
        main_layout = QVBoxLayout(self)
        self.header_area = QGroupBox("Header Details") 
        
        # Header Layout setup
        header_layout = QFormLayout(self.header_area)
        header_layout.addRow("Voucher No:", self.vouch_no_edit)
        header_layout.addRow("Date:", self.date_edit)
        header_layout.addRow("Reference No:", self.ref_no_edit)
        header_layout.addRow("Narration:", self.narration_edit)
        
        self.trans_area = QStackedWidget() 
        
        # NOTE: Both creation methods are called to initialize the widgets in the stacked widget
        self._create_account_voucher_area()
        self._create_item_voucher_area()

        if self.is_item_voucher:
            self.trans_area.addWidget(self.item_area)
            self.trans_area.setCurrentWidget(self.item_area)
        else:
            self.trans_area.addWidget(self.account_area)
            self.trans_area.setCurrentWidget(self.account_area)

        main_layout.addWidget(self.header_area)
        main_layout.addWidget(self.trans_area)

        self.save_button = QPushButton("Save Entry")
        self.save_button.clicked.connect(self._save_voucher)
        main_layout.addWidget(self.save_button)

        # Modification Mode Setup
        type_name = self.VOUCHER_TYPES.get(vouch_type_code, "Voucher")
        if self.voucher_id is not None:
            self.setWindowTitle(f"Modify {type_name} Voucher ID: {self.voucher_id}")
            self.save_button.setText("Update/Modify")
            self.save_button.clicked.disconnect()
            self.save_button.clicked.connect(self._modify_voucher)
            self._load_voucher_data()
        else:
            self.setWindowTitle(f"New {type_name} Entry")

    # --- WIDGET CREATION METHODS ---
    def _create_account_voucher_area(self):
        """Creates the GUI components for account-based vouchers (PAY/REC/JNL/CON)."""
        self.account_area = QWidget()
        layout = QVBoxLayout(self.account_area)
        
        # Table
        self.account_table = QTableWidget()
        self.account_table.setColumnCount(3)
        self.account_table.setHorizontalHeaderLabels(["Account Name", "Debit Amount", "Credit Amount"])
        self.account_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.account_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.account_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Add a default starting row
        self._add_account_row()
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.total_dr_label)
        footer_layout.addWidget(self.total_cr_label)
        
        layout.addWidget(self.account_table)
        layout.addLayout(footer_layout)
        
        # Connect signal for adding new rows when an existing row is used
        self.account_table.itemChanged.connect(self._check_and_add_account_row)
        
    def _create_item_voucher_area(self):
        """Creates the GUI components for item-based vouchers (SAL/PUR/CN/DN)."""
        self.item_area = QWidget()
        main_layout = QVBoxLayout(self.item_area)
        
        # Party Selection
        party_layout = QHBoxLayout()
        self.party_combo = AutoCompleteComboBox(self.party_names)
        party_layout.addWidget(QLabel("Party/Account:"))
        party_layout.addWidget(self.party_combo)
        
        # Table
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(7)
        self.item_table.setHorizontalHeaderLabels(["Item Name", "Qty", "Rate", "Disc (%)", "Taxable Amt", "Tax Amt", "Total"])
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 7):
            self.item_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        # Add a default starting row
        self._add_item_row()
        
        main_layout.addLayout(party_layout)
        main_layout.addWidget(self.item_table)
        
        # Connect signal for adding new rows when an existing row is used
        self.item_table.itemChanged.connect(self._check_and_add_item_row)

    # --- ITEM VOUCHER ROW LOGIC ---
    def _add_item_row_widgets(self, row: int, line_data: Dict = 
 None):
        """Helper to create and populate item row widgets."""
        # New row widgets
        self.item_table.setCellWidget(row, 0, AutoCompleteComboBox(self.item_names))
        self.item_table.setCellWidget(row, 1, DecimalLineEdit())
        self.item_table.setCellWidget(row, 2, DecimalLineEdit())
        self.item_table.setCellWidget(row, 3, DecimalLineEdit())
        self.item_table.setCellWidget(row, 4, DecimalLineEdit())
        self.item_table.setCellWidget(row, 5, DecimalLineEdit())
        total_edit = DecimalLineEdit()
        total_edit.setReadOnly(True)
        total_edit.setStyleSheet("background-color: #f0f0f0;")
        self.item_table.setCellWidget(row, 6, total_edit)

        # Connect signals for row calculation
        for col in range(1, 4):
            self.item_table.cellWidget(row, col).textChanged.connect(partial(self._recalculate_item_row, row))
            
        # If data is provided, populate the widgets
        if line_data:
            self.item_table.cellWidget(row, 0).setCurrentText(line_data['item_name'])
            self.item_table.cellWidget(row, 1).set_value(line_data['qty'])
            self.item_table.cellWidget(row, 2).set_value(line_data['rate'])
            self.item_table.cellWidget(row, 3).set_value(line_data['discount'])
            self.item_table.cellWidget(row, 4).set_value(line_data['taxable_amt'])
            self.item_table.cellWidget(row, 5).set_value(line_data['tax_amt'])
            # The total is calculated automatically by the connected signal after populating inputs

    def _add_item_row(self):
        """Adds a blank row to the item table."""
        row_count = self.item_table.rowCount()
        self.item_table.insertRow(row_count)
        self._add_item_row_widgets(row_count)

    def _check_and_add_item_row(self, item):
        """Checks if the last row is being used and adds a new one if necessary."""
        row = item.row()
        col = item.column()
        # Only consider changes in the last row for the item name column (0)
        if row == self.item_table.rowCount() - 1 and col == 0:
            if self.item_table.cellWidget(row, 0).currentText().strip():
                self._add_item_row()
                
    # --- VOUCHER DATA LOADING AND UTILITIES ---
    def _load_voucher_data(self):
        """Loads data for modification mode."""
        data = self.db_manager.get_voucher_data_by_id(self.voucher_id, self.vouch_type_code)
        
        if data is None:
            show_message(self, "Load Error", f"Voucher ID {self.voucher_id} not found in database.", QMessageBox.Icon.Critical)
            self.reject()
            return

        header_data, line_data = data
        
        # --- Load Header Data ---
        vouch_date_str = header_data.get('vouch_date') or header_data.get('date') # Account vs Item key
        if vouch_date_str:
            self.date_edit.setDate(QDate.fromString(vouch_date_str, Qt.DateFormat.ISODate))
        self.vouch_no_edit.setText(header_data['vouch_no'])
        self.ref_no_edit.setText(header_data.get('ref_no', ''))
        self.narration_edit.setText(header_data.get('narrative') or header_data.get('narration', ''))

        # --- Load Line Data ---
        if self.is_item_voucher:
            # Item Voucher Lines
            self.party_combo.setCurrentText(header_data['party_name'])
            
            # Clear and resize table
            self.item_table.setRowCount(0)
            for i, line in enumerate(line_data):
                self.item_table.insertRow(i)
                self._add_item_row_widgets(i, line)
            
            # Ensure at least one blank row is available
            if not line_data or len(line_data) == self.item_table.rowCount():
                self._add_item_row()
        else:
            # Account Voucher Lines
            # Clear and resize table
            self.account_table.setRowCount(0) 
            for i, line in enumerate(line_data):
                self.account_table.insertRow(i)
                # Use helper to create widgets and connect signals
                self._add_account_row(i, line, connect_signals=True)
            
            # Ensure at least one blank row is available
            if not line_data or len(line_data) == self.account_table.rowCount():
                self._add_account_row()
            
            self._recalculate_account_totals() # Update totals display
            
    # --- VOUCHER ACTIONS (Internal methods) ---
    def _recalculate_item_row(self, row: int):
        try:
            qty = self.item_table.cellWidget(row, 1).value()
            rate = self.item_table.cellWidget(row, 2).value()
            discount = self.item_table.cellWidget(row, 3).value()
            
            if qty == Decimal('0.00') or rate == Decimal('0.00'):
                taxable_amt = Decimal('0.00')
                tax_amt = Decimal('0.00')
            else:
                # 1. Calculate base value
                base_value = qty * rate
                
                # 2. Calculate discount
                discount_amount = base_value * (discount / Decimal('100.00'))
                
                # 3. Calculate taxable amount (Value - Discount)
                taxable_amt = base_value - discount_amount
                
                # 4. Calculate Tax (Using a placeholder lookup for simplicity)
                # NOTE: Real implementation would look up tax rate from Item Master
                # For now, let's use a fixed 18% tax on sales/purchases only
                tax_rate = Decimal('0.00') 
                if self.vouch_type_code in ['SAL', 'PUR']:
                    # Placeholder logic to fetch tax rate from DB based on item name (if needed later)
                    # For now, fixed
                    tax_rate = Decimal('18.00')
                
                tax_amt = taxable_amt * (tax_rate / Decimal('100.00'))

            final_total = taxable_amt + tax_amt
            
            # Update the display widgets
            self.item_table.cellWidget(row, 4).set_value(taxable_amt) # Taxable Amt
            self.item_table.cellWidget(row, 5).set_value(tax_amt) # Tax Amt
            self.item_table.cellWidget(row, 6).set_value(final_total) # Total

        except Exception as e:
            # print(f"Error recalculating item row {row}: {e}") # Debugging
            pass
    
    def _recalculate_account_totals(self):
        """Recalculates the total Debit and Credit amounts."""
        dr_total = Decimal('0.00')
        cr_total = Decimal('0.00')

        for i in range(self.account_table.rowCount()):
            dr_edit = self.account_table.cellWidget(i, 1)
            cr_edit = self.account_table.cellWidget(i, 2)
            
            if dr_edit:
                dr_total += dr_edit.value()
            if cr_edit:
                cr_total += cr_edit.value()
                
        self.total_dr_label.setText(f"Total Dr: {dr_total:,.2f}")
        self.total_cr_label.setText(f"Total Cr: {cr_total:,.2f}")
        
        # Color difference
        if dr_total != cr_total:
            self.total_dr_label.setStyleSheet("font-weight: bold; color: red;")
            self.total_cr_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            self.total_dr_label.setStyleSheet("font-weight: bold; color: green;")
            self.total_cr_label.setStyleSheet("font-weight: bold; color: green;")
            
    def _check_and_add_account_row(self):
        """Checks if the last row is being used (has a name or amount) and adds a new one if necessary."""
        if self.account_table.rowCount() == 0:
            self._add_account_row()
            return
            
        last_row = self.account_table.rowCount() - 1
        account_combo = self.account_table.cellWidget(last_row, 0)
        dr_edit = self.account_table.cellWidget(last_row, 1)
        cr_edit = self.account_table.cellWidget(last_row, 2)
        
        if not (account_combo and dr_edit and cr_edit): return # Should not happen

        account = account_combo.currentText().strip()
        dr_val = dr_edit.value()
        cr_val = cr_edit.value()
        
        # Check if the last row is actually used
        if account and (dr_val > Decimal('0.00') or cr_val > Decimal('0.00')):
            self._add_account_row()
            
    def _add_account_row(self, row: int = -1, line_data: Dict = None, connect_signals: bool = True):
        """Adds an account row and optionally populates it and connects signals."""
        if row == -1:
            row = self.account_table.rowCount()
        self.account_table.insertRow(row)

        # This is where the self.account_names attribute is used.
        account_combo = AutoCompleteComboBox(self.account_names)
        dr_edit = DecimalLineEdit()
        cr_edit = DecimalLineEdit()
        
        self.account_table.setCellWidget(row, 0, account_combo)
        self.account_table.setCellWidget(row, 1, dr_edit)
        self.account_table.setCellWidget(row, 2, cr_edit)
        
        if connect_signals:
            dr_edit.textChanged.connect(self._recalculate_account_totals)
            cr_edit.textChanged.connect(self._recalculate_account_totals)
            
        if line_data:
            account_combo.setCurrentText(line_data['account_name'])
            if line_data['dr_cr'] == 'Dr':
                dr_edit.set_value(line_data['amount'])
            else:
                cr_edit.set_value(line_data['amount'])

    def _get_account_data(self) -> Optional[Tuple[Dict, List[Dict]]]:
        vouch_no = self.vouch_no_edit.text().strip()
        if not vouch_no:
            show_message(self, "Validation Error", "Voucher No. cannot be empty.", QMessageBox.Icon.Warning)
            return None
        
        header_data = {
            'vouch_date': self.date_edit.date().toString(Qt.DateFormat.ISODate),
            'vouch_no': vouch_no,
            'narrative': self.narration_edit.toPlainText().strip(),
            'ref_no': self.ref_no_edit.text().strip(),
            'mode_of_payment_ref': 'CASH/BANK' if self.vouch_type_code in ['PAY', 'REC', 'CON'] else None
        }

        line_data = []
        dr_total = Decimal('0.00')
        cr_total = Decimal('0.00')
        active_lines = 0

        for i in range(self.account_table.rowCount()):
            account_combo = self.account_table.cellWidget(i, 0)
            dr_edit = self.account_table.cellWidget(i, 1)
            cr_edit = self.account_table.cellWidget(i, 2)

            if not (account_combo and dr_edit and cr_edit): continue
            
            account_name = account_combo.currentText().strip()
            dr_val = dr_edit.value()
            cr_val = cr_edit.value()
            
            if not account_name and (dr_val > Decimal('0.00') or cr_val > Decimal('0.00')):
                show_message(self, "Validation Error", f"Account name missing on line {i+1}.", QMessageBox.Icon.Warning)
                return None
                
            if account_name:
                account_id = self.db_manager.get_id_by_name(account_name, 'account')
                if account_id is None:
                    show_message(self, "Validation Error", f"Account '{account_name}' on line {i+1} is not in Account Master.", QMessageBox.Icon.Warning)
                    return None
            
                if dr_val > Decimal('0.00') and cr_val > Decimal('0.00'):
                    show_message(self, "Validation Error", f"Line {i+1} cannot have both Debit and Credit amounts.", QMessageBox.Icon.Warning)
                    return None
                
                if dr_val > Decimal('0.00'):
                    line_data.append({'dr_cr': 'Dr', 'master_account_id': account_id, 'amount': dr_val, 'against_ref_no': '', 'remarks': ''})
                    dr_total += dr_val
                    active_lines += 1
                elif cr_val > Decimal('0.00'):
                    line_data.append({'dr_cr': 'Cr', 'master_account_id': account_id, 'amount': cr_val, 'against_ref_no': '', 'remarks': ''})
                    cr_total += cr_val
                    active_lines += 1

        if active_lines < 2:
            show_message(self, "Validation Error", "Account vouchers require at least two active lines (Dr and Cr).", QMessageBox.Icon.Warning)
            return None
            
        if dr_total != cr_total:
            show_message(self, "Validation Error", f"Debit Total ({dr_total:,.2f}) must equal Credit Total ({cr_total:,.2f}).", QMessageBox.Icon.Warning)
            return None

        header_data['total_amount'] = dr_total # Total amount is the matching Dr/Cr sum

        return header_data, line_data

    def _get_item_data(self) -> Optional[Tuple[Dict, List[Dict]]]:
        vouch_no = self.vouch_no_edit.text().strip()
        party_name = self.party_combo.currentText().strip()
        
        if not vouch_no:
            show_message(self, "Validation Error", "Voucher No. cannot be empty.", QMessageBox.Icon.Warning)
            return None
        if not party_name:
            show_message(self, "Validation Error", "Party/Account must be selected.", QMessageBox.Icon.Warning)
            return None
        
        party_id = self.db_manager.get_id_by_name(party_name, 'account')
        if party_id is None:
            show_message(self, "Validation Error", f"Party '{party_name}' is not in Account Master.", QMessageBox.Icon.Warning)
            return None
            
        line_data = []
        total_taxable_amt = Decimal('0.00')
        total_tax_amt = Decimal('0.00')

        for i in range(self.item_table.rowCount()):
            item_combo = self.item_table.cellWidget(i, 0)
            qty_edit = self.item_table.cellWidget(i, 1)
            rate_edit = self.item_table.cellWidget(i, 2)
            discount_edit = self.item_table.cellWidget(i, 3)
            taxable_edit = self.item_table.cellWidget(i, 4)
            tax_edit = self.item_table.cellWidget(i, 5)

            if not (item_combo and qty_edit and rate_edit and discount_edit and taxable_edit and tax_edit): continue
            
            item_name =  item_combo.currentText().strip()
            qty = qty_edit.value()
            rate = rate_edit.value()
            discount = discount_edit.value()
            taxable_amt = taxable_edit.value()
            tax_amt = tax_edit.value()

            if qty > Decimal('0.00') and item_name:
                item_id = self.db_manager.get_id_by_name(item_name, 'item')
                if item_id is None:
                    show_message(self, "Validation Error", f"Item '{item_name}' on line {i+1} is not in Item Master.", QMessageBox.Icon.Warning)
                    return None
                
                # HSN code is placeholder '0000' as lookup is not implemented
                line_data.append({
                    'item_mas_id': item_id,
                    'hsn_code': '0000',
                    'qty': qty,
                    'rate': rate,
                    'discount': discount,
                    'taxable_amt': taxable_amt,
                    'tax_amt': tax_amt
                })
                total_taxable_amt += taxable_amt
                total_tax_amt += tax_amt

        if not line_data:
            show_message(self, "Validation Error", "Voucher must contain at least one item line.", QMessageBox.Icon.Warning)
            return None

        final_bill_amt = total_taxable_amt + total_tax_amt
        
        header_data = {
            'date': self.date_edit.date().toString(Qt.DateFormat.ISODate),
            'vouch_no': vouch_no,
            'ref_no': self.ref_no_edit.text().strip(),
            'party_mas_id': party_id,
            'tax_type': 'GST',
            'total_taxable_amt': total_taxable_amt,
            'total_tax_amt': total_tax_amt,
            'final_bill_amt': final_bill_amt,
            'narration': self.narration_edit.toPlainText().strip(),
            'against_ref': '' # Placeholder
        }
        
        return header_data, line_data

    def _save_voucher(self):
        vouch_type_name = self.VOUCHER_TYPES.get(self.vouch_type_code, "Voucher")
        
        data = self._get_item_data() if self.is_item_voucher else self._get_account_data()
        if data is None: return

        header_data, line_data = data
        
        try:
            if self.is_item_voucher:
                new_id = self.db_manager.add_item_voucher(self.vouch_type_code, header_data, line_data)
            else:
                new_id = self.db_manager.add_account_voucher(self.vouch_type_code, header_data, line_data)

            if new_id:
                show_message(self, "Success", f"{vouch_type_name} Voucher added successfully (ID: {new_id}).", QMessageBox.Icon.Information)
                self.accept()
            else:
                show_message(self, "Error", f"Failed to add {vouch_type_name} voucher.", QMessageBox.Icon.Critical)

        except ValueError as e:
            show_message(self, "DB Constraint Error", str(e), QMessageBox.Icon.Warning)
        except Exception as e:
            show_message(self, "DB Error", f"An unexpected error occurred while saving: {e}", QMessageBox.Icon.Critical)

    def _modify_voucher(self):
        vouch_type_name = self.VOUCHER_TYPES.get(self.vouch_type_code, "Voucher")
        
        data = self._get_item_data() if self.is_item_voucher else self._get_account_data()
        if data is None: return

        header_data, line_data = data
        
        try:
            if self.is_item_voucher:
                success = self.db_manager.update_item_voucher(self.voucher_id, self.vouch_type_code, header_data, line_data)
            else:
                success = self.db_manager.update_account_voucher(self.voucher_id, self.vouch_type_code, header_data, line_data)

            if success:
                show_message(self, "Success", f"{vouch_type_name} Voucher ID {self.voucher_id} updated successfully.", QMessageBox.Icon.Information)
                self.accept()
            else:
                show_message(self, "Error", f"Failed to update {vouch_type_name} voucher.", QMessageBox.Icon.Critical)

        except ValueError as e:
            show_message(self, "DB Constraint Error", str(e), QMessageBox.Icon.Warning)
        except Exception as e:
            show_message(self, "DB Error", f"An unexpected error occurred while updating: {e}", QMessageBox.Icon.Critical)

# ==============================================================================
# 4. REPORT VIEWS (EXTENDED)
# ==============================================================================

class BaseReportView(QDialog):
    def __init__(self, db_manager, title, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1000, 600)

        self.main_layout = QVBoxLayout(self)
        self.controls_layout = QHBoxLayout()
        
        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.report_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.report_table.horizontalHeader().setStretchLastSection(True)

        self.date_from = QDateEdit(calendarPopup=True)
        self.date_to = QDateEdit(calendarPopup=True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        
        self.generate_button = QPushButton("Generate Report")
        self.generate_button.clicked.connect(self.generate_report)

        self.controls_layout.addWidget(QLabel("From:"))
        self.controls_layout.addWidget(self.date_from)
        self.controls_layout.addWidget(QLabel("To:"))
        self.controls_layout.addWidget(self.date_to)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.generate_button)

        self.main_layout.addLayout(self.controls_layout)
        self.main_layout.addWidget(self.report_table)

    def generate_report(self):
        """Must be implemented by subclasses."""
        pass
        
    def _set_table_data(self, headers, data):
        """Helper to populate the QTableWidget."""
        self.report_table.setRowCount(0)
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)

        for row_index, row_data in enumerate(data):
            self.report_table.insertRow(row_index)
            for col_index, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if isinstance(value, (int, float, Decimal)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.report_table.setItem(row_index, col_index, item)
        
        self.report_table.resizeColumnsToContents()
        
class LedgerReportView(BaseReportView):
    def __init__(self, db_manager, parent=None):
        super().__init__(db_manager, "Account Ledger Report", parent)

        # Additional control for selecting the account
        self.account_names = self.db_manager.get_account_names()
        self.account_combo = AutoCompleteComboBox(self.account_names)
        
        # Add account selector to the controls layout
        self.controls_layout.insertWidget(0, self.account_combo)
        self.controls_layout.insertWidget(0, QLabel("Account:"))
        
    def generate_report(self):
        date_from = self.date_from.date().toString(Qt.DateFormat.ISODate)
        date_to = self.date_to.date().toString(Qt.DateFormat.ISODate)
        account_name = self.account_combo.currentText().strip()
        
        if not account_name:
            show_message(self, "Validation Error", "Please select an account.", QMessageBox.Icon.Warning)
            return

        data = self.db_manager.get_ledger_data(date_from, date_to, account_name)
        
        headers = ["Date", "Voucher No", "Type", "Dr/Cr", "Amount", "Narration", "Balance"]
        
        # Calculate running balance (simple debit/credit)
        running_balance = Decimal('0.00')
        processed_data = []
        for row in data:
            date, vouch_no, vouch_type, dr_cr, amount, narration = row
            amount = Decimal(str(amount))
            if dr_cr == 'Dr':
                running_balance += amount
            else:
                running_balance -= amount

            # Format balance: positive = Dr, negative = Cr
            balance_str = f"{abs(running_balance):,.2f} {'Dr' if running_balance >= 0 else 'Cr'}"
            processed_data.append(row + (balance_str,))

        self._set_table_data(headers, processed_data)
        self.setWindowTitle(f"{account_name} Ledger")

        if not data:
            show_message(self, "No Data", f"No transactions found for {account_name} in the selected date range.", QMessageBox.Icon.Information)

class DayBookReport(BaseReportView):
    def __init__(self, db_manager, parent=None):
        super().__init__(db_manager, "Day Book Report", parent)

        # Day Book is usually for a single day, remove  'From' date edit
        # Remove widgets from controls_layout in reverse order of addition
        self.controls_layout.itemAt(4).widget().deleteLater() # Generate button (removed later)
        self.controls_layout.itemAt(3).widget().deleteLater() # 'To:' label
        self.controls_layout.itemAt(2).widget().deleteLater() # date_to
        self.controls_layout.itemAt(1).widget().deleteLater() # 'From:' label
        self.controls_layout.itemAt(0).widget().deleteLater() # date_from
        
        # Recreate date_to (now acting as single date selector)
        self.date_to = QDateEdit(calendarPopup=True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(100)
        
        self.controls_layout.insertWidget(0, self.date_to)
        self.controls_layout.insertWidget(0, QLabel("Date:"))

        # Re-add generate button
        self.controls_layout.addWidget(self.generate_button)

    def generate_report(self):
        target_date = self.date_to.date().toString(Qt.DateFormat.ISODate)
        data = self.db_manager.get_day_book_data(target_date)
        
        headers = ["Date", "Voucher No", "Type", "Amount", "Narration"]
        self._set_table_data(headers, data)

        self.setWindowTitle(f"Day Book for {self.date_to.date().toString(Qt.DateFormat.TextDate)}")
        
        if not data:
            show_message(self, "No Data", f"No vouchers found for {target_date}.", QMessageBox.Icon.Information)

# ==============================================================================
# 5. MAIN WINDOW AND LAUNCHER
# ==============================================================================

class UtilitiesSettingDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Utilities Master Type Settings")
        self.setGeometry(300, 300, 400, 200)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.setting_type_edit = QLineEdit("PartyMasterType")
        self.setting_type_edit.setToolTip("Defines the Account Group used to populate Party/Customer/Vendor combo boxes.")
        self.setting_type_edit.setReadOnly(True)
        
        self.account_groups = self.db_manager.get_account_group_names()
        self.group_combo = QComboBox()
        self.group_combo.addItems(self.account_groups)

        form_layout.addRow(QLabel("Master Type:"), self.setting_type_edit)
        form_layout.addRow(QLabel("Select Account Group:"), self.group_combo)
        
        current_setting = self.db_manager.get_setting(self.setting_type_edit.text())
        if current_setting and current_setting in self.account_groups:
            self.group_combo.setCurrentText(current_setting)
        elif "Sundry Debtors" in self.account_groups: 
            self.group_combo.setCurrentText("Sundry Debtors")
        main_layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def save_settings(self):
        setting_type = self.setting_type_edit.text().strip()
        setting_value = self.group_combo.currentText().strip()
        description = f"Account Group selected for master type {setting_type}"

        if not setting_type or not setting_value:
            show_message(self, "Error", "Master Type and Account Group cannot be empty.", QMessageBox.Icon.Warning)
            return

        if self.db_manager.save_setting(setting_type, setting_value, description):
            show_message(self, "Success", f"Setting '{setting_type}' saved successfully.", QMessageBox.Icon.Information)
            self.accept()
        else:
            show_message(self, "Error", "Failed to save setting.", QMessageBox.Icon.Critical)

class MainWindow(QMainWindow):
    def __init__(self, db_manager: DBManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Project Suite Accounting Utility (PySide6)")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        status_label = QLabel("Welcome to the Accounting Utility. Use the menus to navigate.")
        main_layout.addWidget(status_label)

        # --------------------------------------------------------------------------
        # --- 1. Actions ---
        # --------------------------------------------------------------------------
        self.action_exit = QAction("&Exit", self)
        self.action_exit.setShortcut("Ctrl+Q")
        self.action_exit.triggered.connect(QApplication.instance().quit)

        # Master Actions
        self.action_add_account = QAction("&Add Account", self)
        self.action_add_item = QAction("Add &Item", self)
        self.action_view_accounts = QAction("&View Accounts", self)
        self.action_view_items = QAction("View I&tems", self)
        
        # Voucher Actions
        self.action_add_payment = QAction("Add &Payment (F5)", self)
        self.action_add_receipt = QAction("Add &Receipt (F6)", self)
        self.action_add_journal = QAction("Add &Journal (F7)", self)
        self.action_add_sales = QAction("Add &Sales (F8)", self)
        self.action_add_purchase = QAction("Add &Purchase (F9)", self)
        self.action_view_vouchers = QAction("&View All Vouchers", self)
        
        # Report Actions
        self.action_daybook = QAction("&Day Book", self)
        self.action_ledger = QAction("&Ledger", self)
        self.action_trail_balance = QAction("&Trial Balance", self)
        
        # Utility Actions
        self.action_settings = QAction("&Settings", self)

        self.action_about = QAction("&About", self)

        # --------------------------------------------------------------------------
        # --- 2. Connections ---
        # --------------------------------------------------------------------------
        self.action_add_account.triggered.connect(lambda: MasterEntryDialog(self.db_manager, 'account', self).exec())
        self.action_add_item.triggered.connect(lambda: MasterEntryDialog(self.db_manager, 'item', self).exec())
        self.action_view_accounts.triggered.connect(lambda: MasterViewWindow(self.db_manager, 'account', self).exec())
        self.action_view_items.triggered.connect(lambda: MasterViewWindow(self.db_manager, 'item', self).exec())
        
        # Voucher connections
        self.action_add_payment.triggered.connect(lambda: VoucherEntryDialog(self.db_manager, 'PAY', self).exec())
        self.action_add_receipt.triggered.connect(lambda: VoucherEntryDialog(self.db_manager, 'REC', self).exec())
        self.action_add_journal.triggered.connect(lambda: VoucherEntryDialog(self.db_manager, 'JNL', self).exec())
        self.action_add_sales.triggered.connect(lambda: VoucherEntryDialog(self.db_manager, 'SAL', self).exec())
        self.action_add_purchase.triggered.connect(lambda: VoucherEntryDialog(self.db_manager, 'PUR', self).exec())
        self.action_view_vouchers.triggered.connect(self._open_view_vouchers_dialog)

        # Report connections
        self.action_daybook.triggered.connect(self._open_report_dialog)
        self.action_ledger.triggered.connect(self._open_report_dialog)
        self.action_trail_balance.triggered.connect(self._open_report_dialog)
        
        # Utility connections
        self.action_settings.triggered.connect(lambda: UtilitiesSettingDialog(self.db_manager, self).exec())
        self.action_about.triggered.connect(self._show_about_dialog)
        
        # --------------------------------------------------------------------------
        # --- 3. Menu Bar ---
        # --------------------------------------------------------------------------
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.action_exit)

        # Master Menu
        master_menu = menu_bar.addMenu("&Master")
        master_menu.addAction(self.action_add_account)
        master_menu.addAction(self.action_add_item)
        master_menu.addSeparator()
        master_menu.addAction(self.action_view_accounts)
        master_menu.addAction(self.action_view_items)
        master_menu.addSeparator()
        master_menu.addAction(self.action_settings)

        # Voucher Menu
        voucher_menu = menu_bar.addMenu("&Voucher")
        voucher_menu.addAction(self.action_add_payment)
        voucher_menu.addAction(self.action_add_receipt)
        voucher_menu.addAction(self.action_add_journal)
        voucher_menu.addAction(self.action_add_sales)
        voucher_menu.addAction(self.action_add_purchase)
        voucher_menu.addSeparator()
        voucher_menu.addAction(self.action_view_vouchers)

        # Report Menu
        report_menu = menu_bar.addMenu("&Report")
        report_menu.addAction(self.action_daybook)
        report_menu.addAction(self.action_ledger)
        report_menu.addAction(self.action_trail_balance)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(self.action_about)

    # --------------------------------------------------------------------------
    # --- 4. Main Window Methods ---
    # --------------------------------------------------------------------------
    def _open_view_vouchers_dialog(self):
        """Displays a simple dialog for selecting a voucher type to view/modify."""
        dialog = QDialog(self)
        dialog.setWindowTitle("View/Modify Vouchers")
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        list_widget.addItems([
            "Payment (PAY)", "Receipt (REC)", "Journal (JNL)", 
            "Sales (SAL)", "Purchase (PUR)", "Credit Note (CN)", "Debit Note (DN)"
        ])
        layout.addWidget(list_widget)

        h_layout = QHBoxLayout()
        vouch_id_edit = QLineEdit()
        vouch_id_edit.setPlaceholderText("Enter Voucher ID to Modify (Optional)")
        view_button = QPushButton("View/Modify")
        
        h_layout.addWidget(vouch_id_edit)
        h_layout.addWidget(view_button)
        layout.addLayout(h_layout)

        view_button.clicked.connect(lambda: self._launch_voucher_view(list_widget, vouch_id_edit.text().strip(), dialog))
        dialog.exec()
        
    def _launch_voucher_view(self, list_widget: QListWidget, voucher_id_str: str, parent_dialog: QDialog):
        selected_items = list_widget.selectedItems()
        if not selected_items:
            show_message(parent_dialog, "Selection Error", "Please select a voucher type.", QMessageBox.Icon.Warning)
            return

        selected_text = selected_items[0].text()
        vouch_type_code = selected_text.split('(')[-1].replace(')', '').strip()
        
        voucher_id = None
        if voucher_id_str:
            try:
                voucher_id = int(voucher_id_str)
            except ValueError:
                show_message(parent_dialog, "Input Error", "Voucher ID must be a number.", QMessageBox.Icon.Warning)
                return

        # Close the selection dialog
        parent_dialog.accept() 
        
        # Open the entry dialog in view/modify mode
        dialog = VoucherEntryDialog(self.db_manager, vouch_type_code, self, voucher_id)
        dialog.exec()
        
    def _open_report_dialog(self):
        """Launches the appropriate report view based on the triggered action."""
        sender = self.sender()
        selected_text = sender.text().replace('&', '').strip()
        report_view = None
        
        if selected_text == "Ledger":
            report_view = LedgerReportView(self.db_manager, self)
        elif selected_text == "Day Book":
            report_view = DayBookReport(self.db_manager, self)
        elif selected_text in ["Trial Balance", "Profit & Loss Account", "Balance Sheet"]:
            report_view = PlaceholderReport(self.db_manager, selected_text, self)
            
        if report_view:
            report_view.exec()

        def PlaceholderReport(db_manager, selected_text, self):
            show_message(self, "placeholder", 
                        "yet to do this part of prg.", 
                        QMessageBox.Icon.Information)        

    def _show_about_dialog(self):
        show_message(self, "About", 
                     "Project Suite Accounting Utility\n\nDeveloped with Python and PySide6.", 
                     QMessageBox.Icon.Information)

class LauncherWindow(QDialog):
    """
    Simple initial dialog to select/create the SQLite database file path.
    This also handles the main application startup logic.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = None
        self.main_window = None
        
        self.setWindowTitle("Application Launcher")
        self.setGeometry(300, 300, 400, 150)
        
        main_layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        self.db_path_edit = QLineEdit("accounting.db")
        self.db_path_edit.setPlaceholderText("Enter database file path (e.g., accounting.db)")
        form_layout.addRow(QLabel("Database File:"), self.db_path_edit)
        main_layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._launch_app)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
    def _launch_app(self):
        db_path = self.db_path_edit.text().strip()
        if not db_path:
            show_message(self, "Error", "Please enter a database file path.", QMessageBox.Icon.Warning)
            return

        try:
            self.db_manager = DBManager(db_path) 
            
            self.main_window = MainWindow(self.db_manager, parent=self) 
            self.main_window.show()
            
            self.accept()
            
        except Exception as e:
            show_message(self, "Application Startup Error", 
                         f"Failed to start the main application: {e}", 
                         QMessageBox.Icon.Critical)
            self.db_manager = None
            self.main_window = None

# ==============================================================================
# --- EXECUTION BLOCK ----------------------------------------------
# ==============================================================================

# ==============================================================================
# --- EXECUTION BLOCK ----------------------------------------------
# ==============================================================================

if __name__ == "__main__":
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    except Exception as e:
        print(f"FATAL: Failed to create QApplication. Error: {e}")
        sys.exit(1)
        
    try:
        # Ensure the application quits when the last main window is closed
        app.setQuitOnLastWindowClosed(True) 
        
        # Set a default locale for consistent number formatting (e.g., DecimalLineEdit)
        locale = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        QLocale.setDefault(locale)
        
        # Launch the initial window to select the database file
        launcher_window = LauncherWindow()
        launcher_window.exec() 
        
        # If the launcher successfully opened the main window, start the event loop
        if launcher_window.main_window:
            sys.exit(app.exec())
        
    except Exception as e:
        print(f"FATAL: Application runtime error: {e}")
        sys.exit(1)
