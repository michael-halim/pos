from connect_db import DatabaseConnection

from products.models.products_models import ProductsModel, ProductsExportModel

from generals.permission_manager import PermissionManager
from generals.cache_manager import CacheManager
from generals.constants import PERM_R_PRODUCTS, PERM_D_PRODUCTS, PERM_E_PRODUCTS
from generals.messages import ERR_PERM_R_PRODUCTS, ERR_PERM_D_PRODUCTS, ERR_PERM_E_PRODUCTS
from response.response_message import ResponseMessage   


class ProductsRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        self.cache_manager = CacheManager()
        self.products_cache = self.cache_manager.get_cache('products')


    def get_products(self, search_text: str = None, limit: int = 100, offset: int = 50):
        if not self.permission_manager.has_permission(PERM_R_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_R_PRODUCTS)

        try:
            # Create cache key based on parameters, handling None values
            cache_key = f"products_{search_text if search_text else 'all'}_{limit}_{offset}"
            
            # Try to get from cache first
            cached_result = self.products_cache.get_value(cache_key)
            if cached_result:
                print(f'cached_result: {cached_result}')
                return ResponseMessage.ok(
                    message="Products fetched from cache successfully!",
                    data=cached_result
                )

            total_count = 0
            products_result = []
            if search_text:
                search_text = f'%{search_text}%'

                sql = '''SELECT COUNT(*)
                        FROM products
                        WHERE sku LIKE ? OR product_name LIKE ? OR cost_price LIKE ? OR price LIKE ? 
                                OR stock LIKE ? OR unit LIKE ? OR remarks LIKE ?'''
                
                total_count = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, 
                                                            search_text, search_text, search_text)).fetchone()[0]
                
                sql = '''SELECT sku, product_name, cost_price, price, stock, unit, remarks 
                            FROM products
                            WHERE sku LIKE ? OR product_name LIKE ? OR cost_price LIKE ? OR price LIKE ? 
                                    OR stock LIKE ? OR unit LIKE ? OR remarks LIKE ?
                            ORDER BY sku
                            LIMIT ? OFFSET ?'''
                
                products_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, 
                                                            search_text, search_text, search_text, limit, offset))
            else:
                sql = '''SELECT COUNT(*) FROM products'''
                total_count = self.cursor.execute(sql).fetchone()[0]

                sql = '''SELECT sku, product_name, cost_price, price, stock, unit, remarks 
                            FROM products
                            ORDER BY sku
                            LIMIT ? OFFSET ?'''
                products_result = self.cursor.execute(sql, (limit, offset))

            products = [
                ProductsModel(sku=r[0], product_name=r[1], cost_price=r[2], 
                              price=r[3], stock=r[4], unit=r[5], remarks=r[6]) 
                for r in products_result
            ]

            result_data = {
                'products': products,
                'total_count': total_count,
            }

            # Cache the result
            self.products_cache.set_value(cache_key, result_data)

            return ResponseMessage.ok(
                message="Products fetched successfully!",
                data=result_data
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

            # Invalidate cache
            self.cache_manager.invalidate('products')

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
                            LIMIT 10000'''
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
            