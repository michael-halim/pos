from ..repositories.roles_dialog_repositories import RolesDialogRepository

class RolesDialogService:
    def __init__(self):
        self.repository = RolesDialogRepository()


    def get_roles(self, search_text: str = None):
        return self.repository.get_roles(search_text)


    def get_permissions(self):
        return self.repository.get_permissions()


    def get_permissions_by_role_id(self, role_id: int):
        return self.repository.get_permissions_by_role_id(role_id)