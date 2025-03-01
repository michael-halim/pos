from connect_db import DatabaseConnection
from response.response_message import ResponseMessage

class ImportProductsDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
