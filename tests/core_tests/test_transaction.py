import uuid
import os
import sqlite3
import pytest
import tempfile
import gc

from decimal import Decimal
from datetime import datetime

from core.transaction.Transaction import Transaction
from core.transaction.TransactionRepository import TransactionRepository

@pytest.fixture
def temp_db():
    """Creates a temporary file-based database for integration testing"""
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema to match production
    cursor.execute("CREATE TABLE categories (category_id INTEGER PRIMARY KEY, category_name TEXT)")
    cursor.execute("""
                   CREATE TABLE vendors
                   (
                       vendor_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                       vendor_name         TEXT UNIQUE,
                       default_category_id INTEGER,
                       FOREIGN KEY (default_category_id) REFERENCES categories (category_id)
                   )
                   """)
    cursor.execute("""
                   CREATE TABLE transactions
                   (
                       transaction_id   TEXT PRIMARY KEY,
                       account_id       TEXT    NOT NULL,
                       vendor_id        INTEGER NOT NULL,
                       category_id      INTEGER NOT NULL,
                       amount           REAL    NOT NULL,
                       transaction_date TEXT    NOT NULL,
                       transaction_type TEXT    NOT NULL,
                       FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id),
                       FOREIGN KEY (category_id) REFERENCES categories (category_id)
                   )
                   """)

    # Seed required base data for JOINs
    cursor.execute("INSERT INTO categories VALUES (1, 'Utilities'), (2, 'Food')")
    cursor.execute("INSERT INTO vendors (vendor_name, default_category_id) VALUES ('TEST VENDOR', 1)")
    conn.commit()
    conn.close()

    yield db_path

    gc.collect()

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass

# --- TRANSACTION DOMAIN TESTS ---

def test_transaction_initialization():
    """Tests that the Transaction object correctly stores and returns data via attributes"""
    txn_id = uuid.uuid4()
    acc_id = uuid.uuid4()
    now = datetime.now()

    txn = Transaction(
        txn_id=txn_id,
        account_id=acc_id,
        vendor_id=50,
        vendor_name="STEAM",
        category_id=9,
        category_name="Entertainment",
        amount=Decimal("59.99"),
        date=now,
        txn_type="EXPENSE"
    )

    assert txn.id == txn_id
    assert txn.amount == Decimal("59.99")
    assert txn.vendor_name == "STEAM"
    assert txn.category_name == "Entertainment"

# --- REPOSITORY INTEGRATION TESTS ---

def test_repository_save_and_fetch(temp_db):
    """Tests saving a transaction and retrieving it with JOIN-ed names"""
    repo = TransactionRepository(temp_db)
    txn_id = uuid.uuid4()
    acc_id = uuid.uuid4()

    txn = Transaction(
        txn_id=txn_id,
        account_id=acc_id,
        vendor_id=1,
        vendor_name="TEST VENDOR",
        category_id=1,
        category_name="Utilities",
        amount=Decimal("100.00"),
        date=datetime(2026, 4, 5, 12, 0),
        txn_type="EXPENSE"
    )

    repo.save_transaction(txn)
    results = repo.fetch_transactions(acc_id)

    assert len(results) == 1
    assert results[0].id == txn_id
    assert results[0].vendor_name == "TEST VENDOR"
    assert results[0].category_name == "Utilities"

def test_repository_delete(temp_db):
    """Tests deletion logic in the repository"""
    repo = TransactionRepository(temp_db)
    txn_id = uuid.uuid4()
    acc_id = uuid.uuid4()

    txn = Transaction(txn_id, acc_id, 1, "TEST VENDOR", 1, "Utilities", Decimal("10.00"), datetime.now(), "EXPENSE")
    repo.save_transaction(txn)

    # Ensure it saved
    assert len(repo.fetch_transactions(acc_id)) == 1

    repo.delete_transaction(txn_id)
    assert len(repo.fetch_transactions(acc_id)) == 0

def test_repository_aggregation(temp_db):
    """Tests the SQL GROUP BY logic for category spending used by Analytics"""
    repo = TransactionRepository(temp_db)
    acc_id = uuid.uuid4()

    # Create transactions in the same category
    t1 = Transaction(uuid.uuid4(), acc_id, 1, "TEST VENDOR", 1, "Utilities", Decimal("50.00"), datetime.now(),
                     "EXPENSE")
    t2 = Transaction(uuid.uuid4(), acc_id, 1, "TEST VENDOR", 1, "Utilities", Decimal("25.00"), datetime.now(),
                     "EXPENSE")

    repo.save_transaction(t1)
    repo.save_transaction(t2)

    spending = repo.get_total_spending_by_category(acc_id)
    assert spending["Utilities"] == Decimal("75.00")

if __name__ == "__main__":
    pytest.main([__file__])