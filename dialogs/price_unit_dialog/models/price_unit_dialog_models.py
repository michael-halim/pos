from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductInPriceUnitModel:
    product_name: str
    barcode: str
    unit: str
    price: int

@dataclass
class PriceUnitTableItemModel:
    unit: str
    barcode: str
    unit_value: int
    price: int


@dataclass
class PriceUnitsModel:
    sku: str
    unit: str
    barcode: str
    unit_value: int
    price: int


