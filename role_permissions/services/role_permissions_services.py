from ..repositories.role_permissions_repositories import RolePermissionsRepository
from ..models.role_permissions_models import RolesModel

class RolePermissionsService:
    def __init__(self):
        self.repository = RolePermissionsRepository()


    def get_roles(self, search_text: str = None):
        return self.repository.get_roles(search_text)


    def get_permissions(self):
        return self.repository.get_permissions()


    def get_permissions_by_role_id(self, role_id: int):
        return self.repository.get_permissions_by_role_id(role_id)
    

    def submit_role_permissions(self, roles_form_data: RolesModel, selected_permissions: set[str]):
        return self.repository.submit_role_permissions(roles_form_data, selected_permissions)


    def update_role_permissions(self, roles_form_data: RolesModel, added_permissions: set[str], deleted_permissions: set[str]):
        return self.repository.update_role_permissions(roles_form_data, added_permissions, deleted_permissions)


    def delete_role_permissions_by_role_id(self, role_id: int):
        return self.repository.delete_role_permissions_by_role_id(role_id)

