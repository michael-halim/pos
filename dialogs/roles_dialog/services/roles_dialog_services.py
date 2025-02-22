from typing import List, Optional
from ..repositories.roles_dialog_repositories import RolesDialogRepository

class RolesService:
    def __init__(self):
        self.repository = RolesDialogRepository()
