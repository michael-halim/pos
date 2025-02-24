from typing import List, Optional
from ..repositories.products_dialog_repositories import ProductsDialogRepository
from ..models.products_dialog_models import ProductsDialogModel

class ProductsDialogService:
    def __init__(self):
        self.repository = ProductsDialogRepository()


    def get_products(self, search_text: str = None):
        return self.repository.get_products(search_text)

