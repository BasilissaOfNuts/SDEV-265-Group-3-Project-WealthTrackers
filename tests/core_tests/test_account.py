import uuid
import os
import sqlite3
import pytest
import tempfile
import gc

from decimal import Decimal
from datetime import datetime

from core.account.CheckingAccount import CheckingAccount
from core.account.SavingsAccount import SavingsAccount
from core.account.CreditCardAccount import CreditCardAccount
from core.account.DebitCardAccount import DebitCardAccount
from core.account.AccountRepository import AccountRepository

# --- HELPERS FOR TESTING ---
class MockTransaction:
    def __init__(self, txn_id):
        self.id = txn_id

# --- FIXTURES (Setup/Teardown for Repository) ---
@pytest.fixture
def temp_db():
    """Creates a temporary file-based database with full schema for integration testing"""
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Relational pre-requisites
    cursor.execute("CREATE TABLE categories (category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE NOT NULL)")
    cursor.execute(
        "CREATE TABLE vendors (vendor_id INTEGER PRIMARY KEY, vendor_name TEXT UNIQUE NOT NULL, default_category_id INTEGER)")
    cursor.execute(
        "CREATE TABLE users (user_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash BLOB NOT NULL, encryption_salt BLOB NOT NULL)")

    # Base accounts table
    cursor.execute(
        "CREATE TABLE accounts (account_id TEXT PRIMARY KEY, user_id TEXT, account_name TEXT, account_type TEXT, enc_acc_num BLOB)")

    # Detail tables
    cursor.execute("CREATE TABLE checking_details (account_id TEXT PRIMARY KEY, routing_number TEXT)")
    cursor.execute("CREATE TABLE credit_card_details (account_id TEXT PRIMARY KEY, enc_cvv BLOB, credit_limit REAL)")
    cursor.execute("CREATE TABLE savings_details (account_id TEXT PRIMARY KEY, interest_rate REAL)")
    cursor.execute(
        "CREATE TABLE debit_card_details (account_id TEXT PRIMARY KEY, enc_cvv BLOB, linked_checking_id TEXT)")

    # Transaction table (Reconstructed balance depends on this)
    cursor.execute("""
                   CREATE TABLE transactions
                   (
                       transaction_id   TEXT PRIMARY KEY,
                       account_id       TEXT    NOT NULL,
                       vendor_id        INTEGER NOT NULL,
                       category_id      INTEGER NOT NULL,
                       amount           REAL    NOT NULL,
                       transaction_date TEXT    NOT NULL,
                       transaction_type TEXT    NOT NULL
                   )
                   """)

    cursor.execute("""
                   INSERT INTO users (user_id, username, password_hash, encryption_salt)
                   VALUES (?, ?, ?, ?)
                   """, ('user123', 'testuser', b'hash', b'salt'))
    conn.commit()
    conn.close()

    yield db_path

    gc.collect()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass

# --- DOMAIN LOGIC TESTS ---

def test_base_account_logic():
    print("Testing Base Account Logic...")
    acc_num_enc = b'encrypted_acc_number'
    checking = CheckingAccount(uuid.uuid4(), "Test Checking", Decimal('1000.00'), acc_num_enc, "123456789")

    checking.deposit(Decimal('500.00'))
    assert checking.balance == Decimal('1500.00')

    checking.withdraw(Decimal('200.00'))
    assert checking.balance == Decimal('1300.00')

    txn_id = uuid.uuid4()
    mock_txn = MockTransaction(txn_id)
    checking.add_transaction(mock_txn)
    assert len(checking.get_transactions()) == 1

    checking.remove_transaction(txn_id)
    assert len(checking.get_transactions()) == 0

def test_checking_subclass():
    checking_acc = CheckingAccount(uuid.uuid4(), "Student Checking", Decimal('500.00'), b'enc', "074029032")
    assert checking_acc.routing_number == "074029032"

def test_savings_interest_logic():
    savings = SavingsAccount(uuid.uuid4(), "Emergency Fund", Decimal('10000.00'), b'enc', Decimal('0.045'))
    interest = savings.calculate_monthly_interest()
    assert interest == Decimal('37.50')
    savings.apply_interest()
    assert savings.balance == Decimal('10037.50')

def test_credit_card_debt_logic():
    credit = CreditCardAccount(uuid.uuid4(), "Titanium Rewards", Decimal('500.00'), b'enc', b'cvv',
                               Decimal('15000.00'), Decimal('0.24'))
    charge = credit.calculate_interest_charge(Decimal('500.00'))
    assert charge == Decimal('10.00')
    credit.apply_interest_charge(Decimal('500.00'))
    assert credit.balance == Decimal('510.00')

def test_debit_card_subclass():
    """Uses the DebitCardAccount import"""
    print("Testing Debit Card Logic...")
    linked_id = uuid.uuid4()
    debit = DebitCardAccount(uuid.uuid4(), "Daily Swipe", Decimal('100.00'), b'enc', b'cvv', linked_id)
    assert debit.linked_checking_id == linked_id

# --- REPOSITORY INTEGRATION TESTS ---

def test_repository_save_and_fetch_all(temp_db):
    """Tests saving multiple subclasses and retrieving them with reconstructed balances"""
    repo = AccountRepository(temp_db)
    user_id = 'user123'

    # Using datetime for the transaction timestamp
    txn_time = datetime.now().isoformat()

    check_id = uuid.uuid4()
    checking = CheckingAccount(check_id, "Main Checking", Decimal('0.00'), b'enc_checking', "074029032")
    repo.save_new_account(user_id, checking)

    cc_id = uuid.uuid4()
    credit = CreditCardAccount(cc_id, "Visa", Decimal('0.00'), b'enc_cc', b'cvv', Decimal('5000.00'), Decimal('0.24'))
    repo.save_new_account(user_id, credit)

    # Use transactions to test balance reconstruction
    conn = sqlite3.connect(temp_db)
    conn.execute("INSERT INTO transactions VALUES (?, ?, 1, 1, 1000.00, ?, 'INCOME')",
                 (str(uuid.uuid4()), str(check_id), txn_time))
    conn.execute("INSERT INTO transactions VALUES (?, ?, 1, 1, 200.00, ?, 'EXPENSE')",
                 (str(uuid.uuid4()), str(cc_id), txn_time))
    conn.commit()
    conn.close()

    accounts = repo.fetch_all_accounts(user_id)
    assert len(accounts) == 2

    # Verify balances were reconstructed correctly
    for acc in accounts:
        if isinstance(acc, CheckingAccount):
            assert acc.balance == Decimal('1000.00')
        if isinstance(acc, CreditCardAccount):
            assert acc.balance == Decimal('200.00')

if __name__ == "__main__":
    pytest.main([__file__])