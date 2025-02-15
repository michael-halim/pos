from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class TransactionListModel:
    created_at: datetime
    transaction_id: str
    payment_rp: int
    payment_method: str
    payment_remarks: str

@dataclass
class DetailTransactionListModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    discount_rp: int
    discount_pct: int
    subtotal: int