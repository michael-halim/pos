from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProductModel:
    product_name: str
    price: int
    unit: str
    stock: int


@dataclass
class CustomerModel:
    customer_id: str
    customer_name: str


@dataclass
class ProductUnitsModel:
    unit: str
    unit_value: int


@dataclass
class SalesReturnModel:
    sales_return_id: str
    customer_id: str
    sales_return_date: datetime
    total_amount: int
    created_at: datetime
    created_by: int
    sales_return_remarks: str
    updated_at: datetime
    updated_by: int


@dataclass
class DetailSalesReturnModel:
    sales_return_id: str
    sku: str
    product_name: str
    price: int
    qty: int
    unit: str
    unit_value: int
    subtotal: int
