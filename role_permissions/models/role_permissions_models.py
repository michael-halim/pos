from dataclasses import dataclass
from typing import Optional

@dataclass
class RolePermissionsModel:
    id: int
    name: str
    description: Optional[str] = None
