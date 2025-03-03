from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class UsersTableItemModel:
    user_id: str
    username: str
    role_id: str
    role_name: str
    is_active: bool
    created_at: datetime


@dataclass
class UsersFormModel:
    user_id: str
    username: str
    password: str
    role_id: str
    role_name: str


@dataclass
class RolesModel:
    role_id: str
    role_name: str

