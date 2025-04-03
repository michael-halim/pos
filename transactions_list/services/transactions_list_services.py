from datetime import datetime

from transactions_list.repositories.transactions_list_repository import TransactionRepository

from generals.constants import PERM_R_TRANSACTIONS, PERM_D_TRANSACTIONS
from generals.messages import ERR_PERM_R_TRANSACTIONS, ERR_PERM_D_TRANSACTIONS
from generals.permission_manager import PermissionManager
from response.response_message import ResponseMessage

class TransactionListService:
    def __init__(self):
        self.repository = TransactionRepository()
        self.permission_manager = PermissionManager()


    def get_transactions_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_TRANSACTIONS)
        
        return self.repository.get_transactions_list(start_date, end_date, search_text)
    

    def get_transaction_by_id(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_TRANSACTIONS)
        
        return self.repository.get_transaction_by_id(transaction_id)


    def get_transactions_table_data(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_TRANSACTIONS)
        
        return self.repository.get_transactions_table_data(transaction_id)
    
    
    def get_customer_by_id(self, customer_id: str):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_TRANSACTIONS)
        
        return self.repository.get_customer_by_id(customer_id)


    def get_detail_transactions_list(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_R_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_TRANSACTIONS)
        
        return self.repository.get_detail_transactions_list(transaction_id)


    def delete_transactions_by_id(self, transaction_id: str):
        if not self.permission_manager.has_permission(PERM_D_TRANSACTIONS):
            return ResponseMessage.fail(message=ERR_PERM_D_TRANSACTIONS)
        
        return self.repository.delete_transactions_by_id(transaction_id)

