from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PurchaseReturnModel:
    id: int
    name: str
    description: Optional[str] = None


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


@dataclass
class PurchaseReturnModel:
    purchase_return_id: str
    supplier_id: str
    purchase_return_date: datetime
    total_amount: int
    created_at: datetime
    created_by: int
    purchase_return_remarks: str
    updated_at: datetime
    updated_by: int

@dataclass
class DetailPurchaseReturnModel:
    purchase_return_id: str
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    unit_value: int
    subtotal: int
