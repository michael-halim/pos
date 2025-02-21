from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class MasterStockModel:
    sku: str
    product_name: str
    barcode: str
    category_id: str
    supplier_id: str
    unit: str
    price: int
    stock: int
    remarks: str
    category_name: str
    supplier_name: str
    last_price: int
    average_price: int

@dataclass
class PurchasingHistoryTableItemModel:
    created_at: datetime
    supplier_name: str
    qty: int
    unit: str
    price: int
    discount_rp: int
    discount_pct: int
    subtotal: int
