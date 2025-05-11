from dialogs.customers_dialog.repositories.customers_dialog_repositories import CustomersDialogRepository

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_CUSTOMERS
from generals.messages import ERR_PERM_R_CUSTOMERS
from response.response_message import ResponseMessage

class CustomersDialogService:
    def __init__(self):
        self.repository = CustomersDialogRepository()
        self.permission_manager = PermissionManager()



    def get_customers(self, search_text: str = None):
        if not self.permission_manager.has_permission(PERM_R_CUSTOMERS):
            return ResponseMessage.fail(message=ERR_PERM_R_CUSTOMERS)

        return self.repository.get_customers(search_text)
