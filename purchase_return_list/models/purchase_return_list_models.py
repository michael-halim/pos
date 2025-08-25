from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class PurchaseReturnListModel:
    created_at: datetime
    purchase_return_id: str
    supplier_name: str
    total_amount: int
    remarks: str


@dataclass
class DetailPurchaseReturnListModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    subtotal: int
