from dataclasses import dataclass
from typing import Optional

@dataclass
class CashierSalesReportModel:
    id: int
    name: str
    description: Optional[str] = None
