from decimal import Decimal
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel)

from ui.component.TransactionList import TransactionList
from ui.component.AnalyticsPanel import AnalyticsPanel

from core.transaction.TransactionRepository import TransactionRepository
from core.account.AccountRepository import AccountRepository
from core.account.CheckingAccount import CheckingAccount
from core.account.CreditCardAccount import CreditCardAccount
from core.account.DebitCardAccount import DebitCardAccount
from core.authentication.UserSession import UserSession
from core.utils.Signal import global_signal

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
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
        card_layout = QVBoxLayout(middle_card)

        card_layout.addWidget(QLabel("Analytics Overview", objectName="header"))

        # Injecting the reusable Analytics Panel (Global)
        self.analytics_panel = AnalyticsPanel()
        card_layout.addWidget(self.analytics_panel, stretch=1)

        middle_layout.addWidget(middle_card)

        # --- Right Column: Totals & Activity ---
        right_layout = QVBoxLayout()

        # Totals Card
        totals_card = QFrame(objectName="card")
        t_layout = QVBoxLayout(totals_card)
        t_layout.addWidget(QLabel("Global Totals", objectName="header"))

        self.global_balance_label = QLabel("Global Balance: $0.00")
        self.global_balance_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #004879; margin-bottom: 5px;")
        t_layout.addWidget(self.global_balance_label)

        self.total_spending_label = QLabel("Total Spending: $0.00")
        self.total_income_label = QLabel("Total Money In: $0.00")
        t_layout.addWidget(self.total_spending_label)
        t_layout.addWidget(self.total_income_label)

        # Recent Activity Card
        recent_card = QFrame(objectName="card")
        r_layout = QVBoxLayout(recent_card)
        r_layout.addWidget(QLabel("Recent Activity (Global)", objectName="header"))

        # Using the reusable component
        self.tx_list = TransactionList()
        r_layout.addWidget(self.tx_list)

        right_layout.addWidget(totals_card)
        right_layout.addWidget(recent_card, stretch=1)

        layout.addLayout(middle_layout, stretch=2)
        layout.addLayout(right_layout, stretch=1)

    def refresh_data(self):
        """Calculates global totals and refreshes the transaction component."""
        # GUARD: Avoid login crashes
        user_id = self.session.active_user_id
        if not user_id:
            return

        transactions = self.repo.fetch_user_transactions(user_id)

        total_spent = Decimal("0.00")
        total_income = Decimal("0.00")

        for tx in transactions:
            if tx.type in ("EXPENSE", "TRANSFER_OUT"):
                total_spent += tx.amount
            elif tx.type in ("INCOME", "TRANSFER_IN"):
                total_income += tx.amount

        # Calculate Global Balance (Net Worth)
        all_accounts = self.acc_repo.fetch_all_accounts(user_id)
        global_balance = Decimal("0.00")

        # Track checking IDs to prevent double-counting via Debit Cards
        counted_checking_ids = set()

        for acc in all_accounts:
            if isinstance(acc, CreditCardAccount):
                # CC Balance is debt, so we subtract it
                global_balance -= acc.balance
            elif isinstance(acc, DebitCardAccount):
                # Only count debit balance if its parent checking hasn't been added
                if acc.linked_checking_id not in counted_checking_ids:
                    global_balance += acc.balance
                    counted_checking_ids.add(acc.linked_checking_id)
            else:
                global_balance += acc.balance
                if isinstance(acc, CheckingAccount):
                    counted_checking_ids.add(acc.id)

        # Update labels
        self.total_spending_label.setText(f"Total Spending: ${total_spent:,.2f}")
        self.total_income_label.setText(f"Total Money In: ${total_income:,.2f}")
        self.global_balance_label.setText(f"Global Balance: ${global_balance:,.2f}")

        # Dynamic coloring for the global balance
        if global_balance < 0:
            self.global_balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #D22E1E;")
        else:
            self.global_balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #004879;")

        # Refresh the reusable transaction list component
        self.tx_list.update_with_data(transactions)

        # Trigger chart reload
        self.analytics_panel.refresh_chart()