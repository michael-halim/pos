from connect_db import DatabaseConnection

from dialogs.products_dialog.models.products_dialog_models import ProductsDialogModel   

from response.response_message import ResponseMessage

class ProductsDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        
    def get_products(self, search_text: str = None, limit: int = 100):
        try:
            products_result = []
            if search_text:
                sql = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, p.created_at 
                            FROM products p 
                            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit  
                            WHERE p.sku LIKE ? OR p.product_name LIKE ? OR p.unit LIKE ?'''
                
                search_text = f'%{search_text}%'
                products_result = self.cursor.execute(sql, (search_text, search_text, search_text))

            elif limit:
                sql = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, p.created_at 
                            FROM products p 
                            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit
                            ORDER BY p.sku
                            LIMIT ?'''

                products_result = self.cursor.execute(sql, (limit,))

            else:
                sql = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, p.created_at 
                            FROM products p 
                            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit
                            ORDER BY p.sku
                            LIMIT 100'''
                
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