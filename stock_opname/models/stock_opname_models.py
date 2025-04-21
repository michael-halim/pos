from dataclasses import dataclass
from typing import Optional

@dataclass
class StockOpnameModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    

@dataclass
class EditStockOpnameModel:
    sku: str
    product_name: str
    price: int
    original_stock: int
    final_stock: int
