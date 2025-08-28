from typing import List

from transactions.models.transactions_models import (
    ProductModel, TransactionModel, DetailTransactionModel, 
    ProductUnitDetailModel, PendingTransactionModel
)
from transactions.repositories.transaction_repository import TransactionRepository

from response.response_message import ResponseMessage
from generals.constants import (
    PERM_C_TRANSACTIONS, PERM_U_TRANSACTIONS, PERM_R_PENDING_TRANSACTIONS,
    PERM_C_PENDING_TRANSACTIONS, PERM_R_PENDING_TRANSACTIONS
)
from generals.messages import (
    ERR_PERM_C_TRANSACTIONS, ERR_PERM_U_TRANSACTIONS, ERR_PERM_R_PENDING_TRANSACTIONS,
    ERR_PERM_C_PENDING_TRANSACTIONS
)
from generals.permission_manager import PermissionManager


class TransactionService:
    def __init__(self):
        self.repository = TransactionRepository()
        self.permission_manager = PermissionManager()


    def submit_transaction(self, transaction: TransactionModel, detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_C_TRANSACTIONS)

        return self.repository.submit_transaction(transaction, detail_transactions)
    
    
    def update_transaction(self, transaction: TransactionModel, 
                            added_detail_transactions: List[DetailTransactionModel], 
                            updated_detail_transactions: List[DetailTransactionModel],
                            deleted_detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        if not self.permission_manager.has_permission(PERM_U_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_U_TRANSACTIONS)

        return self.repository.update_transaction(transaction, added_detail_transactions, updated_detail_transactions, deleted_detail_transactions)


    def create_transaction_id(self, is_pending: bool = False) -> str:
        if not self.permission_manager.has_permission(PERM_C_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_C_TRANSACTIONS)

        return self.repository.create_transaction_id(is_pending)


    def create_pending_transaction(self, pending_transaction: PendingTransactionModel, detail_transactions: List[DetailTransactionModel]) -> ResponseMessage:
        if not self.permission_manager.has_permission(PERM_C_PENDING_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_C_PENDING_TRANSACTIONS)

        return self.repository.create_pending_transaction(pending_transaction, detail_transactions)


    def get_pending_transactions_by_id(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_PENDING_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PENDING_TRANSACTIONS)

        return self.repository.get_pending_transactions_by_id(transaction_id)


    def get_pending_transactions_details_by_id(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_PENDING_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PENDING_TRANSACTIONS)

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


    def get_detail_transactions_by_id(self, transaction_id: str):
        return self.repository.get_detail_transactions_by_id(transaction_id)


    def get_transactions_by_id(self, transaction_id: str):
        return self.repository.get_transactions_by_id(transaction_id)
