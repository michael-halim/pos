from typing import List, Optional
from sales_return.repositories.sales_return_repositories import SalesReturnRepository
from generals.permission_manager import PermissionManager


class SalesReturnService:
    def __init__(self):
        self.repository = SalesReturnRepository()
        self.permission_manager = PermissionManager()
