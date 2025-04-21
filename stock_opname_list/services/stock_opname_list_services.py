from datetime import datetime

from stock_opname_list.repositories.stock_opname_list_repositories import StockOpnameListRepository

from generals.constants import PERM_R_STOCK_OPNAME, PERM_D_STOCK_OPNAME
from generals.messages import ERR_PERM_R_STOCK_OPNAME, ERR_PERM_D_STOCK_OPNAME
from generals.permission_manager import PermissionManager
from response.response_message import ResponseMessage


class StockOpnameListService:
    def __init__(self):
        self.repository = StockOpnameListRepository()
        self.permission_manager = PermissionManager()


    def get_stock_opname_list(self, start_date: datetime, end_date: datetime, search_text: str):
        if not self.permission_manager.has_permission(PERM_R_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_R_STOCK_OPNAME)
        
        return self.repository.get_stock_opname_list(start_date, end_date, search_text)


    def delete_stock_opname_by_id(self, stock_opname_id: str):
        if not self.permission_manager.has_permission(PERM_D_STOCK_OPNAME):
            return ResponseMessage.fail(message=ERR_PERM_D_STOCK_OPNAME)
        
        return self.repository.delete_stock_opname_by_id(stock_opname_id)

