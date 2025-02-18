from typing import List
from ..repositories.purchasing_repositories import PurchasingRepository
from ..models.purchasing_models import PurchasingModel, DetailPurchasingModel

from response.response_message import ResponseMessage
class PurchasingService:
    def __init__(self):
        self.repository = PurchasingRepository()
        
    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)


    def get_product_unit_details(self, sku: str):
        return self.repository.get_product_unit_details(sku)


    def create_purchasing_id(self) -> str:
        return self.repository.create_purchasing_id()


    def submit_purchasing(self, purchasing: PurchasingModel, detail_purchasing: List[DetailPurchasingModel]) -> ResponseMessage:
        return self.repository.submit_purchasing(purchasing, detail_purchasing)


    def get_supplier_by_id(self, supplier_id: str):
        return self.repository.get_supplier_by_id(supplier_id)


    def get_purchasing_history_by_sku(self, sku: str):
        return self.repository.get_purchasing_history_by_sku(sku)

