from uuid import UUID
from decimal import Decimal

from core.account.Account import Account

class SavingsAccount(Account):
    def __init__(self, account_id: UUID, name: str, balance: Decimal, enc_acc_num: bytes, interest_rate: Decimal):
        super().__init__(account_id, name, balance, enc_acc_num)
        self._interest_rate = interest_rate

    @property
    def interest_rate(self) -> Decimal:
        return self._interest_rate

    def calculate_monthly_interest(self) -> Decimal:
        """Calculates monthly interest - (Balance * Rate) / 12 months"""
        monthly_rate = self._interest_rate / Decimal('12')
        interest_earned = self.balance * monthly_rate

        return interest_earned.quantize(Decimal('0.01'))

    def apply_interest(self):
        """Applies the interest to the balance"""
        earned = self.calculate_monthly_interest()
        self.deposit(earned)

        return earned
