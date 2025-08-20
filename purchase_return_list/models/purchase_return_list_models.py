from dataclasses import dataclass
from typing import Optional

@dataclass
class PurchaseReturnListModel:
    id: int
    name: str
    description: Optional[str] = None
