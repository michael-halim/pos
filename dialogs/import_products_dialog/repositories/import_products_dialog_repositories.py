from typing import List
from connect_db import DatabaseConnection

from dialogs.import_products_dialog.models.import_products_dialog_models import ImportProductsModel

from response.response_message import ResponseMessage
from generals.cache_manager import CacheManager


class ImportProductsDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.cache_manager = CacheManager()
        self.products_cache = self.cache_manager.get_cache('products')


    def import_products_to_database(self, products: List[ImportProductsModel], batch_size: int = 100, category_set: set = set(), supplier_set: set = set()) -> ResponseMessage:
        try:
            if not products:
                return ResponseMessage(False, "No products to import")
            
            self.cursor.execute('BEGIN TRANSACTION')
            total_products = len(products)
            total_imported = 0
            

            # Get Category and Supplier Data
            categories_map = self.get_category_map()
            suppliers_map = self.get_supplier_map()


            # Process Category Data
            for cat_key in categories_map:
                if cat_key in category_set:
                    category_set.remove(cat_key)


            # Process Supplier Data
            for sup_key in suppliers_map:
                if sup_key in supplier_set:
                    supplier_set.remove(sup_key)


            # Insert in Bulk Category Data
            sql = '''INSERT INTO categories (category_name) VALUES (?)'''
            self.cursor.executemany(sql, [(category,) for category in category_set])


            # Insert in Bulk Supplier Data
            sql = '''INSERT INTO suppliers (supplier_name) VALUES (?)'''
            self.cursor.executemany(sql, [(supplier,) for supplier in supplier_set])


            # Get Latest Category and Supplier Data
            categories_map = self.get_category_map()
            suppliers_map = self.get_supplier_map()


            categories_detail = []

            # Process in batches
            for i in range(0, total_products, batch_size):
                batch = products[i:i + batch_size]
                current_batch_size = len(batch)

                # Prepare batch insert query
                sql = '''
                    INSERT INTO products 
                    (sku, product_name, barcode, unit, cost_price, price, stock, remarks, category_id, supplier_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                
                # Prepare data for executemany
                values = []
                for product in batch:
                    # Handle category_id
                    category_id = None
                    if product.category:
                        category_id = int(categories_map[product.category])
                    
                    # Handle supplier_id
                    supplier_id = None
                    if product.supplier:
                        supplier_id = int(suppliers_map[product.supplier])

                    values.append((
                        product.sku,
                        product.product_name,
                        product.barcode,
                        product.unit,
                        product.cost_price,
                        product.price,
                        product.stock,
                        product.remarks,
                        category_id,
                        supplier_id
                    ))

                    if category_id:
                        categories_detail.append((category_id, product.sku,))
                

                # Execute the batch insert
                self.cursor.executemany(sql, values)
                total_imported += current_batch_size


            # Insert in Bulk Category Detail Data
            sql = '''INSERT INTO product_categories_detail (category_id, sku) VALUES (?, ?)'''

            self.cursor.executemany(sql, categories_detail)

            self.db.commit()

            self.cache_manager.invalidate('products')

            return ResponseMessage(True, f"Successfully imported {total_imported} products")
            

        except Exception as e:
            self.db.rollback()
            error_message = f"Error importing products: {str(e)}"
            return ResponseMessage(False, error_message)
        

    def get_category_map(self) -> dict:
        try:
            sql = '''SELECT category_id, category_name FROM categories'''
        
            self.cursor.execute(sql)
        
            categories_result = self.cursor.fetchall()
        
            return {category[1]: category[0] for category in categories_result}
        
        except Exception as e:
            return {}
        
    
    def get_supplier_map(self) -> dict:
        try:
            sql = '''SELECT supplier_id, supplier_name FROM suppliers'''
        
            self.cursor.execute(sql)
        
            suppliers_result = self.cursor.fetchall()
        
            return {supplier[1]: supplier[0] for supplier in suppliers_result}
        
        except Exception as e:
            return {}
        