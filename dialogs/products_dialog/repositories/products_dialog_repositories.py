from typing import List, Optional
from datetime import datetime, timedelta
from connect_db import DatabaseConnection
from response.response_message import ResponseMessage
from dialogs.products_dialog.models.products_dialog_models import ProductsDialogModel   

class ProductsDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
    def get_products(self, search_text: str = None):
        try:
            products_result = []
            if search_text:
                sql = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, p.created_at 
                            FROM products p 
                            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit  
                            WHERE p.sku LIKE ? OR p.product_name LIKE ? OR p.unit LIKE ?'''
                
                search_text = f'%{search_text}%'
                products_result = self.cursor.execute(sql, (search_text, search_text, search_text))

            else:
                sql = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, p.created_at 
                            FROM products p 
                            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit '''
                
                products_result = self.cursor.execute(sql)

            products = [
                ProductsDialogModel(sku=p[0], product_name=p[1], price=p[2], 
                                    stock=p[3], unit=p[4], created_at=p[5]) 
                for p in products_result
            ]

            return ResponseMessage.ok(
                message="Products fetched successfully!",
                data=products
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")