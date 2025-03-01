from dataclasses import dataclass
from typing import Optional

@dataclass
class ImportProductsDialogModel:
    id: int
    name: str
    description: Optional[str] = None
