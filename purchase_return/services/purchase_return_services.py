from purchase_return.repositories.purchase_return_repositories import PurchaseReturnRepository
from generals.permission_manager import PermissionManager
from purchase_return.models.purchase_return_models import PurchaseReturnModel, DetailPurchaseReturnModel
from response.response_message import ResponseMessage
from generals.constants import PERM_C_PURCHASE_RETURN
from generals.messages import ERR_PERM_C_PURCHASE_RETURN

class PurchaseReturnService:
    def __init__(self):
        self.repository = PurchaseReturnRepository()
        self.permission_manager = PermissionManager()


    def get_supplier_by_id(self, supplier_id: str):
        return self.repository.get_supplier_by_id(supplier_id)
    
    
    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)
    

    def get_product_unit_details(self, sku: str):
        return self.repository.get_product_unit_details(sku)
    

    def create_purchase_return_id(self):
        return self.repository.create_purchase_return_id()
    

    def submit_purchase_return(self, purchase_return_data: PurchaseReturnModel, detail_purchase_return_data: list[DetailPurchaseReturnModel]):
        if not self.permission_manager.has_permission(PERM_C_PURCHASE_RETURN):
            return ResponseMessage.fail(message=ERR_PERM_C_PURCHASE_RETURN)
        
        return self.repository.submit_purchase_return(purchase_return_data, detail_purchase_return_data)