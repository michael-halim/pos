from ..repositories.suppliers_repositories import SuppliersRepository
from ..models.suppliers_models import SuppliersModel

class SuppliersService:
    def __init__(self):
        self.repository = SuppliersRepository()


    def get_suppliers(self, search_text: str = None):
        return self.repository.get_suppliers(search_text)

    
    def get_supplier_by_id(self, supplier_id: int):
        return self.repository.get_supplier_by_id(supplier_id)
    

    def submit_supplier(self, supplier_data: SuppliersModel):
        return self.repository.submit_supplier(supplier_data)
    

    def update_supplier(self, supplier_data: SuppliersModel):
        return self.repository.update_supplier(supplier_data)
    

    def delete_supplier_by_id(self, supplier_id: int):
        return self.repository.delete_supplier_by_id(supplier_id)