from dataclasses import dataclass
from datetime import datetime


@dataclass
class PurchasingListModel:
    created_at: datetime
    purchasing_id: str
    supplier_name: str
    total_amount: int
    remarks: str


@dataclass
class DetailPurchasingModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    discount_pct: int
    discount_rp: int
    subtotal: int