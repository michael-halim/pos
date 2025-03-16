from dataclasses import dataclass

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
