from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QStackedWidget, QFrame, QMessageBox)

from ui.dialog.AddAccount import AddAccount
from ui.view.Dashboard import Dashboard
from ui.view.SpecificAccount import SpecificAccount

from core.account.AccountRepository import AccountRepository
from core.authentication.UserSession import UserSession

class MainApp(QWidget):
    def __init__(self, on_logout):
        super().__init__()
        self.on_logout = on_logout
        self.session = UserSession()
        self.repo = AccountRepository("WealthTrackersDB.sqlite")
        self.active_account_map = {}

        self.setup_ui()
        self.load_user_accounts()

    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QFrame(objectName="sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar_layout = QVBoxLayout(self.sidebar)

        logo = QLabel("WealthTrackers")
        logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin: 20px 10px;")
        self.sidebar_layout.addWidget(logo)

        self.dash_btn = QPushButton(" Dashboard", objectName="sidebarBtn")
        self.sidebar_layout.addWidget(self.dash_btn)

        self.sidebar_layout.addWidget(
            QLabel("ACCOUNTS", styleSheet="color: #8da9c4; font-size: 11px; font-weight: bold; margin: 20px 10px 5px 10px;"))

        # Layout for dynamic account buttons
        self.accounts_layout = QVBoxLayout()
        self.accounts_layout.setSpacing(2)
        self.sidebar_layout.addLayout(self.accounts_layout)

        self.add_acc_btn = QPushButton(" + Add Account", objectName="sidebarBtn")
        self.add_acc_btn.setStyleSheet("color: #8da9c4; font-weight: bold;")
        self.add_acc_btn.clicked.connect(self.trigger_add_account)
        self.sidebar_layout.addWidget(self.add_acc_btn)

        self.sidebar_layout.addStretch()

        # Bottom Actions
        self.delete_btn = QPushButton(" 🗑 Delete current account", objectName="sidebarBtn")
        self.delete_btn.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        self.delete_btn.clicked.connect(self.trigger_delete_account)
        self.sidebar_layout.addWidget(self.delete_btn)

        self.logout_btn = QPushButton(" 🚪 Logout", objectName="sidebarBtn")
        self.logout_btn.clicked.connect(self.on_logout)
        self.sidebar_layout.addWidget(self.logout_btn)

        # --- Content Stack ---
        self.content_stack = QStackedWidget()
        self.dashboard_page = Dashboard()
        self.content_stack.addWidget(self.dashboard_page)
        self.dash_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))

        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.content_stack, stretch=1)

    def load_user_accounts(self):
        if not self.session.active_user_id: return
        accounts = self.repo.fetch_all_accounts(self.session.active_user_id)

        for acc in accounts:
            try:
                dec = acc.get_decrypted_number(self.session.get_key())
                display = f"  {acc.name} (...{dec[-4:]})"
            except:
                display = f"  {acc.name}"

            btn = QPushButton(display, objectName="sidebarBtn")
            self.accounts_layout.addWidget(btn)

            page = SpecificAccount(acc)
            self.content_stack.addWidget(page)
            idx = self.content_stack.count() - 1
            self.active_account_map[idx] = acc.id

            btn.clicked.connect(lambda _, i=idx: self.content_stack.setCurrentIndex(i))

    def trigger_add_account(self):
        dialog = AddAccount(self)
        if dialog.exec():
            if dialog.new_account and self.session.active_user_id:
                self.repo.save_new_account(self.session.active_user_id, dialog.new_account)
                self.refresh_ui()

    def refresh_ui(self):
        while self.accounts_layout.count():
            item = self.accounts_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        while self.content_stack.count() > 1:
            w = self.content_stack.widget(1)
            self.content_stack.removeWidget(w)
            w.deleteLater()

        self.active_account_map = {}
        self.load_user_accounts()
        self.dashboard_page.refresh_data()

    def trigger_delete_account(self):
        idx = self.content_stack.currentIndex()
        if idx == 0: return

        acc_id = self.active_account_map.get(idx)
        if QMessageBox.warning(self, 'Confirm', "Delete this account?",
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.repo.delete_financial_account(acc_id):
                self.refresh_ui()
                self.content_stack.setCurrentIndex(0)