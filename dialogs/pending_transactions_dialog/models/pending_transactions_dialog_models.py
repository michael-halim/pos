from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass 
class PendingTransactionModel:
    transaction_id: str
    customer_id: str | None
    total_amount: int
    discount_transaction_id: str
    discount_amount: int
    created_at: datetime
    payment_remarks: str


@dataclass
class PendingDetailTransactionModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    discount_pct: int
    discount_rp_per_item: int
    discount_rp: int
    subtotal: int

