from datetime import date

from stock_card_list.repositories.stock_card_list_repositories import StockCardListRepository

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_STOCK_CARD
from generals.messages import ERR_PERM_R_STOCK_CARD
from response.response_message import ResponseMessage


class StockCardListService:
    def __init__(self):
        self.repository = StockCardListRepository()
        self.permission_manager = PermissionManager()

    def get_products(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_STOCK_CARD):
            return ResponseMessage.fail(message=ERR_PERM_R_STOCK_CARD)

        return self.repository.get_products(search_text)


    def get_stock_card(self, sku: str, start_date: date, end_date: date):
        if not self.permission_manager.has_permission(PERM_R_STOCK_CARD):
            return ResponseMessage.fail(message=ERR_PERM_R_STOCK_CARD)

        return self.repository.get_stock_card(sku, start_date, end_date)

