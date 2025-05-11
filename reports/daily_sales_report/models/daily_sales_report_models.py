from dataclasses import dataclass
from typing import Optional

@dataclass
class DailySalesReportModel:
    created_at: str
    total_sales: float
    payment_method: str
    created_by: str
