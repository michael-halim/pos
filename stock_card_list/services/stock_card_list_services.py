from datetime import date

from stock_card_list.models.stock_card_list_models import ProductStockCardListModel, StockCardListModel
from stock_card_list.repositories.stock_card_list_repositories import StockCardListRepository

class StockCardListService:
    def __init__(self):
        self.repository = StockCardListRepository()


    def get_products(self, search_text: str = None):
        return self.repository.get_products(search_text)


    def get_stock_card(self, sku: str, start_date: date, end_date: date):
        return self.repository.get_stock_card(sku, start_date, end_date)

