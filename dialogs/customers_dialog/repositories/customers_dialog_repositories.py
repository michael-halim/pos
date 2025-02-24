from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection

from dialogs.customers_dialog.models.customers_dialog_models import CustomersDialogModel
from response.response_message import ResponseMessage

class CustomersDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        
    def get_customers(self, search_text: str = None):
        try:
            customers_result = []
            if search_text:
                sql = '''SELECT customer_id, customer_name, customer_phone, customer_points, number_of_transactions, transaction_value 
                            FROM customers
                            WHERE customer_id LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR 
                                    customer_points LIKE ? OR number_of_transactions LIKE ? OR transaction_value LIKE ?'''
                
                search_text = f'%{search_text}%'
                customers_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, search_text, search_text))
            else:
                sql = '''SELECT customer_id, customer_name, customer_phone, customer_points, number_of_transactions, transaction_value 
                            FROM customers'''
                customers_result = self.cursor.execute(sql)

            customers = [
                CustomersDialogModel(customer_id=r[0], customer_name=r[1], customer_phone=r[2], 
                               customer_points=r[3], number_of_transactions=r[4], 
                               transaction_value=r[5]) 
                for r in customers_result
            ]

            return ResponseMessage.ok(
                message="Customers fetched successfully!",
                data=customers
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
