from typing import List, Optional
from ..repositories.products_repositories import ProductsRepository

class ProductsService:
    def __init__(self):
        self.repository = ProductsRepository()


    def get_products(self, search_text: str = None):
        return self.repository.get_products(search_text)


    def delete_products_by_sku(self, sku: str):
        return self.repository.delete_products_by_sku(sku)
