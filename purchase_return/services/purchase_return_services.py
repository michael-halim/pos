from typing import List, Optional
from purchase_return.repositories.purchase_return_repositories import PurchaseReturnRepository
from generals.permission_manager import PermissionManager


class PurchaseReturnService:
    def __init__(self):
        self.repository = PurchaseReturnRepository()
        self.permission_manager = PermissionManager()
