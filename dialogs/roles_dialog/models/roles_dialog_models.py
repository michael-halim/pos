from dataclasses import dataclass
from typing import Optional

@dataclass
class RolesModel:
    id: int
    name: str
    description: Optional[str] = None
