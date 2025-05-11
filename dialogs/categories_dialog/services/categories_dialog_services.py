from dialogs.categories_dialog.repositories.categories_dialog_repositories import CategoriesDialogRepository

from generals.constants import PERM_R_CATEGORIES
from response.response_message import ResponseMessage
from generals.messages import ERR_PERM_R_CATEGORIES
from generals.permission_manager import PermissionManager


class CategoriesDialogService:
    def __init__(self):
        self.repository = CategoriesDialogRepository()
        self.permission_manager = PermissionManager()


    def get_categories(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_CATEGORIES):
                return ResponseMessage.fail(message=ERR_PERM_R_CATEGORIES)

        return self.repository.get_categories(search_text)
