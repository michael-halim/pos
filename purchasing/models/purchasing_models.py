from dataclasses import dataclass
from datetime import datetime


@dataclass
class PurchasingTableItemModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    unit_value: int
    discount_rp: int
    discount_pct: int
    subtotal: int


@dataclass
class PurchasingModel:
    purchasing_id: str
    supplier_id: str
    invoice_date: datetime
    invoice_number: str
    invoice_expired_date: datetime
    created_at: datetime
    purchasing_remarks: str
    total_amount: int


@dataclass
class DetailPurchasingModel:
    purchasing_id: str
    sku: str
    price: int
    qty: int
    unit: str
    unit_value: int
    discount_rp: int
    discount_pct: int
    subtotal: int


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
class PurchasingHistoryTableItemModel:
    created_at: datetime
    supplier_name: str
    qty: int
    unit: str
    price: int
    discount_rp: int
    discount_pct: int
    subtotal: int
