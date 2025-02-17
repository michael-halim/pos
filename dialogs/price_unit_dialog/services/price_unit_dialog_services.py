from typing import List, Optional
from ..repositories.price_unit_dialog_repositories import PriceUnitDialogRepository
from ..models.price_unit_dialog_models import PriceUnitTableItemModel

class PriceUnitDialogService:
    def __init__(self):
        self.repository = PriceUnitDialogRepository()
        
    def get_product_by_sku(self, sku: str):
        return self.repository.get_product_by_sku(sku)
   

    def get_product_units_by_sku(self, sku: str):
        return self.repository.get_product_units_by_sku(sku)


    def submit_price_unit(self, price_unit_data: PriceUnitTableItemModel):
        return self.repository.submit_price_unit(price_unit_data)


    def update_price_unit(self, price_unit_data: PriceUnitTableItemModel):
        return self.repository.update_price_unit(price_unit_data)


    def delete_price_unit_by_sku_and_unit(self, sku: str, unit: str):
        return self.repository.delete_price_unit_by_sku_and_unit(sku, unit)


