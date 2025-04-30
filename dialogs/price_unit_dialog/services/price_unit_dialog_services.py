from dialogs.price_unit_dialog.repositories.price_unit_dialog_repositories import PriceUnitDialogRepository
from dialogs.price_unit_dialog.models.price_unit_dialog_models import PriceUnitTableItemModel, PriceUnitsModel

from response.response_message import ResponseMessage
from generals.constants import (
    PERM_C_PRODUCTS, PERM_R_PRODUCTS, PERM_U_PRODUCTS, PERM_D_PRODUCTS
)
from generals.messages import (
    ERR_PERM_C_PRODUCTS, ERR_PERM_R_PRODUCTS, ERR_PERM_U_PRODUCTS, ERR_PERM_D_PRODUCTS
)
from generals.permission_manager import PermissionManager


class PriceUnitDialogService:
    def __init__(self):
        self.repository = PriceUnitDialogRepository()
        self.permission_manager = PermissionManager()


    def get_product_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_R_PRODUCTS)
        
        return self.repository.get_product_by_sku(sku)
   

    def get_product_units_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_R_PRODUCTS)
        
        return self.repository.get_product_units_by_sku(sku)


    def submit_price_unit(self, price_unit_data: PriceUnitTableItemModel):
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_C_PRODUCTS)
        
        if int(price_unit_data.unit_value) <= 1:
            return ResponseMessage.fail(message='Unit value cannot be 1 or lower than 1')
        
        return self.repository.submit_price_unit(price_unit_data)


    def update_price_unit(self, price_unit_data: PriceUnitsModel):
        if not self.permission_manager.has_permission(PERM_U_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_U_PRODUCTS)
        
        return self.repository.update_price_unit(price_unit_data)


    def delete_price_unit_by_sku_and_unit(self, sku: str, unit: str):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_D_PRODUCTS)
        
        return self.repository.delete_price_unit_by_sku_and_unit(sku, unit)


