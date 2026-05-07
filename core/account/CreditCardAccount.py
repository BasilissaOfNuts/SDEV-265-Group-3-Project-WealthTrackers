from uuid import UUID
from decimal import Decimal

from core.account.Account import Account
from core.authentication.AuthenticationService import AuthenticationService

class CreditCardAccount(Account):
    def __init__(self, account_id: UUID, name: str, balance: Decimal, enc_acc_num: bytes,
                 enc_cvv: bytes, credit_limit: Decimal, apr: Decimal):
        super().__init__(account_id, name, balance, enc_acc_num)
        self._enc_cvv = enc_cvv
        self._credit_limit = credit_limit
        self._apr = apr

    @property
    def credit_limit(self) -> Decimal:
        return self._credit_limit

    def get_decrypted_cvv(self, key: bytes) -> str:
        return AuthenticationService.decrypt(self._enc_cvv, key)

    def calculate_interest_charge(self, overdue_amount: Decimal) -> Decimal:
        """Calculates interest on overdue balance."""

        if overdue_amount <= 0:
            return Decimal('0.00')

        monthly_apr = self._apr / Decimal('12')
        charge = overdue_amount * monthly_apr

        return charge.quantize(Decimal('0.01'))

    def apply_interest_charge(self, overdue_amount: Decimal):
        charge = self.calculate_interest_charge(overdue_amount)
        if charge > 0:
            # We use deposit because balance represents debt for CCs
            self.deposit(charge)

        return charge