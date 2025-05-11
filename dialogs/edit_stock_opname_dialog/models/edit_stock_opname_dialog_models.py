from dataclasses import dataclass
from typing import Optional

@dataclass
class EditStockOpnameDialogModel:
    id: int
    name: str
    description: Optional[str] = None
