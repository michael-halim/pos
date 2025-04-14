from dataclasses import dataclass
from typing import Optional

@dataclass
class ProfitAndLossReportModel:
    id: int
    name: str
    description: Optional[str] = None
