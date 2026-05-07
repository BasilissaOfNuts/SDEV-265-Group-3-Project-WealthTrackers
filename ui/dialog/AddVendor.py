import sqlite3

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt

class AddVendor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Vendor")
        self.setFixedSize(400, 500)
        self.selected_category_id = None
        self.all_categories = []
        self.setup_ui()
        self.load_categories()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Register New Vendor", objectName="header", alignment=Qt.AlignmentFlag.AlignCenter))

        self.name_input = QLineEdit(placeholderText="Vendor Name (e.g., Starbucks)")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Select Default Category:"))
        self.cat_search = QLineEdit(placeholderText="Search categories...")
        self.cat_search.textChanged.connect(self.filter_categories)
        layout.addWidget(self.cat_search)

        self.cat_list = QListWidget()
        self.cat_list.itemClicked.connect(self.handle_selection)
        layout.addWidget(self.cat_list)

        self.selection_label = QLabel("Selected: None")
        layout.addWidget(self.selection_label)

        save_btn = QPushButton("Add Vendor", objectName="redButton")
        save_btn.clicked.connect(self.handle_save)
        layout.addWidget(save_btn)

    def load_categories(self):
        conn = sqlite3.connect("WealthTrackersDB.sqlite")
        self.all_categories = conn.execute("SELECT category_id, category_name FROM categories ORDER BY category_name").fetchall()

        conn.close()
        self.filter_categories("")

    def filter_categories(self, text):
        self.cat_list.clear()

        for c_id, c_name in self.all_categories:
            if text.lower() in c_name.lower():
                item = QListWidgetItem(c_name)
                item.setData(Qt.ItemDataRole.UserRole, c_id)
                self.cat_list.addItem(item)

    def handle_selection(self, item):
        self.selected_category_id = item.data(Qt.ItemDataRole.UserRole)
        self.selection_label.setText(f"Selected: {item.text()}")

    def handle_save(self):
        name = self.name_input.text().strip()

        if not name or not self.selected_category_id:
            QMessageBox.warning(self, "Error", "Input name and select a category.")
            return
        try:
            conn = sqlite3.connect("WealthTrackersDB.sqlite")
            conn.execute("INSERT INTO vendors (vendor_name, default_category_id) VALUES (?, ?)", (name, self.selected_category_id))
            
            conn.commit()
            conn.close()
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Vendor already exists.")