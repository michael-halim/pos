from dataclasses import dataclass
from typing import Optional

@dataclass
class PurchaseReturnModel:
    id: int
    name: str
    description: Optional[str] = None
