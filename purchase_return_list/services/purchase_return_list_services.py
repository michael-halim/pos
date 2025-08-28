from datetime import datetime

from purchase_return_list.repositories.purchase_return_list_repositories import PurchaseReturnListRepository

from response.response_message import ResponseMessage
from generals.constants import PERM_D_PURCHASE_RETURN
from generals.messages import ERR_PERM_D_PURCHASE_RETURN
from generals.permission_manager import PermissionManager


class PurchaseReturnListService:
    def __init__(self):
        self.repository = PurchaseReturnListRepository()
        self.permission_manager = PermissionManager()


    def get_purchase_return_list(self, start_date: datetime, end_date: datetime, search_text: str = None):
        return self.repository.get_purchase_return_list(start_date, end_date, search_text)


    def get_detail_purchase_return_by_id(self, purchase_return_id: str):
        return self.repository.get_detail_purchase_return_by_id(purchase_return_id)


    def delete_purchase_return_by_id(self, purchase_return_id: str):
        if not self.permission_manager.has_permission(PERM_D_PURCHASE_RETURN):
            return ResponseMessage.fail(message=ERR_PERM_D_PURCHASE_RETURN)
        
        return self.repository.delete_purchase_return_by_id(purchase_return_id)