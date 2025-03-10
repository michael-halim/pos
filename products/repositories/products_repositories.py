from connect_db import DatabaseConnection

from products.models.products_models import ProductsModel

from generals.permission_manager import PermissionManager
from generals.constants import PERM_D_PRODUCTS
from generals.messages import ERR_PERM_D_PRODUCTS
from response.response_message import ResponseMessage   

class ProductsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_products(self, search_text: str = None):
        try:
            products_result = []
            if search_text:
                sql = '''SELECT sku, product_name, cost_price, price, stock, unit, remarks 
                            FROM products
                            WHERE sku LIKE ? OR product_name LIKE ? OR cost_price LIKE ? OR price LIKE ? 
                                    OR stock LIKE ? OR unit LIKE ? OR remarks LIKE ?
                            ORDER BY sku'''
                
                search_text = f'%{search_text}%'
                products_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, 
                                                            search_text, search_text, search_text))
            else:
                sql = '''SELECT sku, product_name, cost_price, price, stock, unit, remarks 
                            FROM products
                            ORDER BY sku
                            LIMIT 100'''
                products_result = self.cursor.execute(sql)

            products = [
                ProductsModel(sku=r[0], product_name=r[1], cost_price=r[2], 
                              price=r[3], stock=r[4], unit=r[5], remarks=r[6]) 
                for r in products_result
            ]

            return ResponseMessage.ok(
                message="Products fetched successfully!",
                data=products
            )
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def delete_products_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_D_PRODUCTS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Delete product
            sql = '''DELETE FROM products WHERE sku = ?'''
            self.cursor.execute(sql, (sku,))

            # Commit Transaction  
            self.db.commit()

            return ResponseMessage.ok(message="Product deleted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to delete product: {str(e)}")