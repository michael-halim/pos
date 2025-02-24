from dataclasses import dataclass

@dataclass
class ProductsModel:
    sku: str
    product_name: str
    cost_price: int
    price: int
    stock: int
    unit: str
    remarks: str

