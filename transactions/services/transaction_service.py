from typing import List

from transactions.models.transactions_models import ProductModel, TransactionModel, DetailTransactionModel, ProductUnitDetailModel
from transactions.models.transactions_models import PendingTransactionModel

from transactions.repositories.transaction_repository import TransactionRepository
from response.response_message import ResponseMessage

class TransactionService:
    def __init__(self):
        self.repository = TransactionRepository()

    def submit_transaction(self, transaction: TransactionModel, detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        return self.repository.submit_transaction(transaction, detail_transactions)


    def create_transaction_id(self, is_pending: bool = False) -> str:
        return self.repository.create_transaction_id(is_pending)


    def create_pending_transaction(self, pending_transaction: PendingTransactionModel, detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        return self.repository.create_pending_transaction(pending_transaction, detail_transactions)


    def get_pending_transactions_by_id(self, transaction_id: str):
        return self.repository.get_pending_transactions_by_id(transaction_id)


    def get_pending_transactions_details_by_id(self, transaction_id: str):
        return self.repository.get_pending_transactions_details_by_id(transaction_id)


    def get_product_unit_details(self, sku: str) -> list[ProductUnitDetailModel]:
        return self.repository.get_product_unit_details(sku)


    def get_product_by_sku(self, sku: str) -> ProductModel:
        return self.repository.get_product_by_sku(sku)


    def get_customer_by_id(self, customer_id: str) -> str:
        return self.repository.get_customer_by_id(customer_id)

    
    def get_purchasing_history_by_sku(self, sku: str):
        return self.repository.get_purchasing_history_by_sku(sku)
    

    def get_transaction_history_by_sku(self, sku: str):
        return self.repository.get_transaction_history_by_sku(sku)
