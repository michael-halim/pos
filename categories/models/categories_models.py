from dataclasses import dataclass
from datetime import datetime

@dataclass
class CategoriesTableModel:
    category_id: int
    category_name: str


@dataclass
class ProcuctsTableModel:
    sku: str
    product_name: str
    price: float
    stock: int
    unit: str
    created_at: datetime
