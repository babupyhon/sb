import sqlite3
from typing import List, Dict, Tuple, Optional

class DBManager:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        # Same CREATE TABLE statements you already have
        # Ensure these exist: account_master, item_master, voucher_master, transactions
        pass  # keep your existing code

    # --- Master CRUD ---
    def add_master_entry(self, master_type: str, data: dict) -> int | None:
        if master_type == 'account':
            sql = "INSERT INTO account_master (master_name, group_type) VALUES (?, ?)"
            args = (data['name'], data['group_or_hsn'])
        elif master_type == 'item':
            sql = "INSERT INTO item_master (item_name, hsn_code) VALUES (?, ?)"
            args = (data['name'], data['group_or_hsn'])
        else:
            raise ValueError("Invalid master type")
        try:
            self.cursor.execute(sql, args)
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            raise ValueError(f"{master_type.capitalize()} '{data['name']}' already exists.") from e

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
        return [{'id': r['id'], 'name': r[name_col], 'group_or_hsn': r[extra_col]} for r in self.cursor.fetchall()]

    def get_account_names(self) -> List[str]:
        self.cursor.execute("SELECT master_name FROM account_master ORDER BY master_name")
        return [r['master_name'] for r in self.cursor.fetchall()]

    def get_item_names(self) -> List[str]:
        self.cursor.execute("SELECT item_name FROM item_master ORDER BY item_name")
        return [r['item_name'] for r in self.cursor.fetchall()]

    def get_id_by_name(self, name: str, master_type: str) -> Optional[int]:
        table = "account_master" if master_type == "account" else "item_master"
        column = "master_name" if master_type == "account" else "item_name"
        self.cursor.execute(f"SELECT id FROM {table} WHERE {column}=?", (name,))
        row = self.cursor.fetchone()
        return row['id'] if row else None

    def get_account_group_names(self) -> List[str]:
        self.cursor.execute("SELECT DISTINCT group_type FROM account_master ORDER BY group_type")
        return [row['group_type'] for row in self.cursor.fetchall()]

    # --- Voucher Handling (account vouchers only for now) ---
    def add_account_voucher(self, vouch_type_code: str, header_data: dict, line_data: list) -> int:
        try:
            self.cursor.execute("""
                INSERT INTO voucher_master (voucher_type, date, narration, reference_no)
                VALUES (?, ?, ?, ?)
            """, (vouch_type_code, header_data['vouch_date'], header_data.get('narrative', ''), header_data.get('ref_no', '')))
            voucher_id = self.cursor.lastrowid

            # If no line_data provided, create a single line against a generic account (optional)
            for line in line_data:
                self.cursor.execute("""
                    INSERT INTO transactions (voucher_id, account_id, is_debit, amount)
                    VALUES (?, ?, ?, ?)
                """, (voucher_id, line['account_id'], int(line['is_debit']), float(line['amount'])))

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

    # --- Reports ---
    def get_ledger_data(self, date_from: str, date_to: str, account_name: str) -> List[Tuple]:
        account_id = self.get_id_by_name(account_name, 'account')
        if not account_id:
            return []
        self.cursor.execute("""
            SELECT v.date AS date, v.voucher_type AS type, t.amount AS amount,
                   CASE WHEN t.is_debit=1 THEN 'Dr' ELSE 'Cr' END AS drcr,
                   v.id AS vouch_no
            FROM voucher_master v
            JOIN transactions t ON v.id = t.voucher_id
            WHERE v.date BETWEEN ? AND ? AND t.account_id = ?
            ORDER BY v.date, v.id
        """, (date_from, date_to, account_id))
        rows = self.cursor.fetchall()
        return [(r['date'], r['vouch_no'], r['type'], r['drcr'], r['amount']) for r in rows]

    def get_day_book_data(self, date: str) -> List[Tuple]:
        self.cursor.execute("""
            SELECT v.date, v.id AS voucher_no, v.voucher_type,
                   SUM(CASE WHEN t.is_debit=1 THEN t.amount ELSE 0 END) AS dr_sum,
                   v.narration
            FROM voucher_master v
            LEFT JOIN transactions t ON v.id = t.voucher_id
            WHERE v.date = ?
            GROUP BY v.id
            ORDER BY v.id
        """, (date,))
        rows = self.cursor.fetchall()
        return [(r['date'], r['voucher_no'], r['voucher_type'], r['dr_sum'], r['narration'] or '') for r in rows]

    def get_stock_register_data(self, date_from: str, date_to: str) -> List[Tuple]:
        # Placeholder — return an empty list or synthesize demo rows
        # If you later add item transactions, adapt this to your item tables.
        return []  # [(date, item_name, hsn, qty, rate, amount), ...]

    def get_subsidiary_book_data(self, date_from: str, date_to: str, group_type: str) -> List[Tuple]:
        self.cursor.execute("""
            SELECT v.date, v.id AS voucher_no, v.voucher_type,
                   a.master_name, a.group_type,
                   SUM(CASE WHEN t.is_debit=1 THEN t.amount ELSE -t.amount END) AS net_amount
            FROM voucher_master v
            JOIN transactions t ON v.id = t.voucher_id
            JOIN account_master a ON t.account_id = a.id
            WHERE v.date BETWEEN ? AND ? AND a.group_type = ?
            GROUP BY v.id, a.id
            ORDER BY v.date, v.id
        """, (date_from, date_to, group_type))
        rows = self.cursor.fetchall()
        return [(r['date'], r['voucher_no'], r['voucher_type'], r['master_name'], r['group_type'], r['net_amount']) for r in rows]

    def get_trial_balance_rows(self) -> List[Tuple[str, float, float]]:
        # Sum across all accounts: total Dr and Cr per account
        self.cursor.execute("""
            SELECT a.master_name,
                   SUM(CASE WHEN t.is_debit=1 THEN t.amount ELSE 0 END) AS dr_total,
                   SUM(CASE WHEN t.is_debit=0 THEN t.amount ELSE 0 END) AS cr_total
            FROM account_master a
            LEFT JOIN transactions t ON a.id = t.account_id
            GROUP BY a.id
            ORDER BY a.master_name
        """)
        rows = self.cursor.fetchall()
        return [(r['master_name'], float(r['dr_total'] or 0.0), float(r['cr_total'] or 0.0)) for r in rows]
