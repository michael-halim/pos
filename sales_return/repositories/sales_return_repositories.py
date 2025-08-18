from connect_db import DatabaseConnection
from typing import List
from response.response_message import ResponseMessage
from sales_return.models.sales_return_models import SalesReturnModel
from generals.permission_manager import PermissionManager

class SalesReturnRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        
