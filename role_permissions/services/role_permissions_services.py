from role_permissions.repositories.role_permissions_repositories import RolePermissionsRepository
from role_permissions.models.role_permissions_models import RolesModel

from generals.permission_manager import PermissionManager
from generals.constants import PERM_U_PERMISSIONS,  PERM_R_PERMISSIONS, PERM_D_PERMISSIONS
from generals.messages import ERR_PERM_U_PERMISSIONS, ERR_PERM_D_PERMISSIONS, ERR_PERM_R_PERMISSIONS
from response.response_message import ResponseMessage


class RolePermissionsService:
    def __init__(self):
        self.repository = RolePermissionsRepository()
        self.permission_manager = PermissionManager()


    def get_roles(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PERMISSIONS)

        return self.repository.get_roles(search_text)


    def get_permissions(self):
        if not self.permission_manager.has_permission(PERM_R_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PERMISSIONS)

        return self.repository.get_permissions()


    def get_permissions_by_role_id(self, role_id: int):
        if not self.permission_manager.has_permission(PERM_R_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_R_PERMISSIONS)

        return self.repository.get_permissions_by_role_id(role_id)
    

    def submit_role_permissions(self, roles_form_data: RolesModel, selected_permissions: set[str]):
        if not self.permission_manager.has_permission(PERM_U_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_U_PERMISSIONS)

        return self.repository.submit_role_permissions(roles_form_data, selected_permissions)


    def update_role_permissions(self, roles_form_data: RolesModel, added_permissions: set[str], deleted_permissions: set[str]):
        if not self.permission_manager.has_permission(PERM_U_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_U_PERMISSIONS)

        return self.repository.update_role_permissions(roles_form_data, added_permissions, deleted_permissions)


    def delete_role_permissions_by_role_id(self, role_id: int):
        if not self.permission_manager.has_permission(PERM_D_PERMISSIONS):
            return ResponseMessage.fail(message=ERR_PERM_D_PERMISSIONS)

        return self.repository.delete_role_permissions_by_role_id(role_id)

