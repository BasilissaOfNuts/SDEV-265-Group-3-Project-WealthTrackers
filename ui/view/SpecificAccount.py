from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QListWidget, QFrame, QPushButton)
from PyQt6.QtCore import Qt

from core.account.Account import Account
from core.account.AccountRepository import AccountRepository
from core.transaction.TransactionRepository import TransactionRepository
from core.authentication.UserSession import UserSession
from core.utils.Signal import global_signal

from ui.dialog.AddTransaction import AddTransaction
from ui.dialog.DeleteTransaction import DeleteTransaction
from ui.component.AnalyticsPanel import AnalyticsPanel

class SpecificAccount(QWidget):
    def __init__(self, account: Account):
        super().__init__()
        self.account = account
        self.repo = TransactionRepository("WealthTrackersDB.sqlite")
        self.acc_repo = AccountRepository("WealthTrackersDB.sqlite")
        self.session = UserSession()

        self.setup_ui()
        self.refresh_data()

        # Respond to global updates
        global_signal.refresh_requested.connect(self.refresh_data)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- Middle Column: Analytics ---
        middle_layout = QVBoxLayout()
        middle_card = QFrame(objectName="card")
        m_card_layout = QVBoxLayout(middle_card)

        m_card_layout.addWidget(QLabel(f"{self.account.name} Overview", objectName="header"))

        # Injecting the reusable Analytics Panel (Specific Account)
        self.analytics_panel = AnalyticsPanel(account_id=self.account.id)
        m_card_layout.addWidget(self.analytics_panel, stretch=1)

        middle_layout.addWidget(middle_card)

        # --- Right Column: Balance & Activity ---
        right_layout = QVBoxLayout()

        balance_card = QFrame(objectName="card")
        b_layout = QVBoxLayout(balance_card)
        b_layout.addWidget(QLabel("Current Balance", objectName="header"))

        self.balance_label = QLabel("$0.00")
        self.balance_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #004879;")
        b_layout.addWidget(self.balance_label)

        right_layout.addWidget(balance_card)

        # Recent Activity List
        activity_card = QFrame(objectName="card")
        act_layout = QVBoxLayout(activity_card)
        act_layout.addWidget(QLabel("Recent Activity", objectName="header"))

        self.tx_list = QListWidget()
        act_layout.addWidget(self.tx_list)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Transaction", objectName="actionButton")
        add_btn.clicked.connect(self.trigger_add_transaction)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("Delete Transaction", objectName="redButton")
        del_btn.clicked.connect(self.trigger_delete_transaction)
        btn_layout.addWidget(del_btn)

        act_layout.addLayout(btn_layout)

        right_layout.addWidget(activity_card, stretch=1)

        layout.addLayout(middle_layout, stretch=2)
        layout.addLayout(right_layout, stretch=1)

    def trigger_add_transaction(self):
        """Opens the dialog and EMITS the signal if a transaction is saved."""
        dialog = AddTransaction(self.account.id, self)

        if dialog.exec():
            new_txn = dialog.new_txn
            if new_txn:
                self.repo.save_transaction(new_txn)
                # SEND SIGNAL: Tell the Dashboard and Sidebar to update too
                global_signal.refresh_requested.emit()

    def trigger_delete_transaction(self):
        """Opens the delete dialog and EMITS the signal if a transaction is deleted."""
        dialog = DeleteTransaction(self.account.id, self)
        dialog.exec()

        if dialog.transactions_deleted:
            global_signal.refresh_requested.emit()

    def refresh_data(self):
        """Refreshes transactions and re-calculates balance from the DB."""
        # GUARD: Prevent crash if session isn't fully initialized during login
        user_id = self.session.active_user_id
        if not user_id:
            return

        self.tx_list.clear()

        # 1. Update List
        transactions = self.repo.fetch_transactions(self.account.id)

        if not transactions:
            self.tx_list.addItem("No recent transactions found.")
        else:
            for tx in transactions:
                # Use robust sign check for all types
                sign = "-" if tx.type in ("EXPENSE", "TRANSFER_OUT") else "+"
                date_str = tx.date.strftime("%b %d")
                self.tx_list.addItem(f"{date_str}   {tx.vendor_name}   {sign}${tx.amount:,.2f}")

        # 2. Update Balance (Re-fetch the account to get the latest calculated balance)
        all_accounts = self.acc_repo.fetch_all_accounts(user_id)

        for acc in all_accounts:
            if acc.id == self.account.id:
                self.account = acc
                break

        self.balance_label.setText(f"${self.account.balance:,.2f}")

        # Trigger chart reload
        self.analytics_panel.refresh_chart()