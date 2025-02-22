from datetime import datetime
from ..repositories.purchasing_list_repositories import PurchasingListRepository

class PurchasingListService:
    def __init__(self):
        self.repository = PurchasingListRepository()


    def get_purchasing_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        return self.repository.get_purchasing_list(start_date, end_date, search_text)


    def get_detail_purchasing_by_id(self, purchasing_id: str):
        return self.repository.get_detail_purchasing_by_id(purchasing_id)

