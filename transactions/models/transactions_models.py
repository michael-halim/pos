from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class ProductModel:
    product_name: str
    price: int
    unit: str
    stock: int
    

@dataclass
class ProductUnitDetailModel:
    unit: str
    unit_value: int
    price: int


@dataclass
class DetailTransactionModel:
    transaction_id: str
    sku: str
    unit: str
    unit_value: int
    qty: int
    price: int
    discount: int
    subtotal: int


@dataclass
class TransactionModel:
    transaction_id: str
    total_amount: int
    payment_method: str
    payment_amount: int
    payment_change: int
    payment_remarks: str
    created_at: datetime


@dataclass 
class PendingTransactionModel:
    transaction_id: str
    total_amount: int
    discount_transaction_id: str
    discount_amount: int
    created_at: datetime
    payment_remarks: str


@dataclass
class TransactionTableItemModel:
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    unit_value: int
    discount: int
    subtotal: int