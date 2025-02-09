from datetime import datetime, timedelta
from typing import Optional, List

# Import Models
from ..models.transactions_models import ProductModel, TransactionModel, DetailTransactionModel, ProductUnitDetailModel
from ..models.transactions_models import PendingTransactionModel, PendingDetailTransactionModel, PendingDetailTransactionToTransactionModel

from ..repositories.transaction_repository import TransactionRepository
from ..models.result import ResponseMessage


class TransactionService:
    def __init__(self):
        self.repository = TransactionRepository()

    def submit_transaction(self, transaction: TransactionModel, detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        return self.repository.submit_transaction(transaction, detail_transactions)


    def create_transaction_id(self, is_pending: bool = False) -> str:
        return self.repository.create_transaction_id(is_pending)


    def create_pending_transaction(self, pending_transaction: PendingTransactionModel, pending_detail_transactions: List[PendingDetailTransactionModel]) -> ResponseMessage:
        return self.repository.create_pending_transaction(pending_transaction, pending_detail_transactions)


    def get_pending_transactions_by_transaction_id(self, transaction_id: str):
        return self.repository.get_pending_transactions_by_transaction_id(transaction_id)


    def get_product_unit_details(self, sku: str) -> list[ProductUnitDetailModel]:
        return self.repository.get_product_unit_details(sku)


    def get_product_by_sku(self, sku: str) -> ProductModel:
        return self.repository.get_product_by_sku(sku)
