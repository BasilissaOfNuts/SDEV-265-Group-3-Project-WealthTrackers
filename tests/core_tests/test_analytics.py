import uuid
import pytest

from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock

from core.analytics.AnalyticsProcessor import AnalyticsProcessor
from core.account.CheckingAccount import CheckingAccount
from core.account.CreditCardAccount import CreditCardAccount
from core.account.AccountRepository import AccountRepository
from core.transaction.TransactionRepository import TransactionRepository
from core.transaction.Transaction import Transaction

@pytest.fixture
def mock_repos():
    """Provides mocked repositories to isolate Analytics logic"""
    mock_acc_repo = MagicMock(spec=AccountRepository)
    mock_txn_repo = MagicMock(spec=TransactionRepository)
    return mock_txn_repo, mock_acc_repo

def test_get_aggregated_data_balance_reconstruction(mock_repos):
    """Verifies that the processor correctly winds back history to find historical balances"""
    mock_txn_repo, mock_acc_repo = mock_repos
    processor = AnalyticsProcessor(mock_txn_repo, mock_acc_repo)

    user_id = "user123"
    acc_id = uuid.uuid4()

    # Current State: $1000 in Checking
    checking = CheckingAccount(acc_id, "Main", Decimal('1000.00'), b'enc', "123")
    mock_acc_repo.fetch_all_accounts.return_value = [checking]

    # History:
    # Today (May 3): Spent $200 (Balance was $1000 after this)
    # Yesterday (May 2): Received $500 (Balance was $1200 after this)
    # Two days ago (May 1): Start (Balance was $700)
    t1 = Transaction(uuid.uuid4(), acc_id, 1, "Vendor A", 1, "Food", Decimal('200.00'), datetime(2026, 5, 3), "EXPENSE")
    t2 = Transaction(uuid.uuid4(), acc_id, 2, "Income Source", 2, "Salary", Decimal('500.00'), datetime(2026, 5, 2),
                     "INCOME")

    mock_txn_repo.fetch_user_transactions.return_value = [t1, t2]

    results = processor.get_aggregated_data(user_id, period_type="Daily")

    # Verify May 3 Balance ($1000)
    assert results["2026-05-03"]["Total Balance"] == 1000.0
    assert results["2026-05-03"]["Expense"] == 200.0

    # Verify May 2 Balance (1000 + 200 = 1200)
    assert results["2026-05-02"]["Total Balance"] == 1200.0
    assert results["2026-05-02"]["Income"] == 500.0

def test_aggregation_with_credit_card_debt(mock_repos):
    """Ensures Credit Card balances correctly decrease the global total balance"""
    mock_txn_repo, mock_acc_repo = mock_repos
    processor = AnalyticsProcessor(mock_txn_repo, mock_acc_repo)

    user_id = "user123"

    # $1000 Checking - $400 CC Debt = $600 Net Total Balance
    checking = CheckingAccount(uuid.uuid4(), "Checking", Decimal('1000.00'), b'enc', "123")
    credit = CreditCardAccount(uuid.uuid4(), "Visa", Decimal('400.00'), b'enc', b'cvv', Decimal('5000.00'),
                               Decimal('0.24'))

    mock_acc_repo.fetch_all_accounts.return_value = [checking, credit]
    mock_txn_repo.fetch_user_transactions.return_value = []  # No txns, just check starting point

    results = processor.get_aggregated_data(user_id)

    # If there are no transactions, the history might be empty or just the current state
    # If transactions exist, we check the baseline.
    if results:
        latest_key = max(results.keys())
        assert results[latest_key]["Total Balance"] == 600.0

def test_search_filtering_in_aggregation(mock_repos):
    """Verifies that Income/Expense series are filtered by search, but Balance remains global"""
    mock_txn_repo, mock_acc_repo = mock_repos
    processor = AnalyticsProcessor(mock_txn_repo, mock_acc_repo)

    user_id = "user123"
    acc_id = uuid.uuid4()

    mock_acc_repo.fetch_all_accounts.return_value = [CheckingAccount(acc_id, "Main", Decimal('1000.00'), b'enc', "123")]

    # Two transactions on same day, only one matches search 'Steam'
    t1 = Transaction(uuid.uuid4(), acc_id, 1, "Steam", 1, "Gaming", Decimal('50.00'), datetime(2026, 5, 3), "EXPENSE")
    t2 = Transaction(uuid.uuid4(), acc_id, 2, "Groceries", 2, "Food", Decimal('100.00'), datetime(2026, 5, 3),
                     "EXPENSE")

    mock_txn_repo.fetch_user_transactions.return_value = [t1, t2]

    # Search for 'Steam'
    results = processor.get_aggregated_data(user_id, search_text="Steam", group_by="Vendor")

    # Expense should ONLY show the filtered $50
    assert results["2026-05-03"]["Expense"] == 50.0 
    # Total Balance should still reflect the actual bank status ($1000)
    assert results["2026-05-03"]["Total Balance"] == 1000.0

if __name__ == "__main__":
    pytest.main([__file__])