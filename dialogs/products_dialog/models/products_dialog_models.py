from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProductsDialogModel:
    sku: str
    product_name: str
    price: float
    stock: int
    unit: str
    created_at: datetime
