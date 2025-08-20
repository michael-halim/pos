from dataclasses import dataclass
from typing import Optional

@dataclass
class SalesReturnListModel:
    id: int
    name: str
    description: Optional[str] = None
