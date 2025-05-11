from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProductModel:
    product_name: str
    price: int
    unit: str
    stock: int


@dataclass
class SalesPerItemReportModel:
    transaction_id: str
    created_at: datetime
    username: str
    qty: int
    unit: str
    price: int
    unit_value: int
    discount_pct: int
    discount_rp_per_item: int
    discount_rp: int
    sub_total: int