from connect_db import DatabaseConnection
from typing import List
from response.response_message import ResponseMessage
from sales_return_list.models.sales_return_list_models import SalesReturnListModel
from generals.permission_manager import PermissionManager

class SalesReturnListRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        
