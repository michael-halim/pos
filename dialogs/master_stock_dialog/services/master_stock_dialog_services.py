from typing import List, Optional

from response.response_message import ResponseMessage
from dialogs.master_stock_dialog.repositories.master_stock_dialog_repositories import MasterStockDialogRepository
class MasterStockDialogService:
    def __init__(self):
        self.repository = MasterStockDialogRepository()
        
    def get_suppliers(self, search_text: str = ''):
        return self.repository.get_suppliers(search_text)
    
    
    def get_supplier_by_id(self, supplier_id: str):
        return self.repository.get_supplier_by_id(supplier_id)


    def get_purchasing_history_by_sku(self, sku: str):
        return self.repository.get_purchasing_history_by_sku(sku)


    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)
