from typing import List

from generals.permission_manager import PermissionManager

from purchasing.repositories.purchasing_repositories import PurchasingRepository
from purchasing.models.purchasing_models import (
    PurchasingModel, 
    DetailPurchasingModel
)

from response.response_message import ResponseMessage
from generals.constants import PERM_C_PURCHASING, PERM_U_PURCHASING
from generals.messages import ERR_PERM_C_PURCHASING, ERR_PERM_U_PURCHASING

class PurchasingService:
    def __init__(self):
        self.repository = PurchasingRepository()
        self.permission_manager = PermissionManager()


    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)


    def get_product_unit_details(self, sku: str):
        return self.repository.get_product_unit_details(sku)


    def create_purchasing_id(self) -> str:
        return self.repository.create_purchasing_id()


    def submit_purchasing(self, purchasing: PurchasingModel, detail_purchasing: List[DetailPurchasingModel]) -> ResponseMessage:
        if not self.permission_manager.has_permission(PERM_C_PURCHASING):
            return ResponseMessage.fail(message=ERR_PERM_C_PURCHASING)
        
        return self.repository.submit_purchasing(purchasing, detail_purchasing)


    def update_purchasing(self, purchasing: PurchasingModel, 
                          added_detail_purchasing: List[DetailPurchasingModel], 
                          updated_detail_purchasing: List[DetailPurchasingModel], 
                          deleted_detail_purchasing: List[DetailPurchasingModel]) -> ResponseMessage:
        if not self.permission_manager.has_permission(PERM_U_PURCHASING):
            return ResponseMessage.fail(message=ERR_PERM_U_PURCHASING)
        
        return self.repository.update_purchasing(purchasing, added_detail_purchasing, 
                                                 updated_detail_purchasing, 
                                                 deleted_detail_purchasing)


    def get_purchasing_history_by_sku(self, sku: str):
        return self.repository.get_purchasing_history_by_sku(sku)


    def get_detail_purchasing_by_id(self, purchasing_id: str):
        return self.repository.get_detail_purchasing_by_id(purchasing_id)


    def get_purchasing_by_id(self, purchasing_id: str):
        return self.repository.get_purchasing_by_id(purchasing_id)


    def get_supplier_by_id(self, supplier_id: str):
        return self.repository.get_supplier_by_id(supplier_id)
