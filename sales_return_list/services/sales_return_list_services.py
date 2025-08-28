from sales_return_list.repositories.sales_return_list_repositories import SalesReturnListRepository
from generals.permission_manager import PermissionManager
from datetime import datetime
from response.response_message import ResponseMessage
from generals.constants import PERM_D_SALES_RETURN
from generals.messages import ERR_PERM_D_SALES_RETURN


class SalesReturnListService:
    def __init__(self):
        self.repository = SalesReturnListRepository()
        self.permission_manager = PermissionManager()


    def get_sales_return_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        return self.repository.get_sales_return_list(start_date, end_date, search_text)


    def get_detail_sales_return_by_id(self, sales_return_id: str):
        return self.repository.get_detail_sales_return_by_id(sales_return_id)


    def delete_sales_return_by_id(self, sales_return_id: str):
        if not self.permission_manager.has_permission(PERM_D_SALES_RETURN):
            return ResponseMessage.fail(message=ERR_PERM_D_SALES_RETURN)
        
        return self.repository.delete_sales_return_by_id(sales_return_id)