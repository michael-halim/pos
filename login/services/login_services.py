from typing import List, Optional
from login.repositories.login_repositories import LoginRepository

class LoginService:
    def __init__(self):
        self.repository = LoginRepository()


    def login(self, username: str, password: str):
        return self.repository.login(username, password)

