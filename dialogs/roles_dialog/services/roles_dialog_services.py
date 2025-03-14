from dialogs.roles_dialog.repositories.roles_dialog_repositories import RolesDialogRepository

from response.response_message import ResponseMessage
from generals.messages import ERR_PERM_R_ROLES
from generals.constants import PERM_R_ROLES
from generals.permission_manager import PermissionManager

class RolesDialogService:
    def __init__(self):
        self.repository = RolesDialogRepository()
        self.permission_manager = PermissionManager()


    def get_roles(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_ROLES):
            return ResponseMessage.fail(message=ERR_PERM_R_ROLES)

        return self.repository.get_roles(search_text)


    def get_permissions(self):
        if not self.permission_manager.has_permission(PERM_R_ROLES):
            return ResponseMessage(success=False, message=ERR_PERM_R_ROLES)

        return self.repository.get_permissions()


    def get_permissions_by_role_id(self, role_id: int):
        if not self.permission_manager.has_permission(PERM_R_ROLES):
            return ResponseMessage(success=False, message=ERR_PERM_R_ROLES)

        return self.repository.get_permissions_by_role_id(role_id)