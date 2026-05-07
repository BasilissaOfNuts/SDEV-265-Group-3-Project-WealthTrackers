import uuid
import sqlite3

from decimal import Decimal
from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QComboBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate

from core.transaction.Transaction import Transaction

from ui.dialog.AddVendor import AddVendor
from ui.dialog.EditVendor import EditVendor

class AddTransaction(QDialog):
    def __init__(self, account_id, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.new_txn = None
        self.selected_category_id = None
        self.selected_vendor_id = None
        self.selected_vendor_name = ""

        self.all_categories = []
        self.all_vendors = []

        self.setWindowTitle("Record Transaction")
        self.setFixedSize(450, 800)
        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Add Transaction", objectName="header", alignment=Qt.AlignmentFlag.AlignCenter))

        # Date
        layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.dateChanged.connect(self.update_status)
        layout.addWidget(self.date_input)

        # Amount
        layout.addWidget(QLabel("Amount:"))
        self.amount_input = QLineEdit(placeholderText="0.00")
        layout.addWidget(self.amount_input)

        # Type
        layout.addWidget(QLabel("Transaction Type:"))
        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems(["EXPENSE", "INCOME", "TRANSFER_OUT", "TRANSFER_IN"])
        layout.addWidget(self.type_dropdown)

        # Vendor Selection
        layout.addWidget(QLabel("Search Vendor:"))
        vendor_row = QHBoxLayout()
        self.vendor_search = QLineEdit(placeholderText="Type to find vendor...")
        self.vendor_search.textChanged.connect(self.filter_vendors)
        vendor_row.addWidget(self.vendor_search)

        self.add_vendor_btn = QPushButton("+", objectName="actionButton")
        self.add_vendor_btn.clicked.connect(self.open_add_vendor)
        vendor_row.addWidget(self.add_vendor_btn)

        self.edit_vendor_btn = QPushButton("...", objectName="actionButton")
        self.edit_vendor_btn.clicked.connect(self.open_edit_vendor)
        vendor_row.addWidget(self.edit_vendor_btn)
        layout.addLayout(vendor_row)

        self.vendor_list = QListWidget()
        self.vendor_list.setFixedHeight(120)
        self.vendor_list.itemClicked.connect(self.handle_vendor_selection)
        layout.addWidget(self.vendor_list)

        # Category Selection
        layout.addWidget(QLabel("Search Category (or enter new and add with +):"))
        cat_search_row = QHBoxLayout()
        self.cat_search = QLineEdit(placeholderText="Type to find category...")
        self.cat_search.textChanged.connect(self.filter_categories)
        cat_search_row.addWidget(self.cat_search)

        self.add_cat_btn = QPushButton("+", objectName="actionButton")
        self.add_cat_btn.clicked.connect(self.handle_add_new_category)
        cat_search_row.addWidget(self.add_cat_btn)
        layout.addLayout(cat_search_row)

        self.cat_list = QListWidget()
        self.cat_list.setFixedHeight(120)
        self.cat_list.itemClicked.connect(self.handle_category_selection)
        layout.addWidget(self.cat_list)

        self.status_label = QLabel("Date: None | Vendor: None | Category: None",
                                   styleSheet="color: #004879; font-weight: bold;")
        layout.addWidget(self.status_label)
        self.update_status()

        save_btn = QPushButton("Save Transaction", objectName="redButton")
        save_btn.clicked.connect(self.handle_save)
        layout.addWidget(save_btn)

    def load_initial_data(self):
        conn = sqlite3.connect("WealthTrackersDB.sqlite")
        self.all_vendors = conn.execute(
            "SELECT vendor_id, vendor_name, default_category_id FROM vendors ORDER BY vendor_name").fetchall()
        self.all_categories = conn.execute(
            "SELECT category_id, category_name FROM categories ORDER BY category_name").fetchall()
        conn.close()

        self.filter_vendors("")
        self.filter_categories("")

    def filter_vendors(self, text):
        self.vendor_list.clear()
        matches = [v for v in self.all_vendors if text.lower() in v[1].lower()]

        for v_id, v_name, def_cat in matches:
            item = QListWidgetItem(v_name)
            item.setData(Qt.ItemDataRole.UserRole, (v_id, def_cat))
            self.vendor_list.addItem(item)

    def handle_vendor_selection(self, item):
        v_id, def_cat_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_vendor_id = v_id
        self.selected_vendor_name = item.text()
        self.vendor_search.setText(item.text())
        self.apply_category_id(def_cat_id)
        self.update_status()

    def filter_categories(self, text):
        self.cat_list.clear()
        matches = [c for c in self.all_categories if text.lower() in c[1].lower()]

        for c_id, c_name in matches:
            item = QListWidgetItem(c_name)
            item.setData(Qt.ItemDataRole.UserRole, c_id)
            self.cat_list.addItem(item)

    def handle_category_selection(self, item):
        self.selected_category_id = item.data(Qt.ItemDataRole.UserRole)
        self.cat_search.setText(item.text())
        self.update_status()

    def apply_category_id(self, cat_id):
        self.selected_category_id = cat_id

        for c_id, c_name in self.all_categories:
            if c_id == cat_id:
                self.cat_search.setText(c_name)
                break

    def handle_add_new_category(self):
        name = self.cat_search.text().strip()
        if not name: return

        try:
            conn = sqlite3.connect("WealthTrackersDB.sqlite")
            conn.execute("INSERT INTO categories (category_name) VALUES (?)", (name,))
            conn.commit()
            conn.close()

            self.load_initial_data()
            self.filter_categories(name)
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Category already exists.")

    def update_status(self):
        v_name = self.selected_vendor_name if self.selected_vendor_name else "None"
        c_name = "None"
        date_str = self.date_input.date().toString("MMM dd, yyyy")

        for c_id, name in self.all_categories:
            if c_id == self.selected_category_id:
                c_name = name
                break

        self.status_label.setText(f"Date: {date_str} | Vendor: {v_name} | Category: {c_name}")

    def open_add_vendor(self):
        if AddVendor(self).exec():
            self.load_initial_data()

    def open_edit_vendor(self):
        if not self.selected_vendor_id:
            QMessageBox.warning(self, "Selection Required", "Please select a vendor to edit.")
            return
        if EditVendor(self.selected_vendor_id, self).exec():
            self.load_initial_data()

    def handle_save(self):
        try:
            raw_amt = self.amount_input.text().strip()
            if not raw_amt: raise ValueError("Amount required")

            amt = Decimal(raw_amt)
            if not self.selected_vendor_id: raise ValueError("Select a vendor")
            if not self.selected_category_id: raise ValueError("Select a category")

            q_date = self.date_input.date()
            py_date = datetime(q_date.year(), q_date.month(), q_date.day())

            self.new_txn = Transaction(
                uuid.uuid4(),
                self.account_id,
                self.selected_vendor_id,
                self.selected_vendor_name,
                self.selected_category_id,
                "",
                amt,
                py_date,
                self.type_dropdown.currentText()
            )

            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))