from dataclasses import dataclass
from typing import Optional

@dataclass
class RolesModel:
    role_id: int
    role_name: str
    role_description: str


@dataclass
class PermissionsModel:
    permission_id: str
    permission_name: str