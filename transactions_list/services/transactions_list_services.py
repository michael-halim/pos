from datetime import datetime

from transactions_list.repositories.transactions_list_repository import TransactionRepository

class TransactionListService:
    def __init__(self):
        self.repository = TransactionRepository()

    def get_transactions_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        return self.repository.get_transactions_list(start_date, end_date, search_text)
    

    def get_detail_transactions_list(self, transaction_id: str):
        return self.repository.get_detail_transactions_list(transaction_id)


    def delete_transactions_by_id(self, transaction_id: str):
        return self.repository.delete_transactions_by_id(transaction_id)

