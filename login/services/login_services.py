from typing import List, Optional
from login.repositories.login_repositories import LoginRepository
from generals.permission_manager import PermissionManager

class LoginService:
    def __init__(self):
        self.repository = LoginRepository()
        self.permission_manager = PermissionManager()


    def login(self, username: str, password: str):
        result = self.repository.login(username, password)
        if result.success:
            self.permission_manager.set_username(username)
            self.permission_manager.set_permissions(result.data)

        return result
