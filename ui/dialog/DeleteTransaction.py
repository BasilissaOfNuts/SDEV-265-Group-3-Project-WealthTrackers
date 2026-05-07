import sqlite3

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QMessageBox,
                             QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView)
from PyQt6.QtCore import Qt

from core.transaction.TransactionRepository import TransactionRepository


class DeleteTransaction(QDialog):
    def __init__(self, account_id, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.repo = TransactionRepository("WealthTrackersDB.sqlite")
        self.all_transactions = []
        self.transactions_deleted = False

        self.setWindowTitle("Delete Transaction")
        self.setFixedSize(550, 650)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(
            QLabel("Manage & Delete Transactions", objectName="header", alignment=Qt.AlignmentFlag.AlignCenter))

        # Filter & Sort Row
        ctrl_layout = QHBoxLayout()

        self.filter_type = QComboBox()
        self.filter_type.addItems(["Vendor", "Category"])
        self.filter_type.currentIndexChanged.connect(self.render_table)
        ctrl_layout.addWidget(self.filter_type)

        self.search_box = QLineEdit(placeholderText="Search text...")
        self.search_box.textChanged.connect(self.render_table)
        ctrl_layout.addWidget(self.search_box)

        self.sort_box = QComboBox()
        self.sort_box.addItems(["Date Asc (↑)", "Date Desc (↓)", "Amount Asc (↑)", "Amount Desc (↓)"])
        self.sort_box.currentIndexChanged.connect(self.render_table)
        ctrl_layout.addWidget(self.sort_box)

        layout.addLayout(ctrl_layout)

        # Table for Results
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Transaction Details", "Amount"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

        del_btn = QPushButton("Delete Selected Transaction(s)", objectName="redButton")
        del_btn.clicked.connect(self.handle_delete)
        layout.addWidget(del_btn)

    def load_data(self):
        self.all_transactions = self.repo.fetch_transactions(self.account_id)
        self.render_table()

    def render_table(self):
        # 1. Apply Filter
        f_type = self.filter_type.currentText()
        s_text = self.search_box.text().lower()

        filtered = []
        for tx in self.all_transactions:
            target = tx.vendor_name.lower() if f_type == "Vendor" else tx.category_name.lower()
            if s_text in target:
                filtered.append(tx)

        # 2. Apply Sort
        sort_val = self.sort_box.currentText()
        if sort_val == "Date Asc (↑)":
            filtered.sort(key=lambda t: (t.date, t.amount))
        elif sort_val == "Date Desc (↓)":
            filtered.sort(key=lambda t: (t.date, t.amount), reverse=True)
        elif sort_val == "Amount Asc (↑)":
            filtered.sort(key=lambda t: (t.amount, t.date))
        elif sort_val == "Amount Desc (↓)":
            filtered.sort(key=lambda t: (t.amount, t.date), reverse=True)

        # 3. Populate Table
        self.table.setRowCount(0)

        for tx in filtered:
            row = self.table.rowCount()
            self.table.insertRow(row)

            date_str = tx.date.strftime("%Y-%m-%d")
            details = f"{date_str}  |  {tx.vendor_name}  ({tx.category_name})"

            item_details = QTableWidgetItem(details)
            item_details.setData(Qt.ItemDataRole.UserRole, str(tx.id))
            item_details.setForeground(Qt.GlobalColor.black)  # Double safety for text color

            sign = "-" if tx.type in ("EXPENSE", "TRANSFER_OUT") else "+"
            item_amt = QTableWidgetItem(f"{sign}${tx.amount:,.2f}")
            item_amt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_amt.setForeground(Qt.GlobalColor.black)

            self.table.setItem(row, 0, item_details)
            self.table.setItem(row, 1, item_amt)

    def handle_delete(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select at least one transaction to delete.")
            return

        selected_rows = set(item.row() for item in selected_items)
        tx_ids = [self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) for row in selected_rows]

        confirm = QMessageBox.question(self, "Confirm Deletion",
                                       f"Are you sure you want to permanently delete these transaction(s)?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            for tx_id in tx_ids:
                self.repo.delete_transaction(tx_id)

            self.transactions_deleted = True
            self.load_data()