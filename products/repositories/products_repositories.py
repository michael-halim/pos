from connect_db import DatabaseConnection

from products.models.products_models import ProductsModel, ProductsExportModel

from generals.permission_manager import PermissionManager
from generals.constants import PERM_R_PRODUCTS, PERM_D_PRODUCTS, PERM_E_PRODUCTS
from generals.messages import ERR_PERM_R_PRODUCTS, ERR_PERM_D_PRODUCTS, ERR_PERM_E_PRODUCTS
from response.response_message import ResponseMessage   

class ProductsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()


    def get_products(self, search_text: str = None, limit: int = 100):
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_R_PRODUCTS)

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
            elif limit:
                sql = '''SELECT sku, product_name, cost_price, price, stock, unit, remarks 
                            FROM products
                            ORDER BY sku
                            LIMIT ?'''
                products_result = self.cursor.execute(sql, (limit,))

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
        

    # Export
    # ===============
    def get_products_for_export(self, limit: int = 1000):
        if not self.permission_manager.has_permission(PERM_E_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_E_PRODUCTS)

        try:
            products_result = []
            if limit:
                sql = '''SELECT sku, product_name, barcode, unit, cost_price, price, stock, remarks 
                            FROM products
                            ORDER BY sku
                            LIMIT ?'''
                products_result = self.cursor.execute(sql, (limit,))

            else:
                sql = '''SELECT sku, product_name, barcode, unit, cost_price, price, stock, remarks 
                            FROM products
                            ORDER BY sku
                            LIMIT 1000'''
                products_result = self.cursor.execute(sql)


            products = [
                ProductsExportModel(sku=r[0], product_name=r[1], barcode=r[2], unit=r[3], 
                                    cost_price=r[4], price=r[5], stock=r[6], remarks=r[7]) 
                for r in products_result
            ]

            return ResponseMessage.ok(
                message="Products fetched successfully!",
                data=products
            )
        
        except Exception as e:
            self.db.rollback()
            return ResponseMessage.fail(message=f"Error: {str(e)}")
            

    