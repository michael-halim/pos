from categories.repositories.categories_repositories import CategoriesRepository
from categories.models.categories_models import CategoriesTableModel

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_CATEGORIES, PERM_C_CATEGORIES, PERM_U_CATEGORIES, PERM_D_CATEGORIES
from generals.messages import ERR_PERM_R_CATEGORIES, ERR_PERM_C_CATEGORIES, ERR_PERM_U_CATEGORIES, ERR_PERM_D_CATEGORIES

from response.response_message import ResponseMessage

class CategoriesService:
    def __init__(self):
        self.repository = CategoriesRepository()
        self.permission_manager = PermissionManager()


    def get_categories(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_CATEGORIES):
            return ResponseMessage.fail(message=ERR_PERM_R_CATEGORIES)
        
        return self.repository.get_categories(search_text)


    def get_products(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_CATEGORIES):
            return ResponseMessage.fail(message=ERR_PERM_R_CATEGORIES)
        
        return self.repository.get_products(search_text)

    
    def get_selected_products_by_category_id(self, category_id: int):
        if not self.permission_manager.has_permission(PERM_R_CATEGORIES):
            return ResponseMessage.fail(message=ERR_PERM_R_CATEGORIES)
        
        return self.repository.get_selected_products_by_category_id(category_id)


    def get_category_by_id(self, category_id: int):
        if not self.permission_manager.has_permission(PERM_R_CATEGORIES):
            return ResponseMessage.fail(message=ERR_PERM_R_CATEGORIES)
        
        return self.repository.get_category_by_id(category_id)


    def submit_category(self, data: CategoriesTableModel, products: set[str]):
        if not self.permission_manager.has_permission(PERM_C_CATEGORIES):
            return ResponseMessage.fail(message=ERR_PERM_C_CATEGORIES)
        
        return self.repository.submit_category(data, products)
    

    def update_category(self, data: CategoriesTableModel, added_products: set[str], deleted_products: set[str]):
        if not self.permission_manager.has_permission(PERM_U_CATEGORIES):
            return ResponseMessage.fail(message=ERR_PERM_U_CATEGORIES)
        
        return self.repository.update_category(data, added_products, deleted_products)
    

    def delete_category_by_id(self, category_id: int):
        if not self.permission_manager.has_permission(PERM_D_CATEGORIES):
            return ResponseMessage.fail(message=ERR_PERM_D_CATEGORIES)
        
        return self.repository.delete_category_by_id(category_id)
