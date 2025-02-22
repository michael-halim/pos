from dataclasses import dataclass
from typing import Optional

@dataclass
class LogsModel:
    id: int
    name: str
    description: Optional[str] = None
