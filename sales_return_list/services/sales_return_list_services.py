from typing import List, Optional
from sales_return_list.repositories.sales_return_list_repositories import SalesReturnListRepository
from generals.permission_manager import PermissionManager


class SalesReturnListService:
    def __init__(self):
        self.repository = SalesReturnListRepository()
        self.permission_manager = PermissionManager()
