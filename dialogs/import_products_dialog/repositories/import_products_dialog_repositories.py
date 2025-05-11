from typing import List
from connect_db import DatabaseConnection

from dialogs.import_products_dialog.models.import_products_dialog_models import ImportProductsModel

from response.response_message import ResponseMessage

class ImportProductsDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        

    def import_products_to_database(self, products: List[ImportProductsModel], batch_size: int = 100) -> ResponseMessage:
        try:
            if not products:
                return ResponseMessage(False, "No products to import")
            
            total_products = len(products)
            total_imported = 0
            
            # Process in batches
            for i in range(0, total_products, batch_size):
                batch = products[i:i + batch_size]
                current_batch_size = len(batch)

                self.cursor.execute('BEGIN TRANSACTION')

                # Prepare batch insert query
                sql = '''
                    INSERT INTO products 
                    (sku, product_name, barcode, unit, cost_price, price, stock, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                
                # Prepare data for executemany
                values = []
                for product in batch:
                    values.append((
                        product.sku,
                        product.product_name,
                        product.barcode,
                        product.unit,
                        product.cost_price,
                        product.price,
                        product.stock,
                        product.remarks
                    ))
                
                # Execute the batch insert
                self.cursor.executemany(sql, values)
                self.db.commit()
                
                total_imported += current_batch_size
            
            return ResponseMessage(True, f"Successfully imported {total_imported} products")
            
        except Exception as e:
            self.db.rollback()
            error_message = f"Error importing products: {str(e)}"
            return ResponseMessage(False, error_message)