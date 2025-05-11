from suppliers.repositories.suppliers_repositories import SuppliersRepository
from suppliers.models.suppliers_models import SuppliersModel

from generals.constants import (
    PERM_R_SUPPLIERS, PERM_C_SUPPLIERS, PERM_U_SUPPLIERS, PERM_D_SUPPLIERS
)
from generals.messages import (
    ERR_PERM_R_SUPPLIERS, ERR_PERM_C_SUPPLIERS, ERR_PERM_U_SUPPLIERS, ERR_PERM_D_SUPPLIERS
)
from generals.permission_manager import PermissionManager
from response.response_message import ResponseMessage


class SuppliersService:
    def __init__(self):
        self.repository = SuppliersRepository()
        self.permission_manager = PermissionManager()


    def get_suppliers(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_R_SUPPLIERS)

        return self.repository.get_suppliers(search_text)

    
    def get_supplier_by_id(self, supplier_id: int):
        if not self.permission_manager.has_permission(PERM_R_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_R_SUPPLIERS)

        return self.repository.get_supplier_by_id(supplier_id)
    

    def submit_supplier(self, supplier_data: SuppliersModel):
        if not self.permission_manager.has_permission(PERM_C_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_C_SUPPLIERS)

        return self.repository.submit_supplier(supplier_data)
    

    def update_supplier(self, supplier_data: SuppliersModel):
        if not self.permission_manager.has_permission(PERM_U_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_U_SUPPLIERS)

        return self.repository.update_supplier(supplier_data)
    

    def delete_supplier_by_id(self, supplier_id: int):
        if not self.permission_manager.has_permission(PERM_D_SUPPLIERS):
            return ResponseMessage.fail(message=ERR_PERM_D_SUPPLIERS)

        return self.repository.delete_supplier_by_id(supplier_id)