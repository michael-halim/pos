from users.repositories.users_repositories import UsersRepository
from users.models.users_models import UsersFormModel

class UsersService:
    def __init__(self):
        self.repository = UsersRepository()


    def get_users(self, search_text: str = None):
        return self.repository.get_users(search_text)


    def get_user_by_id(self, user_id: int):
        return self.repository.get_user_by_id(user_id)


    def set_user_status(self, user_id: int, status: bool):
        return self.repository.set_user_status(user_id, status)


    def submit_user(self, user_data: UsersFormModel):
        return self.repository.submit_user(user_data)


    def update_user(self, user_data: UsersFormModel):
        return self.repository.update_user(user_data)


    def delete_user(self, user_id: int):
        return self.repository.delete_user(user_id)


    def get_role_by_id(self, role_id: int):
        return self.repository.get_role_by_id(role_id)


    def change_password(self, user_id: int, old_password: str, new_password: str):
        return self.repository.change_password(user_id, old_password, new_password)
