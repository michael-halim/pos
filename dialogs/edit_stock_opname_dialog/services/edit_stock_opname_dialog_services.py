from dialogs.edit_stock_opname_dialog.repositories.edit_stock_opname_dialog_repositories import EditStockOpnameDialogRepository

from generals.permission_manager import PermissionManager
from generals.constants import PERM_U_STOCK_OPNAME
from generals.messages import ERR_PERM_U_STOCK_OPNAME
from response.response_message import ResponseMessage


class EditStockOpnameDialogService:
    def __init__(self):
        self.repository = EditStockOpnameDialogRepository()
        self.permission_manager = PermissionManager()


    def edit_stock_opname(self, stock_opname_id: str, final_stock: str):
        if not self.permission_manager.has_permission(PERM_U_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_U_STOCK_OPNAME)
        
        return self.repository.edit_stock_opname(stock_opname_id, final_stock)

