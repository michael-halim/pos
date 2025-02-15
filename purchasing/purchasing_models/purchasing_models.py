from dataclasses import dataclass
from typing import Optional

@dataclass
class PurchasingTableItemModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    discount_rp: int
    discount_pct: int
    subtotal: int


@dataclass
class ProductModel:
    product_name: str
    price: int
    unit: str
    stock: int


@dataclass
class ProductUnitsModel:
    unit: str
    unit_value: int
