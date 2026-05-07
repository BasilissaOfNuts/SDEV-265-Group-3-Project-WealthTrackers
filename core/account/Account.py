from abc import ABC
from decimal import Decimal
from uuid import UUID
from typing import List

from core.authentication.AuthenticationService import AuthenticationService

class Account(ABC):
    def __init__(self, account_id: UUID, name: str, balance: Decimal, enc_acc_num: bytes):
        self._id = account_id
        self._name = name
        self._balance = balance
        self._enc_acc_num = enc_acc_num
        self._transaction_history: List = []

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def balance(self) -> Decimal:
        return self._balance

    def get_decrypted_number(self, key: bytes) -> str:
        """Uses AuthenticationService to decrypt account number"""
        return AuthenticationService.decrypt(self._enc_acc_num, key)

    def add_transaction(self, txn) -> None:
        self._transaction_history.append(txn)

    def remove_transaction(self, txn_id: UUID) -> None:
        """Remove a transaction by UUID"""
        self._transaction_history = [t for t in self._transaction_history if getattr(t, 'id', None) != txn_id]

    def get_transactions(self) -> List:
        return self._transaction_history

    def deposit(self, amount: Decimal) -> None:
        if amount > 0:
            self._balance += amount

    def withdraw(self, amount: Decimal) -> None:
        if amount > 0:
            self._balance -= amount