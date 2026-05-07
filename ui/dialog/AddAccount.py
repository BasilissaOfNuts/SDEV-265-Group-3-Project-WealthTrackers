import uuid

from decimal import Decimal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QMessageBox, QStackedWidget, QWidget)
from PyQt6.QtCore import Qt

from core.authentication.AuthenticationService import AuthenticationService
from core.authentication.UserSession import UserSession
from core.account.CheckingAccount import CheckingAccount
from core.account.SavingsAccount import SavingsAccount
from core.account.CreditCardAccount import CreditCardAccount
from core.account.DebitCardAccount import DebitCardAccount

class AddAccount(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Financial Account")
        self.setFixedSize(450, 400)
        self.session = UserSession()
        self.new_account = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        header = QLabel("Create New Account")
        header.setObjectName("header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        self.name_input = QLineEdit(placeholderText="Account Nickname (e.g., Primary Checking)")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Account Type:"))
        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems(["Checking", "Savings", "Credit Card", "Debit Card"])
        self.type_dropdown.setStyleSheet("color: #333333; background-color: white;")
        self.type_dropdown.currentIndexChanged.connect(self.switch_dynamic_fields)
        layout.addWidget(self.type_dropdown)

        self.acc_num_input = QLineEdit(placeholderText="Account Number")
        layout.addWidget(self.acc_num_input)

        self.dynamic_stack = QStackedWidget()

        # 0: Checking
        chk_w = QWidget(); chk_l = QVBoxLayout(chk_w); chk_l.setContentsMargins(0,0,0,0)
        self.routing_input = QLineEdit(placeholderText="Routing Number")
        chk_l.addWidget(self.routing_input); self.dynamic_stack.addWidget(chk_w)

        # 1: Savings
        sav_w = QWidget(); sav_l = QVBoxLayout(sav_w); sav_l.setContentsMargins(0,0,0,0)
        self.interest_input = QLineEdit(placeholderText="Interest Rate (e.g., 0.04)")
        sav_l.addWidget(self.interest_input); self.dynamic_stack.addWidget(sav_w)

        # 2: Credit Card
        cc_w = QWidget(); cc_l = QVBoxLayout(cc_w); cc_l.setContentsMargins(0,0,0,0)
        self.cc_cvv = QLineEdit(placeholderText="CVV"); self.cc_limit = QLineEdit(placeholderText="Credit Limit")
        self.cc_apr = QLineEdit(placeholderText="APR (e.g., 0.24)")
        cc_l.addWidget(self.cc_cvv); cc_l.addWidget(self.cc_limit); cc_l.addWidget(self.cc_apr)
        self.dynamic_stack.addWidget(cc_w)

        # 3: Debit Card
        dc_w = QWidget(); dc_l = QVBoxLayout(dc_w); dc_l.setContentsMargins(0,0,0,0)
        self.dc_cvv = QLineEdit(placeholderText="CVV"); self.dc_linked_id = QLineEdit(placeholderText="Linked Checking UUID")
        dc_l.addWidget(self.dc_cvv); dc_l.addWidget(self.dc_linked_id); self.dynamic_stack.addWidget(dc_w)

        layout.addWidget(self.dynamic_stack)

        self.balance_input = QLineEdit(placeholderText="Initial Balance (e.g., 1500.00)")
        layout.addWidget(self.balance_input)

        layout.addStretch()
        submit_btn = QPushButton("Save Account", objectName="redButton")
        submit_btn.clicked.connect(self.build_account)
        layout.addWidget(submit_btn)

    def switch_dynamic_fields(self, index):
        self.dynamic_stack.setCurrentIndex(index)

    def build_account(self):
        name = self.name_input.text().strip()
        raw_acc_num = self.acc_num_input.text().strip()
        try:
            balance = Decimal(self.balance_input.text() or "0.00")
        except:
            QMessageBox.warning(self, "Error", "Invalid balance format."); return

        if not name or not raw_acc_num:
            QMessageBox.warning(self, "Error", "Name and Account Number are required."); return

        session_key = self.session.get_key()

        if not session_key:
            QMessageBox.critical(self, "Security Error", "No active session key found."); return

        enc_acc_num = AuthenticationService.encrypt(raw_acc_num, session_key)
        acc_id = uuid.uuid4()
        acc_type = self.type_dropdown.currentText()

        try:
            if acc_type == "Checking":
                self.new_account = CheckingAccount(acc_id, name, balance, enc_acc_num, self.routing_input.text())
            elif acc_type == "Savings":
                self.new_account = SavingsAccount(acc_id, name, balance, enc_acc_num, Decimal(self.interest_input.text() or "0"))
            elif acc_type == "Credit Card":
                enc_cvv = AuthenticationService.encrypt(self.cc_cvv.text(), session_key)
                self.new_account = CreditCardAccount(acc_id, name, balance, enc_acc_num, enc_cvv,
                                                     Decimal(self.cc_limit.text() or "0"), Decimal(self.cc_apr.text() or "0"))
            elif acc_type == "Debit Card":
                enc_cvv = AuthenticationService.encrypt(self.dc_cvv.text(), session_key)
                self.new_account = DebitCardAccount(acc_id, name, balance, enc_acc_num, enc_cvv, uuid.UUID(self.dc_linked_id.text()))

            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create account: {e}")