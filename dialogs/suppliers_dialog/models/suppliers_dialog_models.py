from dataclasses import dataclass

@dataclass
class SupplierModel:
    supplier_id: str
    supplier_name: str
    supplier_address: str
    supplier_city: str
    supplier_phone: str
    supplier_remarks: str
