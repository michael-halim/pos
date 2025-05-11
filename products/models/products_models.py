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


@dataclass
class ProductsExportModel:
    sku: str
    product_name: str
    barcode: str
    unit: str
    cost_price: int
    price: int
    stock: int
    remarks: str
    