from uuid import UUID
from decimal import Decimal

from core.account.Account import Account

class DebitCardAccount(Account):
    def __init__(self, account_id: UUID, name: str, balance: Decimal, enc_acc_num: bytes, enc_cvv: bytes, linked_checking_id: UUID):
        super().__init__(account_id, name, balance, enc_acc_num)
        self._enc_cvv = enc_cvv
        self._linked_checking_id = linked_checking_id

    @property
    def linked_checking_id(self) -> UUID:
        return self._linked_checking_id