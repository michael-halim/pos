from typing import List, Optional

from response.response_message import ResponseMessage
from dialogs.master_stock_dialog.repositories.master_stock_dialog_repositories import MasterStockDialogRepository
from dialogs.master_stock_dialog.models.master_stock_dialog_models import MasterStockModel

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


    def get_category_by_id(self, category_id: str):
        return self.repository.get_category_by_id(category_id)
    

    def submit_master_stock(self, master_stock_form_data: MasterStockModel):
        return self.repository.submit_master_stock(master_stock_form_data)
    

    def update_master_stock(self, master_stock_form_data: MasterStockModel):
        return self.repository.update_master_stock(master_stock_form_data)


    def delete_master_stock_by_sku(self, sku: str):
        return self.repository.delete_master_stock_by_sku(sku)