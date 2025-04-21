from dataclasses import dataclass
from datetime import datetime


@dataclass
class StockOpnameListModel:
    stock_opname_id: str
    created_at: datetime
    sku: str
    product_name: str
    price: int
    original_stock: int
    opname_stock: int
    final_stock: int
