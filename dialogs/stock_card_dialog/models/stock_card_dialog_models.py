from dataclasses import dataclass
from datetime import date, time

@dataclass
class StockCardTableItemModel:
    date: date
    time: time
    transaction_id: str
    stock_in: int
    stock_out: int
    running_balance: int
    remarks: str
