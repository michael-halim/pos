from dataclasses import dataclass
from typing import Optional

@dataclass
class CustomersModel:
    id: int
    name: str
    description: Optional[str] = None
