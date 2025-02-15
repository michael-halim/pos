from typing import List, Optional
from ..purchasing_repositories.purchasing_repositories import PurchasingRepository

class PurchasingService:
    def __init__(self):
        self.repository = PurchasingRepository()
        
    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)
    
    def get_product_unit_details(self, sku: str):
        return self.repository.get_product_unit_details(sku)
