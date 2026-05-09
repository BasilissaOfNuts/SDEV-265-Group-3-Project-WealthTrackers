from decimal import Decimal
from uuid import UUID
from datetime import datetime
from typing import Dict, List, Optional, Set

from core.account.AccountRepository import AccountRepository
from core.account.CreditCardAccount import CreditCardAccount
from core.account.DebitCardAccount import DebitCardAccount
from core.transaction.TransactionRepository import TransactionRepository

def _get_period_key(date, p_type):
    if p_type == "Daily": return date.strftime("%Y-%m-%d")
    if p_type == "Monthly": return date.strftime("%Y-%m")
    return date.strftime("%Y")

def _key_to_datetime(key, p_type):
    if p_type == "Daily": return datetime.strptime(key, "%Y-%m-%d")
    if p_type == "Monthly": return datetime.strptime(key, "%Y-%m")
    return datetime.strptime(key, "%Y")

class AnalyticsProcessor:
    def __init__(self, txn_repo: TransactionRepository, acc_repo: AccountRepository):
        self._txn_repo = txn_repo
        self._acc_repo = acc_repo

    def get_aggregated_data(
            self,
            user_id: str,
            account_id: Optional[UUID] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            group_by: str = "Category",
            period_type: str = "Daily",
            search_text: str = ""
    ) -> Dict[str, Dict[str, float]]:
        """
        Processes transactions and reconstructs the balance history.
        Series: Income (Filtered), Expense (Filtered), Total Balance (Cumulative/Global)
        """
        # 1. Fetch current context
        all_accounts = self._acc_repo.fetch_all_accounts(user_id)
        if account_id:
            target_accounts = [acc for acc in all_accounts if acc.id == account_id]
            all_txns = self._txn_repo.fetch_transactions(account_id)
        else:
            target_accounts = all_accounts
            all_txns = self._txn_repo.fetch_user_transactions(user_id)

        # 2. Calculate "Current Starting Point" for balance
        # Credit Card balances are treated as negative for Net Worth/Total Balance
        current_total_balance = Decimal("0.00")
        for acc in target_accounts:
            if isinstance(acc, CreditCardAccount):
                current_total_balance -= acc.balance
            elif isinstance(acc, DebitCardAccount):
                continue
            else:
                current_total_balance += acc.balance

        # 3. Sort ALL transactions descending to walk backwards and find historical balances
        all_txns.sort(key=lambda x: x.date, reverse=True)

        history = {}
        running_bal = current_total_balance
        search_lower = search_text.lower()

        # We bucket data by date string first
        for tx in all_txns:
            key = _get_period_key(tx.date, period_type)
            if key not in history:
                history[key] = {"Income": Decimal("0.00"), "Expense": Decimal("0.00"), "Balance": Decimal("0.00")}

            # Cumulative Balance Logic (Unfiltered)
            # We assign the 'running_bal' to the period as the balance at the END of that period
            if history[key]["Balance"] == 0:
                history[key]["Balance"] = running_bal

            # Filtered Series (Income/Expense)
            match = True
            if search_text:
                target = tx.vendor_name.lower() if group_by == "Vendor" else tx.category_name.lower()
                if search_lower not in target:
                    match = False

            if match:
                if tx.type in ("INCOME", "TRANSFER_IN"):
                    history[key]["Income"] += tx.amount
                elif tx.type in ("EXPENSE", "TRANSFER_OUT"):
                    history[key]["Expense"] += tx.amount

            # Wind back the balance for the next (chronologically previous) transaction
            if tx.type in ("INCOME", "TRANSFER_IN"):
                running_bal -= tx.amount
            elif tx.type in ("EXPENSE", "TRANSFER_OUT"):
                running_bal += tx.amount

        # 4. Filter by requested date range and convert to floats for Matplotlib
        final_results = {}
        sorted_keys = sorted(history.keys())

        for k in sorted_keys:
            dt = _key_to_datetime(k, period_type)
            if start_date and dt < start_date: continue
            if end_date and dt > end_date: continue

            final_results[k] = {
                "Income": float(history[k]["Income"]),
                "Expense": float(history[k]["Expense"]),
                "Total Balance": float(history[k]["Balance"])  # No longer "Net"
            }

        return final_results