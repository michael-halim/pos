from users.repositories.users_repositories import UsersRepository
from users.models.users_models import UsersFormModel

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_USERS, PERM_C_USERS, PERM_U_USERS, PERM_D_USERS
from generals.messages import ERR_PERM_R_USERS, ERR_PERM_C_USERS, ERR_PERM_U_USERS, ERR_PERM_D_USERS

from response.response_message import ResponseMessage


class UsersService:
    def __init__(self):
        self.repository = UsersRepository()
        self.permission_manager = PermissionManager()


    def get_users(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return ResponseMessage.fail(message=ERR_PERM_R_USERS)

        return self.repository.get_users(search_text)


    def get_user_by_id(self, user_id: int):
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return ResponseMessage.fail(message=ERR_PERM_R_USERS)

        return self.repository.get_user_by_id(user_id)


    def set_user_status(self, user_id: int, status: bool):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            return ResponseMessage.fail(message=ERR_PERM_U_USERS)

        return self.repository.set_user_status(user_id, status)


    def submit_user(self, user_data: UsersFormModel):
        if not self.permission_manager.has_permission(PERM_C_USERS):
            return ResponseMessage.fail(message=ERR_PERM_C_USERS)

        if user_data.username.strip() == '':
            return ResponseMessage.fail(message="Username cannot be empty")
        
        if user_data.password.strip() == '':
            return ResponseMessage.fail(message="Password cannot be empty")

        if user_data.role_id.strip() == '':
            return ResponseMessage.fail(message="Role id cannot be empty")

        return self.repository.submit_user(user_data)


    def update_user(self, user_data: UsersFormModel):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            return ResponseMessage.fail(message=ERR_PERM_U_USERS)

        return self.repository.update_user(user_data)


    def delete_user(self, user_id: int):
        if not self.permission_manager.has_permission(PERM_D_USERS):
            return ResponseMessage.fail(message=ERR_PERM_D_USERS)

        return self.repository.delete_user(user_id)


    def get_role_by_id(self, role_id: int):
        if not self.permission_manager.has_permission(PERM_R_USERS):
            return ResponseMessage.fail(message=ERR_PERM_R_USERS)

        return self.repository.get_role_by_id(role_id)


    def change_password(self, user_id: int, old_password: str, new_password: str):
        if not self.permission_manager.has_permission(PERM_U_USERS):
            return ResponseMessage.fail(message=ERR_PERM_U_USERS)

        return self.repository.change_password(user_id, old_password, new_password)
