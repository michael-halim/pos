from dataclasses import dataclass
from typing import Optional

@dataclass
class SuppliersModel:
    supplier_id: int
    supplier_name: str
    supplier_address: str
    supplier_phone: str
    supplier_city: str
    supplier_remarks: str