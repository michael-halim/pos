from typing import List, Optional
from ..repositories.role_permissions_repositories import RolePermissionsRepository

class RolePermissionsService:
    def __init__(self):
        self.repository = RolePermissionsRepository()
