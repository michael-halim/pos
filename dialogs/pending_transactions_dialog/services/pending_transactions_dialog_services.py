from typing import List, Optional
from ..repositories.pending_transactions_dialog_repositories import PendingTransactionsDialogRepository

class PendingTransactionsDialogService:
    def __init__(self):
        self.repository = PendingTransactionsDialogRepository()


    def get_pending_transactions(self, search_text: str = None):
        return self.repository.get_pending_transactions(search_text)


    def get_pending_detail_transactions(self, transaction_id: str):
        return self.repository.get_pending_detail_transactions(transaction_id)

