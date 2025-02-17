from typing import List, Optional

from response.response_message import ResponseMessage
from dialogs.suppliers_dialog.suppliers_dialog_repositories.suppliers_dialog_repositories import SuppliersDialogRepository

class SuppliersDialogService:
    def __init__(self):
        self.repository = SuppliersDialogRepository()
        
    def get_suppliers(self, search_text: str = ''):
        return self.repository.get_suppliers(search_text)
    
    
    def get_supplier_by_id(self, supplier_id: str):
        return self.repository.get_supplier_by_id(supplier_id)

