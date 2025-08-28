from dataclasses import dataclass
from datetime import datetime


@dataclass
class SalesReturnListModel:
    created_at: datetime
    sales_return_id: str
    customer_name: str
    total_amount: int
    remarks: str


@dataclass
class DetailSalesReturnListModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    subtotal: int
