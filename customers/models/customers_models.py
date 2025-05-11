from dataclasses import dataclass
from typing import Optional

@dataclass
class CustomersModel:
    customer_id: int
    customer_name: str
    customer_phone: str
    customer_points: int
    number_of_transactions: int
    transaction_value: int
