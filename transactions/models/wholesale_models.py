from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class WholesaleTableModel:
    unit: str
    unit_value: int
    price: int