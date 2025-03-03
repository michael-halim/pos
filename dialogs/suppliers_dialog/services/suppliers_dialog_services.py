from dialogs.suppliers_dialog.repositories.suppliers_dialog_repositories import SuppliersDialogRepository

from response.response_message import ResponseMessage

class SuppliersDialogService:
    def __init__(self):
        self.repository = SuppliersDialogRepository()
        

    def get_suppliers(self, search_text: str = '') -> ResponseMessage:
        return self.repository.get_suppliers(search_text)
    
    
    def get_supplier_by_id(self, supplier_id: str) -> ResponseMessage:
        return self.repository.get_supplier_by_id(supplier_id)

