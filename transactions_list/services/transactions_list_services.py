from datetime import datetime, timedelta
from typing import Optional, List

# Import Models
from transactions_list.models.transactions_list_models import TransactionListModel
from transactions_list.repositories.transactions_list_repository import TransactionRepository

class TransactionListService:
    def __init__(self):
        self.repository = TransactionRepository()

    def get_transactions_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        return self.repository.get_transactions_list(start_date, end_date, search_text)
    
    def get_detail_transactions_list(self, transaction_id: str):
        return self.repository.get_detail_transactions_list(transaction_id)
