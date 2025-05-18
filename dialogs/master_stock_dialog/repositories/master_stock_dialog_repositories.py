from connect_db import DatabaseConnection
import json
from datetime import datetime

from dialogs.suppliers_dialog.models.suppliers_dialog_models import SupplierModel
from dialogs.master_stock_dialog.models.master_stock_dialog_models import PurchasingHistoryTableItemModel, MasterStockModel, CategoriesModel

from response.response_message import ResponseMessage
from generals.constants import (
    PERM_C_PRODUCTS, PERM_U_PRODUCTS, PERM_D_PRODUCTS,
)
from generals.messages import ( 
    ERR_PERM_C_PRODUCTS, ERR_PERM_U_PRODUCTS, ERR_PERM_D_PRODUCTS,
)
from generals.permission_manager import PermissionManager
from generals.cache_manager import CacheManager


class MasterStockDialogRepository:
    def __init__(self):
        self.db = DatabaseConnection().get_connection()
        self.cursor = self.db.cursor()
        self.permission_manager = PermissionManager()
        self.cache_manager = CacheManager()
        self.products_cache = self.cache_manager.get_cache('products')
    

    def get_suppliers(self, search_text: str = ''):
        try:
            suppliers_result = []
            if search_text:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks 
                            FROM suppliers
                            WHERE supplier_id LIKE ? OR supplier_name LIKE ? OR supplier_address LIKE ? OR supplier_city LIKE ? OR supplier_phone LIKE ? OR supplier_remarks LIKE ?'''
                
                search_text = f'%{search_text}%'
                suppliers_result = self.cursor.execute(sql, (search_text, search_text, search_text, search_text, search_text, search_text))
            else:
                sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks 
                            FROM suppliers'''

                suppliers_result = self.cursor.execute(sql)

            suppliers = [
                SupplierModel(supplier_id=r[0], supplier_name=r[1], supplier_address=r[2], supplier_city=r[3], supplier_phone=r[4], supplier_remarks=r[5]) 
                for r in suppliers_result
            ]

            return ResponseMessage.ok(
                message="Suppliers fetched successfully!",
                data=suppliers
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_supplier_by_id(self, supplier_id: str):
        try:
            sql = '''SELECT supplier_id, supplier_name, supplier_address, supplier_city, supplier_phone, supplier_remarks 
                        FROM suppliers 
                        WHERE supplier_id = ?
                        LIMIT 1'''
            
            self.cursor.execute(sql, (supplier_id,))
            result = self.cursor.fetchone()

            if result:
                return ResponseMessage.ok(
                    message="Success", 
                    data=SupplierModel(supplier_id=result[0], supplier_name=result[1], supplier_address=result[2], 
                                       supplier_city=result[3], supplier_phone=result[4], supplier_remarks=result[5])
                )

            return ResponseMessage.ok(message="Category not found!", data=None)

        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
       

    def get_purchasing_history_by_sku(self, sku: str):
        try:
            sql = '''SELECT ph.created_at, s.supplier_name, dph.qty, dph.unit, dph.price, 
                            dph.discount_rp, dph.discount_pct, dph.subtotal
                    FROM detail_purchasing_history dph 
                    JOIN purchasing_history ph on ph.purchasing_id = dph.purchasing_id
                    LEFT JOIN suppliers s on s.supplier_id = ph.supplier_id
                    WHERE dph.sku = ?
                    ORDER BY ph.created_at DESC'''
            
            self.cursor.execute(sql, (sku,))

            purchasing_history_results = self.cursor.fetchall()

            if purchasing_history_results:
                purchasing_history = [
                    PurchasingHistoryTableItemModel(created_at=ph[0], 
                                                    supplier_name=ph[1], 
                                                    qty=ph[2], 
                                                    unit=ph[3], 
                                                    price=ph[4], 
                                                    discount_rp=ph[5], 
                                                    discount_pct=ph[6], 
                                                    subtotal=ph[7]) 
                    for ph in purchasing_history_results
                ]

                return ResponseMessage.ok(
                    message="Purchasing history fetched successfully!",
                    data=purchasing_history
                )
            
            return ResponseMessage.ok(
                message="Purchasing history not found!",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")
        

    def get_product_by_sku(self, sku: str):
        try:
            sql = '''SELECT p.product_name, p.barcode, p.category_id, p.supplier_id, p.unit, p.cost_price, 
                            p.price, p.stock, p.remarks, c.category_name, s.supplier_name, 
                            p.last_price, p.average_price
                    FROM products p
                    LEFT JOIN categories c on c.category_id = p.category_id
                    LEFT JOIN suppliers s on s.supplier_id = p.supplier_id
                    WHERE p.sku = ?
                    LIMIT 1'''
            
            self.cursor.execute(sql, (sku,))

            result = self.cursor.fetchone()
            if result:
                return ResponseMessage.ok(
                    message="Success",
                    data=MasterStockModel(
                        sku=sku,
                        product_name=result[0],
                        barcode=result[1],
                        category_id=result[2],
                        supplier_id=result[3],
                        unit=result[4],
                        cost_price=result[5],
                        price=result[6],
                        stock=result[7],
                        remarks=result[8],
                        category_name=result[9],
                        supplier_name=result[10],
                        last_price=result[11],
                        average_price=result[12]
                    )
                )
            
            return ResponseMessage.ok(
                message="Success",
                data=None
            )
        
        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def get_category_by_id(self, category_id: str):
        try:
            sql = '''SELECT category_id, category_name 
                        FROM categories 
                        WHERE category_id = ?
                        LIMIT 1'''
            
            self.cursor.execute(sql, (category_id,))
            result = self.cursor.fetchone()

            if result:
                return ResponseMessage.ok(
                    message="Success", 
                    data=CategoriesModel(category_id=result[0], category_name=result[1])
                )

            return ResponseMessage.ok(message="Category not found!", data=None)
        

        except Exception as e:
            return ResponseMessage.fail(message=f"Error: {str(e)}")


    def submit_master_stock(self, master_stock: MasterStockModel):
        if not self.permission_manager.has_permission(PERM_C_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_C_PRODUCTS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Insert master stock
            sql = '''INSERT INTO products (sku, product_name, barcode, category_id, 
                                        supplier_id, unit, cost_price, price, stock, 
                                        remarks, last_price, average_price) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            
            self.cursor.execute(sql, (master_stock.sku, master_stock.product_name, master_stock.barcode, 
                                      master_stock.category_id, master_stock.supplier_id, master_stock.unit, 
                                      master_stock.cost_price, master_stock.price, master_stock.stock, 
                                      master_stock.remarks, 0, 0))
            
            # Create Json Object
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            master_stock_data = {
                'sku': master_stock.sku,
                'product_name': master_stock.product_name,
                'barcode': master_stock.barcode,
                'category_id': master_stock.category_id,
                'supplier_id': master_stock.supplier_id,
                'unit': master_stock.unit,
                'cost_price': master_stock.cost_price,
                'price': master_stock.price,
                'stock': master_stock.stock,
                'remarks': master_stock.remarks,
                'last_price': 0,
                'average_price': 0
            }

            # Insert Log
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Master Stock {master_stock.sku} created', f'Master Stock {master_stock.sku} created successfully!', 'C', 
                                        None, json.dumps(master_stock_data), today, self.permission_manager.get_user_id()))
            
            # Commit Transaction
            self.db.commit()

            # Invalidate cache
            self.cache_manager.invalidate('products')
            
            return ResponseMessage.ok(message="Master stock submitted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to submit master stock: {str(e)}")


    def update_master_stock(self, master_stock: MasterStockModel):
        if not self.permission_manager.has_permission(PERM_U_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_U_PRODUCTS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')

            # Get the old master stock data
            sql = '''SELECT product_name, barcode, category_id, supplier_id, unit, cost_price, price, stock, remarks 
                        FROM products 
                        WHERE sku = ?
                        LIMIT 1'''
            self.cursor.execute(sql, (master_stock.sku,))
            result = self.cursor.fetchone()

            if not result:
                self.db.rollback()
                return ResponseMessage.fail(message="Can't Update Master Stock, SKU not found!")

            old_data = {
                'product_name': result[0],
                'barcode': result[1],
                'category_id': result[2],
                'supplier_id': result[3],
                'unit': result[4],
                'cost_price': result[5],
                'price': result[6],
                'stock': result[7],
                'remarks': result[8]
            }


            # Update master stock
            sql = '''UPDATE products 
                    SET product_name = ?, barcode = ?, category_id = ?, supplier_id = ?, 
                        unit = ?, cost_price = ?, price = ?, stock = ?, remarks = ? 
                    WHERE sku = ?'''
            
            self.cursor.execute(sql, (master_stock.product_name, master_stock.barcode, master_stock.category_id, 
                                      master_stock.supplier_id, master_stock.unit, master_stock.cost_price, 
                                      master_stock.price, master_stock.stock, master_stock.remarks, master_stock.sku))
            

            # Create Json Object
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data = {
                'product_name': master_stock.product_name,
                'barcode': master_stock.barcode,
                'category_id': master_stock.category_id,
                'supplier_id': master_stock.supplier_id,
                'unit': master_stock.unit,
                'cost_price': master_stock.cost_price,
                'price': master_stock.price,
                'stock': master_stock.stock,
                'remarks': master_stock.remarks
            }

            # Insert Log
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Master Stock {master_stock.sku} updated', f'Master Stock {master_stock.sku} updated successfully!', 'U', 
                                        json.dumps(old_data), json.dumps(new_data), today, self.permission_manager.get_user_id()))
            
            # Commit Transaction  
            self.db.commit()

            # Invalidate cache
            self.cache_manager.invalidate('products')

            return ResponseMessage.ok(message="Master stock updated successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to update master stock: {str(e)}")


    def delete_master_stock_by_sku(self, sku: str):
        if not self.permission_manager.has_permission(PERM_D_PRODUCTS):
            return ResponseMessage.fail(message=ERR_PERM_D_PRODUCTS)

        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Get the old master stock data
            sql = '''SELECT product_name, barcode, category_id, supplier_id, unit, cost_price, price, stock, remarks 
                        FROM products 
                        WHERE sku = ?
                        LIMIT 1'''
            self.cursor.execute(sql, (sku,))
            result = self.cursor.fetchone()

            old_data = {
                'product_name': result[0],
                'barcode': result[1],
                'category_id': result[2],
                'supplier_id': result[3],
                'unit': result[4],
                'cost_price': result[5],
                'price': result[6],
                'stock': result[7],
                'remarks': result[8]
            }

            # Delete master stock
            sql = '''DELETE FROM products WHERE sku = ?'''
            self.cursor.execute(sql, (sku,))

            # Create Json Object
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
            # Insert Log
            sql = '''INSERT INTO logs (log_name, log_description, log_type, old_data, 
                                        new_data, created_at, created_by) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            self.cursor.execute(sql, (f'Master Stock {sku} deleted', f'Master Stock {sku} deleted successfully!', 'D', 
                                        json.dumps(old_data), None, today, self.permission_manager.get_user_id()))

            # Commit Transaction  
            self.db.commit()

            # Invalidate cache
            self.cache_manager.invalidate('products')

            return ResponseMessage.ok(message="Master stock deleted successfully!")

        except Exception as e:
            # If any error occurs, rollback all changes
            self.db.rollback()
            return ResponseMessage.fail(message=f"Failed to delete master stock: {str(e)}")
        