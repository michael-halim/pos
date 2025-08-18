from connect_db import DatabaseConnection
from typing import List
from response.response_message import ResponseMessage
from purchase_return.models.purchase_return_models import PurchaseReturnModel
from generals.permission_manager import PermissionManager

class PurchaseReturnRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        
