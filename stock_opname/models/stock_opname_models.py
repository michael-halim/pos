from dataclasses import dataclass
from typing import Optional

@dataclass
class StockOpnameModel:
    sku: str
    product_name: str
    qty: int
    unit: str
    