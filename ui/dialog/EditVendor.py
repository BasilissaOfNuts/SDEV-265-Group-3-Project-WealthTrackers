import sqlite3

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt

class EditVendor(QDialog):
    def __init__(self, vendor_id=None, parent=None):
        super().__init__(parent)
        self.active_vendor_id = vendor_id
        self.selected_category_id = None
        self.setWindowTitle("Manage Vendors")
        self.setFixedSize(450, 650)
        self.setup_ui()
        self.refresh_all_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Vendor Search/Select
        layout.addWidget(QLabel("Search Vendor to Edit:", objectName="header"))
        self.vendor_search = QLineEdit(placeholderText="Type vendor name...")
        self.vendor_search.textChanged.connect(self.filter_vendors)
        layout.addWidget(self.vendor_search)

        self.vendor_list = QListWidget()
        self.vendor_list.itemClicked.connect(self.handle_vendor_selection)
        layout.addWidget(self.vendor_list, stretch=1)

        layout.addWidget(QLabel("Change Category Selection:"))
        self.cat_search = QLineEdit(placeholderText="Filter categories...")
        self.cat_search.textChanged.connect(self.filter_categories)
        layout.addWidget(self.cat_search)

        self.cat_list = QListWidget()
        self.cat_list.itemClicked.connect(self.handle_cat_selection)
        layout.addWidget(self.cat_list, stretch=1)

        self.status_label = QLabel("Editing: None | Category: None")
        layout.addWidget(self.status_label)

        save_btn = QPushButton("Update Vendor Info", objectName="redButton")
        save_btn.clicked.connect(self.handle_save)
        layout.addWidget(save_btn)

    def refresh_all_data(self):
        conn = sqlite3.connect("WealthTrackersDB.sqlite")
        self.all_vendors = conn.execute("SELECT vendor_id, vendor_name, default_category_id FROM vendors").fetchall()
        self.all_categories = conn.execute("SELECT category_id, category_name FROM categories").fetchall()

        conn.close()
        self.filter_vendors("")
        self.filter_categories("")

    def filter_vendors(self, text):
        self.vendor_list.clear()

        for v_id, v_name, _ in self.all_vendors:
            if text.lower() in v_name.lower():
                item = QListWidgetItem(v_name)
                item.setData(Qt.ItemDataRole.UserRole, v_id)
                self.vendor_list.addItem(item)

    def filter_categories(self, text):
        self.cat_list.clear()

        for c_id, c_name in self.all_categories:
            if text.lower() in c_name.lower():
                item = QListWidgetItem(c_name)
                item.setData(Qt.ItemDataRole.UserRole, c_id)
                self.cat_list.addItem(item)

    def handle_vendor_selection(self, item):
        self.active_vendor_id = item.data(Qt.ItemDataRole.UserRole)
        # Find current category
        for v_id, v_name, c_id in self.all_vendors:
            if v_id == self.active_vendor_id:
                self.selected_category_id = c_id
                self.status_label.setText(f"Editing: {v_name}")
                self.highlight_category(c_id)
                break

    def highlight_category(self, c_id):
        for i in range(self.cat_list.count()):
            item = self.cat_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == c_id:
                self.cat_list.setCurrentItem(item)
                break

    def handle_cat_selection(self, item):
        self.selected_category_id = item.data(Qt.ItemDataRole.UserRole)

    def handle_save(self):
        if not self.active_vendor_id or not self.selected_category_id: return

        conn = sqlite3.connect("WealthTrackersDB.sqlite")
        conn.execute("UPDATE vendors SET default_category_id = ? WHERE vendor_id = ?",
                     (self.selected_category_id, self.active_vendor_id))
        
        conn.commit()
        conn.close()
        self.accept()