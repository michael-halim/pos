from dataclasses import dataclass
from datetime import date, time


@dataclass
class ProductStockCardListModel:
    sku: str
    product_name: str
    current_stock: int
    unit: str


@dataclass
class StockCardListModel:
    date: date
    time: time
    transaction_id: str
    stock_in: int
    stock_out: int
    running_balance: int
    remarks: str
