from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel

class Analytics(QDialog):
    def __init__(self, parent=None, account_name="All Accounts"):
        super().__init__(parent)

        self.setWindowTitle(f"Detailed Analytics - {account_name}")
        self.setFixedSize(600, 400)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Category Breakdown for: {account_name}", objectName="header"))
        layout.addWidget(QLabel("Detailed pie charts/bar graphs regarding category spending go here."))

        self.setLayout(layout)