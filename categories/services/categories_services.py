from ..repositories.categories_repositories import CategoriesRepository
from ..models.categories_models import CategoriesTableModel


class CategoriesService:
    def __init__(self):
        self.repository = CategoriesRepository()


    def get_categories(self, search_text: str = None):
        return self.repository.get_categories(search_text)


    def get_products(self, search_text: str = None):
        return self.repository.get_products(search_text)

    
    def get_selected_products_by_category_id(self, category_id: int):
        return self.repository.get_selected_products_by_category_id(category_id)


    def get_category_by_id(self, category_id: int):
        return self.repository.get_category_by_id(category_id)


    def submit_category(self, data: CategoriesTableModel, products: set[str]):
        return self.repository.submit_category(data, products)
    

    def update_category(self, data: CategoriesTableModel, added_products: set[str], deleted_products: set[str]):
        return self.repository.update_category(data, added_products, deleted_products)
    

    def delete_category_by_id(self, category_id: int):
        return self.repository.delete_category_by_id(category_id)
