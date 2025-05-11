from dataclasses import dataclass
from typing import Optional

@dataclass
class ImportProductsModel:
    sku: str
    product_name: str
    barcode: str
    unit: str
    cost_price: int
    price: int
    stock: int
    remarks: str
    category: Optional[str] = None
    supplier: Optional[str] = None
