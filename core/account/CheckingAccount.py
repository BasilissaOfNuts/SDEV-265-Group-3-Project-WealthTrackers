from uuid import UUID
from decimal import Decimal

from core.account.Account import Account

class CheckingAccount(Account):
    def __init__(self, account_id: UUID, name: str, balance: Decimal, enc_acc_num: bytes, routing_number: str):
        super().__init__(account_id, name, balance, enc_acc_num)
        self._routing_number = routing_number

    @property
    def routing_number(self) -> str:
        return self._routing_number