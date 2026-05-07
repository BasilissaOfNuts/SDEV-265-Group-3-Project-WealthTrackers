from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class TransactionList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # The QSS styling from styles.py will apply to this automatically

    def update_with_data(self, transactions):
        """Standardized way to refresh transaction items across all views."""
        self.clear()

        if not transactions:
            item = QListWidgetItem("No recent activity found.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.addItem(item)
            return

        for tx in transactions:
            # Determine sign and display
            sign = "+" if tx.type in ("INCOME", "TRANSFER_IN") else "-"
            date_str = tx.date.strftime("%b %d")

            display_text = f"{date_str:<8} {tx.vendor_name:<15} {sign}${tx.amount:,.2f}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, str(tx.id))
            self.addItem(item)