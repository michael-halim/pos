from dataclasses import dataclass

@dataclass
class RolesModel:
    role_id: int
    role_name: str
    role_description: str


@dataclass
class PermissionsModel:
    permission_id: str
    permission_name: str


@dataclass
class RolePermissionsModel:
    role_id: int
    permission_id: str
