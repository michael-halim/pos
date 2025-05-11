from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MonthlySalesReportModel:
    created_at: datetime
    total_sales: int
    payment_method: str
    created_by: str
