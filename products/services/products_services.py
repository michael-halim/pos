from products.repositories.products_repositories import ProductsRepository

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_PRODUCTS, PERM_D_PRODUCTS
from generals.messages import ERR_PERM_R_PRODUCTS, ERR_PERM_D_PRODUCTS

from response.response_message import ResponseMessage

class ProductsService:
    def __init__(self):
        self.repository = ProductsRepository()
        self.permission_manager = PermissionManager()


    def get_products(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_R_PRODUCTS)
        
        return self.repository.get_products(search_text)


    def delete_products_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_D_PRODUCTS)
        
        return self.repository.delete_products_by_sku(sku)
