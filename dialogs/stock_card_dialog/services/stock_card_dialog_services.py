from datetime import date

from dialogs.stock_card_dialog.repositories.stock_card_dialog_repositories import StockCardDialogRepository

class StockCardDialogService:
    def __init__(self):
        self.repository = StockCardDialogRepository()


    def get_stock_card(self, sku: str, start_date: date, end_date: date):
        return self.repository.get_stock_card(sku, start_date, end_date)

