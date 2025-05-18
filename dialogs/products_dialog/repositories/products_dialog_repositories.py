from connect_db import DatabaseConnection

from dialogs.products_dialog.models.products_dialog_models import ProductsDialogModel   

from response.response_message import ResponseMessage


class ProductsDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        
        
    def get_products(self, search_text: str = None, limit: int = 100, offset: int = 25):
        try:
            total_count = 0
            products_result = []
            if search_text:
                search_text = f'%{search_text}%'

                total_count_sql = '''SELECT COUNT(*) 
                        FROM products p 
                        LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit  
                        WHERE p.sku LIKE ? OR p.product_name LIKE ? OR p.unit LIKE ?'''
                
                total_count = self.cursor.execute(total_count_sql, (search_text, search_text, search_text)).fetchone()[0]


                sql = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, p.created_at 
                            FROM products p 
                            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit  
                            WHERE p.sku LIKE ? OR p.product_name LIKE ? OR p.unit LIKE ?
                            ORDER BY p.sku
                            LIMIT ? OFFSET ?'''
                
                products_result = self.cursor.execute(sql, (search_text, search_text, search_text, limit, offset))

            else:
                total_count_sql = '''SELECT COUNT(*) 
                        FROM products p 
                        LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit'''
                
                total_count = self.cursor.execute(total_count_sql).fetchone()[0]


                sql = '''SELECT p.sku, p.product_name, p.price, p.stock, p.unit, p.created_at 
                            FROM products p 
                            LEFT JOIN units u ON p.sku = u.sku and p.unit = u.unit
                            ORDER BY p.sku
                            LIMIT ? OFFSET ?'''
                
                products_result = self.cursor.execute(sql, (limit, offset))


            products = [
                ProductsDialogModel(sku=p[0], product_name=p[1], price=p[2], 
                                    stock=p[3], unit=p[4], created_at=p[5]) 
                for p in products_result
            ]

            return ResponseMessage.ok(
                message = "Products fetched successfully!",
                data = {
                    'products': products,
                    'total_count': total_count,
                }
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        