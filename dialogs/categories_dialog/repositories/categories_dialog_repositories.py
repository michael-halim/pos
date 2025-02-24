from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection
from dialogs.categories_dialog.models.categories_dialog_models import CategoriesDialogModel
from response.response_message import ResponseMessage

class CategoriesDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def get_categories(self, search_text: str = None):
        try:
            categories_result = []
            if search_text:
                sql = '''SELECT c.category_id, c.category_name
                            FROM categories c 
                            WHERE c.category_id LIKE ? OR c.category_name LIKE ? '''

                search_text = f'%{search_text}%'
                categories_result = self.cursor.execute(sql, (search_text, search_text))

            else:
                sql = '''SELECT c.category_id, c.category_name 
                            FROM categories c'''
                
                categories_result = self.cursor.execute(sql)

            categories = [
                CategoriesDialogModel(category_id=c[0], category_name=c[1]) 
                for c in categories_result
            ]

            return ResponseMessage.ok(
                message="Categories fetched successfully!",
                data=categories
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
